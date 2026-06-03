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


def now_iso_millis() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/fall-events/analyze", response_model=FallAnalyzeResponse)
def analyze_fall_event(request: FallAnalyzeRequest):
    result = analyze_sensor_event_with_rag(request.model_dump() if hasattr(request, "model_dump") else request.dict())
    return result


@app.post("/api/v1/notifications/guardian", response_model=NotificationResult)
def send_guardian_notification(request: NotificationRequest):
    request_data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    print("NOTIFICATION.REQUEST:", request_data)

    # 사용자 확인 결과가 OK면 보호자 알림을 보내지 않는다.
    # 원칙적으로 이 엔드포인트는 알림이 필요할 때만 호출되지만,
    # 실수 방지를 위한 안전장치다.
    if request.verification.userResponse == "OK":
        return {
            "type": "notification.result",
            "eventId": request.eventId,
            "timestamp": now_iso_millis(),
            "notificationStatus": "NOT_REQUIRED",
            "channels": [],
            "attemptCount": 0,
            "error": None,
        }

    discord_result = send_discord_notification(
        event_id=request.eventId,
        situation_summary=request.situationSummary,
        risk_level=request.riskLevel,
        room_id=request.roomId,
        escalation_reason=request.escalationReason,
        user_response=request.verification.userResponse or "UNKNOWN",
        transcript=request.verification.transcript,
        timestamp=request.timestamp,
    )

    if discord_result["success"]:
        return {
            "type": "notification.result",
            "eventId": request.eventId,
            "timestamp": now_iso_millis(),
            "notificationStatus": "SENT",
            "channels": ["DISCORD"],
            "attemptCount": 1,
            "error": None,
        }

    return {
        "type": "notification.result",
        "eventId": request.eventId,
        "timestamp": now_iso_millis(),
        "notificationStatus": "FAILED",
        "channels": ["DISCORD"],
        "attemptCount": 1,
        "error": discord_result["error"],
    }


@app.post("/api/v1/fall-events/outcome")
def save_fall_outcome(request: FallOutcomeRequest):
    # TODO: Save to DB or log storage.
    print("RESPONSE.OUTCOME:", request.model_dump() if hasattr(request, "model_dump") else request.dict())
    return {"saved": True}
