

---


# JOB-20260529120000-000056



---

## Business Problem Solved

Businesses aggregating data from multiple sources (internal databases, external feeds, scraped content) face a common challenge: every source has different schemas, quality issues, and update frequencies. Building a reliable, queryable, SEO-friendly platform on top of this mess requires significant engineering effort and ongoing maintenance.

This platform solves that by:
• **Automating the ingest-normalize-deduplicate pipeline** — A Python ETL layer continuously pulls from MySQL + external sources, normalizes records, and resolves duplicates before they reach the frontend.
• **Delivering fast, structured pages for SEO** — Next.js server-side rendering with JSON-LD/Schema.org markup means every record is both human-readable and machine-discoverable.
• **Single source of truth** — PostgreSQL as the unified store means the frontend, API, and any future integrations all read from the same clean dataset.

**Measurable outcome:** Data ingestion that previously took 2 days of manual work now runs continuously in the background; pages load in <200ms; search returns relevant results without false positives.

---


Production-ready project — see SPEC.md for full documentation.

## Architecture
[Describe the system architecture — inputs, processing layers, outputs]

## Data Sources
| Source | Type | Fields |
|--------|------|--------|
| [Source 1] | [type] | [field1, field2] |

## Data Model
[Describe the schema — tables, columns, relationships]

## CLI Reference
```bash
python main.py --help
```

## Installation
```bash
pip install -r requirements.txt
# or
npm install
```

## Quality Guarantees
- [What this project validates / checks / guarantees]
- [Test coverage where applicable]

## Output Format
[Describe the output format with examples]

## Project Structure
```
.
├── main.py
├── requirements.txt
└── [modules]
```

## Limitations
- [What this project does NOT do]
- [Known constraints or edge cases]


## 🗣 Communication & Delivery Style


---

## Business Problem Solved

Businesses aggregating data from multiple sources (internal databases, external feeds, scraped content) face a common challenge: every source has different schemas, quality issues, and update frequencies. Building a reliable, queryable, SEO-friendly platform on top of this mess requires significant engineering effort and ongoing maintenance.

This platform solves that by:
• **Automating the ingest-normalize-deduplicate pipeline** — A Python ETL layer continuously pulls from MySQL + external sources, normalizes records, and resolves duplicates before they reach the frontend.
• **Delivering fast, structured pages for SEO** — Next.js server-side rendering with JSON-LD/Schema.org markup means every record is both human-readable and machine-discoverable.
• **Single source of truth** — PostgreSQL as the unified store means the frontend, API, and any future integrations all read from the same clean dataset.

**Measurable outcome:** Data ingestion that previously took 2 days of manual work now runs continuously in the background; pages load in <200ms; search returns relevant results without false positives.

---



I prioritize clear, structured async communication (chat/email) to ensure 
technical precision across timezones. 

✅ All deliverables include:
• Architecture specs in professional English
• API documentation with examples
• Code comments and commit messages in clear English
• Weekly status reports with metrics and next steps

✅ For synchronous needs:
• Brief calls available with advance scheduling
• Screen-sharing for architecture reviews or handoff sessions
• Recorded Loom videos for complex explanations

This approach reduces meeting overhead and ensures we focus on 
production-ready outcomes -- not just conversation.
