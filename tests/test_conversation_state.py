#!/usr/bin/env python3
"""
Unit tests for conversation state and follow-up resolution.

Deliberately free of GTFS: these exercise the rewrite rules and the store
directly, so the whole file runs in milliseconds.
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from conversation_state import (  # noqa: E402
    ConversationState,
    ConversationStore,
    resolve_open_origin,
    rewrite_followup,
)


def routed(origin="Dwarka", destination="Rajiv Chowk", mode="metro"):
    return ConversationState(
        last_origin=origin, last_destination=destination, last_mode=mode
    )


class TestAnchor(unittest.TestCase):
    def test_destination_is_the_anchor(self):
        self.assertEqual(routed().anchor(), "Rajiv Chowk")

    def test_falls_back_to_food_area(self):
        state = ConversationState(last_area="Vasant Kunj")
        self.assertEqual(state.anchor(), "Vasant Kunj")

    def test_blank_state_has_no_anchor(self):
        self.assertIsNone(ConversationState().anchor())


class TestThereAsOrigin(unittest.TestCase):
    def test_english_from_there(self):
        r = rewrite_followup("and from there to saket", routed())
        self.assertEqual(r.query, "metro from Rajiv Chowk to saket")
        self.assertIn("Rajiv Chowk", r.note)

    def test_hinglish_wahan_se_keeps_se(self):
        """The Hinglish form must stay parseable by the route patterns.

        Substituting "from X" here would yield "from X saket kaise jaun",
        which matches none of them.
        """
        r = rewrite_followup("wahan se saket kaise jaun", routed())
        self.assertEqual(r.query, "Rajiv Chowk se saket kaise jaun")

    def test_udhar_se(self):
        r = rewrite_followup("udhar se hauz khas", routed())
        self.assertTrue(r.query.startswith("Rajiv Chowk se"))

    def test_no_anchor_leaves_query_alone(self):
        r = rewrite_followup("and from there to saket", ConversationState())
        self.assertEqual(r.query, "and from there to saket")
        self.assertIsNone(r.note)


class TestThereAsPlace(unittest.TestCase):
    def test_food_near_there(self):
        r = rewrite_followup("food near there", routed())
        self.assertEqual(r.query, "food near Rajiv Chowk")

    def test_place_lookup_gets_no_mode_word(self):
        """Injecting "metro" would divert a food query into routing."""
        r = rewrite_followup("food near there", routed())
        self.assertNotIn("metro", r.query)


class TestModeSwitch(unittest.TestCase):
    def test_and_by_bus(self):
        r = rewrite_followup("and by bus?", routed())
        self.assertEqual(r.query, "bus from Dwarka to Rajiv Chowk")

    def test_dtc_maps_to_bus(self):
        r = rewrite_followup("aur dtc", routed())
        self.assertTrue(r.query.startswith("bus from"))

    def test_mode_switch_preserves_the_anchor(self):
        """A mode switch re-asks a known journey; it establishes no new place.

        Bus stop names and metro station names do not correspond, so allowing a
        fuzzy bus match to move the anchor corrupts every later follow-up.
        """
        r = rewrite_followup("and by bus?", routed())
        self.assertTrue(r.preserve_anchor)

    def test_normal_rewrite_does_not_preserve_anchor(self):
        r = rewrite_followup("and from there to saket", routed())
        self.assertFalse(r.preserve_anchor)

    def test_needs_a_full_route_to_switch_mode(self):
        state = ConversationState(last_area="Vasant Kunj")
        r = rewrite_followup("and by bus?", state)
        self.assertIsNone(r.note)


class TestBareDestination(unittest.TestCase):
    def test_to_station(self):
        r = rewrite_followup("to rajiv chowk", routed(destination="Saket"))
        self.assertEqual(r.query, "metro from Saket to rajiv chowk")

    def test_tak_form(self):
        r = rewrite_followup("saket tak", routed())
        self.assertEqual(r.query, "metro from Rajiv Chowk to saket")

    def test_carries_the_remembered_mode(self):
        r = rewrite_followup("to saket", routed(mode="bus"))
        self.assertTrue(r.query.startswith("bus from"))

    def test_same_place_is_not_a_journey(self):
        r = rewrite_followup("to rajiv chowk", routed(destination="Rajiv Chowk"))
        self.assertIsNone(r.note)


class TestExplicitQueriesUntouched(unittest.TestCase):
    """The rules must never override something the user actually said."""

    def test_full_route_english(self):
        for q in (
            "dwarka to saket",
            "bus from nehru place to saket",
            "how do i get from dwarka to cp",
        ):
            with self.subTest(q=q):
                self.assertIsNone(rewrite_followup(q, routed()).note)

    def test_full_route_hinglish(self):
        for q in ("dwarka se saket kaise jaun", "nehru place se hauz khas tak"):
            with self.subTest(q=q):
                self.assertIsNone(rewrite_followup(q, routed()).note)

    def test_unrelated_message(self):
        for q in ("what's the weather", "hello", "best momos in dwarka"):
            with self.subTest(q=q):
                self.assertIsNone(rewrite_followup(q, routed()).note)


class TestResolveOpenOrigin(unittest.TestCase):
    def test_fills_the_placeholder_origin(self):
        r = resolve_open_origin(
            "how to reach saket", {"from": "current location", "to": "saket"}, routed()
        )
        self.assertEqual(r.query, "metro from Rajiv Chowk to saket")

    def test_leaves_a_real_origin_alone(self):
        r = resolve_open_origin(
            "dwarka to saket", {"from": "dwarka", "to": "saket"}, routed()
        )
        self.assertIsNone(r.note)

    def test_needs_an_anchor(self):
        r = resolve_open_origin(
            "how to reach saket",
            {"from": "current location", "to": "saket"},
            ConversationState(),
        )
        self.assertIsNone(r.note)


class TestStore(unittest.TestCase):
    def test_round_trip(self):
        store = ConversationStore()
        cid = store.new_id()
        store.save(cid, routed())
        self.assertEqual(store.get(cid).last_destination, "Rajiv Chowk")

    def test_unknown_id_gives_blank_state(self):
        store = ConversationStore()
        self.assertIsNone(store.get("never-seen").anchor())

    def test_missing_id_gives_blank_state(self):
        self.assertIsNone(ConversationStore().get(None).anchor())

    def test_conversations_are_isolated(self):
        store = ConversationStore()
        store.save("a", routed(destination="Rajiv Chowk"))
        store.save("b", routed(destination="Saket"))
        self.assertEqual(store.get("a").last_destination, "Rajiv Chowk")
        self.assertEqual(store.get("b").last_destination, "Saket")

    def test_expired_session_is_forgotten(self):
        store = ConversationStore(ttl_seconds=1)
        state = routed()
        state.updated_at = time.time() - 5
        # Write past the public API so the stale timestamp survives save().
        store._sessions["old"] = state
        self.assertIsNone(store.get("old").anchor())

    def test_cap_evicts_oldest_first(self):
        store = ConversationStore(max_sessions=3)
        for i in range(5):
            store.save(f"c{i}", routed(destination=f"Stop {i}"))
        self.assertEqual(len(store), 3)
        self.assertIsNone(store.get("c0").anchor())
        self.assertEqual(store.get("c4").last_destination, "Stop 4")

    def test_ids_are_unique(self):
        self.assertEqual(len({ConversationStore.new_id() for _ in range(200)}), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
