from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    __table_args__ = (UniqueConstraint("bidder_id", "requirement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[str] = mapped_column(String(50), index=True)
    machine_status: Mapped[str] = mapped_column(String(50))
    effective_status: Mapped[str] = mapped_column(String(50))
    required: Mapped[str | None] = mapped_column(Text, nullable=True)
    found: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    compliance_check_id: Mapped[int] = mapped_column(ForeignKey("compliance_checks.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(50))
    old_status: Mapped[str] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50))
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(200), default="officer")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ClarificationRequest(Base):
    __tablename__ = "clarification_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    compliance_check_id: Mapped[int] = mapped_column(ForeignKey("compliance_checks.id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
