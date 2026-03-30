import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_tenant_member
from app.db.models import SalesforceConfig, SyncConfig, SyncRun
from app.db.session import SessionLocal, get_db
from app.salesforce.client import SalesforceClient
from app.sync import schemas, service
from app.sync.sse import (
    create_run_queue,
    get_run_queue,
    mint_sse_token,
    sse_event_generator,
    verify_sse_token,
)

router = APIRouter(tags=["sync"])


# ── Start sync ────────────────────────────────────────────────────────────────

@router.post("/tenants/{tenant_id}/sync/run", response_model=schemas.StartSyncOut)
async def start_sync_run(
    tenant_id: str,
    request: Request,
    enable_positions: Annotated[bool, Query()] = True,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Read raw CSV body — never stored
    content_type = request.headers.get("content-type", "")
    if "text/csv" not in content_type and "text/plain" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Expected Content-Type: text/csv",
        )
    csv_bytes = await request.body()
    csv_content = csv_bytes.decode("utf-8-sig")  # strip BOM if present

    # Load configs
    sf_cfg = db.query(SalesforceConfig).filter(SalesforceConfig.tenant_id == tid).first()
    if not sf_cfg:
        raise HTTPException(status_code=400, detail="Salesforce config not saved yet")
    sync_cfg = db.query(SyncConfig).filter(SyncConfig.tenant_id == tid).first()

    # Build Salesforce client (auth happens here — fail fast before creating run)
    try:
        sf = SalesforceClient.from_config(sf_cfg)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Salesforce auth failed: {exc}") from exc

    # Detach sync_cfg from the session now, before db.commit() expires it.
    # run_sync runs as a background task after this session closes, so it
    # must not hold a live SQLAlchemy reference that needs a session to load.
    if sync_cfg:
        db.expunge(sync_cfg)

    # Create SyncRun row
    run = SyncRun(
        tenant_id=tid,
        status="running",
        enable_positions=enable_positions,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = str(run.id)

    # Create event queue and mint SSE token
    queue = create_run_queue(run_id)
    sse_token = mint_sse_token(tenant_id, run_id)

    # Fire-and-forget background task
    import asyncio
    asyncio.create_task(
        service.run_sync(
            run_id=run_id,
            tenant_id=tenant_id,
            csv_content=csv_content,
            enable_positions=enable_positions,
            sf=sf,
            sync_cfg=sync_cfg,
            queue=queue,
        )
    )

    return schemas.StartSyncOut(runId=run_id, sseToken=sse_token)


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/tenants/{tenant_id}/sync/runs/{run_id}/events")
async def sync_run_events(
    tenant_id: str,
    run_id: str,
    token: str,
):
    try:
        claims = verify_sse_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid SSE token") from exc

    if claims.get("tenant_id") != tenant_id or claims.get("run_id") != run_id:
        raise HTTPException(status_code=403, detail="Token mismatch")

    queue = get_run_queue(run_id)
    if queue is None:
        # Run is already complete — return a minimal done stream
        async def _done_only():
            # Fetch status from DB
            with SessionLocal() as db:
                try:
                    run = db.get(SyncRun, uuid.UUID(run_id))
                except Exception:
                    run = None
            import json
            if run:
                payload = {
                    "type": "done",
                    "status": run.status,
                    "successCount": run.success_count,
                    "failureCount": run.failure_count,
                    "duplicateCount": run.duplicate_count,
                }
            else:
                payload = {"type": "done", "status": "unknown"}
            yield f"data: {json.dumps(payload)}\n\n"
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

        return StreamingResponse(
            _done_only(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return StreamingResponse(
        sse_event_generator(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Run list ──────────────────────────────────────────────────────────────────

@router.get(
    "/tenants/{tenant_id}/sync/runs",
    response_model=list[schemas.SyncRunListItem],
)
def list_sync_runs(
    tenant_id: str,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Tenant not found")

    runs = (
        db.query(SyncRun)
        .filter(SyncRun.tenant_id == tid)
        .order_by(SyncRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [schemas.SyncRunListItem.from_model(r) for r in runs]


# ── Run detail ────────────────────────────────────────────────────────────────

@router.get(
    "/tenants/{tenant_id}/sync/runs/{run_id}",
    response_model=schemas.SyncRunOut,
)
def get_sync_run(
    tenant_id: str,
    run_id: str,
    member=Depends(require_tenant_member),
    db: Session = Depends(get_db),
):
    try:
        tid = uuid.UUID(tenant_id)
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")

    run = (
        db.query(SyncRun)
        .filter(SyncRun.tenant_id == tid, SyncRun.id == rid)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return schemas.SyncRunOut.from_model(run)
