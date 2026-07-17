#!/usr/bin/env python3
"""Minimal BM25 for maestro skill search."""

from __future__ import annotations

from collections import defaultdict
from math import log

from text_normalization import search_tokens


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avgdl = 0.0
        self.idf: dict[str, float] = {}
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.n = 0

    def tokenize(self, text: str) -> list[str]:
        return search_tokens(text)

    def fit(self, documents: list[str]) -> None:
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.n = len(self.corpus)
        if self.n == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.n
        self.doc_freqs = defaultdict(int)
        self.idf = {}

        for doc in self.corpus:
            seen: set[str] = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.n - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query: str) -> list[tuple[int, float]]:
        if self.n == 0:
            return []
        query_tokens = self.tokenize(query)
        scores: list[tuple[int, float]] = []

        for idx, doc in enumerate(self.corpus):
            total = 0.0
            doc_len = self.doc_lengths[idx]
            term_freqs: dict[str, int] = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token not in self.idf:
                    continue
                tf = term_freqs[token]
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                total += idf * numerator / denominator

            scores.append((idx, total))

        return sorted(scores, key=lambda x: x[1], reverse=True)
