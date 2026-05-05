import os
from dotenv import load_dotenv
from google import genai
import json

# 1. API 키 설정
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=GOOGLE_API_KEY)

# 2. 시스템 프롬프트 정의
system_instruction = """
너는 Wi-Fi CSI 및 IoT 센서 기반의 낙상 감지 에이전트야. 
사용자의 사생활을 보호하면서 정확한 응급 상황을 판단하는 것이 네 임무야.

[판단 원칙 및 우선순위]
1. 인체 감지(PIR) 우선순위: PIR이 False라면 열을 가진 '사람'의 움직임이 없다는 뜻이야. 
   - CSI 변동이 크고 ToF가 낮더라도 PIR이 계속 False라면 '사람의 낙상'이 아닌 '무생물(스마트폰 등) 낙하'로 판단해.
2. 높이 판단 기준(ToF): 
   - 400mm 이상: 앉기, 눕기 등 정상 활동으로 간주.
   - 300mm 이하: 바닥 낙상 후보로 간주.
3. 무동작의 해석: 낙상 의심 정황(CSI 급변 + ToF 급락) 직후의 PIR 무동작(False)은 의식 불명이나 정지 상태를 나타내는 고위험 지표로 해석해.

[응답 형식] 반드시 아래의 JSON 형식으로만 답변해.
{
  "eventId": "EVT_001",
  "isFall": true/false,
  "confidence": 0.0~1.0,
  "riskLevel": "LOW/MEDIUM/HIGH",
  "situationSummary": "상황 요약 문장",
  "reasoning": "판단 근거",
  "recommendedAction": "즉시 알림 권장/사용자 확인 후 알림/추가 관찰 필요",
  "verificationMessage": "사용자에게 보낼 확인 문구"
}
"""

# 3. 가짜 센서 데이터
mock_sensor_data = {
    "csi_variation": 0.85,
    "pir_motion": False,
    "tof_distance_mm": 200,
    "duration_sec": 10
}

# '평상시 빈 방' 상황 시뮬레이션
empty_room_data = {
    "csi_variation": 0.05,     # 매우 안정적
    "pir_motion": False,        # 움직임 없음
    "tof_distance_mm": 1500,   # 천장/벽까지의 정상 거리
    "duration_sec": 60         # 1분째 이 상태
}

sitting_data = {
    "csi_variation": 0.6,      # 앉는 동작으로 인한 중간 정도의 흔들림
    "pir_motion": True,        # 앉는 순간 움직임 감지
    "tof_distance_mm": 550,    # 바닥(200)이 아닌 의자/소파 높이(550mm)
    "duration_sec": 5
}

dropping_object_data = {
    "csi_variation": 0.9,      # 물체가 떨어지며 강한 신호 산란 발생
    "pir_motion": False,       # 물체는 열이 없으므로 PIR은 조용함
    "tof_distance_mm": 100,    # 바닥에 물체가 닿음
    "duration_sec": 3
}

# 4. 분석 요청 (새로운 라이브러리 방식)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    config={"system_instruction": system_instruction},
    contents=f"아래 센서 데이터를 분석해서 낙상 여부를 판정해줘:\n{sitting_data}"
)

# 5. 결과 출력
print("--- AI 분석 결과 ---")
# .text 대신 직접 응답 객체에서 텍스트를 추출합니다.
print(response.text)