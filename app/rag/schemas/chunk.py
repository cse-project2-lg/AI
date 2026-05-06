from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime


@dataclass
class Chunk:
    # RAG에서 사용하는 최소 단위 데이터 구조

    # 식별 정보
    chunk_id: str
    doc_id: str

    # 콘텐츠
    text: str

    # 구조 메타데이터
    metadata: Dict = field(default_factory=dict)

    # 추적 정보
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        # JSON 저장용 변환
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }