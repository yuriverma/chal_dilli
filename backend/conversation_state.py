#!/usr/bin/env python3
"""
CHAL DILLI - Conversation state

/chat is otherwise stateless: every call is parsed on its own, so a follow-up
like "and from there to Saket?" has nothing to resolve "there" against. This
module keeps a small, bounded, expiring record of what a conversation has
already established - the last route, the last area - and rewrites elliptical
follow-ups into fully specified queries before the intent router sees them.

This is deliberately not a language model. It covers the handful of follow-up
shapes that are unambiguous in practice and passes everything else through
untouched, so the worst case is exactly the previous behaviour.

The rewritten query is echoed back to the caller so the assumption is visible
rather than silent: if we guess the wrong anchor, the user can see why.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Tuple

# A conversation is forgotten after this long without a message. Long enough to
# survive someone being interrupted mid-trip-planning, short enough that the
# store stays small.
SESSION_TTL_SECONDS = 2 * 60 * 60

# Hard cap on tracked conversations, oldest evicted first. The state is a few
# hundred bytes each, so this is trivial memory - the point of the cap is that
# a crawler POSTing a fresh conversation_id every request cannot grow it
# without bound.
MAX_SESSIONS = 500


@dataclass
class ConversationState:
    """What a conversation has established so far."""

    last_origin: Optional[str] = None
    last_destination: Optional[str] = None
    last_area: Optional[str] = None
    last_mode: Optional[str] = None  # "metro" or "bus"
    updated_at: float = field(default_factory=time.time)

    def anchor(self) -> Optional[str]:
        """The place a follow-up most likely means by "there".

        The destination of the last route, because that is where the user now
        conceptually is. Falls back to the last food area for conversations
        that never asked for a route.
        """
        return self.last_destination or self.last_area

    def has_route(self) -> bool:
        return bool(self.last_origin and self.last_destination)


class ConversationStore:
    """Bounded, expiring, thread-safe conversation store.

    In-memory on purpose. The app runs a single uvicorn worker (each worker
    would otherwise build its own GTFS graph), so there is exactly one store
    and no need for Redis. The tradeoff is that conversations reset when the
    container restarts or wakes from sleep, which for follow-up resolution
    degrades to "the first question has to name its stations" - acceptable.
    """

    def __init__(
        self,
        ttl_seconds: int = SESSION_TTL_SECONDS,
        max_sessions: int = MAX_SESSIONS,
    ):
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._lock = threading.Lock()
        self._sessions: "OrderedDict[str, ConversationState]" = OrderedDict()

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex

    def get(self, conversation_id: Optional[str]) -> ConversationState:
        """Return the state for this conversation, or a blank one.

        Unknown and expired ids both yield blank state rather than an error:
        a stale id from a browser tab left open overnight should behave like a
        new conversation, not a failure.
        """
        if not conversation_id:
            return ConversationState()

        now = time.time()
        with self._lock:
            self._expire_locked(now)
            state = self._sessions.get(conversation_id)
            if state is None:
                return ConversationState()
            # Mark as most-recently-used for the LRU cap.
            self._sessions.move_to_end(conversation_id)
            return state

    def save(self, conversation_id: str, state: ConversationState) -> None:
        if not conversation_id:
            return
        state.updated_at = time.time()
        with self._lock:
            self._sessions[conversation_id] = state
            self._sessions.move_to_end(conversation_id)
            self._expire_locked(state.updated_at)
            while len(self._sessions) > self._max:
                self._sessions.popitem(last=False)

    def _expire_locked(self, now: float) -> None:
        """Drop timed-out sessions. Caller must hold the lock.

        Entries are ordered by last use, so this stops at the first live one.
        """
        cutoff = now - self._ttl
        while self._sessions:
            oldest_id, oldest = next(iter(self._sessions.items()))
            if oldest.updated_at >= cutoff:
                break
            self._sessions.pop(oldest_id, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)


# ========== FOLLOW-UP SHAPES ==========

# "there" as an origin. Split by language because the replacement has to keep
# the sentence parseable by the route patterns downstream: English wants
# "from <station>", Hinglish wants "<station> se". Substituting "from X" into
# "wahan se saket kaise jaun" yields "from X saket kaise jaun", which matches
# none of the route patterns and silently dead-ends.
_THERE_AS_ORIGIN_EN = re.compile(r"\b(?:from\s+there|from\s+that\s+station)\b")

_THERE_AS_ORIGIN_HI = re.compile(
    r"\b(?:there\s+se|wahan?\s+se|vahan?\s+se|udhar\s+se|uske\s+baad)\b"
)

# "there" as a place to look around:
#   "food near there", "wahan ke paas momos", "there ke paas khana"
_THERE_AS_PLACE = re.compile(
    r"\b(?:"
    r"(?:near|around|next\s+to)\s+there|"
    r"there\s+(?:ke\s+)?p?aas|"
    r"wahan?\s+(?:ke\s+)?p?aas|vahan?\s+(?:ke\s+)?p?aas"
    r")\b"
)

# A message that is nothing but a mode switch, so the stations must come from
# the previous turn: "and by bus?", "metro se?", "aur dtc", "what about bus".
# Anchored at both ends on purpose - if the user named a station anywhere in
# the message we must not override it with remembered state.
_BARE_MODE_SWITCH = re.compile(
    r"^\s*(?:and|aur|ok|okay|toh|so|but|par)?\s*"
    r"(?:what\s+about\s+|how\s+about\s+|kya\s+)?"
    r"(?:by\s+|via\s+|through\s+)?"
    r"(?P<mode>bus|dtc|metro|train|subway)"
    r"\s*(?:se|by|mein|me|ka|se\s+jaun|se\s+jaana)?\s*"
    r"[?.!]*\s*$",
    re.IGNORECASE,
)

_MODE_CANONICAL = {
    "bus": "bus",
    "dtc": "bus",
    "metro": "metro",
    "train": "metro",
    "subway": "metro",
}

# A message that is nothing but a destination, continuing the journey:
#   "to rajiv chowk", "and to saket?", "saket tak"
# Both ends are anchored so a fully specified "dwarka to saket" cannot match.
_LEADING_FILLER = r"(?:and|aur|ok|okay|toh|so|then|phir|but|par)?\s*"
_BARE_DESTINATION_TO = re.compile(
    r"^\s*" + _LEADING_FILLER + r"(?:what\s+about\s+|how\s+about\s+)?"
    r"(?:to|till|until)\s+(?P<dest>[a-z0-9 .'&/-]{2,40}?)\s*[?.!]*\s*$",
    re.IGNORECASE,
)
_BARE_DESTINATION_TAK = re.compile(
    r"^\s*" + _LEADING_FILLER + r"(?P<dest>[a-z0-9 .'&/-]{2,40}?)\s+tak\s*[?.!]*\s*$",
    re.IGNORECASE,
)

# A captured destination that still contains a connective means the message
# already named its own origin: "nehru place se hauz khas tak" is a complete
# route, not a follow-up, and must not be rewritten. The destination patterns
# allow spaces (station names have them), so without this guard the greedy
# capture swallows the origin too.
_HAS_CONNECTIVE = re.compile(r"\b(?:se|from|to|tak|till|until)\b", re.IGNORECASE)

# Words the intent router keys off. A rewrite can be slot-complete and still
# route to the fallback if it names no mode, so the remembered mode is
# reinstated whenever the rewritten text has lost it.
_MODE_WORDS = re.compile(r"\b(?:metro|train|subway|bus|dtc)\b", re.IGNORECASE)
_STRIP_FILLER = re.compile(r"^\s*(?:and|aur|ok|okay|toh|so|then|phir|but|par)\s+", re.IGNORECASE)


@dataclass
class Rewrite:
    """The outcome of resolving a follow-up."""

    query: str
    note: Optional[str] = None
    # True when the turn asks about a journey already established rather than
    # establishing a new place. A mode switch ("and by bus?") must not move the
    # anchor: the bus and metro networks have different stop names, and letting
    # a fuzzy bus match overwrite a known metro station corrupts the anchor for
    # every later follow-up.
    preserve_anchor: bool = False

    def __bool__(self) -> bool:
        return self.note is not None


def _with_mode(query: str, state: ConversationState) -> str:
    """Reinstate the remembered travel mode when the query names none."""
    if _MODE_WORDS.search(query):
        return query
    return f"{state.last_mode or 'metro'} {_STRIP_FILLER.sub('', query)}"


def rewrite_followup(query: str, state: ConversationState) -> Rewrite:
    """Rewrite an elliptical follow-up into a self-contained query.

    Only fires when there is an anchor to resolve against, so a first message
    mentioning "there" is passed through rather than mangled.
    """
    anchor = state.anchor()
    if not anchor:
        return Rewrite(query)

    # "and from there to saket" -> "metro from Rajiv Chowk to saket"
    if _THERE_AS_ORIGIN_EN.search(query):
        rewritten = _THERE_AS_ORIGIN_EN.sub(f"from {anchor}", query, count=1)
        return Rewrite(_with_mode(rewritten, state), f'"there" -> {anchor}')

    # "wahan se saket kaise jaun" -> "Hauz Khas se saket kaise jaun"
    if _THERE_AS_ORIGIN_HI.search(query):
        rewritten = _THERE_AS_ORIGIN_HI.sub(f"{anchor} se", query, count=1)
        return Rewrite(rewritten, f'"wahan" -> {anchor}')

    # "food near there" -> "food near Rajiv Chowk". No mode: this is a place
    # lookup, and injecting "metro" would send it to the routing pipeline.
    if _THERE_AS_PLACE.search(query):
        rewritten = _THERE_AS_PLACE.sub(f"near {anchor}", query, count=1)
        return Rewrite(rewritten, f'"there" -> {anchor}')

    # "and by bus?" -> "bus from Dwarka to Rajiv Chowk"
    if state.has_route():
        match = _BARE_MODE_SWITCH.match(query)
        if match:
            mode = _MODE_CANONICAL[match.group("mode").lower()]
            return Rewrite(
                f"{mode} from {state.last_origin} to {state.last_destination}",
                f"{mode}: {state.last_origin} to {state.last_destination}",
                preserve_anchor=True,
            )

    # "to rajiv chowk" / "saket tak" -> continue from where the last one ended
    for pattern in (_BARE_DESTINATION_TO, _BARE_DESTINATION_TAK):
        match = pattern.match(query)
        if match:
            destination = match.group("dest").strip()
            if _HAS_CONNECTIVE.search(destination):
                continue
            # Guard against the anchor and the destination being the same place,
            # which would ask the router for a zero-length journey.
            if destination and destination.lower() != anchor.lower():
                mode = state.last_mode or "metro"
                return Rewrite(
                    f"{mode} from {anchor} to {destination}",
                    f"assumed from {anchor}",
                )

    return Rewrite(query)


def resolve_open_origin(
    query: str, route: dict, state: ConversationState
) -> Rewrite:
    """Rewrite a destination-only query to start from the last destination.

    Backstop for the phrasings the bare-destination patterns above do not
    catch ("how to reach saket", "which line goes to saket"). The route
    extractor reports those as origin "current location" - a literal it has no
    way to resolve - so the query dead-ends. Where a conversation has already
    established a route, the natural reading is that the journey continues from
    wherever the last one ended.

    Rewrites the query text rather than patching the parsed dict, because the
    router re-parses the query downstream and would otherwise discard the fix.
    """
    anchor = state.anchor()
    if not anchor:
        return Rewrite(query)
    if route.get("from") not in (None, "", "current location"):
        return Rewrite(query)

    destination = (route.get("to") or "").strip()
    if not destination or destination.lower() == anchor.lower():
        return Rewrite(query)

    mode = state.last_mode or "metro"
    return Rewrite(
        f"{mode} from {anchor} to {destination}", f"assumed from {anchor}"
    )
