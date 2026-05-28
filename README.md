# Data Platform

A multi-source data ingestion, deduplication, and search platform built with Next.js, PostgreSQL, and Python ETL.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Internal       │     │  Python ETL      │     │  Next.js        │
│  MySQL          │────▶│  (FastAPI +      │────▶│  (SSR + ISR)    │
│  (Read-only)    │     │  Celery + Redis)│     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  PostgreSQL      │     │  JSON-LD        │
                        │  (Primary Store) │     │  Schema.org     │
                        └──────────────────┘     └─────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: Python 3.12, FastAPI, Celery, Redis
- **Database**: PostgreSQL 15+ with Prisma ORM
- **Full-text Search**: PostgreSQL tsvector + pg_trgm
- **Structured Data**: Schema.org + JSON-LD

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.12+ (for local ETL development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Copy environment file
cp .env.example .env
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
sleep 5

# Generate Prisma client
cd frontend && npx prisma generate && cd ..
cd prisma && npx prisma generate && cd ..
```

### 3. Initialize Database

```bash
# Push schema to PostgreSQL
cd prisma && npx prisma db push && cd ..

# Or via docker-compose
docker-compose up -d
docker-compose exec postgres psql -U platform -d platform -f /docker-entrypoint-initdb.d/01-schema.prisma
```

### 4. Start ETL Service

```bash
cd etl
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Start Celery Workers

```bash
cd etl
celery -A tasks worker --loglevel=info &
celery -A tasks beat --loglevel=info &
```

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

## Data Model

### Core Entities

- **Entity**: The primary record with name, description, type, and status
- **EntityAttribute**: Key-value attributes with typed values
- **EntityRelation**: Relationships between entities
- **DuplicateCandidate**: Fuzzy match candidates for deduplication
- **DataQualityRecord**: Freshness, completeness, and consistency scores
- **BackgroundJob**: Celery task audit trail

### Entity Types

Supported Schema.org types: Product, Place, Person, Organization, Event, Article

## API Reference

### ETL Service (FastAPI)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest` | POST | Trigger ingestion from sources |
| `/jobs/{id}` | GET | Get job status |
| `/jobs` | GET | List recent jobs |
| `/metrics` | GET | Prometheus metrics |

### Frontend API Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/entities` | GET | List/search entities |
| `/api/search` | GET | Full-text search |
| `/api/ingest` | POST | Trigger ingestion (internal) |

## ETL Sources

- `internal_mysql`: Existing internal MySQL system (read-only)
- `feed_a`: External REST feed A
- `feed_b`: External REST feed B

## Background Jobs

| Task | Schedule | Description |
|------|----------|-------------|
| `ingest_source` | Hourly | Ingest from configured sources |
| `score_data_quality` | On entity update + nightly | Compute quality scores |
| `resolve_duplicates` | Nightly | Fuzzy dedup using pg_trgm |

## Structured Data

Every entity page outputs JSON-LD Schema.org markup:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Entity Name",
  "description": "Entity description",
  "url": "https://platform.example/entity/entity-slug"
}
```

## Development

### Adding a New Feed

1. Add feed URL to `etl/ingestion/feed_fetch.py`
2. Update `IngestionPipeline.fetch()` to handle the source
3. Add source to Celery beat schedule in `docker-compose.yml`

### Running Tests

```bash
# Frontend
cd frontend && npm test

# ETL
cd etl && pytest
```

## Environment Variables

See `.env.example` for the complete list of environment variables.

## License

Private - All rights reserved