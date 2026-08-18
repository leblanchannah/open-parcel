import os

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from open_parcel.db.models import EMBEDDING_DIM, DocumentChunk

load_dotenv()


def get_url() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(get_url())
df = pd.read_csv("data/toronto/output/bylaw_processed.csv")
df = df.where(pd.notna(df), "")  # NaN -> None everywhere

with Session(engine) as session:
    chunks = [
        DocumentChunk(
            chunk_index=row["chunk_id"],
            document_index=row["doc_id"],
            content=row["text"],
            chapter=row["chapter"],
            section=row["section"],
            page=row["link"],
            embedding=np.random.rand(EMBEDDING_DIM).tolist(),
        )
        for row in df.to_dict("records")
    ]

    session.add_all(chunks)
    session.commit()
