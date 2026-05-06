from typing import List
import math

# 두 embedding 벡터 간의 cosine similarity를 계산
def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:

    if len(vector_a) != len(vector_b):
        raise ValueError("두 벡터의 차원이 서로 다릅니다.")

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))

    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)