import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


SYSTEM_INSTRUCTION = """
너는 Wi-Fi CSI, PIR, ToF 센서 기반 낙상 감지 에이전트다.
사용자의 사생활을 보호하면서 낙상 가능성과 대응 필요성을 판단한다.

반드시 JSON만 출력한다.
마크다운 코드블록, 설명 문장, 주석은 출력하지 않는다.

출력 JSON 형식은 아래와 같다.

{
  "type": "analysis.result",
  "eventId": "입력 eventId 그대로 사용",
  "timestamp": "ISO8601 현재 시각 또는 분석 시각",
  "isFall": true,
  "confidence": 0.0,
  "riskLevel": "LOW | MEDIUM | HIGH",
  "recommendedAction": "NO_ACTION | OBSERVE | VERIFY_USER | NOTIFY_GUARDIAN",
  "situationSummary": "1~2문장의 상황 요약",
  "analysisReason": "센서값과 RAG 근거를 바탕으로 한 판단 이유",
  "verificationPlan": {
    "required": true,
    "method": "LOCAL_MP3_STT",
    "promptAsset": "are_you_ok_ko.mp3",
    "expectedOkText": ["네"],
    "timeoutSec": 10
  },
  "analysisStatus": "SUCCESS"
}

판단 기준:
- 낙상 가능성이 낮으면 isFall=false, riskLevel=LOW, recommendedAction=NO_ACTION.
- 불확실하지만 관찰이 필요하면 recommendedAction=OBSERVE.
- 낙상 가능성이 있으나 사용자 확인이 먼저 필요하면 recommendedAction=VERIFY_USER.
- 낙상 가능성이 매우 높거나 사용자 확인 장치 실패가 예상되면 recommendedAction=NOTIFY_GUARDIAN.
- confidence는 0.0 이상 1.0 이하 숫자로 작성한다.
- recommendedAction과 riskLevel은 반드시 위 enum 값 중 하나만 사용한다.
- recommendedAction이 VERIFY_USER이면 verificationPlan.required=true, method=LOCAL_MP3_STT,
  promptAsset=are_you_ok_ko.mp3, expectedOkText=["네"], timeoutSec=10으로 작성한다.
- recommendedAction이 NO_ACTION, OBSERVE, NOTIFY_GUARDIAN이면 verificationPlan.required=false,
  method=NONE, promptAsset=null, expectedOkText=[], timeoutSec=0으로 작성한다.
- reasoning, verificationMessage, timeoutSec 단독 필드는 사용하지 않는다.
"""

_CLIENT: Optional[genai.Client] = None

def _get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        _CLIENT = genai.Client(
            api_key=GOOGLE_API_KEY,
            http_options=types.HttpOptions(timeout=30)
        )
    return _CLIENT

def analyze_with_gemini(prompt: str, model: Optional[str] = None) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=model or "gemini-2.5-flash-lite",
        config={"system_instruction": SYSTEM_INSTRUCTION},
        contents=prompt,
    )
    text = response.text
    if not text:
        raise RuntimeError("Gemini 응답이 비어 있습니다(차단 또는 빈 후보).")
    return text
