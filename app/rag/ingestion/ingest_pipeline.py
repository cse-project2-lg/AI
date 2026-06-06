import json
import logging
from pathlib import Path
from typing import List

from app.rag.ingestion.loader import load_document
from app.rag.ingestion.cleaner import clean_document
from app.rag.ingestion.chunker import split_into_chunks
from app.rag.ingestion.metadata import enrich_chunk_metadata
from app.rag.schemas.chunk import Chunk

logger = logging.getLogger(__name__)


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
    failed_files = []

    input_dir = Path(input_dir_path)

    if not input_dir.exists():
        raise FileNotFoundError(f"입력 폴더를 찾을 수 없습니다: {input_dir_path}")

    for file_path in sorted(input_dir.rglob("*")):
        if file_path.suffix.lower() not in [".txt", ".docx"]:
            continue

        try:
            document = load_document(str(file_path))
            document = clean_document(document)

            chunks = split_into_chunks(document)
            chunks = enrich_chunk_metadata(chunks)

            logger.info("%s chunk 수: %d", file_path.name, len(chunks))

            all_chunks.extend(chunks)

        except Exception:
            logger.exception("문서 처리 실패: %s", file_path)
            failed_files.append(str(file_path))

    if failed_files:
        logger.warning("처리 실패한 파일 %d개: %s", len(failed_files), failed_files)

    _save_chunks(all_chunks, output_file_path)

    return all_chunks

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    chunks = run_ingestion_directory()
    logger.info("%d개의 chunk를 저장했습니다.", len(chunks))