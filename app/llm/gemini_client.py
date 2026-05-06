import os
from dotenv import load_dotenv
from google import genai


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)


SYSTEM_INSTRUCTION = """
너는 Wi-Fi CSI 및 IoT 센서 기반의 낙상 감지 에이전트야. 
사용자의 사생활을 보호하면서 정확한 응급 상황을 판단하는 것이 네 임무야.

[응답 형식] 반드시 아래의 JSON 형식으로만 답변해.
{
  "eventId": "이벤트 고유 ID",
  "isFall": 낙상 확정 시 true/낙상이 아닐 시 false,
  "confidence": 0.0~1.0 사이의 판단 신뢰도,
    // 예: 0.9 이상 = 매우 확실, 0.6~0.9 = 보통, 0.6 미만 = 불확실
  "riskLevel": "LOW/MEDIUM/HIGH",
    // 위험도 3단계
    // "LOW"    = 낮음 (일상적 움직임)
    // "MEDIUM" = 중간 (불확실하거나 경미한 낙상)
    // "HIGH"   = 높음 (명확한 낙상 또는 장시간 미동)
  "situationSummary": "1~2문장의 상황 요약 문장",
  "reasoning": "왜 이렇게 판단했는지 근거 설명 (센서값, 패턴 등 구체적으로)",
  "recommendedAction": "즉시 알림 권장/사용자 확인 후 알림/추가 관찰 필요",
    // "즉시 알림 권장"       → isFall=true + confidence 높을 때
    // "사용자 확인 후 알림"  → isFall=true + confidence 낮을 때
    // "추가 관찰 필요"       → isFall=false 이지만 불확실할 때
  "verificationMessage": "지금 괜찮으십니까? 괜찮으시다면 '네'라고 대답해주세요."
    // isFall=true일 때만 포함
    // isFall=false일 때는 null 또는 빈 문자열 "" 처리
}
"""


def analyze_with_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        config={"system_instruction": SYSTEM_INSTRUCTION},
        contents=prompt,
    )

    return response.text