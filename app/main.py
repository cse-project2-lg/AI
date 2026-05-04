from app.ingestion.loader import load_document
from app.ingestion.cleaner import clean_document
from app.ingestion.chunker import split_into_chunks


def main():
    file_path = "data/raw/srs/요구사항분석_v2.0.docx"

    doc = load_document(file_path)
    doc = clean_document(doc)

    chunks = split_into_chunks(doc)

    print("총 chunk 개수:", len(chunks))

    print("\n앞쪽 chunk 5개 미리보기")
    print("-" * 50)

    for index, chunk in enumerate(chunks[:5], start=1):
        print(f"\n[{index}] {chunk.metadata['section_title']}")
        print(chunk.text[:500])
        print("metadata:", chunk.metadata)


if __name__ == "__main__":
    main()