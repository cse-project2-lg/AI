import json
from pathlib import Path
from typing import List, Dict, Any

from app.embeddings.embedder import Embedder


def create_chunk_embeddings(
    chunk_file_path: str = "data/chunks/chunks.json",
    output_file_path: str = "data/chunks/chunk_embeddings.json",
) -> List[Dict[str, Any]]:
    
    chunks = _load_chunks(chunk_file_path)

    if not chunks:
        raise ValueError("chunk 데이터가 비어 있습니다.")

    texts = [chunk["text"] for chunk in chunks]

    embedder = Embedder()
    embeddings = embedder.embed_texts(texts)

    embedded_chunks = []

    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunk = {
            **chunk,
            "embedding": embedding,
            "embedding_metadata": {
                "model_name": embedder.model_name,
                "embedding_dimension": len(embedding),
                "normalized": True,
            },
        }

        embedded_chunks.append(embedded_chunk)

    _save_embeddings(embedded_chunks, output_file_path)

    return embedded_chunks


def _load_chunks(chunk_file_path: str) -> List[Dict[str, Any]]:

    path = Path(chunk_file_path)

    if not path.exists():
        raise FileNotFoundError(f"chunk 파일을 찾을 수 없습니다: {chunk_file_path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_embeddings(
    embedded_chunks: List[Dict[str, Any]],
    output_file_path: str,
) -> None:

    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(embedded_chunks, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    create_chunk_embeddings()