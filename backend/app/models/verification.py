from sqlalchemy import Boolean, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RegistryVerification(Base):
    __tablename__ = "registry_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(50))
    identifier: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(50))
    matched: Mapped[bool] = mapped_column(Boolean)
    registry_record_json: Mapped[dict] = mapped_column(JSON, default=dict)
    discrepancies_json: Mapped[list] = mapped_column(JSON, default=list)
