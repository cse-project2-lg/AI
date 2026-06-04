from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime, timezone


@dataclass
class Document:
    """
    <원본 문서 단위의 데이터 구조>
    ingestion 파이프라인의 시작점이며
    이후 cleaning → chunking → metadata 부여의 기준이 되는 핵심 데이터 구조
    """

    # 기본 식별 정보
    doc_id: str                          # 고유 문서 ID 
    source: str                          # 파일 경로

    # 콘텐츠
    text: str                            # 원본 텍스트
    cleaned_text: Optional[str] = None   # 정제된 텍스트

    # 문서 메타 
    title: Optional[str] = None          # 문서 제목
    doc_type: Optional[str] = None       # srs / policy / rule

    # 추적/디버깅
    created_at: datetime = field(default_factory=datetime.utcnow)
    extra_metadata: Dict = field(default_factory=dict)

    def get_active_text(self) -> str:

        return self.cleaned_text if self.cleaned_text else self.text

    def to_dict(self) -> Dict:

        return {
            "doc_id": self.doc_id,
            "source": self.source,
            "text": self.text,
            "cleaned_text": self.cleaned_text,
            "title": self.title,
            "doc_type": self.doc_type,
            "created_at": self.created_at.isoformat(),
            "extra_metadata": self.extra_metadata,
        }