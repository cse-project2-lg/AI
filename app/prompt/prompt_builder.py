from typing import Dict, Any, List


def build_rag_prompt(
    sensor_event: Dict[str, Any],
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:

    evidence_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})

        evidence_blocks.append(
            f"""
[근거 {index}]
section_title: {metadata.get("section_title", "unknown")}
category: {metadata.get("category", "unknown")}
priority: {metadata.get("priority", "unknown")}
chunk_index: {metadata.get("chunk_index", "unknown")}
score: {chunk.get("rerank_score", 0):.4f}

content:
{chunk.get("text", "")}
""".strip()
        )

    evidence_text = "\n\n".join(evidence_blocks)

    prompt = f"""
너는 Wi-Fi CSI, PIR, ToF 센서 기반 낙상 감지 시스템의 판단 보조 모델이다.

너의 역할은 센서 이벤트와 검색된 SRS 근거 문서를 바탕으로
낙상 후보 여부, 사용자 확인 필요 여부, 보호자 알림 필요 여부, 관리자 표시 정보를 판단하는 것이다.

반드시 아래 규칙을 지켜라.

1. 검색된 근거 문서에 기반해서만 판단한다.
2. 근거 문서에 없는 내용을 임의로 만들어내지 않는다.
3. 판단이 불확실하면 confidence를 낮게 설정한다.
4. 응답은 반드시 JSON 형식으로만 작성한다.
5. JSON 외의 설명 문장은 출력하지 않는다.

[센서 이벤트]
{sensor_event}

[검색 Query]
{query}

[검색된 근거 문서]
{evidence_text}

[출력 JSON 형식]
{{
  "fall_status": "NORMAL | FALL_CANDIDATE | FALL_CONFIRMED | UNCERTAIN",
  "confidence": 0.0,
  "reason": "판단 이유를 근거 기반으로 작성",
  "evidence": [
    {{
      "section_title": "참고한 section_title",
      "chunk_index": "참고한 chunk_index",
      "used_reason": "이 근거를 사용한 이유"
    }}
  ],
  "user_confirmation_required": true,
  "guardian_notification_required": false,
  "admin_display_message": "관리자 화면에 표시할 요약 메시지",
  "recommended_action": "다음 시스템 대응"
}}
""".strip()

    return prompt