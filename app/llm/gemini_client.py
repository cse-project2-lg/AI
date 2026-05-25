import os
from typing import Optional

from dotenv import load_dotenv
from google import genai


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


SYSTEM_INSTRUCTION = """
너는 Wi-Fi CSI, PIR, ToF 센서 기반 낙상 감지 에이전트다.
사용자의 사생활을 보호하면서 낙상 가능성과 대응 필요성을 판단한다.

반드시 JSON만 출력한다.
마크다운 코드블록, 설명 문장, 주석은 출력하지 않는다.

출력 JSON 형식은 아래와 같다.

{
  "eventId": "입력 eventId 그대로 사용",
  "isFall": true,
  "confidence": 0.0,
  "riskLevel": "LOW | MEDIUM | HIGH",
  "recommendedAction": "NO_ACTION | OBSERVE | VERIFY_USER | NOTIFY_GUARDIAN",
  "situationSummary": "1~2문장의 상황 요약",
  "reasoning": "센서값과 RAG 근거를 바탕으로 한 판단 이유",
  "verificationMessage": "사용자 확인이 필요할 때만 작성, 아니면 빈 문자열",
  "timeoutSec": 10
}

판단 기준:
- 낙상 가능성이 낮으면 isFall=false, riskLevel=LOW, recommendedAction=NO_ACTION.
- 불확실하지만 관찰이 필요하면 recommendedAction=OBSERVE.
- 낙상 가능성이 있으나 사용자 확인이 먼저 필요하면 recommendedAction=VERIFY_USER.
- 낙상 가능성이 매우 높고 즉시 조치가 필요하면 recommendedAction=NOTIFY_GUARDIAN.
- confidence는 0.0 이상 1.0 이하 숫자로 작성한다.
- recommendedAction과 riskLevel은 반드시 위 enum 값 중 하나만 사용한다.
"""


def _get_client() -> genai.Client:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    return genai.Client(api_key=GOOGLE_API_KEY)


def analyze_with_gemini(prompt: str, model: Optional[str] = None) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=model or "gemini-2.5-flash-lite",
        config={"system_instruction": SYSTEM_INSTRUCTION},
        contents=prompt,
    )
    return response.text
