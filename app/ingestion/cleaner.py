import re
from app.schemas.document import Document

# Document 객체의 원본 텍스트를 정제하고 cleaned_text에 저장

def clean_document(document: Document) -> Document:
    """
    정제 목표:
    1. 과도한 공백 제거
    2. 깨진 줄바꿈 정리
    3. 목차 영역 제거
    4. SRS 번호 체계 보존
    5. 요구사항 ID 보존
    """

    raw_text = document.text

    cleaned_text = raw_text

    cleaned_text = _normalize_line_endings(cleaned_text)
    cleaned_text = _remove_table_of_contents(cleaned_text)
    cleaned_text = _normalize_spaces(cleaned_text)
    cleaned_text = _normalize_blank_lines(cleaned_text)
    cleaned_text = _strip_lines(cleaned_text)

    document.cleaned_text = cleaned_text

    document.extra_metadata["cleaning"] = {
        "original_length": len(raw_text),
        "cleaned_length": len(cleaned_text),
        "removed_chars": len(raw_text) - len(cleaned_text),
    }

    return document

# 운영체제마다 다른 줄바꿈 문자를 \n으로 통일한다.
def _normalize_line_endings(text: str) -> str:

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _remove_table_of_contents(text: str) -> str:
    """
    문서 앞부분의 목차 영역을 제거

    ( SRS 문서는 초반에 목차가 포함되어 있는데,
      목차의 1.1, 1.2 같은 번호가 실제 본문 section으로 오인될 수 있다.
      따라서 '목 차' 이후부터 실제 1 Introduction 시작 전까지 제거)
    """

    toc_pattern = re.compile(
        r"목\s*차.*?(?=\n1\s+Introduction|\n1\s+개요|\n1\s+Introduction\s*\(개요\))",
        re.DOTALL,
    )

    return re.sub(toc_pattern, "", text)


def _normalize_spaces(text: str) -> str:
    # 줄 내부의 과도한 공백을 하나로 줄인다. 단, 줄바꿈은 유지한다.

    lines = text.split("\n")
    normalized_lines = []

    for line in lines:
        normalized_line = re.sub(r"[ \t]+", " ", line)
        normalized_lines.append(normalized_line)

    return "\n".join(normalized_lines)

# 3줄 이상의 연속 빈 줄을 2줄로 줄인다.
def _normalize_blank_lines(text: str) -> str:
 
    return re.sub(r"\n{3,}", "\n\n", text)

# 각 줄의 앞뒤 공백을 제거한다. 문단 내부의 내용은 유지
def _strip_lines(text: str) -> str:

    lines = text.split("\n")
    stripped_lines = [line.strip() for line in lines]

    return "\n".join(stripped_lines).strip()