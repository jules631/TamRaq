"""
SSE token minting/verification and per-run asyncio.Queue registry.
"""

import asyncio
import json
import time
from typing import AsyncGenerator

import jwt

from app.settings import settings

# Global map of run_id -> asyncio.Queue
_run_queues: dict[str, asyncio.Queue] = {}


def create_run_queue(run_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _run_queues[run_id] = q
    return q


def get_run_queue(run_id: str) -> asyncio.Queue | None:
    return _run_queues.get(run_id)


def remove_run_queue(run_id: str) -> None:
    _run_queues.pop(run_id, None)


def mint_sse_token(tenant_id: str, run_id: str) -> str:
    payload = {
        "tenant_id": str(tenant_id),
        "run_id": str(run_id),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, settings.SSE_TOKEN_SIGNING_KEY, algorithm="HS256")


def verify_sse_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SSE_TOKEN_SIGNING_KEY,
        algorithms=["HS256"],
    )


async def sse_event_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings from the queue.
    Sends keepalive comments every 15 s to prevent proxy timeouts.
    Terminates when None sentinel is received.
    """
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=15.0)
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
            continue

        if event is None:
            # Sync is done; send a final DONE frame then close
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
            break

        yield f"data: {json.dumps(event)}\n\n"
