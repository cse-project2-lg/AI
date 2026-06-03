import re
from app.rag.schemas.document import Document

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
    SRS 문서의 목차 영역을 제거한다.

    제거 기준:
    - '목 차' 또는 '목차'가 등장하면 목차 시작으로 판단
    - 이후 실제 본문 시작인 'Introduction (개요)'가 나오기 전까지 제거
    - 목차 제목이 깨져서 일부 항목만 남는 경우도 추가 제거
    """

    lines = text.split("\n")
    cleaned_lines = []

    in_toc_area = False
    toc_started = False

    toc_title_pattern = re.compile(r"^\s*목\s*차\s*$")
    intro_body_pattern = re.compile(r"^\s*Introduction\s*\(개요\)\s*$")
    toc_line_pattern = re.compile(r"^\s*\d+(\.\d+)*\.?\s+.+\s+\d+\s*$")

    for line in lines:
        stripped = line.strip()

        # 목차 제목 발견
        if toc_title_pattern.match(stripped):
            in_toc_area = True
            toc_started = True
            continue

        # 목차 영역 이후 실제 본문 시작 발견
        if in_toc_area and intro_body_pattern.match(stripped):
            in_toc_area = False
            cleaned_lines.append(line)
            continue

        # 목차 영역 안의 모든 줄 제거
        if in_toc_area:
            continue

        # 목차 제목 탐지가 불완전했을 경우를 대비해
        # 문서 초반의 "section 번호 + 제목 + 페이지번호" 형태 줄 제거
        if not toc_started and toc_line_pattern.match(stripped):
            continue

        # 목차 제거 후 남은 잔여 목차 줄 제거
        if toc_started and toc_line_pattern.match(stripped):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


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