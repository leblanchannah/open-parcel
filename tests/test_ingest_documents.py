import pandas as pd
import pytest

from open_parcel.ingest.documents import validate_required_columns


def test_valid_dataframe_passes():
    df = pd.DataFrame(
        [
            {
                "chunk_id": 0,
                "doc_id": 0,
                "text": "hello",
                "chapter": "1",
                "section": "1.1",
                "link": "chapter1.htm",
            }
        ]
    )

    assert validate_required_columns(df) is None


def test_missing_column_raises():
    df = pd.DataFrame([{"chunk_id": 0, "doc_id": 0, "text": "hello"}])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_required_columns(df)
