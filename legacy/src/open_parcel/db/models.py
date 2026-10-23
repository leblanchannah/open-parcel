import datetime as dt

from pgvector.sqlalchemy import Vector
from sqlalchemy import Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class DocumentChunk(Base):
    """A single chunk of bylaw text"""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("document_index", "chunk_index", name="uq_doc_chunk"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    document_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    chapter: Mapped[str | None] = mapped_column(Text, index=True)
    section: Mapped[str | None] = mapped_column(Text, index=True)
    page: Mapped[str | None] = mapped_column(Text)

    # everything else, still-evolving / city-specific shape
    doc_metadata: Mapped[dict | None] = mapped_column(JSONB)  # e.g. chapter, section, page
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
