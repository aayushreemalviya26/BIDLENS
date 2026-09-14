from sqlalchemy import inspect, text

from .base import Base
from .session import engine


def init_db() -> None:
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Lightweight compatibility migration for demo databases created before
    # original-upload provenance was persisted on classified documents.
    columns = {column["name"] for column in inspect(engine).get_columns("bidder_documents")}
    if "uploaded_file_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE bidder_documents ADD COLUMN uploaded_file_id INTEGER REFERENCES bidder_uploaded_files(id)"))
