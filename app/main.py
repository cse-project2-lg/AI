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

    # 앞쪽 chunk 확인 (구조 검증)
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

    # 중요한 chunk만 따로 확인해보기
    important_chunks = [
        chunk for chunk in chunks
        if chunk.metadata["priority"] == "high"
        or chunk.metadata["category"] != "general"
    ]

    print("\n중요 chunk 개수:", len(important_chunks))

    print("\n중요 chunk 5개 미리보기")
    print("-" * 50)

    for index, chunk in enumerate(important_chunks[:5], start=1):
        print(f"\n[{index}] {chunk.metadata['section_title']}")
        print("category:", chunk.metadata["category"])
        print("priority:", chunk.metadata["priority"])
        print("keywords:", chunk.metadata["keywords"])
        print("chunk_length:", chunk.metadata["chunk_length"])

        print("\n본문 일부:")
        print(chunk.text[:300])


if __name__ == "__main__":
    main()