from app.query.query_generator import generate_query_from_event
from app.retrieval.retriever import JsonRetriever


def main() -> None:
    retriever = JsonRetriever(
        embedding_file_path="data/chunks/chunk_embeddings.json"
    )

    sensor_event = {
        "pir_detected": True,
        "tof_distance_drop_cm": 45,
        "csi_variance_level": "high",
        "user_response": "no_response",
        "llm_status": "available",
        "event_type": "fall_candidate",
    }

    query = generate_query_from_event(sensor_event)

    results = retriever.retrieve(query=query, top_k=3)

    print("\n센서 이벤트:")
    print(sensor_event)

    print("\n생성된 Query:")
    print(query)

    print("\n검색 결과:")
    for index, result in enumerate(results, start=1):
        print(f"\n[{index}] rerank_score: {result['rerank_score']:.4f}")
        print(f"final_score: {result['final_score']:.4f}")
        print(f"embedding_score: {result['embedding_score']:.4f}")
        print(f"keyword_score: {result['keyword_score']:.4f}")
        print(f"metadata_score: {result['metadata_score']:.4f}")
        print(f"section_title: {result['metadata'].get('section_title')}")
        print(f"category: {result['metadata'].get('category')}")
        print("text:")
        print(result["text"][:500])


if __name__ == "__main__":
    main()