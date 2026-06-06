from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class Event(Base):
    __tablename__ = "events"
    
    __table_args__ = (
        Index("ix_events_created_at_desc", "created_at"),
    )

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="CANDIDATE",
    )
    rule_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
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
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    window_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    window_end: Mapped[datetime | None] = mapped_column(
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="window_summaries")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    llm_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="analysis_results")


class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    stt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="voice_interactions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    guardian_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notification_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="notifications")


class ResponseOutcome(Base):
    __tablename__ = "response_outcomes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    final_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="response_outcomes")


class EventEmbedding(Base):
    __tablename__ = "event_embeddings"

    __table_args__ = (
        Index("ix_event_embeddings_event_id_created_at", "event_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    # SQLAlchemy declarative model에서 metadata는 예약어라서
    # Python 속성명은 metadata_로 두고, 실제 DB 컬럼명은 "metadata"로 매핑한다.
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="embeddings")


class EventStatusHistory(Base):
    __tablename__ = "event_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="status_histories")