import re
import uuid
from typing import List

from app.schemas.document import Document
from app.schemas.chunk import Chunk

# Document를 받아서 Chunk 리스트로 분할
def split_into_chunks(document: Document) -> List[Chunk]:
    """
    기준:
    - 제목 기반 분할
    - "제목 + 내용" 단위 유지
    """

    text = document.get_active_text()
    lines = text.split("\n")

    chunks = []

    current_title = None
    current_content = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        # 제목인지 판단
        if _is_section_title(stripped):
            # 기존 chunk 저장
            if current_title and current_content:
                if _is_meaningful_chunk(current_title, current_content):
                    chunk = _build_chunk(
                        document,
                        current_title,
                        current_content
                    )
                    chunks.append(chunk)

            # 새로운 chunk 시작
            current_title = stripped
            current_content = []

        else:
            current_content.append(stripped)

    # 마지막 chunk 처리
    if current_title and current_content:
        if _is_meaningful_chunk(current_title, current_content):
            chunk = _build_chunk(
                document,
                current_title,
                current_content
            )
            chunks.append(chunk)

    return chunks


def _is_section_title(line: str) -> bool:
    """
    제목 여부를 판단한다.

    SRS 문서에서 실제 제목은 보통 다음 특징을 가진다.
    - 영어 제목 + 한글 번역 괄호 형태
    - 비교적 짧은 길이
    - 문장형 서술이 아님
    - 목록 항목이 아님
    """

    if len(line) < 3:
        return False

    if len(line) > 80:
        return False

    if line.endswith((".", "다", "요", "함")):
        return False

    # 목록/본문 항목으로 자주 등장하는 표현은 제목으로 보지 않음
    body_like_keywords = [
        "개발자",
        "담당자",
        "테스터",
        "기획자",
        "평가자",
        "기능",
        "시스템",
        "환경에서",
        "포함되지",
        "활용",
    ]

    if any(keyword in line for keyword in body_like_keywords):
        return False

    # 실제 SRS 제목 형태: English Title (한글)
    english_korean_title_pattern = re.compile(
        r"^[A-Za-z][A-Za-z0-9\s/\-]+ \([가-힣A-Za-z0-9\s/·\-]+\)$"
    )

    if english_korean_title_pattern.match(line):
        return True

    # 큰 장 제목 중 번호가 제거된 경우 대응
    known_section_titles = {
        "Introduction (개요)",
        "Purpose (목표)",
        "Product Scope (범위)",
        "Document Conventions (문서규칙)",
        "Terms and Abbreviations (정의 및 약어)",
        "Related Documents (관련문서)",
        "Intended Audience and Reading Suggestions (대상 및 읽는 방법)",
        "Project Output (프로젝트 산출물)",
        "Overall Description (전체 설명)",
        "Product Perspective (제품 조망)",
        "Overall System Configuration (전체 시스템 구성)",
        "Overall Operation (전체 동작방식)",
        "Product Functions (제품 주요 기능)",
        "User Classes and Characteristics (사용자 계층과 특징)",
        "Assumptions and Dependencies (가정과 종속 관계)",
        "Environment (환경)",
        "Functional Requirements (기능 요구사항)",
        "Non-functional Requirements (비기능 요구사항)",
    }

    return line in known_section_titles

# "제목 + 내용" 단위로 Chunk 객체를 생성
def _build_chunk(document: Document, title: str, content_lines: List[str]) -> Chunk:

    content = "\n".join(content_lines)

    return Chunk(
        chunk_id=str(uuid.uuid4()),
        doc_id=document.doc_id,
        text=f"{title}\n{content}",
        metadata={
            "section_title": title,
            "doc_type": document.doc_type,
            "source": document.source,
        }
    )

def _is_meaningful_chunk(title: str, content_lines: List[str]) -> bool:
    """
    RAG 검색에 사용할 가치가 있는 chunk인지 판단한다.
    """

    content = "\n".join(content_lines).strip()

    if len(content) < 80:
        return False

    skip_titles = {
        "Software Requirements Specification",
        "문서정보 / 수정 내역",
        "Version",
        "Date",
        "Writer",
    }

    if title in skip_titles:
        return False

    if "Wi-Fi CSI" in title and "기반 사용자 행동 인식 시스템" in title:
        return False

    return True