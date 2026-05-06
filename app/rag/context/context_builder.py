from typing import List, Dict, Any

def extract_key_sentences(text: str) -> List[str]:

    lines = text.split("\n")

    keywords = [
        "낙상",
        "후보",
        "감지",
        "판정",
        "판단",
        "대응",
        "알림",
        "확인",
        "사용자",
        "보호자",
        "거리",
        "움직임",
        "CSI",
        "PIR",
        "ToF",
    ]

    selected = []

    for line in lines:
        for keyword in keywords:
            if keyword in line:
                selected.append(line.strip())
                break

    # 중복 제거 + 최대 5줄 제한
    unique = list(dict.fromkeys(selected))

    return unique[:5]


# 검색된 chunk들을 근거 요약 형태로 변환
def summarize_chunk(chunk: Dict[str, Any]) -> str:

    metadata = chunk.get("metadata", {})
    text = chunk.get("text", "")

    key_sentences = extract_key_sentences(text)

    if not key_sentences:
        return text[:200]

    summary = " / ".join(key_sentences)

    return summary


# 검색된 chunk들을 근거 요약 형태로 변환
def build_context_summary(
    retrieved_chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    summarized = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})

        summary = summarize_chunk(chunk)

        summarized.append(
            {
                "index": index,
                "section_title": metadata.get("section_title"),
                "chunk_index": metadata.get("chunk_index"),
                "summary": summary,
                "score": chunk.get("rerank_score"),
            }
        )

    return summarized