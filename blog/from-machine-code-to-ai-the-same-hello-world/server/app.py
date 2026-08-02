"""HTTP adapter for the deep execute API (execute.py).

This file is intentionally thin: rate limits, JSON, timeouts, and status codes.
All allowlisted program execution lives in execute.py.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field

import execute as core

RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60
BENCH_RATE_LIMIT = 4
BENCH_RATE_WINDOW_SECONDS = 300
REQUEST_TIMEOUT_SLACK = 5
BENCH_TOTAL_TIMEOUT_SECONDS = 420

_requests: dict[str, deque[float]] = defaultdict(deque)
_bench_requests: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(title="Hello ladder runner", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1_000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stephens.page", "https://www.stephens.page"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class BenchmarkRequest(BaseModel):
    samples: int = Field(
        default=10,
        ge=core.BENCH_SAMPLES_MIN,
        le=core.BENCH_SAMPLES_MAX,
    )
    languages: list[str] | None = None


def _rate_limit(
    store: dict[str, deque[float]],
    request: Request,
    limit: int,
    window: int,
    message: str,
) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = store[client]
    while bucket and bucket[0] <= now - window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=429,
            detail=message,
            headers={"Retry-After": str(window)},
        )
    bucket.append(now)


def enforce_rate_limit(request: Request) -> None:
    _rate_limit(
        _requests,
        request,
        RATE_LIMIT,
        RATE_WINDOW_SECONDS,
        "Run limit reached; try again in one minute.",
    )


def enforce_bench_rate_limit(request: Request) -> None:
    _rate_limit(
        _bench_requests,
        request,
        BENCH_RATE_LIMIT,
        BENCH_RATE_WINDOW_SECONDS,
        "Benchmark limit reached; try again in a few minutes.",
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"


@app.on_event("startup")
def on_startup() -> None:
    core.warm_builds()


@app.get("/health")
def health() -> dict:
    errors = {
        k: v.get("_build_error")
        for k, v in core.LANGS.items()
        if v.get("_build_error")
    }
    hist_total = 0
    try:
        import run_history

        hist_total = int(run_history.read_stats().get("total_runs") or 0)
    except Exception:  # noqa: BLE001
        hist_total = 0
    return {
        "status": "ok",
        "machine": core.hardware_info().get("architecture"),
        "system": __import__("platform").system(),
        "languages": core.known_languages(),
        "bands": len(core.BANDS),
        "hardware": core.hardware_info(),
        "defaultSamples": 10,
        "totalHistoricalRuns": hist_total,
        "tools": core.tools_present(),
        "buildErrors": errors,
        "api": {
            "execute": "execute.run_samples / execute.benchmark",
            "stats": "GET /stats - all-visitor aggregate timings",
            "http": "thin FastAPI adapter over execute.py",
        },
    }


@app.get("/languages")
def languages() -> list[dict]:
    return core.catalog_languages()


@app.get("/levels")
def levels() -> list[dict]:
    return core.catalog_levels()


@app.get("/stats")
def stats(response: Response) -> dict:
    """All-visitor aggregate run history for the public table."""
    import run_history

    _no_store(response)
    payload = run_history.public_stats()
    payload["hardware"] = core.hardware_info()
    return payload


@app.post("/run/{language}")
async def run_endpoint(
    language: str,
    request: Request,
    response: Response,
    samples: int = 10,
) -> dict:
    """Deep execute: allowlisted language + N server-side samples → mean stats."""
    enforce_rate_limit(request)
    if language not in core.LANGS:
        raise HTTPException(status_code=404, detail=f"Unknown language: {language}")
    samples = max(core.BENCH_SAMPLES_MIN, min(core.BENCH_SAMPLES_MAX, int(samples)))
    timeout = core.BUILD_TIMEOUT_SECONDS + (core.RUN_TIMEOUT_SECONDS + 1) * samples + REQUEST_TIMEOUT_SLACK
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(core.run_samples, language, samples),
            timeout=timeout,
        )
    except core.UnknownLanguage as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Run exceeded its time limit.") from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Process timed out.") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _no_store(response)
    return result


@app.post("/benchmark")
async def benchmark_endpoint(
    payload: BenchmarkRequest,
    request: Request,
    response: Response,
) -> dict:
    """Benchmark many languages via execute.benchmark (deep execute surface)."""
    enforce_bench_rate_limit(request)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(core.benchmark, payload.samples, payload.languages),
            timeout=BENCH_TOTAL_TIMEOUT_SECONDS,
        )
    except core.UnknownLanguage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Benchmark exceeded the global time limit.",
        ) from exc

    # Tag events from full-ladder benchmarks (run_samples already recorded each)
    # Re-fetch aggregate for the client table payload.
    try:
        import run_history

        hist = run_history.public_stats()
        result = dict(result)
        result["history"] = hist
    except Exception:  # noqa: BLE001
        pass

    _no_store(response)
    return result
