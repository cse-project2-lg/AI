import psycopg2
import json
from typing import List, Dict, Any
from app.rag.embeddings.embedder import Embedder


class PgVectorRetriever:
    def __init__(self, conn_string: str):
        self.conn = psycopg2.connect(conn_string)
        self.embedder = Embedder()

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_text(query)
        results = []

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    ee.event_id,
                    ee.content,
                    ee.metadata,
                    ar.is_fall,
                    ar.confidence,
                    ar.risk_level,
                    ar.recommended_action,
                    ar.llm_result,
                    ews.csi_change_score,
                    ews.pir_detected,
                    ews.tof_distance,
                    1 - (ee.embedding <=> %s::vector) AS score
                FROM event_embeddings ee
                JOIN analysis_results ar ON ee.event_id = ar.event_id
                JOIN event_window_summary ews ON ee.event_id = ews.event_id
                WHERE ee.embedding IS NOT NULL
                ORDER BY ee.embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, top_k))

            for row in cur.fetchall():
                llm_result = row[7] or {}
                results.append({
                    "chunk_id": row[0],
                    "section_title": "과거 낙상 판단 이력",
                    "text": (
                        f"센서요약: CSI변화율={row[8]}, PIR={row[9]}, ToF거리={row[10]}mm\n"
                        f"판단결과: {'낙상' if row[3] else '정상'} "
                        f"(신뢰도: {row[4]}, 위험도: {row[5]})\n"
                        f"권장조치: {row[6]}\n"
                        f"상황요약: {llm_result.get('situationSummary', '')}\n"
                        f"판단근거: {llm_result.get('analysisReason', '')}"
                    ),
                    "metadata": {
                        "is_fall": row[3],
                        "risk_level": row[5],
                        "source": "event_history"
                    },
                    "final_score": float(row[11]),
                })

        return results