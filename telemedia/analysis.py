"""Deterministic content analysis utilities."""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Sequence, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schemas import AnalysisResult, KeywordCount

_TOKEN_REGEX = re.compile(r"[\w\-']{2,}")
_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "however",
    "because",
    "about",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "as",
    "is",
    "it",
    "this",
    "that",
    "these",
    "those",
    "are",
    "was",
    "were",
    "be",
    "by",
    "from",
    "at",
    "have",
    "has",
    "had",
    "not",
    "we",
    "you",
    "they",
    "their",
    "our",
    "your",
}


class ContentAnalyzer:
    """Runs keyword statistics and cosine similarity analysis on plain text."""

    def __init__(self, max_features: int = 1000, top_n: int = 10) -> None:
        self.max_features = max_features
        self.top_n = top_n

    def _tokenize(self, text: str) -> List[str]:
        tokens = _TOKEN_REGEX.findall(text.lower())
        return [token for token in tokens if token not in _STOPWORDS]

    def analyze_content(self, text: str) -> Tuple[AnalysisResult, Counter[str]]:
        """Return keyword frequency statistics for the provided text."""

        if not text:
            empty_result = AnalysisResult(
                total_tokens=0, unique_tokens=0, top_keywords=[])
            return empty_result, Counter()

        tokens = self._tokenize(text)
        counts: Counter[str] = Counter(tokens)
        top_keywords = [KeywordCount(word=word, count=count)
                        for word, count in counts.most_common(self.top_n)]
        analysis = AnalysisResult(
            total_tokens=len(tokens),
            unique_tokens=len(counts),
            top_keywords=top_keywords,
        )
        return analysis, counts

    def compute_similarity(self, texts: Sequence[str]) -> List[List[float]]:
        """Return a cosine similarity matrix from the supplied texts."""

        texts = [text for text in texts if text]
        if not texts:
            return []
        if len(texts) == 1:
            return [[1.0]]

        processed = [" ".join(self._tokenize(text)) for text in texts]
        if not any(processed):
            return self._identity_matrix(len(texts))

        vectorizer = TfidfVectorizer(max_features=self.max_features)
        matrix = vectorizer.fit_transform(processed)
        similarity = cosine_similarity(matrix)
        return similarity.round(4).tolist()

    @staticmethod
    def _identity_matrix(size: int) -> List[List[float]]:
        return [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]
