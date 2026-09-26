from sqlalchemy import Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BidderDocument(Base):
    __tablename__ = "bidder_documents"
    __table_args__ = (UniqueConstraint("bidder_id", "document_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id", ondelete="CASCADE"), index=True)
    uploaded_file_id: Mapped[int | None] = mapped_column(ForeignKey("bidder_uploaded_files.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100), index=True)
    filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_start: Mapped[int | None] = mapped_column(nullable=True)
    page_end: Mapped[int | None] = mapped_column(nullable=True)
    pages_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="CLASSIFIED")


class BidderUploadedFile(Base):
    __tablename__ = "bidder_uploaded_files"
    __table_args__ = (UniqueConstraint("bidder_id", "filename"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(Text)
    stored_path: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int] = mapped_column()
    page_end: Mapped[int] = mapped_column()
