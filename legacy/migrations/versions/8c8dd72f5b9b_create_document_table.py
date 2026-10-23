"""create document table

Revision ID: 8c8dd72f5b9b
Revises:
Create Date: 2026-08-17 20:39:31.399700

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

EMBEDDING_DIM = 384


# revision identifiers, used by Alembic.
revision: str = "8c8dd72f5b9b"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("document_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chapter", sa.Text()),
        sa.Column("section", sa.Text()),
        sa.Column("page", sa.Text()),
        sa.Column("doc_metadata", postgresql.JSONB()),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("document_index", "chunk_index", name="uq_documents_chunk"),
    )
    op.create_index("ix_documents_chapter", "documents", ["chapter"])
    op.create_index("ix_documents_section", "documents", ["section"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_documents_chapter", table_name="documents")
    op.drop_index("ix_documents_section", table_name="documents")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
