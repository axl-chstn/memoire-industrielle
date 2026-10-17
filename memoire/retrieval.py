"""BM25 local et recherche hybride avec embeddings E5 facultatifs."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from memoire.documents import Passage, references

MODEL_NAME = "intfloat/multilingual-e5-small"
STOPWORDS = set("a au aux avec ce ces cette dans de des du elle en est et il la le les leur leurs on ou par pas pour que quel quelle quelles quels qui se sur un une vos vous nous notre sont ete etait ont ne qu d l s t y comment pourquoi deja fait faire avoir peut tout tous dont entre apres avant lors concernant concerne concernant fois".split())


def tokens(text: str) -> list[str]:
    clean = "".join(c for c in unicodedata.normalize("NFKD", text.lower())
                    if not unicodedata.combining(c))
    words = re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", clean)
    return [w[:-1] if len(w) > 4 and w.endswith("s") else w
            for w in words if len(w) > 1 and w not in STOPWORDS]


class Encoder(Protocol):
    def encode(self, texts: list[str], **kwargs) -> np.ndarray: ...


@dataclass(frozen=True)
class Hit:
    passage: Passage
    score: float
    lexical_score: float
    semantic_score: float | None = None


def has_reference(text: str, reference: str) -> bool:
    # P01 peut désigner P01_RA ; P01 ne doit pas sélectionner P010.
    pattern = r"(?<![A-Za-z0-9])" + re.escape(reference) + r"(?=$|[^A-Za-z0-9])"
    return bool(re.search(pattern, text, re.I))


class SearchIndex:
    def __init__(self, passages: list[Passage], encoder: Encoder | None = None):
        if not passages:
            raise ValueError("Ajoute au moins un document contenant du texte.")
        self.passages = passages
        self.encoder = encoder
        self.counts = [Counter(tokens(p.text)) for p in passages]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average_length = max(sum(self.lengths) / len(passages), 1)
        frequencies = Counter(term for c in self.counts for term in c)
        self.idf = {term: math.log(1 + (len(passages) - n + 0.5) / (n + 0.5))
                    for term, n in frequencies.items()}
        self.embeddings = None
        if encoder is not None:
            self.embeddings = np.asarray(encoder.encode(
                [f"passage: {p.text}" for p in passages],
                normalize_embeddings=True, show_progress_bar=False,
            ))

    def search(self, question: str, *, top_k: int = 4, equipment: str | None = None,
               min_semantic: float = 0.78) -> list[Hit]:
        if top_k < 1 or not question.strip():
            return []
        candidates = [i for i, p in enumerate(self.passages)
                      if equipment is None or equipment in p.equipment]
        # Comparaisons : OU entre références de même nature, ET entre catégories.
        groups: dict[str, list[str]] = {}
        for reference in references(question):
            kind = ("incident" if reference.startswith("INC") else
                    "rapport" if reference.startswith("RAP") else
                    "composant" if "_" in reference else "équipement")
            groups.setdefault(kind, []).append(reference)
        for group in groups.values():
            candidates = [i for i in candidates if any(has_reference(
                self.passages[i].text + " " + self.passages[i].source, ref) for ref in group)]
        if not candidates:
            return []
        lexical: dict[int, float] = {}
        for i in candidates:
            total = 0.0
            for term in set(tokens(question)):
                frequency = self.counts[i][term]
                denominator = frequency + 1.5 * (
                    0.25 + 0.75 * self.lengths[i] / self.average_length)
                if frequency:
                    total += self.idf[term] * frequency * 2.5 / denominator
            lexical[i] = total
        semantic: dict[int, float] = {}
        if self.encoder is not None:
            query = np.asarray(self.encoder.encode(
                [f"query: {question}"], normalize_embeddings=True,
                show_progress_bar=False,
            ))[0]
            semantic = {i: float(self.embeddings[i] @ query) for i in candidates}
        ranks: Counter = Counter()
        for scores, threshold in ((lexical, 0.0), (semantic, min_semantic)):
            ordered = sorted((i for i in candidates if scores.get(i, 0) > threshold),
                             key=lambda i: scores[i], reverse=True)
            for rank, i in enumerate(ordered, 1):
                ranks[i] += 1 / (60 + rank)
        return [Hit(self.passages[i], ranks[i], lexical[i], semantic.get(i))
                for i in sorted(ranks, key=lambda i: ranks[i], reverse=True)[:top_k]]
