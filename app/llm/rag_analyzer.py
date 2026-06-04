import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.llm.gemini_client import analyze_with_gemini
from app.rag.prompt.prompt_builder import build_rag_prompt
from app.rag.query.query_generator import generate_query_from_event
from app.rag.retrieval.retriever import JsonRetriever
from app.rag.retrieval.pg_retriever import PgVectorRetriever
from app.rag.ingestion.event_store import save_analysis_result

DB_CONN = os.getenv("DATABASE_URL")  # .env에서 관리

ALLOWED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_ACTIONS = {"NO_ACTION", "OBSERVE", "VERIFY_USER", "NOTIFY_GUARDIAN"}
ALLOWED_ANALYSIS_STATUS = {"SUCCESS", "FALLBACK_RULE", "FAILED"}
DEFAULT_PROMPT_ASSET = "are_you_ok_ko.mp3"
DEFAULT_EXPECTED_OK_TEXT = ["네"]
_RETRIEVER: Optional[JsonRetriever] = None


def now_iso_millis() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


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


def _verification_plan_for_action(action: str) -> Dict[str, Any]:
    if action == "VERIFY_USER":
        return {
            "required": True,
            "method": "LOCAL_MP3_STT",
            "promptAsset": DEFAULT_PROMPT_ASSET,
            "expectedOkText": DEFAULT_EXPECTED_OK_TEXT,
            "timeoutSec": 10,
        }
    return {
        "required": False,
        "method": "NONE",
        "promptAsset": None,
        "expectedOkText": [],
        "timeoutSec": 0,
    }


def fallback_response(sensor_event: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "type": "analysis.result",
        "eventId": sensor_event.get("eventId"),
        "timestamp": now_iso_millis(),
        "isFall": True,
        "confidence": 0.6,
        "riskLevel": "MEDIUM",
        "recommendedAction": "VERIFY_USER",
        "situationSummary": "AI/RAG 분석 실패로 엣지 rule-based 판단을 기반으로 사용자 확인 절차를 수행합니다.",
        "analysisReason": reason,
        "verificationPlan": _verification_plan_for_action("VERIFY_USER"),
        "analysisStatus": "FALLBACK_RULE",
    }


def _normalize_verification_plan(plan: Any, action: str) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        return _verification_plan_for_action(action)

    default_plan = _verification_plan_for_action(action)
    normalized = {**default_plan, **plan}

    if action == "VERIFY_USER":
        normalized["required"] = True
        normalized["method"] = "LOCAL_MP3_STT"
        normalized["promptAsset"] = normalized.get("promptAsset") or DEFAULT_PROMPT_ASSET
        expected = normalized.get("expectedOkText")
        normalized["expectedOkText"] = expected if isinstance(expected, list) and expected else DEFAULT_EXPECTED_OK_TEXT
        try:
            timeout_sec = int(normalized.get("timeoutSec", 10))
        except (TypeError, ValueError):
            timeout_sec = 10
        normalized["timeoutSec"] = max(timeout_sec, 0)
    else:
        normalized = _verification_plan_for_action(action)

    return normalized


def normalize_response(result: Dict[str, Any], sensor_event: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(result)

    normalized["type"] = "analysis.result"
    normalized["eventId"] = sensor_event.get("eventId")
    normalized["timestamp"] = normalized.get("timestamp") or now_iso_millis()

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

    # Backward-compatible migration from old LLM contract.
    if "analysisReason" not in normalized:
        normalized["analysisReason"] = normalized.pop("reasoning", "")
    else:
        normalized.pop("reasoning", None)

    old_timeout = normalized.pop("timeoutSec", None)
    normalized.pop("verificationMessage", None)

    plan = normalized.get("verificationPlan")
    if old_timeout is not None and not isinstance(plan, dict) and action == "VERIFY_USER":
        plan = {"timeoutSec": old_timeout}
    normalized["verificationPlan"] = _normalize_verification_plan(plan, action)

    if normalized.get("analysisStatus") not in ALLOWED_ANALYSIS_STATUS:
        normalized["analysisStatus"] = "SUCCESS"

    return normalized


def analyze_sensor_event_with_rag(sensor_event: Dict[str, Any]) -> str:
    retriever = get_retriever()
    query = generate_query_from_event(sensor_event)
    retrieved_chunks = retriever.retrieve(query=query, top_k=3)
    rag_prompt = build_rag_prompt(
        sensor_event=sensor_event,
        query=query,
        retrieved_chunks=retrieved_chunks,
    )

    response_text = analyze_with_gemini(rag_prompt)
    return response_text


if __name__ == "__main__":
    sample_event = {
        "type": "event.candidate",
        "eventId": "EVT-TEST-001",
        "timestamp": "2026-05-24T18:30:12+09:00",
        "deviceId": "RPi4-001",
        "roomId": "living-room",
        "window": {
            "startMonotonicNs": 123456789000,
            "endMonotonicNs": 124456789000,
            "durationMs": 1000,
        },
        "sensorSummary": {
            "pirMotion": False,
            "pirLastMotionMs": 2400,
            "tofDistanceMm": 1820,
            "tofChangeMm": 680,
            "tofStableMs": 2100,
            "csi": {"status": "AVAILABLE", "changeScore": 0.82, "packetCount": 57},
        },
        "localScore": 0.86,
        "localRiskLevel": "HIGH",
        "candidateReason": ["CSI 급격 변화", "ToF 거리 급변", "움직임 정지 지속"],
    }
    print(json.dumps(analyze_sensor_event_with_rag(sample_event), ensure_ascii=False, indent=2))
