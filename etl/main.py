import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from ingestion.pipeline import IngestionPipeline
from ingestion.mysql_reader import get_mysql_last_updated
from models import (
    IngestSourceRequest,
    HealthResponse,
    BackgroundJobResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('etl_requests_total', 'Total ETL requests', ['method', 'endpoint'])
INGEST_COUNT = Counter('etl_ingest_total', 'Total records ingested', ['source'])
REQUEST_LATENCY = Histogram('etl_request_latency_seconds', 'Request latency', ['method', 'endpoint'])

_last_ingest_time: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("ETL service starting up...")
    yield
    logger.info("ETL service shutting down...")


app = FastAPI(
    title="Data Platform ETL API",
    description="Multi-source data ingestion and processing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", last_ingest=_last_ingest_time)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


@app.post("/ingest")
async def ingest_sources(request: IngestSourceRequest):
    """Trigger ingestion from specified sources."""
    global _last_ingest_time
    
    try:
        pipeline = IngestionPipeline()
        result = await pipeline.run(request.sources)
        
        if request.sources:
            _last_ingest_time = datetime.utcnow().isoformat()
        
        # Update metrics
        for source in request.sources:
            INGEST_COUNT.labels(source=source).inc(result.get('ingested', 0))
        
        return {
            "status": "success",
            "ingested": result.get('ingested', 0),
            "errors": result.get('errors', []),
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=BackgroundJobResponse)
async def get_job_status(job_id: str):
    """Get status of a background job."""
    from prisma import Prisma
    
    db = Prisma()
    await db.connect()
    
    try:
        job = await db.backgroundjob.find_unique(where={"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return BackgroundJobResponse(
            id=job.id,
            job_type=job.jobtype,
            status=job.status,
            payload=job.payload,
            error=job.error,
            started_at=job.started_at,
            finished_at=job.finished_at,
            created_at=job.created_at,
        )
    finally:
        await db.disconnect()


@app.get("/jobs")
async def list_jobs(limit: int = 50):
    """List recent background jobs."""
    from prisma import Prisma
    
    db = Prisma()
    await db.connect()
    
    try:
        jobs = await db.backgroundjob.find_many(
            take=limit,
            order={"created_at": "desc"},
        )
        return [
            BackgroundJobResponse(
                id=job.id,
                job_type=job.jobtype,
                status=job.status,
                payload=job.payload,
                error=job.error,
                started_at=job.started_at,
                finished_at=job.finished_at,
                created_at=job.created_at,
            )
            for job in jobs
        ]
    finally:
        await db.disconnect()


@app.get("/mysql-last-updated")
async def mysql_last_updated():
    """Get the last update timestamp from MySQL source."""
    try:
        return {"last_updated": get_mysql_last_updated()}
    except Exception as e:
        logger.error(f"Failed to get MySQL last updated: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("ETL_PORT", 8000)),
        reload=True,
    )