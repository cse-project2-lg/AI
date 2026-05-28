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
    # MVP stub: 실제 Kakao/SMS 연동 전까지 클라우드 알림 서비스 계약을 고정한다.
    # escalationReason은 내부 로그용이며 보호자 메시지 본문으로 직접 사용하지 않는다.
    print("NOTIFICATION.REQUEST:", request.model_dump() if hasattr(request, "model_dump") else request.dict())
    return {
        "type": "notification.result",
        "eventId": request.eventId,
        "timestamp": now_iso_millis(),
        "notificationStatus": "SENT",
        "channels": request.notification.channels,
        "attemptCount": 1,
        "error": None,
    }


@app.post("/api/v1/fall-events/outcome")
def save_fall_outcome(request: FallOutcomeRequest):
    # TODO: Save to DB or log storage.
    print("RESPONSE.OUTCOME:", request.model_dump() if hasattr(request, "model_dump") else request.dict())
    return {"saved": True}
