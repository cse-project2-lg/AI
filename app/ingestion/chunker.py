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

    # 길이 기준
    if len(line) < 3:
        return False

    # 문장 형태 제거
    if line.endswith("."):
        return False

    # 괄호 포함
    if "(" in line and ")" in line:
        return True

    # 영어 + 한글 혼합 제목
    if re.match(r"^[A-Za-z\s]+\(.+\)", line):
        return True

    return False

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