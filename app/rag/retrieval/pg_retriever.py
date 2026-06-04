import psycopg2
import json
from typing import List, Dict, Any
from app.rag.embeddings.embedder import Embedder

class PgVectorRetriever:
    def __init__(self, conn_string: str):
        self.conn = psycopg2.connect(conn_string)
        self.embedder = Embedder()  # 기존 Embedder 재사용

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_text(query)
        results = []

        with self.conn.cursor() as cur:
            # 과거 판단 이력에서 유사 사례 검색
            cur.execute("""
                SELECT 
                    ar.event_id,
                    ar.is_fall,
                    ar.confidence,
                    ar.risk_level,
                    ar.situation_summary,
                    ar.reasoning,
                    ews.avg_csi_change,
                    ews.pir_motion_detected,
                    ews.net_tof_distance_change,
                    1 - (ar.embedding <=> %s::vector) AS score
                FROM analysis_results ar
                JOIN event_window_summary ews ON ar.event_id = ews.event_id
                WHERE ar.embedding IS NOT NULL
                ORDER BY ar.embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, top_k))

            for row in cur.fetchall():
                results.append({
                    "chunk_id": row[0],
                    "section_title": "과거 낙상 판단 이력",
                    "text": (
                        f"센서요약: CSI변화율={row[6]}, PIR={row[7]}, ToF변화={row[8]}mm\n"
                        f"판단결과: {'낙상' if row[2] else '정상'} "
                        f"(신뢰도: {row[3]}, 위험도: {row[4]})\n"
                        f"상황요약: {row[5]}\n"
                        f"판단근거: {row[6]}"
                    ),
                    "metadata": {
                        "is_fall": row[2],
                        "risk_level": row[4],
                        "source": "event_history"
                    },
                    "final_score": float(row[9]),
                })

        return results