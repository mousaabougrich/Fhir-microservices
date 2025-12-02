# Featurizer microservice

This service fetches de-identified FHIR resources from the DeID API and produces patient-level features for ML.

## Database setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE featDB;
```

2. Run the migration:
```bash
psql -h localhost -U postgres -d featDB -f migrations/create_tables.sql
```

Or let SQLAlchemy create tables automatically on startup.

## Quickstart

1. Copy environment configuration
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Create venv and install dependencies

```bash
cd featurizer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. Run locally

```bash
uvicorn main:app --reload --port 8001
```

5. Example requests

```bash
# single patient
curl http://localhost:8001/featurize/patient/<patient_resource_id>

# bulk
curl -X POST -H "Content-Type: application/json" -d '["id1","id2"]' http://localhost:8001/featurize/bulk
```

## Configuration

The service uses environment variables loaded from `.env` file:

- `DEID_BASE_URL` - DeID service endpoint (default: http://deid:8000)
- `DATABASE_URL` - PostgreSQL connection string (default: postgresql://postgres:root@localhost:5432/featDB)
- `USE_BIOBERT` - Enable BioBERT embeddings (default: false)

## Notes

- Set `DEID_BASE_URL` to point to your DeID service if not running locally.
- Set `DATABASE_URL` for custom database connection (default: `postgresql://postgres:root@localhost:5432/featDB`)
- To enable BioBERT set `USE_BIOBERT=true` and ensure PyTorch is installed; otherwise sentence-transformers is used.
- Features are cached in the database - use `?force_refresh=true` to bypass cache.
- New endpoints: `/features/patient/{id}` for cached-only lookup, `/features/all` for bulk retrieval.
- This scaffold focuses on a minimal workable pipeline; production needs include error handling, rate limiting and careful governance for storing decoded attachments.
