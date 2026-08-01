"""LLM spend ledger for the Hello World ladder AI rungs.

Durable totals under /var/lib/hello-ladder so dashboard.stephens.page can read
them. Emails jacob@stephens.page once when cumulative spend crosses $5.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# Luna list prices (USD per 1M tokens) after Jul 2026 cut.
LUNA_INPUT_PER_M = float(os.environ.get("HELLO_LADDER_LUNA_INPUT_PER_M", "0.20"))
LUNA_OUTPUT_PER_M = float(os.environ.get("HELLO_LADDER_LUNA_OUTPUT_PER_M", "1.20"))
LUNA_CACHED_INPUT_PER_M = float(os.environ.get("HELLO_LADDER_LUNA_CACHED_INPUT_PER_M", "0.02"))

SPEND_DIR = Path(os.environ.get("HELLO_LADDER_SPEND_DIR", "/var/lib/hello-ladder"))
SPEND_PATH = Path(os.environ.get("HELLO_LADDER_SPEND_PATH", str(SPEND_DIR / "llm_spend.json")))
EVENTS_PATH = Path(os.environ.get("HELLO_LADDER_EVENTS_PATH", str(SPEND_DIR / "llm_events.jsonl")))

SPEND_ALERT_USD = float(os.environ.get("HELLO_LADDER_SPEND_ALERT_USD", "5.0"))
ADMIN_EMAIL = os.environ.get("HELLO_LADDER_ADMIN_EMAIL", "jacob@stephens.page")
MAIL_FROM = os.environ.get(
    "HELLO_LADDER_MAIL_FROM",
    os.environ.get("MAIL_FROM_EMAIL", "jacob@stephens.page"),
)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY") or os.environ.get("SMTP_PASS") or ""

_empty = {
    "total_usd": 0.0,
    "request_count": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cached_input_tokens": 0,
    "currency": "USD",
    "model": "gpt-5.6-luna",
    "alert_threshold_usd": SPEND_ALERT_USD,
    "alerted_5usd": False,
    "updated_at": 0,
    "note": (
        "Cumulative OpenAI GPT-5.6 Luna spend for the Hello World ladder "
        "AI engineering + vibe coding rungs on stephens.page."
    ),
}


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
) -> float:
    cached = max(0, int(cached_input_tokens))
    inp = max(0, int(input_tokens) - cached)
    out = max(0, int(output_tokens))
    cost = (
        (inp / 1_000_000.0) * LUNA_INPUT_PER_M
        + (cached / 1_000_000.0) * LUNA_CACHED_INPUT_PER_M
        + (out / 1_000_000.0) * LUNA_OUTPUT_PER_M
    )
    return round(cost, 8)


def _read_spend(fh) -> dict:
    raw = fh.read()
    if not raw or not str(raw).strip():
        return dict(_empty)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return dict(_empty)
    if not isinstance(data, dict):
        return dict(_empty)
    out = dict(_empty)
    out.update(
        {
            "total_usd": float(data.get("total_usd") or 0),
            "request_count": int(data.get("request_count") or 0),
            "input_tokens": int(data.get("input_tokens") or 0),
            "output_tokens": int(data.get("output_tokens") or 0),
            "cached_input_tokens": int(data.get("cached_input_tokens") or 0),
            "currency": str(data.get("currency") or "USD"),
            "model": str(data.get("model") or "gpt-5.6-luna"),
            "alert_threshold_usd": float(data.get("alert_threshold_usd") or SPEND_ALERT_USD),
            "alerted_5usd": bool(data.get("alerted_5usd")),
            "updated_at": int(data.get("updated_at") or 0),
            "note": str(data.get("note") or _empty["note"]),
            "last_request": data.get("last_request"),
        }
    )
    return out


def read_spend() -> dict:
    path = SPEND_PATH
    if not path.is_file():
        return dict(_empty)
    with path.open("r", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_SH)
            return _read_spend(fh)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _send_threshold_email(total_usd: float, event: dict) -> None:
    subject = f"[stephens.page] Hello ladder LLM spend exceeded ${SPEND_ALERT_USD:.2f}"
    body = (
        f"Cumulative GPT-5.6 Luna spend for the Hello World ladder is now "
        f"${total_usd:.4f} (threshold ${SPEND_ALERT_USD:.2f}).\n\n"
        f"Last request:\n"
        f"  mode:    {event.get('mode')}\n"
        f"  cost:    ${float(event.get('cost_usd') or 0):.6f}\n"
        f"  tokens:  in={event.get('input_tokens')} out={event.get('output_tokens')} "
        f"cached_in={event.get('cached_input_tokens')}\n"
        f"  model:   {event.get('model')}\n\n"
        f"Dashboard: https://dashboard.stephens.page/\n"
        f"Post: https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/\n"
    )
    if not RESEND_API_KEY:
        # Best-effort local log if mail is not configured.
        try:
            SPEND_DIR.mkdir(parents=True, exist_ok=True)
            (SPEND_DIR / "alert_email_skipped.log").write_text(
                f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} no RESEND/SMTP key\n{body}\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return

    payload = json.dumps(
        {
            "from": f"Hello ladder <{MAIL_FROM}>",
            "to": [ADMIN_EMAIL],
            "subject": subject,
            "text": body,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        try:
            SPEND_DIR.mkdir(parents=True, exist_ok=True)
            with (SPEND_DIR / "alert_email_errors.log").open("a", encoding="utf-8") as fh:
                fh.write(f"{time.time()} {exc}\n")
        except OSError:
            pass


def record_spend(
    *,
    mode: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    cost_usd: float | None = None,
    meta: dict | None = None,
) -> dict:
    """Append event + update totals. Returns spend snapshot including this request."""
    cost = (
        float(cost_usd)
        if cost_usd is not None
        else estimate_cost_usd(input_tokens, output_tokens, cached_input_tokens)
    )
    event = {
        "ts": int(time.time()),
        "mode": mode,
        "model": model,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "cached_input_tokens": int(cached_input_tokens),
        "cost_usd": cost,
        "meta": meta or {},
    }

    SPEND_DIR.mkdir(parents=True, exist_ok=True)
    if not SPEND_PATH.is_file():
        SPEND_PATH.write_text(json.dumps(_empty, indent=2) + "\n", encoding="utf-8")

    crossed = False
    with SPEND_PATH.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            data = _read_spend(fh)
            before = float(data["total_usd"])
            data["total_usd"] = round(before + cost, 8)
            data["request_count"] = int(data["request_count"]) + 1
            data["input_tokens"] = int(data["input_tokens"]) + int(input_tokens)
            data["output_tokens"] = int(data["output_tokens"]) + int(output_tokens)
            data["cached_input_tokens"] = int(data["cached_input_tokens"]) + int(
                cached_input_tokens
            )
            data["updated_at"] = int(time.time())
            data["model"] = model
            data["last_request"] = event
            threshold = float(data.get("alert_threshold_usd") or SPEND_ALERT_USD)
            if before < threshold <= data["total_usd"] and not data.get("alerted_5usd"):
                data["alerted_5usd"] = True
                crossed = True
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(data, indent=2) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            snapshot = dict(data)
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    with EVENTS_PATH.open("a", encoding="utf-8") as ef:
        fcntl.flock(ef.fileno(), fcntl.LOCK_EX)
        try:
            ef.write(json.dumps(event, ensure_ascii=False) + "\n")
            ef.flush()
        finally:
            fcntl.flock(ef.fileno(), fcntl.LOCK_UN)

    if crossed:
        _send_threshold_email(snapshot["total_usd"], event)

    snapshot["this_request_usd"] = cost
    return snapshot
