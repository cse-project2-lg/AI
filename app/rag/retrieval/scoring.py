from typing import Dict, Any, List


PRIORITY_SCORE = {
    "high": 0.08,
    "medium": 0.04,
    "low": 0.0,
}


CATEGORY_SCORE = {
    "sensor": 0.08,
    "fall_detection": 0.08,
    "notification": 0.06,
    "system": 0.02,
}

# query에 metadata keywords가 얼마나 포함되어 있는지 기반으로 점수를 계산
def calculate_keyword_score(query: str, keywords: List[str]) -> float:

    if not keywords:
        return 0.0

    normalized_query = query.lower()
    matched_count = 0

    for keyword in keywords:
        if keyword.lower() in normalized_query:
            matched_count += 1

    return matched_count * 0.04


def calculate_metadata_score(metadata: Dict[str, Any]) -> float:

    priority = metadata.get("priority", "low")
    category = metadata.get("category", "")

    priority_score = PRIORITY_SCORE.get(priority, 0.0)
    category_score = CATEGORY_SCORE.get(category, 0.0)

    return priority_score + category_score


def calculate_final_score(
    embedding_score: float,
    keyword_score: float,
    metadata_score: float,
) -> float:

    return embedding_score + keyword_score + metadata_score