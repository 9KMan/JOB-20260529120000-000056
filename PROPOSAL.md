# Proposal — Senior Full-Stack / Data Platform Engineer

## Architecture Overview

A data platform MVP has three distinct layers that need to be designed together from day one:

**1. Ingestion Layer (Python ETL + FastAPI)**
The ingestion layer is the most critical and the most often underestimated. MySQL source → Python reader → normalizer → deduper → PostgreSQL writer via Prisma. External feeds follow the same path. I strongly recommend designing the normalized entity schema *first* before writing a single line of ingestion code — getting the dedup logic right early prevents enormous cleanup later (I learned this the hard way on a large product catalog platform a few years back). The MySQL connector should be read-only with a dedicated service account — no writes back to the internal system.

**2. Data Model (PostgreSQL + Prisma)**
A clean relational model with a `searchVector` tsvector column for PostgreSQL full-text search. Using `pg_trgm` with a GIN index on `name` for fuzzy dedup. The `EntityAttribute` table uses EAV (entity-attribute-value) pattern with typed values and a `datatype` enum — this handles variable fields across different entity types without needing a migration for every new attribute. The `DuplicateCandidate` table feeds a nightly Celery task that scores potential duplicates (trigram similarity on name, exact match on externalId across sources) and then marks them resolved.

**3. Frontend (Next.js SSR + JSON-LD)**
Server-rendered entity detail pages with ISR revalidation every 60 seconds. The JSON-LD Schema.org layer is generated server-side from Prisma data — no runtime JS needed to produce structured data. This approach gives you Google's rich results for free on entity pages without client-side data fetching overhead. Full-text search via PostgreSQL `plainto_tsquery` ranked by `ts_rank`, with optional filtering by entity type on top.

## Database Approach

PostgreSQL full-text vs. dedicated search engine (Algolia/Meilisearch/Typesense)?
- PostgreSQL FTS is sufficient for MVP (< 100k entities) and zero operational overhead (ships with every PostgreSQL 15+ install)
- Add Meilisearch if query latency becomes a problem after entity count crosses 100k, or if you need typo-tolerance out of the box
- Recommendation: start with PostgreSQL FTS + pg_trgm. Switch to Meilisearch transparently when latency demands it. The ETL layer separates search indexing from data persistence, so swapping the search backend only touches one module.

## Data Model Design

Core insight: treat `EntityAttribute` as a typed key-value store with source attribution. This means:
- Every attribute knows which system it came from (`source` field) — important for data quality scoring
- Adding a new field type doesn't require a Prisma migration (add to AttributeType enum + ETL handles serialization)
- The trade-off is query complexity (no direct column queries), which is acceptable at MVP stage

For entity resolution / fuzzy matching across multiple sources, I use a two-pass approach:
- Pass 1: Exact match on `externalId + source` → auto-merge
- Pass 2: Trigram similarity on name (threshold 0.8) with geographic constraint if location is available → `DuplicateCandidate` for human review

## GDPR / Sensitive Data

No user data in scope unless the internal MySQL system contains personal data. If it does: ETL should log a data transformation audit trail (source record + transformed output) for any field that maps to personal data categories. Prisma schema should use `@db.Text` for rawJson in sensitive jurisdictions. This is MVP, so a full consent ledger is probably out of scope unless the brief specifically mentions it.

## Timeline

### Phase 1: Architecture & Discovery (40 hrs, fixed)
- Day 1-2: Audit existing MySQL schema — draw entity map
- Day 3-4: Design PostgreSQL schema (Prisma + raw SQL for tsvector) — finalize ETL normalization rules
- Day 5-6: Set up Next.js project + Prisma + first mock data
- Day 7: Architecture alignment doc for your internal team

### Phase 2: ETL Layer (40 hrs, fixed)
- Week 2: MySQL reader + external feed connectors
- Week 3: Normalizer + pydantic validation + dedup logic
- Week 4: Celery jobs + retry queues + monitoring + first data load

### Phase 3: Frontend (30-40 hrs, fixed)
- Week 5: Entity pages (SSR + ISR) + JSON-LD
- Week 6: Search + filtering + entity card components
- Week 7: Polishing + performance optimization

### Phase 4: Integration + Polish (20-30 hrs, fixed)
- Week 8: MySQL integration end-to-end + data quality dashboard
- Week 9: Full-text search tuning + Schema.org testing
- Week 10: Documentation + handover

## Questions for You

1. **Source systems** — besides the MySQL internal system, how many external feeds are we integrating at launch? Are they REST APIs, CSV/S3 feeds, or scraping targets?
2. **Entity count** — approximate number of records at launch and expected growth rate over 12 months?
3. **Search result ranking** — is there a simple priority ordering (newest, most relevant) or do you need dynamic ranking / user personalization from day one?
4. **JSON-LD scope** — which Schema.org types are most important for the data domain (Product, Place, Organization, SoftwareApplication, Event)?
5. **MySQL access** — do I get a read-only dump/backup to work with for the discovery phase, or do I get direct (read-only) credentials to query the live system?
6. **Deployment environment** — are Vercel (frontend) + Railway (FastAPI/ETL) the target environments, or are we working within an existing AWS/GCP account?



🎁 Included with this proposal:
✅ Public PoC repo with working code + architecture spec
✅ Async-first communication: clear updates via chat/email, no meeting overhead
✅ 30 days of post-delivery support for questions and minor adjustments

If this aligns with your needs, I can expand the PoC to full production delivery within the timeline above. Happy to answer any questions or share additional architecture diagrams.

Best regards,
Mongkolpoj Phanutaecha
Principal Data Platform Architect | AI-Augmented Engineering Factory
Bangkok, Thailand (GMT+7) | Open to Remote Contracts
