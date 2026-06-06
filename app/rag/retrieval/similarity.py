from typing import List
import numpy as np


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """두 embedding 벡터 간의 cosine similarity를 계산
    
    Args:
        vector_a: 첫 번째 임베딩 벡터
        vector_b: 두 번째 임베딩 벡터
        
    Returns:
        -1.0 ~ 1.0 범위의 코사인 유사도
        
    Raises:
        ValueError: 두 벡터의 차원이 다를 경우
    """
    if len(vector_a) != len(vector_b):
        raise ValueError(
            f"두 벡터의 차원이 서로 다릅니다. "
            f"(vector_a: {len(vector_a)}, vector_b: {len(vector_b)})"
        )

    a = np.array(vector_a, dtype=np.float64)
    b = np.array(vector_b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_similarity_batch(
    query: List[float],
    candidates: List[List[float]]
) -> List[float]:
    """쿼리 벡터와 후보 벡터 목록 간의 유사도를 일괄 계산
    
    FR-ANL-018 리랭킹 수행 시 단일 루프 대신 행렬 연산으로 처리하여
    FR-COL-035 처리 지연 시간 요구사항을 만족시킵니다.
    
    Args:
        query: 검색 쿼리 임베딩 벡터
        candidates: 비교 대상 임베딩 벡터 목록
        
    Returns:
        각 후보 벡터와의 유사도 점수 목록 (candidates와 동일한 순서)
    """
    if not candidates:
        return []

    q = np.array(query, dtype=np.float64)
    matrix = np.array(candidates, dtype=np.float64)  # shape: (N, dim)

    norm_q = np.linalg.norm(q)
    if norm_q == 0:
        return [0.0] * len(candidates)

    norms = np.linalg.norm(matrix, axis=1)            # shape: (N,)

    # 0-norm 벡터는 분모가 0이 되므로 임시로 1로 대체 후 결과를 0으로 덮어씀
    safe_norms = np.where(norms == 0, 1.0, norms)
    scores = (matrix @ q) / (safe_norms * norm_q)
    scores[norms == 0] = 0.0

    return scores.tolist()