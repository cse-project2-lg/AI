from typing import List
from sentence_transformers import SentenceTransformer


class Embedder:
    """
    텍스트를 임베딩 벡터로 변환
    (한국어/영어가 섞인 SRS 문서를 고려해 multilingual sentence-transformer 모델을 사용)
    """

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:

        embedding = self.model.encode(text, normalize_embeddings=True)

        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=True,
        )

        return embeddings.tolist()