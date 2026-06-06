from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="CANDIDATE",
    )
    rule_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    window_summaries: Mapped[list["EventWindowSummary"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    voice_interactions: Mapped[list["VoiceInteraction"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    response_outcomes: Mapped[list["ResponseOutcome"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    embeddings: Mapped[list["EventEmbedding"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    status_histories: Mapped[list["EventStatusHistory"]] = relationship(
    back_populates="event",
    cascade="all, delete-orphan",
    )


class EventWindowSummary(Base):
    __tablename__ = "event_window_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    window_start: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    window_end: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    pir_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tof_distance: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    csi_change_score: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="window_summaries")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    llm_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="analysis_results")


class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    stt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="voice_interactions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    guardian_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notification_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sent_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="notifications")


class ResponseOutcome(Base):
    __tablename__ = "response_outcomes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    final_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="response_outcomes")


class EventEmbedding(Base):
    __tablename__ = "event_embeddings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    # SQLAlchemy declarative model에서 metadata는 예약어라서
    # Python 속성명은 metadata_로 두고, 실제 DB 컬럼명은 "metadata"로 매핑한다.
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="embeddings")


class EventStatusHistory(Base):
    __tablename__ = "event_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    event: Mapped[Event] = relationship(back_populates="status_histories")