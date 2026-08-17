"""Small TF-IDF baseline used only for Seismic's self-authored evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from seismic.models import ArtifactRecord, RepositoryGraph


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """One baseline retrieval result with a transparent cosine score."""

    logical_key: str
    score: float


class SimilarityIndex:
    """TF-IDF index over the same snapshot artifacts evaluated by the graph."""

    def __init__(self, graph: RepositoryGraph) -> None:
        self.artifacts = [artifact for artifact in graph.artifacts if _document(artifact).strip()]
        self.by_key = {artifact.logical_key: artifact for artifact in self.artifacts}
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[A-Za-z_][A-Za-z0-9_.]+\b",
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(
            [_document(artifact) for artifact in self.artifacts]
        )

    def rank(self, target: str, limit: int) -> list[SimilarityResult]:
        """Rank artifacts by similarity to the changed artifact's own source text."""

        changed = self.by_key.get(target)
        if changed is None:
            return []
        query = self.vectorizer.transform([_document(changed)])
        similarities = linear_kernel(query, self.matrix).ravel()
        ranked = sorted(
            (
                SimilarityResult(artifact.logical_key, float(similarities[index]))
                for index, artifact in enumerate(self.artifacts)
                if artifact.logical_key != target and similarities[index] > 0
            ),
            key=lambda item: (-item.score, item.logical_key),
        )
        return ranked[:limit]


def _document(artifact: ArtifactRecord) -> str:
    return " ".join(
        (
            artifact.logical_key,
            artifact.path,
            artifact.qualified_name,
            artifact.kind,
            artifact.text,
        )
    )
