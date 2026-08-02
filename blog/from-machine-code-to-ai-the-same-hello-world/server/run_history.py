"""Persistent run history for the Hello World ladder.

Stores every POST /run (and each language in /benchmark) under
/var/lib/hello-ladder so the public stats table can show aggregate
timings across all visitors.

Privacy: no IP, user-agent, or request body is stored - only language id,
timing stats, exit status, truncated stdout, sample count, and timestamps.
"""

from __future__ import annotations

import fcntl
import json
import math
import os
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("HELLO_LADDER_SPEND_DIR", "/var/lib/hello-ladder"))
AGG_PATH = Path(
    os.environ.get("HELLO_LADDER_RUN_STATS_PATH", str(DATA_DIR / "run_stats.json"))
)
EVENTS_PATH = Path(
    os.environ.get("HELLO_LADDER_RUN_EVENTS_PATH", str(DATA_DIR / "run_events.jsonl"))
)

# Cap growth of the event log (keep last N lines when rotating).
MAX_EVENTS = int(os.environ.get("HELLO_LADDER_RUN_EVENTS_MAX", "50000"))
STDOUT_MAX = 240


def _empty_agg() -> dict:
    return {
        "updated_at": 0,
        "total_runs": 0,
        "languages": {},
        "note": (
            "Aggregate wall-clock run stats for allowlisted Hello World ladder "
            "programs on stephens.page (all visitors)."
        ),
    }


def _empty_lang(lang_id: str, title: str = "", year: str = "") -> dict:
    return {
        "id": lang_id,
        "title": title or lang_id,
        "year": year or "",
        "runs": 0,
        "ok_runs": 0,
        "fail_runs": 0,
        "total_samples": 0,
        "sum_avg_ms": 0.0,
        "sum_sq_avg_ms": 0.0,
        "min_ms": None,
        "max_ms": None,
        "last_avg_ms": None,
        "last_stdout": "",
        "last_ok": None,
        "last_at": 0,
        "first_at": 0,
    }


def _truncate_stdout(text: str) -> str:
    s = (text or "").replace("\r", "").strip()
    if len(s) > STDOUT_MAX:
        return s[: STDOUT_MAX - 1] + "…"
    return s


def _read_agg(fh) -> dict:
    raw = fh.read()
    if not raw or not str(raw).strip():
        return _empty_agg()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_agg()
    if not isinstance(data, dict):
        return _empty_agg()
    out = _empty_agg()
    out.update({k: data.get(k, out[k]) for k in out})
    langs = data.get("languages") or {}
    if isinstance(langs, dict):
        out["languages"] = langs
    return out


def read_stats() -> dict:
    """Return aggregate stats file (creates empty structure if missing)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AGG_PATH.is_file():
        return _empty_agg()
    with AGG_PATH.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_SH)
        try:
            return _read_agg(fh)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _maybe_rotate_events() -> None:
    if not EVENTS_PATH.is_file():
        return
    try:
        # Cheap size check: if file is large, keep tail
        size = EVENTS_PATH.stat().st_size
        if size < 8_000_000:  # ~8 MiB
            return
        with EVENTS_PATH.open("r", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                lines = fh.readlines()
                if len(lines) <= MAX_EVENTS:
                    return
                keep = lines[-MAX_EVENTS:]
                fh.seek(0)
                fh.truncate()
                fh.writelines(keep)
                fh.flush()
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def record_run(
    *,
    language: str,
    title: str = "",
    year: str = "",
    avg_ms: float | None,
    min_ms: float | None = None,
    max_ms: float | None = None,
    stdev_ms: float | None = None,
    samples: int = 1,
    exit_code: int = 0,
    ok: bool = True,
    stdout: str = "",
    source: str = "run",
) -> dict:
    """Append one event and update per-language aggregates. Returns public snapshot row stats."""
    now = int(time.time())
    lang = str(language or "").strip() or "unknown"
    samples = max(1, int(samples or 1))
    avg = float(avg_ms) if avg_ms is not None and math.isfinite(float(avg_ms)) else None
    mn = float(min_ms) if min_ms is not None and math.isfinite(float(min_ms)) else avg
    mx = float(max_ms) if max_ms is not None and math.isfinite(float(max_ms)) else avg
    out_text = _truncate_stdout(stdout)

    event = {
        "ts": now,
        "language": lang,
        "title": title or lang,
        "year": year or "",
        "avgMs": round(avg, 4) if avg is not None else None,
        "minMs": round(mn, 4) if mn is not None else None,
        "maxMs": round(mx, 4) if mx is not None else None,
        "stdevMs": round(float(stdev_ms), 4)
        if stdev_ms is not None and math.isfinite(float(stdev_ms))
        else None,
        "samples": samples,
        "exitCode": int(exit_code),
        "ok": bool(ok),
        "stdout": out_text,
        "source": source if source in ("run", "benchmark") else "run",
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AGG_PATH.is_file():
        AGG_PATH.write_text(json.dumps(_empty_agg(), indent=2) + "\n", encoding="utf-8")

    with AGG_PATH.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            data = _read_agg(fh)
            langs = data.setdefault("languages", {})
            row = langs.get(lang)
            if not isinstance(row, dict):
                row = _empty_lang(lang, title=title, year=year)
            else:
                # refresh titles if provided
                if title:
                    row["title"] = title
                if year:
                    row["year"] = year
                row.setdefault("id", lang)

            row["runs"] = int(row.get("runs") or 0) + 1
            if ok:
                row["ok_runs"] = int(row.get("ok_runs") or 0) + 1
            else:
                row["fail_runs"] = int(row.get("fail_runs") or 0) + 1
            row["total_samples"] = int(row.get("total_samples") or 0) + samples

            if avg is not None:
                row["sum_avg_ms"] = float(row.get("sum_avg_ms") or 0.0) + avg
                row["sum_sq_avg_ms"] = float(row.get("sum_sq_avg_ms") or 0.0) + (avg * avg)
                row["last_avg_ms"] = round(avg, 4)
                prev_min = row.get("min_ms")
                prev_max = row.get("max_ms")
                if mn is not None:
                    row["min_ms"] = round(
                        mn if prev_min is None else min(float(prev_min), mn), 4
                    )
                if mx is not None:
                    row["max_ms"] = round(
                        mx if prev_max is None else max(float(prev_max), mx), 4
                    )

            row["last_stdout"] = out_text
            row["last_ok"] = bool(ok)
            row["last_at"] = now
            if not row.get("first_at"):
                row["first_at"] = now

            langs[lang] = row
            data["languages"] = langs
            data["total_runs"] = int(data.get("total_runs") or 0) + 1
            data["updated_at"] = now

            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(data, indent=2) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            snapshot = dict(data)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    try:
        with EVENTS_PATH.open("a", encoding="utf-8") as ef:
            fcntl.flock(ef.fileno(), fcntl.LOCK_EX)
            try:
                ef.write(json.dumps(event, ensure_ascii=False) + "\n")
                ef.flush()
            finally:
                fcntl.flock(ef.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass

    _maybe_rotate_events()
    return snapshot


def public_stats(*, known_order: list[str] | None = None) -> dict:
    """Shape aggregates for the browser table (sorted by historical avg ms)."""
    raw = read_stats()
    langs = raw.get("languages") or {}
    rows = []
    for lang_id, row in langs.items():
        if not isinstance(row, dict):
            continue
        runs = int(row.get("runs") or 0)
        ok_runs = int(row.get("ok_runs") or 0)
        sum_avg = float(row.get("sum_avg_ms") or 0.0)
        sum_sq = float(row.get("sum_sq_avg_ms") or 0.0)
        avg = (sum_avg / runs) if runs > 0 else None
        # Population stdev of per-request avgMs values
        stdev = None
        if runs >= 2 and avg is not None:
            var = max(0.0, (sum_sq / runs) - (avg * avg))
            stdev = math.sqrt(var)

        rows.append(
            {
                "id": row.get("id") or lang_id,
                "title": row.get("title") or lang_id,
                "year": row.get("year") or "",
                "runs": runs,
                "okRuns": ok_runs,
                "failRuns": int(row.get("fail_runs") or 0),
                "totalSamples": int(row.get("total_samples") or 0),
                "avgMs": round(avg, 3) if avg is not None else None,
                "minMs": row.get("min_ms"),
                "maxMs": row.get("max_ms"),
                "stdevMs": round(stdev, 3) if stdev is not None else None,
                "lastAvgMs": row.get("last_avg_ms"),
                "lastStdout": row.get("last_stdout") or "",
                "lastOk": row.get("last_ok"),
                "lastAt": int(row.get("last_at") or 0),
                "firstAt": int(row.get("first_at") or 0),
                "ok": bool(row.get("last_ok")) if row.get("last_ok") is not None else ok_runs > 0,
            }
        )

    # Sort by historical average ms (missing last); stable id for ties
    def sort_key(r: dict):
        a = r.get("avgMs")
        if a is None:
            return (1, 0.0, r.get("id") or "")
        return (0, float(a), r.get("id") or "")

    rows.sort(key=sort_key)

    # Optional preferred order for languages never run (not included until first run)
    return {
        "totalRuns": int(raw.get("total_runs") or 0),
        "updatedAt": int(raw.get("updated_at") or 0),
        "languageCount": len(rows),
        "rows": rows,
        "note": raw.get("note") or "",
        "source": "aggregate",
    }
