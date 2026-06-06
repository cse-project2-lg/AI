import logging
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


app = FastAPI(title="Fall Detection AI/RAG API", version="1.1.0")

logger = logging.getLogger(__name__)


def now_iso_millis() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/fall-events/analyze", response_model=FallAnalyzeResponse)
def analyze_fall_event(request: FallAnalyzeRequest):
    req_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    return analyze_sensor_event_with_rag(req_dict)


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
    # TODO: Save to DB or log storage.
    logger.info("fall.outcome received eventId=%s", request.eventId)
    return {"saved": False, "note": "stub - persistence not implemented"}