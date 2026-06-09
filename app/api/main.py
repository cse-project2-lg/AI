import logging
import json
from typing import Any
from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.schemas import (
    FallAnalyzeRequest,
    FallAnalyzeResponse,
    FallOutcomeRequest,
    NotificationRequest,
    NotificationResult,
)

from app.llm.rag_analyzer import analyze_sensor_event_with_rag
from app.api.discord_api import send_discord_notification
from app.services.event_pipeline import (
    save_fall_candidate_event,
    save_notification_flow,
    save_outcome_flow,
)

app = FastAPI(title="Fall Detection AI/RAG API", version="1.1.0")

logger = logging.getLogger(__name__)


def now_iso_millis() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def parse_iso_datetime(value: str | None):
    if value is None:
        return None

    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        logger.warning("timestamp 파싱 실패: %s", value)
        return None


def build_edge_event_from_request(request_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": request_data["eventId"],
        "device_id": request_data.get("deviceId"),
        "location": request_data.get("roomId"),
        "rule_score": request_data.get("localScore"),
    }


def build_sensor_summary_from_request(request_data: dict[str, Any]) -> dict[str, Any]:
    sensor_summary = request_data.get("sensorSummary") or {}
    csi = sensor_summary.get("csi") or {}

    candidate_reason = request_data.get("candidateReason") or []
    if isinstance(candidate_reason, list):
        summary = ", ".join(str(reason) for reason in candidate_reason)
    else:
        summary = str(candidate_reason)

    timestamp = parse_iso_datetime(request_data.get("timestamp"))

    return {
        "window_start": timestamp,
        "window_end": timestamp,
        "pir_detected": sensor_summary.get("pirMotion"),
        "tof_distance": sensor_summary.get("tofDistanceMm"),
        "csi_change_score": csi.get("changeScore"),
        "summary": summary,
    }


def build_analysis_result_from_ai_result(ai_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_level": ai_result.get("riskLevel"),
        "confidence": ai_result.get("confidence"),
        "llm_result": ai_result,
        "recommended_action": ai_result.get("recommendedAction"),
    }


def build_embedding_result_from_ai_result(
    request_data: dict[str, Any],
    ai_result: dict[str, Any],
) -> dict[str, Any]:
    event_id = request_data["eventId"]

    content = (
        f"eventId={event_id}, "
        f"roomId={request_data.get('roomId')}, "
        f"localRiskLevel={request_data.get('localRiskLevel')}, "
        f"riskLevel={ai_result.get('riskLevel')}, "
        f"recommendedAction={ai_result.get('recommendedAction')}, "
        f"situationSummary={ai_result.get('situationSummary')}, "
        f"analysisReason={ai_result.get('analysisReason')}"
    )

    return {
        "content": content,
        "embedding": None,
        "metadata": {
            "source": "analysis_result",
            "dimension": 384,
            "riskLevel": ai_result.get("riskLevel"),
            "recommendedAction": ai_result.get("recommendedAction"),
            "analysisStatus": ai_result.get("analysisStatus"),
        },
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/fall-events/analyze", response_model=FallAnalyzeResponse)
def analyze_fall_event(request: FallAnalyzeRequest):
    req_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()

    ai_result = analyze_sensor_event_with_rag(req_dict)

    save_fall_candidate_event(
        edge_event=build_edge_event_from_request(req_dict),
        sensor_summary=build_sensor_summary_from_request(req_dict),
        analysis_result=build_analysis_result_from_ai_result(ai_result),
        embedding_result=build_embedding_result_from_ai_result(req_dict, ai_result),
    )

    return ai_result

@app.post("/api/v1/notifications/guardian", response_model=NotificationResult)
def send_guardian_notification(request: NotificationRequest):
    # MVP stub: 실제 Kakao/SMS 연동 전까지 클라우드 알림 서비스 계약을 고정한다.
    # escalationReason은 내부 로그용이며 보호자 메시지 본문으로 직접 사용하지 않는다.
    req_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    logger.info("notification.request received: %s", req_dict)
    # print("NOTIFICATION.REQUEST:", request.model_dump() if hasattr(request, "model_dump") else request.dict())
    
    if request.verification and request.verification.userResponse == "OK":
        logger.info("Notification omitted. User verification status is OK for eventId=%s", request.eventId)
        return {
            "type": "notification.result",
            "eventId": request.eventId,
            "timestamp": now_iso_millis(),
            "notificationStatus": "NOT_REQUIRED",
            "channels": [],
            "attemptCount": 0,
            "error": None,
        }

    # 디스코드 API 연동 호출 및 파라미터 매핑 (확정 스키마 기준 필드 매핑)
    discord_result = send_discord_notification(
        event_id=request.eventId,
        situation_summary=request.situationSummary,
        risk_level=request.riskLevel,
        room_id=request.roomId,
        escalation_reason=request.escalationReason,
        user_response=request.verification.userResponse if request.verification else "UNKNOWN",
        transcript=request.verification.transcript if request.verification else "",
        timestamp=request.timestamp,
    )

    # 알림 전송 성공 시 응답 구조
    if discord_result.get("success"):
        logger.info("Notification successfully sent via DISCORD for eventId=%s", request.eventId)

        save_notification_flow(
            event_id=request.eventId,
            question_text=request.verification.promptAsset if request.verification else None,
            stt_text=request.verification.transcript if request.verification else "",
            response_type=request.verification.userResponse if request.verification else "UNKNOWN",
            guardian_id=None,
            notification_type="DISCORD",
            notification_status="SENT",
            sent_at=parse_iso_datetime(now_iso_millis()),
        )

        return {
            "type": "notification.result",
            "eventId": request.eventId,
            "timestamp": now_iso_millis(),
            "notificationStatus": "SENT",
            "channels": ["DISCORD"],
            "attemptCount": 1,
            "error": None,
        }

    # 알림 전송 실패 시 응답 구조
    logger.error("Notification failed via DISCORD for eventId=%s, error=%s", request.eventId, discord_result.get("error"))

    save_notification_flow(
        event_id=request.eventId,
        question_text=request.verification.promptAsset if request.verification else None,
        stt_text=request.verification.transcript if request.verification else "",
        response_type=request.verification.userResponse if request.verification else "UNKNOWN",
        guardian_id=None,
        notification_type="DISCORD",
        notification_status="FAILED",
        sent_at=parse_iso_datetime(now_iso_millis()),
    )

    return {
        "type": "notification.result",
        "eventId": request.eventId,
        "timestamp": now_iso_millis(),
        "notificationStatus": "FAILED",
        "channels": ["DISCORD"],
        "attemptCount": 1,
        "error": discord_result.get("error"),
    }


@app.post("/api/v1/fall-events/outcome")
def save_fall_outcome(request: FallOutcomeRequest):
    req_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()

    logger.info("fall.outcome received eventId=%s", request.eventId)

    save_outcome_flow(
        event_id=request.eventId,
        final_status=request.responseOutcome,
        action_taken=json.dumps(req_dict, ensure_ascii=False),
        resolved_at=parse_iso_datetime(request.timestamp),
    )

    return {
        "saved": True,
        "eventId": request.eventId,
    }