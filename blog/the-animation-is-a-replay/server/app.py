"""Native execution service for the replay-post benchmark.

The service imports the same SimPy model the browser runs and loads the same
Rust kernel the browser executes as WebAssembly. It returns canonical event
logs; the page remains responsible for deriving statistics and hashing them.
"""

from __future__ import annotations

import asyncio
import ctypes
import json
import os
import platform
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

import simpy
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field

POST_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(POST_DIR))

from simpy_factory import PARAMS, canonical, run  # noqa: E402

RATE_LIMIT = 30
RATE_WINDOW_SECONDS = 60
RUN_TIMEOUT_SECONDS = 2
RUST_KERNEL_VERSION = "0.1.0"
RUST_LIBRARY_PATH = Path(
    os.environ.get(
        "REPLAY_RUST_LIBRARY",
        "/usr/local/lib/animation-replay/libreplay_kernel.so",
    )
)
_requests: dict[str, deque[float]] = defaultdict(deque)


class RustKernel:
    def __init__(self, library_path: Path) -> None:
        self.library = ctypes.CDLL(str(library_path))
        self.library.run_factory_json_native.argtypes = [ctypes.c_uint32]
        self.library.run_factory_json_native.restype = ctypes.c_void_p
        self.library.replay_kernel_string_free.argtypes = [ctypes.c_void_p]
        self.library.replay_kernel_string_free.restype = None

    def run(self, seed: int) -> dict:
        pointer = self.library.run_factory_json_native(seed)
        if not pointer:
            raise RuntimeError("Native Rust runner returned a null log pointer.")
        try:
            return json.loads(ctypes.string_at(pointer))
        finally:
            self.library.replay_kernel_string_free(pointer)


rust_kernel = RustKernel(RUST_LIBRARY_PATH)


class RunRequest(BaseModel):
    seed: int = Field(ge=0, le=999_999_999)


app = FastAPI(
    title="The Animation Is a Replay runner",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(GZipMiddleware, minimum_size=1_000)


def enforce_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _requests[client]
    while bucket and bucket[0] <= now - RATE_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Run limit reached; try again in one minute.",
            headers={"Retry-After": str(RATE_WINDOW_SECONDS)},
        )
    bucket.append(now)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "pythonVersion": platform.python_version(),
        "simpyVersion": simpy.__version__,
        "rustKernelVersion": RUST_KERNEL_VERSION,
        "rustTarget": f"{platform.machine()}-unknown-linux-gnu",
    }


@app.post("/run/simpy")
async def run_simpy(payload: RunRequest, request: Request, response: Response) -> dict:
    enforce_rate_limit(request)
    started = time.perf_counter()
    try:
        log = await asyncio.wait_for(
            asyncio.to_thread(run, dict(PARAMS), payload.seed),
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Simulation exceeded its time limit.") from exc

    wall_ms = (time.perf_counter() - started) * 1_000
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return {
        "log": json.loads(canonical(log)),
        "wallMs": round(wall_ms, 3),
        "runtime": {
            "engine": "SimPy",
            "engineVersion": simpy.__version__,
            "pythonVersion": platform.python_version(),
            "location": "server",
        },
    }


@app.post("/run/rust")
async def run_rust(payload: RunRequest, request: Request, response: Response) -> dict:
    enforce_rate_limit(request)
    started = time.perf_counter()
    try:
        log = await asyncio.wait_for(
            asyncio.to_thread(rust_kernel.run, payload.seed),
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Simulation exceeded its time limit.") from exc

    wall_ms = (time.perf_counter() - started) * 1_000
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return {
        "log": log,
        "wallMs": round(wall_ms, 3),
        "runtime": {
            "engine": "replay-kernel",
            "engineVersion": RUST_KERNEL_VERSION,
            "target": f"{platform.machine()}-unknown-linux-gnu",
            "location": "server",
        },
    }
