from __future__ import annotations

from typing import Any

from app.db.database import get_db_session
from app.db.repositories import (
    create_event,
    save_analysis_result,
    save_event_embedding,
    save_event_window_summary,
    save_notification,
    save_response_outcome,
    save_voice_interaction,
    update_event_status,
)


def save_fall_candidate_event(
    *,
    edge_event: dict[str, Any],
    sensor_summary: dict[str, Any] | None = None,
    analysis_result: dict[str, Any] | None = None,
    embedding_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_id = edge_event["event_id"]

    with get_db_session() as db:
        create_event(
            db,
            event_id=event_id,
            device_id=edge_event.get("device_id"),
            location=edge_event.get("location"),
            rule_score=edge_event.get("rule_score"),
            event_status="CANDIDATE",
        )

        if sensor_summary is not None:
            save_event_window_summary(
                db,
                event_id=event_id,
                window_start=sensor_summary.get("window_start"),
                window_end=sensor_summary.get("window_end"),
                pir_detected=sensor_summary.get("pir_detected"),
                tof_distance=sensor_summary.get("tof_distance"),
                csi_change_score=sensor_summary.get("csi_change_score"),
                summary=sensor_summary.get("summary"),
            )

        if analysis_result is not None:
            save_analysis_result(
                db,
                event_id=event_id,
                risk_level=analysis_result.get("risk_level"),
                confidence=analysis_result.get("confidence"),
                llm_result=analysis_result.get("llm_result"),
                recommended_action=analysis_result.get("recommended_action"),
            )

            update_event_status(
                db,
                event_id=event_id,
                event_status="AI_ANALYZED",
                reason="AI/RAG 2차 판정 결과 저장 완료",
            )

        if embedding_result is not None:
            save_event_embedding(
                db,
                event_id=event_id,
                content=embedding_result["content"],
                embedding=embedding_result.get("embedding"),
                metadata=embedding_result.get("metadata"),
            )

    return {
        "event_id": event_id,
        "status": "SAVED",
    }


def save_notification_flow(
    *,
    event_id: str,
    question_text: str | None,
    stt_text: str | None,
    response_type: str | None,
    guardian_id: str | None,
    notification_type: str | None,
    notification_status: str | None,
    sent_at,
) -> dict[str, Any]:
    with get_db_session() as db:
        save_voice_interaction(
            db,
            event_id=event_id,
            question_text=question_text,
            stt_text=stt_text,
            response_type=response_type,
        )

        save_notification(
            db,
            event_id=event_id,
            guardian_id=guardian_id,
            notification_type=notification_type,
            status=notification_status,
            sent_at=sent_at,
        )

        update_event_status(
            db,
            event_id=event_id,
            event_status="NOTIFIED",
            reason="보호자 알림 요청 및 전송 결과 저장",
        )

    return {
        "event_id": event_id,
        "status": "NOTIFICATION_SAVED",
    }


def save_outcome_flow(
    *,
    event_id: str,
    final_status: str | None,
    action_taken: str | None,
    resolved_at,
) -> dict[str, Any]:
    with get_db_session() as db:
        save_response_outcome(
            db,
            event_id=event_id,
            final_status=final_status,
            action_taken=action_taken,
            resolved_at=resolved_at,
        )

        update_event_status(
            db,
            event_id=event_id,
            event_status="RESOLVED",
            reason="최종 대응 결과 저장 완료",
        )

    return {
        "event_id": event_id,
        "status": "OUTCOME_SAVED",
    }