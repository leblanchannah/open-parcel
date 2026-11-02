"""open-parcel: answer zoning questions about Ottawa parcels, with citations.

The pipeline is a chain of stages with stable interfaces between them:

    ingest -> chunking -> index -> retrieval -> generation -> eval

See docs/architecture.md for the full picture.
"""
