import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from open_parcel.db.models import EMBEDDING_DIM, DocumentChunk

load_dotenv()

REQUIRED_COLUMNS = ["chunk_id", "doc_id", "text", "chapter", "section", "link"]


def get_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def load_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    validate_required_columns(df)
    return df


def main() -> None:
    engine = create_engine(get_url())
    df = load_dataframe("data/toronto/output/bylaw_processed.csv")

    with Session(engine) as session:
        chunks = [
            DocumentChunk(
                chunk_index=int(row["chunk_id"]),
                document_index=int(row["doc_id"]),
                content=str(row["text"]),
                chapter=row["chapter"],
                section=row["section"],
                page=row["link"],
                embedding=[0.0] * EMBEDDING_DIM,
            )
            for row in df[REQUIRED_COLUMNS].to_dict("records")
        ]

        session.add_all(chunks)
        session.commit()


if __name__ == "__main__":
    main()
