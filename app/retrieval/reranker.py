from typing import List, Dict, Any


INTENT_KEYWORDS = {
    "fall_detection": ["낙상", "후보", "감지", "탐지", "판단", "판정", "분석", "기준"],
    "sensor": ["PIR", "ToF", "CSI", "센서", "거리", "움직임", "신호"],
    "notification": ["알림", "보호자", "응급", "TTS", "확인", "대응"],
    "installation": ["설치", "구성", "환경", "드라이버", "의존성", "배선"],
}


SECTION_BOOST_KEYWORDS = {
    "fall_detection": ["동작", "분석", "판정", "감지", "탐지", "대응", "operation"],
    "sensor": ["interface", "hardware", "sensor", "센서", "인터페이스"],
    "notification": ["알림", "대응", "notification", "response"],
    "installation": ["installation", "configuration", "설치", "설정"],
}


def infer_query_intents(query: str) -> List[str]:
    """
    query에 포함된 단어를 기반으로 사용자의 검색 의도를 추정한다.

    예:
    - '낙상 후보 판단 기준' → fall_detection
    - 'PIR ToF 센서 데이터' → sensor
    - '보호자 알림 방식' → notification
    """

    matched_intents = []

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in query.lower():
                matched_intents.append(intent)
                break

    return matched_intents

# query에 포함된 단어를 기반으로 사용자의 검색 의도를 추정
def calculate_section_boost(metadata: Dict[str, Any], intents: List[str]) -> float:

    section_title = metadata.get("section_title", "").lower()

    if not section_title:
        return 0.0

    boost = 0.0

    for intent in intents:
        section_keywords = SECTION_BOOST_KEYWORDS.get(intent, [])

        for keyword in section_keywords:
            if keyword.lower() in section_title:
                boost += 0.05
                break

    return boost


# query의 의도와 chunk의 section context가 어긋나는 경우 감점
def calculate_context_penalty(metadata: Dict[str, Any], intents: List[str]) -> float:

    section_title = metadata.get("section_title", "").lower()

    if not section_title:
        return 0.0

    penalty = 0.0

    wants_fall_detection = "fall_detection" in intents

    if wants_fall_detection:
        installation_words = ["installation", "configuration", "설치", "설정", "환경"]
        for word in installation_words:
            if word in section_title:
                penalty += 0.08
                break

    return penalty


# 검색 결과를 재정렬 
def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    intents = infer_query_intents(query)

    reranked_results = []

    for result in results:
        metadata = result.get("metadata", {})

        section_boost = calculate_section_boost(metadata, intents)
        context_penalty = calculate_context_penalty(metadata, intents)

        rerank_score = result["final_score"] + section_boost - context_penalty

        reranked_result = {
            **result,
            "intents": intents,
            "section_boost": section_boost,
            "context_penalty": context_penalty,
            "rerank_score": rerank_score,
        }

        reranked_results.append(reranked_result)

    reranked_results.sort(key=lambda item: item["rerank_score"], reverse=True)

    return reranked_results