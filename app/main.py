from app.retrieval.retriever import JsonRetriever


def main() -> None:
    retriever = JsonRetriever(
        embedding_file_path="data/chunks/chunk_embeddings.json"
    )

    query = "PIR 센서에서 움직임이 감지되고 ToF 거리 값이 급격히 감소했을 때 낙상 후보로 판단하는 기준"

    results = retriever.retrieve(query=query, top_k=3)

    print("\n검색 Query:")
    print(query)

    print("\n검색 결과:")
    for index, result in enumerate(results, start=1):
        print(f"\n[{index}] score: {result['score']:.4f}")
        print("metadata:", result["metadata"])
        print("text:")
        print(result["text"][:500])


if __name__ == "__main__":
    main()