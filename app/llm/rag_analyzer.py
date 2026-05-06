import json
from typing import Dict, Any

from app.rag.query.query_generator import generate_query_from_event
from app.rag.retrieval.retriever import JsonRetriever
from app.rag.prompt.prompt_builder import build_rag_prompt
from app.llm.gemini_client import analyze_with_gemini


def analyze_sensor_event_with_rag(sensor_event: Dict[str, Any]) -> str:
    retriever = JsonRetriever(
        embedding_file_path="data/chunks/chunk_embeddings.json"
    )

    query = generate_query_from_event(sensor_event)

    retrieved_chunks = retriever.retrieve(
        query=query,
        top_k=3,
    )

    rag_prompt = build_rag_prompt(
        sensor_event=sensor_event,
        query=query,
        retrieved_chunks=retrieved_chunks,
    )

    response = analyze_with_gemini(rag_prompt)

    return response


if __name__ == "__main__":
    sensor_event = {
        "eventId": "EVT_001",
        "csi_variation": 0.9,
        "pir_motion": False,
        "tof_distance_mm": 100,
        "duration_sec": 3,
    }

    result = analyze_sensor_event_with_rag(sensor_event)

    print("--- RAG + Gemini 분석 결과 ---")
    print(result)