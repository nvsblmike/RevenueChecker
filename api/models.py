import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    assessments: Mapped[list["AssessmentRecord"]] = relationship(back_populates="user")


class AssessmentRecord(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id"), index=True)
    business_name: Mapped[str] = mapped_column(String(120), index=True)
    industry: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="completed", index=True)
    input_data: Mapped[dict] = mapped_column(JSONB)
    report_data: Mapped[dict] = mapped_column(JSONB)
    leakage_low: Mapped[float] = mapped_column(Numeric(18, 2))
    leakage_high: Mapped[float] = mapped_column(Numeric(18, 2))
    recovery_low: Mapped[float] = mapped_column(Numeric(18, 2))
    recovery_high: Mapped[float] = mapped_column(Numeric(18, 2))
    confidence: Mapped[str] = mapped_column(String(20))
    ai_model: Mapped[str] = mapped_column(String(80))
    consent_to_email: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    user: Mapped[AppUser] = relationship(back_populates="assessments")
    email_deliveries: Mapped[list["EmailDelivery"]] = relationship(back_populates="assessment")


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(30), index=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assessment: Mapped[AssessmentRecord] = relationship(back_populates="email_deliveries")
