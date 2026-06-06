from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import check_db_connection, get_db_session
from app.db.repositories import (
    create_event,
    list_event_embeddings,
    list_recent_events,
    save_analysis_result,
    save_event_embedding,
    save_event_window_summary,
    save_notification,
    save_response_outcome,
    save_voice_interaction,
    update_event_status,
)


def main() -> None:
    if not check_db_connection():
        raise RuntimeError("DB 연결에 실패했습니다. DATABASE_URL과 승인된 네트워크를 확인해주세요.")

    now = datetime.now(timezone.utc)
    event_id = f"EVT-TEST-{now.strftime('%Y%m%d%H%M%S')}"

    llm_result = {
        "summary": "센서 변화 패턴을 기준으로 낙상 가능성이 높다고 판단됨",
        "reason": "PIR 감지, ToF 거리 변화, CSI 급격 변화가 같은 시간대에 발생함",
        "riskLevel": "HIGH",
        "recommendedAction": "VERIFY_USER",
        "model": "test-model",
    }

    with get_db_session() as db:
        create_event(
            db,
            event_id=event_id,
            device_id="RASPI-001",
            location="living_room",
            rule_score=87.35,
            event_status="CANDIDATE",
        )

        save_event_window_summary(
            db,
            event_id=event_id,
            window_start=now,
            window_end=now,
            pir_detected=True,
            tof_distance=38.52,
            csi_change_score=0.8421,
            summary="PIR 감지와 ToF 거리 변화, CSI 변화가 같은 시간대에 발생함",
        )

        save_analysis_result(
            db,
            event_id=event_id,
            risk_level="HIGH",
            confidence=91.25,
            llm_result=llm_result,
            recommended_action="VERIFY_USER",
        )

        save_event_embedding(
            db,
            event_id=event_id,
            content=(
                "거실에서 PIR 감지, ToF 거리 변화, CSI 급격 변화가 동시에 발생했고 "
                "AI는 낙상 가능성을 HIGH로 판단했다."
            ),
            embedding=None,
            metadata={
                "source": "analysis_result",
                "dimension": 384,
                "riskLevel": "HIGH",
            },
        )

        save_voice_interaction(
            db,
            event_id=event_id,
            question_text="괜찮으신가요?",
            stt_text=None,
            response_type="NO_RESPONSE",
        )

        save_notification(
            db,
            event_id=event_id,
            guardian_id="GUARDIAN-001",
            notification_type="DISCORD",
            status="REQUESTED",
            sent_at=None,
        )

        update_event_status(
            db,
            event_id=event_id,
            event_status="AI_ANALYZED",
            reason="AI/RAG 2차 판정 결과 저장 완료",
        )

        update_event_status(
            db,
            event_id=event_id,
            event_status="VERIFYING_USER",
            reason="AI 권장 조치가 VERIFY_USER로 반환되어 사용자 확인 단계 진입",
        )

        update_event_status(
            db,
            event_id=event_id,
            event_status="NOTIFIED",
            reason="사용자 응답이 없어 보호자 Discord 알림 요청",
        )

        recent_events = list_recent_events(db, limit=3)
        embeddings = list_event_embeddings(db, event_id=event_id)

    print("DB 저장 테스트 완료")
    print(f"생성된 event_id: {event_id}")
    print(f"최근 이벤트 조회 개수: {len(recent_events)}")
    print(f"생성된 embedding 기록 개수: {len(embeddings)}")


if __name__ == "__main__":
    main()