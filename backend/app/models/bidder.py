from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Bidder(Base):
    __tablename__ = "bidders"
    __table_args__ = (UniqueConstraint("tender_id", "bidder_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    bidder_id: Mapped[str] = mapped_column(String(50))
    bidder_name: Mapped[str] = mapped_column(String(500))
    source_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_status: Mapped[str] = mapped_column(String(50), default="NOT_EVALUATED")
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
