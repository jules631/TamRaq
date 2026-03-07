import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StartSyncOut(BaseModel):
    runId: str
    sseToken: str


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenantId: uuid.UUID
    status: str
    enablePositions: bool
    startedAt: datetime
    completedAt: datetime | None
    totalRows: int
    successCount: int
    failureCount: int
    duplicateCount: int
    stageCounts: dict
    sanitizedErrors: list

    @classmethod
    def from_model(cls, run) -> "SyncRunOut":
        return cls(
            id=run.id,
            tenantId=run.tenant_id,
            status=run.status,
            enablePositions=run.enable_positions,
            startedAt=run.started_at,
            completedAt=run.completed_at,
            totalRows=run.total_rows,
            successCount=run.success_count,
            failureCount=run.failure_count,
            duplicateCount=run.duplicate_count,
            stageCounts=run.stage_counts or {},
            sanitizedErrors=run.sanitized_errors or [],
        )


class SyncRunListItem(BaseModel):
    id: uuid.UUID
    status: str
    startedAt: datetime
    completedAt: datetime | None
    totalRows: int
    successCount: int
    failureCount: int
    duplicateCount: int

    @classmethod
    def from_model(cls, run) -> "SyncRunListItem":
        return cls(
            id=run.id,
            status=run.status,
            startedAt=run.started_at,
            completedAt=run.completed_at,
            totalRows=run.total_rows,
            successCount=run.success_count,
            failureCount=run.failure_count,
            duplicateCount=run.duplicate_count,
        )
