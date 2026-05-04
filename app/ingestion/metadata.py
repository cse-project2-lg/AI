import re
from typing import List

from app.schemas.chunk import Chunk


HIGH_PRIORITY_KEYWORDS = [
    "낙상",
    "fall",
    "긴급",
    "응급",
    "보호자 알림",
    "낙상 의심",
    "이상 행동",
    "위험",
]

SENSOR_KEYWORDS = [
    "Wi-Fi CSI",
    "CSI",
    "PIR",
    "ToF",
    "센서",
    "Channel State Information",
    "움직임",
    "거리",
    "신호",
]

NOTIFICATION_KEYWORDS = [
    "보호자",
    "알림",
    "메시지",
    "푸시",
    "TTS",
    "음성 안내",
    "응답 없음",
    "사용자 응답",
]

SYSTEM_KEYWORDS = [
    "시스템",
    "아키텍처",
    "구성",
    "모듈",
    "환경",
    "배포",
    "설치",
    "운영",
]

REQUIREMENT_KEYWORDS = [
    "요구사항",
    "해야 한다",
    "기능적 요구사항",
    "비기능 요구사항",
    "성능",
    "보안",
    "가용성",
    "확장성",
]

# 문서에서 자주 나오는 섹션 제목들
# chunking 시 섹션 제목을 기준으로 내용을 묶기 위해 사용
def enrich_chunk_metadata(chunks: List[Chunk]) -> List[Chunk]:

    enriched_chunks = []

    for index, chunk in enumerate(chunks, start=1):
        text = chunk.text
        section_title = chunk.metadata.get("section_title", "")

        requirement_ids = _extract_requirement_ids(text)

        chunk.metadata.update(
            {
                "chunk_index": index,
                "category": _classify_category(text, section_title),
                "keywords": _extract_keywords(text),
                "priority": _classify_priority(text),
                "chunk_length": len(text),
                "contains_requirement_id": len(requirement_ids) > 0,
                "requirement_ids": requirement_ids,
            }
        )

        enriched_chunks.append(chunk)

    return enriched_chunks


def _classify_category(text: str, section_title: str) -> str:
    """
    chunk 내용을 기반으로 category를 분류한다.

    분류 우선순위:
    1. 명확한 문서/개요성 섹션은 general
    2. 기능/비기능 요구사항은 requirement
    3. 알림 관련 내용은 notification
    4. 센서 관련 내용은 sensor
    5. 시스템 구성/환경은 system
    """

    title = section_title.lower()
    target = f"{section_title}\n{text}"

    general_titles = [
        "purpose",
        "product scope",
        "document conventions",
        "terms and abbreviations",
        "intended audience",
        "related documents",
        "project output",
    ]

    if any(keyword in title for keyword in general_titles):
        return "general"

    if "requirement" in title or "요구사항" in section_title:
        return "requirement"

    notification_score = _count_keywords(target, NOTIFICATION_KEYWORDS)
    sensor_score = _count_keywords(target, SENSOR_KEYWORDS)
    system_score = _count_keywords(target, SYSTEM_KEYWORDS)
    requirement_score = _count_keywords(target, REQUIREMENT_KEYWORDS)

    scores = {
        "notification": notification_score,
        "sensor": sensor_score,
        "system": system_score,
        "requirement": requirement_score,
    }

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "general"

    return best_category


def _extract_keywords(text: str) -> List[str]:

    all_keywords = (
        HIGH_PRIORITY_KEYWORDS
        + SENSOR_KEYWORDS
        + NOTIFICATION_KEYWORDS
        + SYSTEM_KEYWORDS
        + REQUIREMENT_KEYWORDS
    )

    found_keywords = []

    for keyword in all_keywords:
        if keyword.lower() in text.lower():
            found_keywords.append(keyword)

    return sorted(set(found_keywords))


def _classify_priority(text: str) -> str:
    """
    chunk의 중요도를 분류
        high: 낙상 판단, 보호자 알림, 긴급/응급 대응
        medium: 센서, 요구사항, 시스템 구성
        low: 문서 설명, 용어, 일반 안내
    """

    high_score = _count_keywords(text, HIGH_PRIORITY_KEYWORDS)

    if high_score >= 2:
        return "high"

    if high_score == 1 and _contains_any(text, NOTIFICATION_KEYWORDS + SENSOR_KEYWORDS):
        return "high"

    if _contains_any(text, SENSOR_KEYWORDS + NOTIFICATION_KEYWORDS + REQUIREMENT_KEYWORDS):
        return "medium"

    return "low"


def _extract_requirement_ids(text: str) -> List[str]:

    pattern = re.compile(r"\b(?:FR|NFR)-[A-Z]+-\d{3}\b")
    return pattern.findall(text)


def _contains_any(text: str, keywords: List[str]) -> bool:

    lower_text = text.lower()

    return any(keyword.lower() in lower_text for keyword in keywords)

# chunk metadata enrichment 과정에서 chunk text와 섹션 제목을 활용하여 category, priority, keywords 등을 추출
def _count_keywords(text: str, keywords: List[str]) -> int:

    lower_text = text.lower()

    return sum(1 for keyword in keywords if keyword.lower() in lower_text)