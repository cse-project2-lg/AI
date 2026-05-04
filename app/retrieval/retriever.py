import json
from pathlib import Path
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer

from app.retrieval.similarity import cosine_similarity

# JSON 파일로부터 chunk 임베딩 데이터를 로드하여 사용자 query와 유사한 chunk를 검색하는 클래스
class JsonRetriever:

    def __init__(
        self,
        embedding_file_path: str,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.embedding_file_path = Path(embedding_file_path)
        self.model = SentenceTransformer(model_name)
        self.chunks = self._load_chunks()

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

        return valid_chunks


    # 사용자 query를 임베딩 벡터로 변환
    def _embed_query(self, query: str) -> List[float]:


        if not query.strip():
            raise ValueError("query는 비어 있을 수 없습니다.")

        embedding = self.model.encode(query)

        return embedding.tolist()


    # query 임베딩과 각 chunk 임베딩 간의 cosine similarity를 계산하여 유사한 chunk를 반환
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:

        query_embedding = self._embed_query(query)

        scored_chunks = []

        for chunk in self.chunks:
            score = cosine_similarity(query_embedding, chunk["embedding"])

            scored_chunks.append(
                {
                    "score": score,
                    "text": chunk["text"],
                    "metadata": chunk.get("metadata", {}),
                    "chunk_id": chunk.get("chunk_id"),
                }
            )

        scored_chunks.sort(key=lambda item: item["score"], reverse=True)

        return scored_chunks[:top_k]