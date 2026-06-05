import os
from time import perf_counter

import psutil
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_DURATION, update_uptime
from app.models import Incident, IncidentCreate, IncidentUpdate
from app.store import incident_store

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(
    title="CloudOps Monitor",
    description="Cloud Monitoring and Incident Response Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = perf_counter()
    route = request.url.path
    response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        response = await call_next(request)
        return response
    finally:
        duration = perf_counter() - start_time
        route = getattr(request.scope.get("route"), "path", route)
        status_code = str(response.status_code)
        REQUEST_COUNT.labels(request.method, route, status_code).inc()
        REQUEST_DURATION.labels(request.method, route).observe(duration)
        if response.status_code >= 500:
            ERROR_COUNT.labels(request.method, route, status_code).inc()
        update_uptime()


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/dashboard/summary")
async def dashboard_summary() -> dict[str, float | int | str]:
    request_metric = REQUEST_COUNT.collect()[0]
    error_metric = ERROR_COUNT.collect()[0]
    total_requests = sum(sample.value for sample in request_metric.samples if sample.name == "cloudops_http_requests_total")
    total_errors = sum(sample.value for sample in error_metric.samples if sample.name == "cloudops_http_errors_total")

    return {
        "application_status": "online",
        "api_health_status": "healthy",
        "total_requests": int(total_requests),
        "error_count": int(total_errors),
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "active_incidents": incident_store.active_count(),
        "uptime_seconds": round(update_uptime(), 2),
    }


@app.get("/incidents", response_model=list[Incident])
async def list_incidents() -> list[Incident]:
    return incident_store.list()


@app.post("/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentCreate) -> Incident:
    return incident_store.create(payload)


@app.put("/incidents/{incident_id}", response_model=Incident)
async def update_incident(incident_id: str, payload: IncidentUpdate) -> Incident:
    incident = incident_store.update(incident_id, payload)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@app.delete("/incidents/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str) -> Response:
    deleted = incident_store.delete(incident_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/metrics")
async def metrics() -> Response:
    update_uptime()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
