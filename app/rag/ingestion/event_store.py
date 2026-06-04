import psycopg2
import json
from app.rag.embeddings.embedder import Embedder

embedder = Embedder()

def save_analysis_result(conn_string: str, sensor_event: dict, llm_result: dict):
    """
    Gemini 분석 완료 후 호출
    analysis_results 테이블에 결과 저장 + embedding 생성
    """
    # 임베딩용 요약 텍스트 (검색 시 유사도 비교 기준)
    summary_text = (
        f"CSI변화율={sensor_event.get('csi_variation')} "
        f"PIR={sensor_event.get('pir_motion')} "
        f"ToF={sensor_event.get('tof_distance_mm')}mm "
        f"판단={llm_result.get('fall_status')} "
        f"근거={llm_result.get('reason', '')}"
    )
    embedding = embedder.embed_text(summary_text)

    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO analysis_results (
                    event_id,
                    is_fall,
                    confidence,
                    risk_level,
                    situation_summary,
                    reasoning,
                    recommended_action,
                    verification_message,
                    raw_response_json,
                    embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (event_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    raw_response_json = EXCLUDED.raw_response_json
            """, (
                sensor_event["eventId"],
                llm_result.get("fall_status") == "FALL_CONFIRMED",
                llm_result.get("confidence", 0.0),
                llm_result.get("riskLevel"),
                llm_result.get("situationSummary"),
                llm_result.get("reason"),
                llm_result.get("recommended_action"),
                llm_result.get("verificationMessage"),
                json.dumps(llm_result),
                embedding,
            ))