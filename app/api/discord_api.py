import os
import time
import logger
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = l.getLogger(__name__)

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

DEFAULT_AVATAR_URL = (
    "https://github.com/cse-project2-lg/embedded/blob/feat/discord-notification/"
    "ganadi_emergency.png?raw=true"
)


def _safe_text(value: Optional[str], default: str = "-") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _truncate(value: str, max_len: int = 1000) -> str:
    value = _safe_text(value)
    if len(value) <= max_len:
        return value
    return value[:max_len - 3] + "..."


def send_discord_notification(
    event_id: str,
    situation_summary: str,
    risk_level: str = "HIGH",
    room_id: str = "-",
    escalation_reason: str = "",
    user_response: str = "",
    transcript: str = "",
    timestamp: Optional[str] = None,
) -> dict:
    """
    보호자 알림용 Discord Webhook 전송 함수.
    main.py의 /api/v1/notifications/guardian 엔드포인트에서 호출한다.
    """

    if not WEBHOOK_URL:
        error_message = ".env 파일에 DISCORD_WEBHOOK_URL이 설정되지 않았습니다."
        logger.error(f"에러: {error_message}")
        return {
            "success": False,
            "status_code": None,
            "error": error_message,
        }

    occurred_at = timestamp or time.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "username": "RPi4_Fall_Detector",
        "avatar_url": DEFAULT_AVATAR_URL,
        "embeds": [
            {
                "title": "🚨 [응급 상황] 피보호자 안전 이상 감지",
                "color": 15158332,
                "fields": [
                    {
                        "name": "📌 사건 식별 ID",
                        "value": _truncate(event_id, 1000),
                        "inline": True,
                    },
                    {
                        "name": "⏰ 발생 시각",
                        "value": _truncate(occurred_at, 1000),
                        "inline": True,
                    },
                    {
                        "name": "📍 감지 위치",
                        "value": _truncate(room_id, 1000),
                        "inline": True,
                    },
                    {
                        "name": "📊 위험도",
                        "value": _truncate(risk_level, 1000),
                        "inline": True,
                    },
                    {
                        "name": "🗣 사용자 응답 상태",
                        "value": _truncate(user_response, 1000),
                        "inline": True,
                    },
                    {
                        "name": "🎙 STT 인식 결과",
                        "value": _truncate(transcript, 1000),
                        "inline": False,
                    },
                    {
                        "name": "📝 복합 상황 요약",
                        "value": _truncate(situation_summary, 1000),
                        "inline": False,
                    },
                    {
                        "name": "🚨 보호자 알림 사유",
                        "value": _truncate(escalation_reason, 1000),
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": "경북대학교 종합설계프로젝트 7팀 와사시"
                },
            }
        ],
    }

    logger.info("디스코드 외부 알림 채널 호출 중...")

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=3.0)

        # Discord Webhook은 일반적으로 성공 시 204를 반환한다.
        # wait=true 옵션이 붙는 경우 200이 올 수도 있으므로 둘 다 성공 처리한다.
        if response.status_code in (200, 204):
            logger.info("디스코드 보호자 관제 채널로 비상 알림 전송 성공!")
            return {
                "success": True,
                "status_code": response.status_code,
                "error": None,
            }

        logger.error(f"전송 실패 HTTP 상태 코드: {response.status_code}")
        logger.error(response.text)

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text,
        }

    except Exception as e:
        logger.error(f"디스코드 알림 전송 중 오류 발생: {e}")
        return {
            "success": False,
            "status_code": None,
            "error": str(e),
        }