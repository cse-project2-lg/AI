from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    AnalysisResult,
    Event,
    EventEmbedding,
    EventStatusHistory,
    EventWindowSummary,
    Notification,
    ResponseOutcome,
    VoiceInteraction,
)


def create_event(
    db: Session,
    *,
    event_id: str,
    device_id: str | None = None,
    location: str | None = None,
    rule_score: float | None = None,
    event_status: str = "CANDIDATE",
) -> Event:
    """
    낙상 후보 이벤트 기본 정보를 저장
    - 중복 event_id가 들어오면 IntegrityError가 발생한다.
    """
    event = Event(
        event_id=event_id,
        device_id=device_id,
        location=location,
        event_status=event_status,
        rule_score=rule_score,
    )

    db.add(event)
    _flush_or_raise(db, event_id=event_id)

    return event


#event_id로 이벤트를 조회
def get_event_by_id(db: Session, event_id: str) -> Event | None:
    statement = select(Event).where(Event.event_id == event_id)
    return db.execute(statement).scalar_one_or_none()


# 이벤트 상태 변경 이력을 저장
def update_event_status(
    db: Session,
    *,
    event_id: str,
    event_status: str,
    reason: str | None = None,
    save_history: bool = True,
) -> Event:

    event = get_event_by_id(db, event_id)

    if event is None:
        raise ValueError(f"존재하지 않는 event_id입니다: {event_id}")

    previous_status = event.event_status

    event.event_status = event_status

    if save_history:
        history = EventStatusHistory(
            event_id=event_id,
            from_status=previous_status,
            to_status=event_status,
            reason=reason,
        )
        db.add(history)

    _flush_or_raise(db, event_id=event_id)

    return event


def save_event_status_history(
    db: Session,
    *,
    event_id: str,
    from_status: str | None,
    to_status: str,
    reason: str | None = None,
) -> EventStatusHistory:

    if not to_status.strip():
        raise ValueError("to_status는 빈 문자열일 수 없습니다.")

    history = EventStatusHistory(
        event_id=event_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
    )

    db.add(history)
    _flush_or_raise(db, event_id=event_id)

    return history


# 이벤트 발생 구간의 센서 요약 정보를 저장
def save_event_window_summary(
    db: Session,
    *,
    event_id: str,
    window_start: datetime | None,
    window_end: datetime | None,
    pir_detected: bool | None,
    tof_distance: float | None,
    csi_change_score: float | None,
    summary: str | None,
) -> EventWindowSummary:

    window_summary = EventWindowSummary(
        event_id=event_id,
        window_start=window_start,
        window_end=window_end,
        pir_detected=pir_detected,
        tof_distance=tof_distance,
        csi_change_score=csi_change_score,
        summary=summary,
    )

    db.add(window_summary)
    _flush_or_raise(db, event_id=event_id)

    return window_summary


# AI/RAG 2차 판정 결과를 저장
def save_analysis_result(
    db: Session,
    *,
    event_id: str,
    risk_level: str | None,
    confidence: float | None,
    llm_result: dict[str, Any] | None,
    recommended_action: str | None,
) -> AnalysisResult:

    analysis_result = AnalysisResult(
        event_id=event_id,
        risk_level=risk_level,
        confidence=confidence,
        llm_result=llm_result,
        recommended_action=recommended_action,
    )

    db.add(analysis_result)
    _flush_or_raise(db, event_id=event_id)

    return analysis_result


# RAG 검색용 이벤트 요약 텍스트와 embedding을 저장
def save_event_embedding(
    db: Session,
    *,
    event_id: str,
    content: str,
    embedding: list[float] | None,
    metadata: dict[str, Any] | None,
) -> EventEmbedding:
    if not content.strip():
        raise ValueError("content는 빈 문자열일 수 없습니다.")

    if embedding is not None and len(embedding) != 384:
        raise ValueError(
            f"embedding 차원이 올바르지 않습니다. "
            f"expected=384, actual={len(embedding)}"
        )

    event_embedding = EventEmbedding(
        event_id=event_id,
        content=content,
        embedding=embedding,
        metadata_=metadata,
    )

    db.add(event_embedding)
    _flush_or_raise(db, event_id=event_id)

    return event_embedding


# 사용자 확인 질문과 STT 응답 결과를 저장
def save_voice_interaction(
    db: Session,
    *,
    event_id: str,
    question_text: str | None,
    stt_text: str | None,
    response_type: str | None,
) -> VoiceInteraction:

    voice_interaction = VoiceInteraction(
        event_id=event_id,
        question_text=question_text,
        stt_text=stt_text,
        response_type=response_type,
    )

    db.add(voice_interaction)
    _flush_or_raise(db, event_id=event_id)

    return voice_interaction


# 보호자 알림 요청 및 전송 결과를 저장
def save_notification(
    db: Session,
    *,
    event_id: str,
    guardian_id: str | None,
    notification_type: str | None,
    status: str | None,
    sent_at: datetime | None = None,
) -> Notification:

    notification = Notification(
        event_id=event_id,
        guardian_id=guardian_id,
        notification_type=notification_type,
        status=status,
        sent_at=sent_at,
    )

    db.add(notification)
    _flush_or_raise(db, event_id=event_id)

    return notification


# 해당 낙상 후보 이벤트의 최종 대응 결과를 저장
def save_response_outcome(
    db: Session,
    *,
    event_id: str,
    final_status: str | None,
    action_taken: str | None,
    resolved_at: datetime | None = None,
) -> ResponseOutcome:

    response_outcome = ResponseOutcome(
        event_id=event_id,
        final_status=final_status,
        action_taken=action_taken,
        resolved_at=resolved_at,
    )

    db.add(response_outcome)
    _flush_or_raise(db, event_id=event_id)

    return response_outcome


# 최근 이벤트 목록을 조회
def list_recent_events(
    db: Session,
    *,
    limit: int = 10,
) -> list[Event]:

    statement = (
        select(Event)
        .order_by(Event.created_at.desc())
        .limit(limit)
    )

    return list(db.execute(statement).scalars().all())


# 특정 이벤트에 연결된 embedding 기록을 조회
def list_event_embeddings(
    db: Session,
    *,
    event_id: str,
) -> list[EventEmbedding]:

    statement = (
        select(EventEmbedding)
        .where(EventEmbedding.event_id == event_id)
        .order_by(EventEmbedding.created_at.desc())
    )

    return list(db.execute(statement).scalars().all())


def _flush_or_raise(db: Session, event_id: str | None = None) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        pgcode = getattr(exc.orig, "pgcode", None)

        if pgcode == "23503":
            raise ValueError(
                f"존재하지 않는 event_id입니다: {event_id}. "
                "먼저 events 테이블에 이벤트를 생성해야 합니다."
            ) from exc

        if pgcode == "23505":
            raise ValueError(f"이미 존재하는 event_id입니다: {event_id}") from exc

        raise