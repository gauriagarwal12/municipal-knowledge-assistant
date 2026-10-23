
"""Lightweight lexical retrieval over municipal PDF documents."""

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from document_loader import DocumentChunk, load_pdf_directory


class MunicipalRetriever:
    def __init__(
        self,
        data_dir: str | Path,
        top_k: int = 10,
        min_score: float = 0.055,
    ):
        self.data_dir = Path(data_dir)
        self.top_k = top_k
        self.min_score = min_score

        self.chunks: list[DocumentChunk] = load_pdf_directory(
            self.data_dir
        )

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        self.matrix = self.vectorizer.fit_transform(
            [chunk.text for chunk in self.chunks]
        )

    @property
    def document_count(self) -> int:
        return len({chunk.source for chunk in self.chunks})

    def retrieve(self, question: str) -> list[dict]:
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        ranked = scores.argsort()[::-1]

        results = []
        seen = set()

        for idx in ranked:
            score = float(scores[idx])

            if score < self.min_score:
                break

            chunk = self.chunks[int(idx)]
            key = (
                chunk.source,
                chunk.page,
                chunk.text[:120],
            )

            if key in seen:
                continue

            seen.add(key)

            results.append(
                {
                    "id": f"S{len(results) + 1}",
                    "text": chunk.text,
                    "source": chunk.source,
                    "page": chunk.page,
                    "score": round(score, 4),
                }
            )

            if len(results) >= self.top_k:
                break

        return results

    def retrieve_page(
        self,
        source_filename: str,
        page_number: int,
        question: str,
    ) -> list[dict]:
        """Retrieve the most relevant chunks from one specific PDF page."""

        page_chunks = [
            chunk
            for chunk in self.chunks
            if chunk.source == source_filename
            and chunk.page == page_number
        ]

        if not page_chunks:
            return []

        query = self.vectorizer.transform([question])
        page_texts = [chunk.text for chunk in page_chunks]
        page_matrix = self.vectorizer.transform(page_texts)

        scores = cosine_similarity(query, page_matrix).ravel()
        ranked = scores.argsort()[::-1]

        results = []

        for idx in ranked:
            chunk = page_chunks[int(idx)]

            results.append(
                {
                    "id": f"S{len(results) + 1}",
                    "text": chunk.text,
                    "source": chunk.source,
                    "page": chunk.page,
                    "score": round(float(scores[idx]), 4),
                }
            )

        return results