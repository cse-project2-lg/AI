from app.rag.query.query_generator import generate_query_from_event
from app.rag.retrieval.retriever import JsonRetriever
from app.rag.prompt.prompt_builder import build_rag_prompt

def main() -> None:
    retriever = JsonRetriever(
        embedding_file_path="data/chunks/chunk_embeddings.json"
    )

    sensor_event = {
        "type": "event.candidate",
        "eventId": "EVT-TEST-001",
        "sensorSummary": {
            "pirMotion": False,
            "pirLastMotionMs": 2400,
            "tofChangeMm": 680,
            "tofStableMs": 2100,
            "csi": {"status": "AVAILABLE", "changeScore": 0.87},
        },
        "localScore": 0.86,
        "localRiskLevel": "HIGH",
        "candidateReason": ["CSI 급격 변화", "ToF 거리 급변"],
    }

    query = generate_query_from_event(sensor_event)

    results = retriever.retrieve(query=query, top_k=3)

    rag_prompt = build_rag_prompt(
        sensor_event=sensor_event,
        query=query,
        retrieved_chunks=results,
    )

    print("\n생성된 RAG Prompt:")
    print(rag_prompt)
    
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