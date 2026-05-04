from app.schemas.document import Document
from app.schemas.chunk import Chunk


def main():
    doc = Document(
        doc_id="test_doc",
        source="test.txt",
        text="이것은 테스트 문서입니다."
    )

    chunk = Chunk(
        chunk_id="chunk_1",
        doc_id=doc.doc_id,
        text="이것은 chunk입니다.",
        metadata={"section": "1.1"}
    )

    print(doc.to_dict())
    print(chunk.to_dict())


if __name__ == "__main__":
    main()