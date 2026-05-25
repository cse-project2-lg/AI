from typing import Any, Dict, List

from app.rag.context.context_builder import build_context_summary


def build_rag_prompt(
    sensor_event: Dict[str, Any],
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    summarized_chunks = build_context_summary(retrieved_chunks)

    evidence_blocks = []
    for item in summarized_chunks:
        score = item.get("score")
        score_text = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"
        evidence_blocks.append(
            f"""
[근거 {item.get('index')}]
section_title: {item.get('section_title')}
chunk_index: {item.get('chunk_index')}
score: {score_text}

핵심 요약:
{item.get('summary')}
""".strip()
        )

    evidence_text = "\n\n".join(evidence_blocks) if evidence_blocks else "검색된 근거 없음"

    prompt = f"""
너는 Wi-Fi CSI, PIR, ToF 센서 기반 낙상 감지 시스템의 판단 보조 모델이다.

너의 역할은 센서 이벤트와 검색된 SRS 근거 문서를 바탕으로
낙상 여부, 위험도, 권장 대응, 사용자 확인 문구를 판단하는 것이다.

반드시 아래 규칙을 지켜라.

1. 검색된 근거 문서를 우선 근거로 사용한다.
2. 근거 문서에 없는 내용을 임의로 만들어내지 않는다.
3. 센서 정보가 불충분하면 confidence를 낮게 설정한다.
4. 응답은 반드시 JSON 형식으로만 작성한다.
5. JSON 외의 설명 문장, 마크다운 코드블록, 주석은 출력하지 않는다.
6. eventId는 입력 sensor_event의 eventId 값을 그대로 사용한다.
7. enum 값은 지정된 값만 사용한다.

[센서 이벤트]
{sensor_event}

[검색 Query]
{query}

[검색된 근거 문서]
{evidence_text}

[출력 JSON 형식]
{{
  "eventId": "입력 sensor_event의 eventId 그대로 사용",
  "isFall": true,
  "confidence": 0.0,
  "riskLevel": "LOW | MEDIUM | HIGH",
  "recommendedAction": "NO_ACTION | OBSERVE | VERIFY_USER | NOTIFY_GUARDIAN",
  "situationSummary": "1~2문장의 상황 요약",
  "reasoning": "센서값과 검색 근거를 바탕으로 한 판단 이유",
  "verificationMessage": "사용자 확인이 필요할 때만 작성, 아니면 빈 문자열",
  "timeoutSec": 10
}}

[recommendedAction 기준]
- NO_ACTION: 낙상 가능성이 낮아 추가 대응이 필요 없음
- OBSERVE: 불확실하여 추가 관찰이 필요함
- VERIFY_USER: 사용자에게 TTS로 상태 확인이 필요함
- NOTIFY_GUARDIAN: 보호자에게 즉시 알림이 필요함
""".strip()

    return prompt
