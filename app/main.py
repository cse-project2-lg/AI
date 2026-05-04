from app.ingestion.ingest_pipeline import run_ingestion_pipeline
from app.embeddings.embedding_service import create_chunk_embeddings


def main():
    input_file_path = "data/raw/srs/요구사항분석_v2.0.docx"
    chunk_file_path = "data/chunks/chunks.json"
    embedding_file_path = "data/chunks/chunk_embeddings.json"

    chunks = run_ingestion_pipeline(
        input_file_path=input_file_path,
        output_file_path=chunk_file_path,
    )

    embedded_chunks = create_chunk_embeddings(
        chunk_file_path=chunk_file_path,
        output_file_path=embedding_file_path,
    )

    print("Ingestion + Embedding 완료")
    print("chunk 저장 위치:", chunk_file_path)
    print("embedding 저장 위치:", embedding_file_path)
    print("총 chunk 개수:", len(chunks))
    print("총 embedding 개수:", len(embedded_chunks))

    sample = embedded_chunks[0]

    print("\n샘플 embedding 정보")
    print("-" * 50)
    print("chunk_id:", sample["chunk_id"])
    print("section_title:", sample["metadata"]["section_title"])
    print("embedding_dimension:", sample["embedding_metadata"]["embedding_dimension"])
    print("embedding 앞 5개 값:", sample["embedding"][:5])


if __name__ == "__main__":
    main()