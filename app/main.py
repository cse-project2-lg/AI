from app.ingestion.loader import load_document


def main():
    file_path = "data/raw/srs/요구사항분석_v2.0.docx"

    doc = load_document(file_path)

    print("문서 ID:", doc.doc_id)
    print("문서 타입:", doc.doc_type)
    print("문서 제목:", doc.title)
    print("원본 경로:", doc.source)
    print("텍스트 길이:", len(doc.text))
    print()
    print("본문 미리보기")
    print("-" * 50)
    print(doc.text[:1000])


if __name__ == "__main__":
    main()