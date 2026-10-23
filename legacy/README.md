# legacy

Earlier work, kept for reference while the project restarts notebook-first against the new
milestones. Nothing here is installed or run by default, and imports such as `open_parcel.*`
will not resolve without adding `legacy/src` to the path.

- `src/open_parcel/scrapers/` – Ottawa and Toronto zoning bylaw HTML parsers
- `src/open_parcel/api_clients/ckan.py` – CKAN client (Toronto open data)
- `src/open_parcel/ingest/`, `src/open_parcel/db/` – document ingest and SQLAlchemy models
- `migrations/`, `alembic.ini` – Alembic migrations (document table)
- `Dockerfile`, `docker-compose.yml` – Postgres 16 with PostGIS and pgvector (relevant to #13)
- `tests/` – tests for the ingest code
- `notebooks/toronto_eda.ipynb` – Toronto EDA
- `data/2026-50/` – saved Ottawa bylaw 2026-50 root HTML page
