# Senior Full-Stack / Data Platform Engineer — Next.js, PostgreSQL, Python ETL, Structured Data

## 1. Concept & Vision

A confidential data-driven web platform MVP — not a brochure site or generic SaaS dashboard. The core value proposition is **multi-source data ingestion → structured data model → dynamic SSR pages → search**. Think data directory/marketplace/comparison platform energy: authoritative, fast, queryable, with Schema.org markup for SEO.

The platform ingests structured records from multiple sources (one existing MySQL internal system + external feeds), normalizes and deduplicates them into a PostgreSQL data model, renders fast server-rendered pages from a Next.js frontend, and exposes a clean JSON-LD/Schema.org layer for structured data output. A Python ETL layer handles ingestion, transformation, and background jobs.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                            │
│   SSR + ISR · JSON-LD · Schema.org · React 18 + TypeScript            │
│   Vercel / Railway                                                     │
└─────────────────────────────�──────────────────────────────────────────┘
                                    │ 3000/8000
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      NEXT.JS API ROUTES (/app/api)                   │
│   CRUD · Search · Filtering · Background job triggers               │
│   Prisma ORM → PostgreSQL                                            │
└─────────────────────────────┬──────────────────────────────────────────┘
                              │ External Feeds (scraping, CSV, REST)
┌─────────────────────────────▼──────────────────────────────────────────┐
│                    PYTHON ETL LAYER (FastAPI)                          │
│   ingestion_workers · transform · normalize · deduplicate            │
│   background jobs · retry queues · monitoring                         │
│   MySQL connector → reads from existing internal system                │
└─────┬──────────────────────────────┬──────────────────────────────────┘
      │                              │
      ▼                              ▼
┌───────────────────┐    ┌───────────────────────┐
│   PostgreSQL      │    │   Existing MySQL      │
│   Primary Store   │    │   Internal System     │
│   (Prisma)        │    │   (source of truth)    │
└───────────────────┘    └───────────────────────┘
```

---

## 3. Tech Stack

| Component            | Technology                                    |
|----------------------|-----------------------------------------------|
| Frontend Framework   | Next.js 14+ (App Router, TypeScript)          |
| UI Components        | React 18 + Tailwind CSS / shadcn/ui            |
| Database             | PostgreSQL 15+ (Prisma ORM)                   |
| Background Jobs     | Celery + Redis (or Python-anymq + SQLite)     |
| ETL / Ingestion      | Python 3.12 + pandas + BeautifulSoup/RapidAPI |
| Search               | PostgreSQL full-text + pg_trgm + Gin index     |
| Structured Data      | Schema.org + JSON-LD (nextjsonld or custom)    |
| API Layer (ETL)      | FastAPI uvicorn (port 8000)                   |
| Deployment           | Vercel (frontend) + Railway/Render (ETL)      |
| Internal MySQL       | mysql-connector-python (read-only from MySQL) |

---

## 4. Data Model

### 4.1 Core Entities (PostgreSQL via Prisma)

```prisma
model Entity {
  id            String   @id @default(cuid())
  externalId    String?  @unique  // ID from external source
  source        String            // 'internal_mysql' | 'feed_a' | 'feed_b'
  name          String
  slug          String   @unique
  summary       String?
  description   String?
  rawJson       Json?             // original raw record
  entityType    String            // schema: Product | Place | Person | Organization
  status        EntityStatus @default(PENDING)
  searchVector  Unsupported("tsvector")?  // for PostgreSQL full-text search

  attributes    EntityAttribute[]
  relations     EntityRelation[]  @relation("from")
  inverseRels   EntityRelation[]  @relation("to")
  dataQuality   DataQualityRecord?

  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}

enum EntityStatus {
  PENDING
  VALIDATED
  DUPLICATE_CANDIDATE
  ARCHIVED
}

model EntityAttribute {
  id        String  @id @default(cuid())
  entityId  String
  key       String           // 'price' | 'location' | 'rating'
  value     String           // stored as string, typed on read
  datatype  AttributeType
  source    String
  entity    Entity  @relation(fields: [entityId], references: [id])
  createdAt DateTime @default(now())
}

enum AttributeType {
  STRING
  NUMBER
  BOOLEAN
  DATE
  URL
  EMAIL
}

model EntityRelation {
  id        String  @id @default(cuid())
  fromId   String
  toId     String
  relationType String  // 'related' | 'sibling' | 'parent' | 'child'
  from     Entity  @relation("from", fields: [fromId], references: [id])
  to       Entity  @relation("to", fields: [toId], references: [id])
  createdAt DateTime @default(now())

  @@unique([fromId, toId, relationType])
}

// Deduplication candidates via fuzzy matching
model DuplicateCandidate {
  id        String  @id @default(cuid())
  entityAId String
  entityBId String
  score     Float              // 0.0 – 1.0
  reason    String
  resolved  Boolean @default(false)
  createdAt DateTime @default(now())
}

// Data quality scores per entity
model DataQualityRecord {
  id         String  @id @default(cuid())
  entityId   String  @unique
  freshness  Float   // 0.0 – 1.0  (days since last update)
  completeness Float Float  // 0.0 – 1.0  (% fields populated)
  consistency Float   // 0.0 – 1.0  (schema compliance)
  overall    Float
  entity     Entity  @relation(fields: [entityId], references: [id])
  updatedAt  DateTime @updatedAt
}

// Background job / task tracking
model BackgroundJob {
  id         String  @id @default(cuid())
  jobType    String  // 'ingest' | 'dedup' | 'quality' | 'export'
  status     String  // 'queued' | 'running' | 'done' | 'failed'
  payload    Json?
  error      String?
  startedAt  DateTime?
  finishedAt DateTime?
  createdAt  DateTime @default(now())
}
```

### 4.2 PostgreSQL Full-Text Search Index

```sql
-- Add GiST/GIN tsvector column for full-text search
ALTER TABLE "Entity" ADD COLUMN "searchVector" tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'C')
  ) STORED;

CREATE INDEX "Entity_searchVector_idx" ON "Entity" USING GIN ("searchVector");

-- Fuzzy matching with pg_trgm for deduplication
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX "Entity_name_trgm_idx" ON "Entity" USING GIN (name gin_trgm_ops);
```

### 4.3 Internal MySQL System Integration

```python
# mysql_reader.py — read-only connector to existing internal MySQL system
import mysql.connector

def connect_mysql():
    return mysql.connector.connect(
        host=os.environ['MYSQL_HOST'],
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
        read_default_file='~/.my.cnf'
    )

def fetch_entities(limit=5000, offset=0):
    """Fetch records from internal MySQL as dicts."""
    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, description, created_at, updated_at
        FROM entities
        WHERE status = 'active'
        ORDER BY updated_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
```

---

## 5. ETL / Ingestion Design

### 5.1 Ingestion Pipeline

```python
# ingestion/ingest.py
class IngestionPipeline:
    """
    Multi-source ETL:
      1. Pull from Internal MySQL (existing system)
      2. Pull from external REST/CSV feeds
      3. Normalize → deduplicate → write PostgreSQL via Prisma
      4. Record background job
    """

    def run(self, sources: list[str]):
        for source in sources:
            records = self.fetch(source)
            normalized = [self.normalize(r, source) for r in records]
            # Fuzzy dedup pass
            deduplicated = self.deduplicate(normalized)
            self.load_to_postgres(deduplicated)

    def fetch(self, source: str) -> list[dict]:
        if source == 'internal_mysql':
            return fetch_entities()
        elif source.startswith('feed_'):
            return self.fetch_feed(source)
        return []

    def normalize(self, record: dict, source: str) -> dict:
        return {
            'externalId': record.get('id'),
            'source': source,
            'name': record.get('name', '').strip(),
            'summary': record.get('title') or record.get('summary', ''),
            'description': record.get('description', ''),
            'entityType': record.get('type', 'Product'),
            'rawJson': json.dumps(record),
            'status': 'PENDING',
        }

    def deduplicate(self, records: list[dict]) -> list[dict]:
        """PostgreSQL trigram similarity for fuzzy dedup."""
        ...
```

### 5.2 Background Jobs (Celery / Redis)

```python
# tasks.py
from celery import Celery
app = Celery('etl', broker=os.environ['REDIS_URL'])

@app.task
def ingest_source(source: str):
    pipeline = IngestionPipeline()
    pipeline.run([source])

@app.task
def score_data_quality(entity_id: str):
    record = DataQualityScorer(entity_id)
    record.compute()  # freshness + completeness + consistency

@app.task
def resolve_duplicates(batch_size=200):
    DuplicateResolver(batch_size=batch_size).run()
```

Schedule:
- `ingest_source` — every 1 hour via Celery beat
- `score_data_quality` — on entity update + nightly batch
- `resolve_duplicates` — nightly off-peak

### 5.3 Retry and Monitoring

- Celery task retry: `max_retries=5`, exponential backoff (60s, 300s, 900s, 3600s)
- Dead letter queue for failed tasks
- Prometheus metrics endpoint (`/metrics`) on FastAPI ETL service
- Health check: `GET /health` returns `{"status": "ok", "last_ingest": "..."}`

---

## 6. Next.js Frontend

### 6.1 App Router Structure

```
app/
├── app/
│   ├── page.tsx                   # Home / Search page
│   ├── entity/[slug]/
│   │   └── page.tsx               # Dynamic entity detail (SSR)
│   ├── search/
│   │   └── page.tsx               # Full-text search results
│   └── api/
│       ├── entities/
│       │   └── route.ts           # GET /api/entities?q=&type=&page=
│       ├── search/
│       │   └── route.ts           # Full-text search endpoint
│       └── ingest/
│           └── route.ts           # Trigger manual ingest (internal)
│
├── components/
│   ├── EntityCard.tsx
│   ├── SearchFilters.tsx
│   ├── JsonLd.tsx                 # Schema.org JSON-LD component
│   └── DataQualityBadge.tsx
│
├── lib/
│   ├── prisma.ts                  # Prisma client singleton
│   ├── search.ts                  # PostgreSQL full-text query builder
│   └── structured-data.ts        # Schema.org + JSON-LD helpers
│
└── types/
    └── entity.ts
```

### 6.2 Dynamic Entity Page (SSR + JSON-LD)

```typescript
// app/entity/[slug]/page.tsx — Server Component
import { prisma } from '@/lib/prisma';
import { generateEntityJsonLd } from '@/lib/structured-data';

export const revalidate = 60; // ISR: Revalidate every 60s

export default async function EntityPage({ params }: { params: { slug: string } }) {
  const entity = await prisma.entity.findUnique({
    where: { slug: params.slug },
    include: { attributes: true, dataQuality: true },
  });

  if (!entity) notFound();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(generateEntityJsonLd(entity)) }}
      />
      <EntityDetail entity={entity} />
    </>
  );
}
```

### 6.3 JSON-LD / Schema.org Output

```typescript
// lib/structured-data.ts
export function generateEntityJsonLd(entity: Entity) {
  return {
    "@context": "https://schema.org",
    "@type": entity.entityType,  // Product | Place | Organization | ...
    "name": entity.name,
    "description": entity.description,
    "url": `https://platform.example/entity/${entity.slug}`,
    ...(entity.summary && { "abstract": entity.summary }),
    ...(entity.attributes.reduce(...)) // key-value structured properties
  };
}
```

### 6.4 Search (PostgreSQL Full-Text)

```typescript
// lib/search.ts — server-side search query builder
export async function searchEntities(query: string, type?: string, page=1) {
  const where = type ? { entityType: type } : {};
  if (!query.trim()) {
    return prisma.entity.findMany({
      where: { status: 'VALIDATED', ...where },
      take: 20, skip: (page - 1) * 20,
    });
  }
  // PostgreSQL full-text with ranking
  return prisma.$queryRaw`
    SELECT *, ts_rank("searchVector", plainto_tsquery('english', ${query})) AS rank
    FROM "Entity"
    WHERE "searchVector" @@ plainto_tsquery('english', ${query})
      AND status = 'VALIDATED'
      ${where.entityType ? Prisma.sql`AND "entityType" = ${where.entityType}` : Prisma.sql``}
    ORDER BY rank DESC
    LIMIT 20 OFFSET ${(page - 1) * 20}
  `;
}
```

---

## 7. Configuration (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/platform

# Prisma
DATABASE_URL=postgresql://user:pass@host:5432/platform

# MySQL Internal System (read-only)
MYSQL_HOST=internal-mysql.company.internal
MYSQL_PORT=3306
MYSQL_USER=readonly_client
MYSQL_PASSWORD=
MYSQL_DATABASE=main_db

# ETL / FastAPI
ETL_PORT=8000
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Next.js
NEXT_PUBLIC_BASE_URL=https://platform.example.com
```

---

## 8. File Structure

```
/{job_id}/
├── SPEC.md                        # This spec
├── README.md                      # Setup + architecture + CLI
│
├── frontend/                      # Next.js app
│   ├── app/
│   │   ├── page.tsx               # Home + search
│   │   ├── entity/[slug]/page.tsx  # Dynamic entity pages (SSR + JSON-LD)
│   │   ├── search/page.tsx         # Search results
│   │   └── api/                    # API routes
│   ├── components/                 # EntityCard, JsonLd, etc.
│   ├── lib/                       # prisma.ts, search.ts, structured-data.ts
│   ├── types/
│   ├── prisma/schema.prisma       # Prisma schema (entities + attributes)
│   ├── package.json
│   ├── next.config.js
│   └── .env.local
│
├── etl/                           # Python ETL / FastAPI service
│   ├── main.py                    # FastAPI app + endpoints
│   ├── ingestion/
│   │   ├── pipeline.py             # IngestionPipeline class
│   │   ├── mysql_reader.py         # Read from internal MySQL
│   │   ├── feed_fetch.py           # External feed fetcher
│   │   └── normalize.py            # Data normalization
│   ├── dedup/
│   │   ├── resolver.py             # Fuzzy dedup with pg_trgm
│   │   └── scorer.py               # Similarity scoring
│   ├── tasks.py                    # Celery tasks
│   ├── models.py                   # Pydantic models for FastAPI
│   ├── config.py                   # Env config
│   ├── requirements.txt
│   └── .env.example
│
├── prisma/
│   └── schema.prisma               # Primary Prisma schema (shared)
│
├── docker-compose.yml             # PostgreSQL + Redis + ETL
├── .env.example
└── CONTRIBUTING.md
```

---

## 9. Acceptance Criteria

1. **Ingestion** — Python ETL can fetch from internal MySQL and external REST/CSV sources, normalize records, and write to PostgreSQL via Prisma
2. **Deduplication** — Fuzzy dedup identifies near-duplicate entities using PostgreSQL pg_trgm similarity; human review queue for >0.85 candidates
3. **Search** — PostgreSQL full-text search returns ranked results on entity name/description/summary; pg_trgm handles typos
4. **Dynamic Pages** — `/entity/[slug]` renders SSR entity details with JSON-LD Schema.org markup; ISR revalidates every 60s
5. **Structured Data** — Every entity page emits valid JSON-LD with `@type`, `name`, `description`, and entity-specific fields
6. **Background Jobs** — Celery tasks run ingestion on schedule with retry; failed tasks go to dead letter queue
7. **Data Quality** — Completeness/freshness/consistency scores computed per entity; displayed as badge on entity pages
8. **MySQL Integration** — ETL reads from existing internal MySQL without writing; read-only via dedicated service account
9. **Performance** — Lighthouse score >85 on entity pages; TTFB <200ms with ISR
10. **Documentation** — README covers: setup, architecture diagram, data model table, API endpoints, CLI reference, quality guarantees

---

## 10. Out of Scope

- User authentication / auth0 integration
- Admin CMS UI (data team manages directly in PostgreSQL via Prisma Studio)
- Payment / subscription handling
- Real-time WebSocket updates
- Mobile app
- Multi-language i18n

---

## 11. Quality Guarantees

- All ETL writes validated against Pydantic schemas before PostgreSQL insert
- Prisma schema has `not_null` on `name` and `entityType`; foreign key constraints enforced
- PostgreSQL transaction wraps multi-step ingestion: all or nothing rollback
- Celery task audit trail via BackgroundJob table (not just Redis)
- JSON-LD output tested with Google's Rich Results Test tool
- Full-text search covers `name` (weight A), `summary` (weight B), `description` (weight C)
