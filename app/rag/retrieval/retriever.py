import json
from pathlib import Path
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer
from app.rag.retrieval.reranker import rerank_results
from app.rag.retrieval.similarity import cosine_similarity
from app.rag.retrieval.scoring import (
    calculate_keyword_score,
    calculate_metadata_score,
    calculate_final_score,
)

class JsonRetriever:
    """
    embedding similarity만 사용하는 것이 아니라,
    keyword와 metadata를 함께 반영하는 Hybrid Retriever 방식 사용
    """

    def __init__(
        self,
        embedding_file_path: str,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        self.embedding_file_path = Path(embedding_file_path)
        self.model_name = model_name
        self.chunks = self._load_chunks()
        self.model = SentenceTransformer(model_name)

    def _load_chunks(self) -> List[Dict[str, Any]]:

        if not self.embedding_file_path.exists():
            raise FileNotFoundError(
                f"Embedding 파일을 찾을 수 없습니다: {self.embedding_file_path}"
            )

        with self.embedding_file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("chunk_embeddings.json은 리스트 형태여야 합니다.")

        valid_chunks = []

        for index, item in enumerate(data):
            if "embedding" not in item:
                raise ValueError(f"{index}번째 chunk에 embedding 필드가 없습니다.")

            if "text" not in item:
                raise ValueError(f"{index}번째 chunk에 text 필드가 없습니다.")

            valid_chunks.append(item)

        if valid_chunks:
            stored_model = valid_chunks[0].get("embedding_metadata", {}).get("model_name")
            if stored_model and stored_model != self.model_name:
                raise ValueError(
                    f"저장된 임베딩 모델({stored_model})과 "
                    f"현재 모델({self.model_name})이 다릅니다. "
                    f"re-ingestion이 필요합니다."
                )

        return valid_chunks

    def _embed_query(self, query: str) -> List[float]:

        if not query.strip():
            raise ValueError("query는 비어 있을 수 없습니다.")

        embedding = self.model.encode(query)

        return embedding.tolist()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        query와 가장 유사한 chunk Top-K를 반환

        최종 점수는 다음 요소를 함께 반영한다.
            1. embedding_score: query embedding과 chunk embedding의 의미적 유사도
            2. keyword_score: query에 chunk metadata의 keyword가 포함되어 있는 정도
            3. metadata_score: chunk의 priority, category 기반 중요도
        """

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k는 1 이상의 정수여야 합니다: {top_k}")

        query_embedding = self._embed_query(query)

        scored_chunks = []

        for chunk in self.chunks:
            metadata = chunk.get("metadata", {})
            keywords = metadata.get("keywords", [])

            embedding_score = cosine_similarity(query_embedding, chunk["embedding"])
            keyword_score = calculate_keyword_score(query, keywords)
            metadata_score = calculate_metadata_score(metadata)

            final_score = calculate_final_score(
                embedding_score=embedding_score,
                keyword_score=keyword_score,
                metadata_score=metadata_score,
            )

            scored_chunks.append(
                {
                    "final_score": final_score,
                    "embedding_score": embedding_score,
                    "keyword_score": keyword_score,
                    "metadata_score": metadata_score,
                    "text": chunk["text"],
                    "metadata": metadata,
                    "chunk_id": chunk.get("chunk_id"),
                }
            )

        scored_chunks.sort(key=lambda item: item["final_score"], reverse=True)

        candidate_results = scored_chunks[: top_k * 3]

        reranked_results = rerank_results(
            query=query,
            results=candidate_results,
        )

        return reranked_results[:top_k]