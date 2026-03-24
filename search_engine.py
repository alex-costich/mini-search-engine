"""
search_engine.py — Terraria Wiki Search Engine
Components:
  - Text processing pipeline (tokenize, lowercase, stopwords, stemming)
  - Inverted index with posting lists
  - BM25 ranking
  - Levenshtein spell correction
"""

import json
import math
import time
import re
from typing import Optional
from collections import defaultdict

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "as", "be", "was",
    "are", "were", "been", "has", "have", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "not",
    "this", "that", "these", "those", "their", "they", "them", "then",
    "than", "so", "if", "when", "which", "who", "what", "how", "all",
    "also", "into", "up", "out", "about", "after", "before", "between",
    "through", "during", "while", "each", "other", "more", "most", "such",
    "no", "only", "same", "any", "both", "over", "under", "again", "there",
    "once", "he", "she", "we", "you", "i", "my", "his", "her", "our",
    "your", "its", "one", "two", "three", "new", "use", "used", "using",
}

def stem(word: str) -> str:
    if len(word) <= 3:
        return word

    # plurals and -ed/-ing
    if word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies"):
        word = word[:-3] + "i"
    elif word.endswith("ss"):
        pass
    elif word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]

    # -ed / -ing
    if word.endswith("eed"):
        pass
    elif word.endswith("ed") and len(word) > 4:
        word = word[:-2]
    elif word.endswith("ing") and len(word) > 5:
        word = word[:-3]

    # -ational → -ate, -ization → -ize, -ness/-ment/-ful
    suffixes = [
        ("ational", "ate"), ("tional", "tion"), ("ization", "ize"),
        ("fulness", "ful"), ("ousness", "ous"), ("iveness", "ive"),
        ("ness", ""), ("ment", ""), ("ful", ""), ("ous", ""),
        ("ive", ""), ("ly", ""), ("er", ""), ("al", ""),
    ]
    for suffix, replacement in suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) > 2:
            word = word[: -len(suffix)] + replacement
            break

    return word


def tokenize(text: str) -> list:
    """Lowercase, extract alpha tokens, remove stopwords, stem."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 1]


def tokenize_raw(text: str) -> list:
    """Tokenize without stemming (used for spell correction vocab)."""
    return [t for t in re.findall(r"[a-z]+", text.lower())
            if t not in STOP_WORDS and len(t) > 1]

class InvertedIndex:
    def __init__(self):
        # term → {doc_id: frequency}
        self.index: dict[str, dict[str, int]] = defaultdict(dict)
        self.doc_lengths: dict[str, int] = {}   # doc_id → token, count
        self.doc_meta: dict[str, dict] = {}      # doc_id → {title, url, text, category}
        self.vocab: set = set()                  # unstemmed vocabulary for spell correction
        self.total_docs: int = 0
        self.avg_doc_length: float = 0.0

    def build(self, corpus: list) -> None:
        """Index all documents in the corpus."""
        for doc in corpus:
            doc_id = doc["id"]
            text = doc["title"] + " " + doc["text"]

            # Store metadata
            self.doc_meta[doc_id] = {
                "title": doc["title"],
                "url": doc["url"],
                "text": doc["text"],
                "category": doc.get("category", "General"),
            }

            # Build unstemmed vocab for spell correction
            for raw_token in tokenize_raw(text):
                self.vocab.add(raw_token)

            # Stemmed tokens for index
            tokens = tokenize(text)
            self.doc_lengths[doc_id] = len(tokens)

            # Count term frequencies
            freq: dict[str, int] = defaultdict(int)
            for token in tokens:
                freq[token] += 1

            # Add to posting lists
            for term, count in freq.items():
                self.index[term][doc_id] = count

        self.total_docs = len(corpus)
        self.avg_doc_length = (
            sum(self.doc_lengths.values()) / self.total_docs
            if self.total_docs > 0 else 0
        )

    @property
    def vocab_size(self) -> int:
        return len(self.index)
    
# t t t

# t - term - token

# tf -> more appearances in one doc, higher relevance against others
# idf -> less appearances across doc, higher relevance (more appearances, less relevance)
# dln -> longer documents have more terms but are not necessarily more relevant

class BM25:
    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b

    def idf(self, term: str) -> float:
        """Inverse document frequency."""
        df = len(self.index.index.get(term, {}))
        if df == 0:
            return 0.0
        n = self.index.total_docs
        return math.log((n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query_tokens: list, doc_id: str) -> float:
        """BM25 score for a document given query tokens."""
        score = 0.0
        dl = self.index.doc_lengths.get(doc_id, 0)
        avgdl = self.index.avg_doc_length

        for term in query_tokens:
            tf = self.index.index.get(term, {}).get(doc_id, 0)
            if tf == 0:
                continue
            idf = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / avgdl)
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> list:
        """
        Return top_k results as list of dicts with score and metadata.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Only score docs that contain at least one query term
        candidate_docs: set = set()
        for token in query_tokens:
            candidate_docs.update(self.index.index.get(token, {}).keys())

        scores = []
        for doc_id in candidate_docs:
            s = self.score(query_tokens, doc_id)
            if s > 0:
                scores.append((doc_id, s))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, s in scores[:top_k]:
            meta = self.index.doc_meta[doc_id]
            results.append({
                "doc_id": doc_id,
                "title": meta["title"],
                "url": meta["url"],
                "score": round(s, 4),
                "text": meta["text"],
                "category": meta["category"],
            })

        return results


# SPELL CORRECTION
"""
Levenshtein distance measures:
How many edits are needed to turn one word into another

Allowed edits:
insert a letter
delete a letter
replace a letter
"""

def levenshtein(a: str, b: str) -> int:
    """Compute edit distance between two strings."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    # Use two-row DP to save memory
    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i, ca in enumerate(a, 1):
        curr[0] = i
        for j, cb in enumerate(b, 1):
            if ca == cb:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev, curr = curr, prev

    return prev[len(b)]


def spell_correct(query: str, vocab: set, max_distance: int = 3) -> Optional[str]:
    """
    For each query term not in vocab, find the closest vocab word.
    Returns a corrected query string, or None if no corrections needed.
    """
    raw_tokens = re.findall(r"[a-z]+", query.lower())
    corrected = []
    made_correction = False

    for token in raw_tokens:
        if token in vocab or len(token) <= 2:
            corrected.append(token)
            continue

        # Find closest match within max_distance
        best_word = None
        best_dist = max_distance + 1

        for vocab_word in vocab:
            # Quick length filter to skip obviously distant words
            if abs(len(vocab_word) - len(token)) > max_distance:
                continue
            d = levenshtein(token, vocab_word)
            if d < best_dist:
                best_dist = d
                best_word = vocab_word

        if best_word and best_dist <= max_distance:
            corrected.append(best_word)
            if best_word != token:
                made_correction = True
        else:
            corrected.append(token)

    if made_correction:
        return " ".join(corrected)
    return None


class SearchEngine:
    def __init__(self, corpus_path: str = "corpus.json"):
        self.corpus_path = corpus_path
        self.index = InvertedIndex()
        self.bm25 = None
        self._load()

    def _load(self):
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        self.index.build(corpus)
        self.bm25 = BM25(self.index)

    def search(self, query: str, top_k: int = 10) -> dict:
        """
        Main search method. Returns results + spell suggestion + timing.
        """
        start = time.time()

        # Spell correction
        suggestion = spell_correct(query, self.index.vocab)

        results = self.bm25.search(query, top_k=top_k)

        # If no results and there's a suggestion, search with correction too
        suggested_results = []
        if not results and suggestion:
            suggested_results = self.bm25.search(suggestion, top_k=top_k)

        elapsed = round((time.time() - start) * 1000, 2)  # ms

        return {
            "query": query,
            "suggestion": suggestion,
            "results": results if results else suggested_results,
            "used_suggestion": not results and bool(suggestion),
            "total_results": len(results) if results else len(suggested_results),
            "search_time_ms": elapsed,
            "stats": {
                "total_docs": self.index.total_docs,
                "vocab_size": self.index.vocab_size,
                "avg_doc_length": round(self.index.avg_doc_length, 1),
            }
        }

    def get_stats(self) -> dict:
        return {
            "total_docs": self.index.total_docs,
            "vocab_size": self.index.vocab_size,
            "avg_doc_length": round(self.index.avg_doc_length, 1),
            "total_terms": sum(
                len(postings) for postings in self.index.index.values()
            ),
        }




# TEST

if __name__ == "__main__":
    print("Loading search engine...")
    engine = SearchEngine("corpus.json")

    stats = engine.get_stats()
    print(f"\nIndex stats:")
    print(f"  Documents  : {stats['total_docs']}")
    print(f"  Vocab size : {stats['vocab_size']}")
    print(f"  Avg doc len: {stats['avg_doc_length']} tokens")

    test_queries = [
        "how to defeat moon lord",
        "best sword weapon hardmode",
        "corruption biome enemies",
        "terrablade crafting",       # should suggest terra blade
        "skelton boss",              # should suggest skeletron
    ]

    print("\n--- Search Tests ---")
    for q in test_queries:
        result = engine.search(q, top_k=3)
        print(f"\nQuery: '{q}'")
        if result["suggestion"] and result["suggestion"] != q:
            marker = "(auto-used)" if result["used_suggestion"] else "(suggestion)"
            print(f"  Spell correction: '{result['suggestion']}' {marker}")
        if result["results"]:
            for r in result["results"]:
                print(f"  [{r['score']}] {r['title']} ({r['category']})")
        else:
            print("  No results found.")
        print(f"  Search time: {result['search_time_ms']}ms")