import json
from typing import Any, Dict, Optional

from app.llm.gemini_client import analyze_with_gemini
from app.rag.prompt.prompt_builder import build_rag_prompt
from app.rag.query.query_generator import generate_query_from_event
from app.rag.retrieval.retriever import JsonRetriever


ALLOWED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_ACTIONS = {"NO_ACTION", "OBSERVE", "VERIFY_USER", "NOTIFY_GUARDIAN"}
_RETRIEVER: Optional[JsonRetriever] = None


def get_retriever() -> JsonRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = JsonRetriever(
            embedding_file_path="data/chunks/chunk_embeddings.json"
        )
    return _RETRIEVER


def parse_llm_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return json.loads(cleaned)


def fallback_response(sensor_event: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "eventId": sensor_event.get("eventId"),
        "isFall": True,
        "confidence": 0.6,
        "riskLevel": "MEDIUM",
        "recommendedAction": "VERIFY_USER",
        "situationSummary": "AI/RAG 분석 실패로 보수적 대응을 적용합니다.",
        "reasoning": reason,
        "verificationMessage": "괜찮으십니까? 괜찮으시다면 '네'라고 대답해주세요.",
        "timeoutSec": 10,
    }


def normalize_response(result: Dict[str, Any], sensor_event: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(result)

    normalized["eventId"] = sensor_event.get("eventId")

    if normalized.get("riskLevel") not in ALLOWED_RISK_LEVELS:
        normalized["riskLevel"] = "MEDIUM"

    if normalized.get("recommendedAction") not in ALLOWED_ACTIONS:
        normalized["recommendedAction"] = "VERIFY_USER"

    try:
        confidence = float(normalized.get("confidence", 0.6))
    except (TypeError, ValueError):
        confidence = 0.6
    normalized["confidence"] = max(0.0, min(confidence, 1.0))

    action = normalized["recommendedAction"]
    normalized.setdefault("isFall", action in {"VERIFY_USER", "NOTIFY_GUARDIAN"})
    normalized["isFall"] = bool(normalized.get("isFall"))

    normalized.setdefault("situationSummary", "")
    normalized.setdefault("reasoning", "")

    if action in {"VERIFY_USER", "NOTIFY_GUARDIAN"}:
        normalized.setdefault(
            "verificationMessage",
            "괜찮으십니까? 괜찮으시다면 '네'라고 대답해주세요.",
        )
    else:
        normalized["verificationMessage"] = normalized.get("verificationMessage") or ""

    try:
        timeout_sec = int(normalized.get("timeoutSec", 10))
    except (TypeError, ValueError):
        timeout_sec = 10
    normalized["timeoutSec"] = max(timeout_sec, 0)

    return normalized


def analyze_sensor_event_with_rag(sensor_event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        query = generate_query_from_event(sensor_event)
        retriever = get_retriever()
        retrieved_chunks = retriever.retrieve(query=query, top_k=3)

        rag_prompt = build_rag_prompt(
            sensor_event=sensor_event,
            query=query,
            retrieved_chunks=retrieved_chunks,
        )

        raw_response = analyze_with_gemini(rag_prompt)
        parsed = parse_llm_json(raw_response)
        return normalize_response(parsed, sensor_event)

    except Exception as exc:
        return fallback_response(
            sensor_event,
            f"AI/RAG 분석, 검색, LLM 호출 또는 응답 검증 실패: {exc}",
        )


if __name__ == "__main__":
    sample_event = {
        "eventId": "EVT-TEST-001",
        "timestamp": "2026-05-24T18:30:12+09:00",
        "deviceId": "RPi4-001",
        "roomId": "living-room",
        "sensorSummary": {
            "pirMotion": False,
            "pirLastMotionMs": 2400,
            "tofDistanceMm": 1820,
            "tofChangeMm": 680,
            "tofStableMs": 2100,
            "csiChangeScore": 0.82,
            "csiPacketCount": 57,
        },
        "localScore": 0.86,
    }
    print(json.dumps(analyze_sensor_event_with_rag(sample_event), ensure_ascii=False, indent=2))
