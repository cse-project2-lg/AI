from app.ingestion.loader import load_document
from app.ingestion.cleaner import clean_document


def main():
    file_path = "data/raw/srs/요구사항분석_v2.0.docx"

    doc = load_document(file_path)
    cleaned_doc = clean_document(doc)

    print("문서 ID:", cleaned_doc.doc_id)
    print("문서 타입:", cleaned_doc.doc_type)
    print("원본 텍스트 길이:", len(cleaned_doc.text))
    print("정제 텍스트 길이:", len(cleaned_doc.cleaned_text))
    print("정제 정보:", cleaned_doc.extra_metadata["cleaning"])

    print()
    print("정제 본문 미리보기")
    print("-" * 50)
    print(cleaned_doc.cleaned_text[:1500])


if __name__ == "__main__":
    main()