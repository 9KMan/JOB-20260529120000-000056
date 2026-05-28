from celery import Celery
import os

app = Celery('etl', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

app.conf.update(
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.ingest_source': {'queue': 'ingest'},
        'tasks.score_data_quality': {'queue': 'quality'},
        'tasks.resolve_duplicates': {'queue': 'dedup'},
    },
    task_default_retry_delay=60,
    task_max_retries=5,
    retry_backoff=True,
    retry_backoff_max=3600,
)


@app.task(bind=True, max_retries=5)
def ingest_source(self, source: str):
    """Ingest records from a specified source."""
    from ingestion.pipeline import IngestionPipeline
    import asyncio
    
    try:
        pipeline = IngestionPipeline()
        result = asyncio.run(pipeline.run([source]))
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True, max_retries=5)
def score_data_quality(self, entity_id: str):
    """Compute quality scores for a single entity."""
    from dedup.scorer import DataQualityScorer
    import asyncio
    
    try:
        scorer = DataQualityScorer(entity_id)
        result = asyncio.run(scorer.compute())
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True, max_retries=5)
def resolve_duplicates(self, batch_size: int = 200):
    """Run duplicate resolution on validated entities."""
    from dedup.resolver import DuplicateResolver
    import asyncio
    
    try:
        resolver = DuplicateResolver(batch_size=batch_size)
        result = asyncio.run(resolver.run())
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task
def batch_score_quality(entity_ids: list[str]):
    """Batch score quality for multiple entities."""
    from dedup.scorer import DataQualityScorer
    import asyncio
    
    results = []
    for entity_id in entity_ids:
        try:
            scorer = DataQualityScorer(entity_id)
            result = asyncio.run(scorer.compute())
            results.append(result)
        except Exception:
            results.append({"entity_id": entity_id, "error": "Failed"})
    return results