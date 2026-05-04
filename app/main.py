from app.ingestion.loader import load_document
from app.ingestion.cleaner import clean_document
from app.ingestion.chunker import split_into_chunks
from app.ingestion.metadata import enrich_chunk_metadata


def main():
    file_path = "data/raw/srs/요구사항분석_v2.0.docx"

    doc = load_document(file_path)
    doc = clean_document(doc)

    chunks = split_into_chunks(doc)
    chunks = enrich_chunk_metadata(chunks)

    print("총 chunk 개수:", len(chunks))

    print("\n앞쪽 chunk 5개 metadata 미리보기")
    print("-" * 50)

    for index, chunk in enumerate(chunks[:5], start=1):
        print(f"\n[{index}] {chunk.metadata['section_title']}")
        print("category:", chunk.metadata["category"])
        print("priority:", chunk.metadata["priority"])
        print("keywords:", chunk.metadata["keywords"])
        print("chunk_length:", chunk.metadata["chunk_length"])
        print("contains_requirement_id:", chunk.metadata["contains_requirement_id"])
        print("requirement_ids:", chunk.metadata["requirement_ids"])


if __name__ == "__main__":
    main()