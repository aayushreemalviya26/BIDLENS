from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (UniqueConstraint("tender_id", "requirement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    operator: Mapped[str] = mapped_column(String(50), default="MANUAL_REVIEW")
    required_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    required_document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    source_clause: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    rule_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
