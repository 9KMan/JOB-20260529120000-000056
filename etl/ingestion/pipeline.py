import json
import logging
from datetime import datetime
from typing import Optional
from prisma import Prisma
from .normalize import normalize_record
from .mysql_reader import fetch_entities
from .feed_fetch import fetch_feed

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Multi-source ETL:
      1. Pull from Internal MySQL (existing system)
      2. Pull from external REST/CSV feeds
      3. Normalize → deduplicate → write PostgreSQL via Prisma
      4. Record background job
    """

    def __init__(self):
        self.db = Prisma()

    async def run(self, sources: list[str]) -> dict:
        """Run ingestion for the specified sources."""
        await self.db.connect()
        total_ingested = 0
        errors = []
        
        try:
            for source in sources:
                try:
                    count = await self._ingest_source(source)
                    total_ingested += count
                    logger.info(f"Ingested {count} records from {source}")
                except Exception as e:
                    error_msg = f"Source {source}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
            # Record background job
            await self._record_job(total_ingested, errors)
            return {"ingested": total_ingested, "errors": errors}
            
        finally:
            await self.db.disconnect()

    async def _ingest_source(self, source: str) -> int:
        """Ingest records from a single source."""
        records = self._fetch(source)
        if not records:
            return 0
            
        normalized = [normalize_record(r, source) for r in records]
        await self._write_to_postgres(normalized)
        return len(normalized)

    def _fetch(self, source: str) -> list[dict]:
        """Fetch records from a source."""
        if source == 'internal_mysql':
            return fetch_entities()
        elif source.startswith('feed_'):
            return fetch_feed(source)
        return []

    async def _write_to_postgres(self, records: list[dict]) -> None:
        """Write normalized records to PostgreSQL via Prisma."""
        for record in records:
            try:
                # Check if entity with same externalId exists
                existing = None
                if record.get('externalId'):
                    existing = await self.db.entity.find_first(
                        where={"externalId": record['externalId'], "source": record['source']}
                    )
                
                if existing:
                    # Update existing entity
                    await self.db.entity.update(
                        where={"id": existing.id},
                        data={
                            "name": record['name'],
                            "slug": record['slug'],
                            "summary": record.get('summary'),
                            "description": record.get('description'),
                            "rawjson": record.get('rawJson'),
                            "entitytype": record.get('entityType', 'Product'),
                            "updatedAt": datetime.utcnow(),
                        }
                    )
                else:
                    # Create new entity
                    await self.db.entity.create({
                        "externalid": record.get('externalId'),
                        "source": record['source'],
                        "name": record['name'],
                        "slug": record['slug'],
                        "summary": record.get('summary'),
                        "description": record.get('description'),
                        "entitytype": record.get('entityType', 'Product'),
                        "rawjson": record.get('rawJson'),
                        "status": "PENDING",
                    })
            except Exception as e:
                logger.error(f"Failed to write entity {record.get('name')}: {e}")

    async def _record_job(self, ingested: int, errors: list[str]) -> None:
        """Record the background job execution."""
        await self.db.backgroundjob.create(
            data={
                "jobtype": "ingest",
                "status": "done" if not errors else "failed",
                "payload": json.dumps({"ingested": ingested}),
                "error": "; ".join(errors) if errors else None,
                "startedAt": datetime.utcnow(),
                "finishedAt": datetime.utcnow(),
            }
        )