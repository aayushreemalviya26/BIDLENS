from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[str] = mapped_column(String(50), index=True)
    document_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page: Mapped[int | None] = mapped_column(nullable=True)
    field: Mapped[str | None] = mapped_column(String(300), nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_found: Mapped[bool] = mapped_column(Boolean, default=False)
    ambiguities_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
