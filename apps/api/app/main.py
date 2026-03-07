from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.tenants.router import router as tenants_router
from app.salesforce.router import router as salesforce_router
from app.sync.router import router as sync_router

app = FastAPI(
    title="Tamarac FSC Connector",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants_router, prefix="/api")
app.include_router(salesforce_router, prefix="/api")
app.include_router(sync_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
