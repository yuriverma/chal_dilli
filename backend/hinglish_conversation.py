#!/usr/bin/env python3
"""
Hinglish Conversation Manager
Loads the HuggingFace Hinglish-Everyday-Conversations-1M dataset and
returns suitable small-talk replies using TF-IDF similarity.

Dataset: Abhishekcr448/Hinglish-Everyday-Conversations-1M
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import threading
import random
import os
import csv

try:
    from datasets import load_dataset  # type: ignore
except Exception:
    load_dataset = None  # graceful import

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None


def _normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    # Common Hinglish shorthand expansions
    replacements = {
        "rha": "raha",
        "rhe": "rahe",
        "rhi": "rahi",
        "karliya": "kar liya",
        "karliya?": "kar liya?",
        "karliye": "kar liye",
        "kar diya": "kar diya",
        "kesa": "kaisa",
        "aisa": "aisa",
        "h": "hai",
        "kya chal rha": "kya chal raha",
        "kya chal rh": "kya chal raha",
        "kya kar rha": "kya kar raha",
        "mood kaisa": "mood kaisa",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s


@dataclass
class ConversationEntry:
    input_text: str
    output_text: str


class HinglishConversationManager:
    def __init__(self, max_rows: int = 30000, seed: int = 42):
        self.max_rows = max_rows
        self.seed = seed
        self._entries: List[ConversationEntry] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        self._lock = threading.Lock()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._cache_csv = os.path.normpath(os.path.join(base_dir, "..", "data", "hinglish_smalltalk.csv"))

    def is_available(self) -> bool:
        return load_dataset is not None and TfidfVectorizer is not None

    def _load_from_csv_cache(self) -> bool:
        if not os.path.exists(self._cache_csv) or TfidfVectorizer is None:
            return False
        try:
            inputs: List[str] = []
            outputs: List[str] = []
            with open(self._cache_csv, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    inp = _normalize_text(row.get("input", ""))
                    out = row.get("output", "")
                    if inp and out:
                        inputs.append(inp); outputs.append(out)
            if not inputs:
                return False
            self._entries = [ConversationEntry(i, o) for i, o in zip(inputs, outputs)]
            # Use min_df=1 for tiny local cache
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=1.0)
            self._matrix = self._vectorizer.fit_transform(inputs)
            return True
        except Exception as e:
            print(f"Failed to load Hinglish cache CSV: {e}")
            return False

    def load_index(self) -> bool:
        """Load a subset of the dataset and build a TF-IDF index. Returns True on success."""
        if not self.is_available():
            # try cache CSV
            return self._load_from_csv_cache()
        with self._lock:
            if self._entries:
                return True
            try:
                ds = load_dataset("Abhishekcr448/Hinglish-Everyday-Conversations-1M", split="train")
                # Randomly sample up to max_rows for memory efficiency
                total = len(ds)
                random.seed(self.seed)
                idxs = list(range(total))
                random.shuffle(idxs)
                take = min(self.max_rows, total)
                picked = set(idxs[:take])
                inputs: List[str] = []
                outputs: List[str] = []
                for i, row in enumerate(ds):
                    if i not in picked:
                        continue
                    inp = _normalize_text(str(row.get("input", "")))
                    out = str(row.get("output", ""))
                    if not inp or not out:
                        continue
                    inputs.append(inp)
                    outputs.append(out)
                self._entries = [ConversationEntry(i, o) for i, o in zip(inputs, outputs)]
                # Build TF-IDF
                self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95)
                self._matrix = self._vectorizer.fit_transform(inputs)
                # Save cache for offline use
                try:
                    os.makedirs(os.path.dirname(self._cache_csv), exist_ok=True)
                    with open(self._cache_csv, "w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=["input", "output"])
                        w.writeheader()
                        for i, o in zip(inputs, outputs):
                            w.writerow({"input": i, "output": o})
                except Exception as e:
                    print(f"Warning: couldn't write Hinglish cache CSV: {e}")
                return True
            except Exception as e:
                print(f"Failed to load Hinglish dataset: {e}")
                # try cache CSV if available
                return self._load_from_csv_cache()

    def reply(self, user_text: str, top_k: int = 1, min_sim: float = 0.18) -> Optional[str]:
        """Return the best small-talk reply if similarity passes the threshold."""
        if not self._entries or self._vectorizer is None or self._matrix is None:
            ok = self.load_index()
            if not ok:
                return None
        query = _normalize_text(user_text)
        if not query:
            return None
        try:
            q_vec = self._vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self._matrix).ravel()
            if sims.size == 0:
                return None
            best_idx = int(sims.argmax())
            best_sim = float(sims[best_idx])
            if best_sim < min_sim:
                return None
            return self._entries[best_idx].output_text
        except Exception as e:
            print(f"Hinglish reply failed: {e}")
            return None


