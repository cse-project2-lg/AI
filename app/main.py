from app.ingestion.ingest_pipeline import run_ingestion_pipeline


def main():
    input_file_path = "data/raw/srs/요구사항분석_v2.0.docx"
    output_file_path = "data/chunks/chunks.json"

    chunks = run_ingestion_pipeline(
        input_file_path=input_file_path,
        output_file_path=output_file_path,
    )

    print("Ingestion pipeline 완료")
    print("저장 위치:", output_file_path)
    print("총 chunk 개수:", len(chunks))

    high_priority_chunks = [
        chunk for chunk in chunks
        if chunk.metadata["priority"] == "high"
    ]

    print("high priority chunk 개수:", len(high_priority_chunks))

    print("\n샘플 high priority chunk")
    print("-" * 50)

    for index, chunk in enumerate(high_priority_chunks[:3], start=1):
        print(f"\n[{index}] {chunk.metadata['section_title']}")
        print("category:", chunk.metadata["category"])
        print("priority:", chunk.metadata["priority"])
        print("keywords:", chunk.metadata["keywords"])
        print(chunk.text[:300])


if __name__ == "__main__":
    main()