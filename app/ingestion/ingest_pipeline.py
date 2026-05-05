import json
from pathlib import Path
from typing import List

from app.ingestion.loader import load_document
from app.ingestion.cleaner import clean_document
from app.ingestion.chunker import split_into_chunks
from app.ingestion.metadata import enrich_chunk_metadata
from app.schemas.chunk import Chunk


def run_ingestion_pipeline(
    input_file_path: str,
    output_file_path: str = "data/chunks/chunks.json",
) -> List[Chunk]:
    """
    RAG 지식베이스 생성을 위한 ingestion pipeline을 실행
        1. 원본 문서 로드
        2. 텍스트 정제
        3. chunk 분할
        4. metadata 보강
        5. chunks.json 저장
    """

    document = load_document(input_file_path)
    document = clean_document(document)

    chunks = split_into_chunks(document)
    chunks = enrich_chunk_metadata(chunks)

    _save_chunks(chunks, output_file_path)

    return chunks


def _save_chunks(chunks: List[Chunk], output_file_path: str) -> None:

    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chunk_dicts = [chunk.to_dict() for chunk in chunks]

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(chunk_dicts, file, ensure_ascii=False, indent=2)

def run_ingestion_directory(
    input_dir_path: str = "data/raw",
    output_file_path: str = "data/chunks/chunks.json",
) -> List[Chunk]:
    all_chunks = []

    input_dir = Path(input_dir_path)

    if not input_dir.exists():
        raise FileNotFoundError(f"입력 폴더를 찾을 수 없습니다: {input_dir_path}")

    for file_path in sorted(input_dir.rglob("*")):
        print("FOUND:", file_path)

        if file_path.suffix.lower() not in [".txt", ".docx"]:
            continue

        document = load_document(str(file_path))
        document = clean_document(document)

        chunks = split_into_chunks(document)
        chunks = enrich_chunk_metadata(chunks)

        print(file_path.name, "chunk 수:", len(chunks))

        all_chunks.extend(chunks)
        
    _save_chunks(all_chunks, output_file_path)

    return all_chunks

if __name__ == "__main__":
    chunks = run_ingestion_directory()
    print(f"{len(chunks)}개의 chunk를 저장했습니다.")