from typing import List, Dict, Any


INTENT_KEYWORDS = {
    "fall_detection": ["낙상", "후보", "감지", "탐지", "판단", "판정", "분석", "기준"],
    "sensor": ["PIR", "ToF", "CSI", "센서", "거리", "움직임", "신호"],
    "notification": ["알림", "보호자", "응급", "TTS", "대응"],
    "communication": ["통신", "전달", "MQTT", "메시지", "인터페이스"],
    "user_confirmation": ["확인", "절차", "괜찮으신가요", "사용자", "응답"],
    "admin_display": ["관리자", "화면", "디스플레이", "표시", "로그", "상태"],
    "llm_failure": ["클라우드", "LLM", "AI", "실패", "장애", "오류", "대응", "fallback", "대체"],
    "installation": ["설치", "구성", "환경", "드라이버", "의존성", "배선"],
}


SECTION_BOOST_KEYWORDS = {
    "fall_detection": ["동작", "분석", "판정", "감지", "탐지", "대응", "operation"],
    "sensor": ["interface", "hardware", "sensor", "센서", "인터페이스"],
    "notification": ["알림", "대응", "notification", "response", "communication"],
    "communication": ["communication", "interface", "통신", "인터페이스"],
    "user_confirmation": ["user interface", "communication", "사용자", "인터페이스", "동작", "대응"],
    "admin_display": ["user interface", "사용자 인터페이스", "display", "admin", "관리자"],
    "llm_failure": ["software", "communication", "operation", "reliability", "availability", "인터페이스", "동작"],
    "installation": ["installation", "configuration", "설치", "설정"],
}


TEXT_BOOST_KEYWORDS = {
    "fall_detection": ["낙상 후보", "낙상", "탐지", "판정", "판단", "분석 단계", "판정 단계"],
    "sensor": ["PIR", "ToF", "CSI", "거리", "움직임", "신호", "센서"],
    "notification": ["보호자", "알림", "응급", "TTS", "음성 안내"],
    "communication": ["MQTT", "HTTP", "topic", "메시지", "전송", "통신"],
    "user_confirmation": ["괜찮으신가요", "사용자 확인", "응답", "다시 움직임", "이벤트를 종료"],
    "admin_display": ["관리자", "7인치", "디스플레이", "LLM 분석 전후", "상태", "로그", "표시"],
    "llm_failure": ["실패", "장애", "fallback", "대체", "로컬", "재시도", "오류", "클라우드"],
}


INTENT_CATEGORY_PREFERENCE = {
    "fall_detection": ["sensor", "notification", "system"],
    "sensor": ["sensor"],
    "notification": ["notification"],
    "communication": ["notification", "sensor"],
    "user_confirmation": ["notification", "sensor"],
    "admin_display": ["notification", "system"],
    "llm_failure": ["system", "notification", "sensor"],
}


def infer_query_intents(query: str) -> List[str]:
    """
    query에 포함된 단어를 기반으로 사용자의 검색 의도를 추정한다.

    예:
    - '낙상 후보 판단 기준' → fall_detection
    - 'PIR ToF 센서 데이터' → sensor
    - '보호자 알림 방식' → notification
    """

    normalized_query = query.lower()
    matched_intents = []

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in normalized_query:
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
        for keyword in SECTION_BOOST_KEYWORDS.get(intent, []):
            if keyword.lower() in section_title:
                boost += 0.06
                break

    return boost

def calculate_text_boost(text: str, intents: List[str]) -> float:
    """
    chunk 본문에 query 의도와 직접 관련된 표현이 있으면 boost를 부여한다.
    """

    normalized_text = text.lower()
    boost = 0.0

    for intent in intents:
        matched_count = 0

        for keyword in TEXT_BOOST_KEYWORDS.get(intent, []):
            if keyword.lower() in normalized_text:
                matched_count += 1

        boost += min(matched_count * 0.03, 0.12)

    return boost

def calculate_category_penalty(metadata: Dict[str, Any], intents: List[str]) -> float:

    category = metadata.get("category", "")

    if not category:
        return 0.0

    penalty = 0.0

    for intent in intents:
        preferred_categories = INTENT_CATEGORY_PREFERENCE.get(intent)

        if preferred_categories and category not in preferred_categories:
            penalty += 0.04

    return min(penalty, 0.12)

# query의 의도와 chunk의 section context가 어긋나는 경우 감점
def calculate_context_penalty(metadata: Dict[str, Any], intents: List[str]) -> float:

    section_title = metadata.get("section_title", "").lower()

    if not section_title:
        return 0.0

    penalty = 0.0

    if "fall_detection" in intents or "sensor" in intents:
        weak_context_words = ["installation", "configuration", "설치", "설정"]
        for word in weak_context_words:
            if word in section_title:
                penalty += 0.08
                break

    if "admin_display" in intents:
        weak_context_words = ["hardware environment", "product installation", "사용자 계층"]
        for word in weak_context_words:
            if word in section_title:
                penalty += 0.08
                break

    if "llm_failure" in intents:
        weak_context_words = ["user classes", "사용자 계층", "hardware environment", "제품 설치"]
        for word in weak_context_words:
            if word in section_title:
                penalty += 0.08
                break

    return penalty

# query의 핵심 키워드를 기반으로 intent별 가중치를 계산
def calculate_intent_weights(query: str) -> Dict[str, float]:

    weights = {}

    normalized_query = query.lower()

    # 기본 가중치
    for intent in INTENT_KEYWORDS.keys():
        weights[intent] = 1.0

    # 역할 관련 질문 → sensor 강화
    if "역할" in normalized_query or "어떻게 활용" in normalized_query:
        weights["sensor"] += 0.5
        weights["fall_detection"] += 0.3

    # 통신 관련 질문 → communication 강화
    if "통신" in normalized_query or "전달" in normalized_query:
        weights["communication"] += 0.6
        weights["notification"] += 0.3

        # hardware는 약간 깎기
        weights["sensor"] -= 0.2

    # 확인 절차 질문
    if "확인" in normalized_query or "절차" in normalized_query:
        weights["user_confirmation"] += 0.6

    # 관리자 화면 질문
    if "관리자" in normalized_query or "화면" in normalized_query:
        weights["admin_display"] += 0.7

    # 실패 대응 질문
    if "실패" in normalized_query or "장애" in normalized_query:
        weights["llm_failure"] += 0.7

    return weights

# 검색 결과를 재정렬 
def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    1차 검색 결과를 query intent, section_title, chunk text, category 기반으로 재정렬한다.
    """

    intents = infer_query_intents(query)
    intent_weights = calculate_intent_weights(query)
    reranked_results = []

    for result in results:
        metadata = result.get("metadata", {})
        text = result.get("text", "")

        section_boost = calculate_section_boost(metadata, intents)
        context_penalty = calculate_context_penalty(metadata, intents)

        text_boost = 0.0

        for intent in intents:
            weight = intent_weights.get(intent, 1.0)

            matched_count = 0
            for keyword in TEXT_BOOST_KEYWORDS.get(intent, []):
                if keyword.lower() in text.lower():
                    matched_count += 1

            text_boost += min(matched_count * 0.03, 0.12) * weight
        
        category_penalty = 0.0

        category = metadata.get("category", "")

        for intent in intents:
            preferred = INTENT_CATEGORY_PREFERENCE.get(intent)
            weight = intent_weights.get(intent, 1.0)

            if preferred and category not in preferred:
                category_penalty += 0.04 * weight

        category_penalty = min(category_penalty, 0.15)

        rerank_score = (
            result["final_score"]
            + section_boost
            + text_boost
            - category_penalty
            - context_penalty
        )

        reranked_results.append(
            {
                **result,
                "intents": intents,
                "intent_weights": intent_weights,
                "section_boost": section_boost,
                "text_boost": text_boost,
                "category_penalty": category_penalty,
                "context_penalty": context_penalty,
                "rerank_score": rerank_score,
            }
        )

    reranked_results.sort(key=lambda item: item["rerank_score"], reverse=True)

    return reranked_results