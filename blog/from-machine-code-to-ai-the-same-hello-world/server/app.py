"""Allowlisted Hello World runner for the abstraction-ladder post.

Security model: the client may only pick a language key. Source is never taken
from the request body. Programs are fixed files under ../programs. Compiled
artifacts live under ../cache. Subprocesses have timeouts and no shell.
"""

from __future__ import annotations

import asyncio
import os
import platform
import re
import shutil
import subprocess
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

POST_DIR = Path(__file__).resolve().parent.parent
PROGRAMS = POST_DIR / "programs"
CACHE = POST_DIR / "cache"

RATE_LIMIT = 40
RATE_WINDOW_SECONDS = 60
RUN_TIMEOUT_SECONDS = 3
BUILD_TIMEOUT_SECONDS = 60

PATH_PREFIX = os.environ.get(
    "HELLO_LADDER_PATH",
    "/home/jacob/.cargo/bin:/usr/local/go/bin:/usr/bin:/bin",
)

_requests: dict[str, deque[float]] = defaultdict(deque)

# language_id -> metadata and how to build/run
# highlight: highlight.js language id (or "plaintext")
LANGS: dict[str, dict] = {
    "binary": {
        "title": "Binary program (ELF)",
        "level": 0,
        "source_file": "binary-readme.txt",
        "kind": "binary",
        "highlight": "plaintext",
        "binary": "hello-binary",
        # Built from C; the rung treats only the executable as the artifact.
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-binary"), str(PROGRAMS / "hello.c")],
        "run": [str(CACHE / "hello-binary")],
        "build_source": "hello.c",
    },
    "machine": {
        "title": "Machine code",
        "level": 1,
        "source_file": "hello.s",
        "kind": "machine",
        "highlight": "x86asm",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
    },
    "assembly": {
        "title": "Assembly (x86_64 Linux)",
        "level": 2,
        "source_file": "hello.s",
        "kind": "native",
        "highlight": "x86asm",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
    },
    "c": {
        "title": "C",
        "level": 3,
        "source_file": "hello.c",
        "kind": "native",
        "highlight": "c",
        "binary": "hello-c",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-c"), str(PROGRAMS / "hello.c")],
        "run": [str(CACHE / "hello-c")],
    },
    "cpp": {
        "title": "C++",
        "level": 4,
        "source_file": "hello.cpp",
        "kind": "native",
        "highlight": "cpp",
        "binary": "hello-cpp",
        "build": ["g++", "-O0", "-o", str(CACHE / "hello-cpp"), str(PROGRAMS / "hello.cpp")],
        "run": [str(CACHE / "hello-cpp")],
    },
    "rust": {
        "title": "Rust",
        "level": 5,
        "source_file": "hello.rs",
        "kind": "native",
        "highlight": "rust",
        "binary": "hello-rust",
        "build": ["rustc", "-O", "-o", str(CACHE / "hello-rust"), str(PROGRAMS / "hello.rs")],
        "run": [str(CACHE / "hello-rust")],
    },
    "go": {
        "title": "Go",
        "level": 6,
        "source_file": "hello.go",
        "kind": "native",
        "highlight": "go",
        "binary": "hello-go",
        "build": ["go", "build", "-o", str(CACHE / "hello-go"), str(PROGRAMS / "hello.go")],
        "run": [str(CACHE / "hello-go")],
    },
    "csharp": {
        "title": "C#",
        "level": 7,
        "source_file": "hello.cs",
        "kind": "mono",
        "highlight": "csharp",
        "binary": "hello-cs.exe",
        "build": ["mcs", "-out:" + str(CACHE / "hello-cs.exe"), str(PROGRAMS / "hello.cs")],
        "run": ["mono", str(CACHE / "hello-cs.exe")],
    },
    "python": {
        "title": "Python",
        "level": 8,
        "source_file": "hello.py",
        "kind": "interp",
        "highlight": "python",
        "build": None,
        "run": ["python3", str(PROGRAMS / "hello.py")],
    },
    "javascript": {
        "title": "JavaScript",
        "level": 9,
        "source_file": "hello.js",
        "kind": "interp",
        "highlight": "javascript",
        "build": None,
        "run": ["node", str(PROGRAMS / "hello.js")],
    },
    "ai": {
        "title": "AI engineering",
        "level": 10,
        "source_file": "ai-prompt.txt",
        "kind": "ai-standin",
        "highlight": "plaintext",
        "build": None,
        "run": None,
    },
    "vibe": {
        "title": "Vibe coding",
        "level": 11,
        "source_file": "vibe-session.md",
        "kind": "vibe-standin",
        "highlight": "markdown",
        "build": None,
        "run": ["python3", str(PROGRAMS / "vibe-hello.py")],
        "artifact": "vibe-hello.py",
    },
}

app = FastAPI(title="Hello ladder runner", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1_000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stephens.page", "https://www.stephens.page"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = PATH_PREFIX
    env["HOME"] = "/home/jacob"
    # systemd ProtectHome=read-only blocks ~/.cache; keep tool caches under CACHE.
    cache_tmp = CACHE / "tmp"
    cache_tmp.mkdir(parents=True, exist_ok=True)
    env["TMPDIR"] = str(cache_tmp)
    env["TMP"] = str(cache_tmp)
    env["TEMP"] = str(cache_tmp)
    env["GOCACHE"] = str(CACHE / "go-build")
    env["GOMODCACHE"] = str(CACHE / "go-mod")
    env["GOTMPDIR"] = str(cache_tmp)
    # Keep Go happy without network for a single-file build.
    env.setdefault("GO111MODULE", "off")
    env.setdefault("GOTOOLCHAIN", "local")
    return env


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


def _run_cmd(cmd: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
        cwd=str(CACHE),
        check=False,
    )


def ensure_built(lang: str) -> None:
    meta = LANGS[lang]
    build = meta.get("build")
    if not build:
        return
    binary = CACHE / meta["binary"]
    # Prefer the actual compile input when present (binary rung uses C source).
    src_name = meta.get("build_source") or meta["source_file"]
    source = PROGRAMS / src_name
    if binary.exists() and source.exists() and binary.stat().st_mtime >= source.stat().st_mtime:
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    result = _run_cmd(build, BUILD_TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise RuntimeError(
            f"build failed for {lang}: {result.stderr.strip() or result.stdout.strip()}"
        )


def binary_source_view() -> str:
    """Human-facing view of the ELF: file(1) + head of xxd."""
    ensure_built("binary")
    path = CACHE / "hello-binary"
    file_out = _run_cmd(["file", "-b", str(path)], timeout=5)
    size = path.stat().st_size if path.exists() else 0
    xxd = _run_cmd(["xxd", "-g", "1", "-l", "256", str(path)], timeout=5)
    readme = (PROGRAMS / "binary-readme.txt").read_text(encoding="utf-8").strip()
    return (
        f"{readme}\n\n"
        f"# file: cache/hello-binary ({size} bytes)\n"
        f"# {file_out.stdout.strip()}\n\n"
        f"{xxd.stdout or '(xxd unavailable)'}"
    )


def machine_hex_snippet() -> str:
    """Return a short hex + disassembly slice of the assembly binary's main."""
    ensure_built("assembly")
    binary = CACHE / "hello-asm"
    # objdump main, first ~20 lines
    dump = _run_cmd(
        ["objdump", "-d", "--no-show-raw-insn", str(binary)],
        timeout=5,
    )
    if dump.returncode != 0:
        hexdump = _run_cmd(["xxd", "-g", "4", "-l", "64", str(binary)], timeout=5)
        return hexdump.stdout or "(hex dump unavailable)"

    lines = dump.stdout.splitlines()
    # Prefer the <main> section if present
    out: list[str] = []
    capture = False
    for line in lines:
        if re.search(r"<main>:", line):
            capture = True
            out.append(line)
            continue
        if capture:
            if line.startswith(" ") or line.startswith("\t") or re.match(r"^[0-9a-f]+:", line):
                out.append(line)
                if len(out) >= 16:
                    break
            elif out and not line.strip():
                break
            elif out and re.search(r"<.+>:", line):
                break
    if not out:
        out = lines[:20]

    # Also grab raw text bytes near entry
    raw = _run_cmd(["objdump", "-d", str(binary)], timeout=5)
    raw_lines = []
    capture = False
    for line in raw.stdout.splitlines():
        if re.search(r"<main>:", line):
            capture = True
            raw_lines.append(line)
            continue
        if capture:
            raw_lines.append(line)
            if len(raw_lines) >= 12:
                break
    return "\n".join(raw_lines or out)


def run_language(lang: str) -> dict:
    if lang not in LANGS:
        raise KeyError(lang)
    meta = LANGS[lang]
    started = time.perf_counter()

    if meta["kind"] == "ai-standin":
        prompt = (PROGRAMS / "ai-prompt.txt").read_text(encoding="utf-8")
        wall_ms = (time.perf_counter() - started) * 1000
        return {
            "language": lang,
            "title": meta["title"],
            "level": meta["level"],
            "stdout": "Hello, World!\n",
            "stderr": "",
            "exitCode": 0,
            "wallMs": round(wall_ms, 3),
            "host": {
                "machine": platform.machine(),
                "system": platform.system(),
                "python": platform.python_version(),
            },
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "plaintext"),
            "note": (
                "Deterministic stand-in for an LLM: the server does not call a model. "
                "It returns the exact one-line output the engineered prompt asks for, "
                "so the ladder stays free, offline-safe, and reproducible."
            ),
            "prompt": prompt,
        }

    # Vibe coding: run the fixed chat artifact (python), show the session as source.
    if meta["kind"] == "vibe-standin":
        result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
        wall_ms = (time.perf_counter() - started) * 1000
        session = (PROGRAMS / meta["source_file"]).read_text(encoding="utf-8")
        return {
            "language": lang,
            "title": meta["title"],
            "level": meta["level"],
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exitCode": result.returncode,
            "wallMs": round(wall_ms, 3),
            "host": {
                "machine": platform.machine(),
                "system": platform.system(),
                "python": platform.python_version(),
            },
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "markdown"),
            "command": meta["run"],
            "session": session,
            "note": (
                "Vibe coding stand-in: the chat transcript is the process; "
                "Run executes programs/vibe-hello.py (the frozen 'whatever the agent wrote'). "
                "No live model is called. Contrast with AI engineering's tight prompt contract."
            ),
        }

    build_lang = {
        "machine": "assembly",
        "binary": "binary",
    }.get(lang, lang)
    ensure_built(build_lang)
    result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
    wall_ms = (time.perf_counter() - started) * 1000

    payload: dict = {
        "language": lang,
        "title": meta["title"],
        "level": meta["level"],
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exitCode": result.returncode,
        "wallMs": round(wall_ms, 3),
        "host": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "sourceFile": meta["source_file"],
        "highlight": meta.get("highlight", "plaintext"),
        "command": meta["run"],
    }
    if lang == "machine":
        payload["machineView"] = machine_hex_snippet()
        payload["note"] = (
            "stdout is from executing the assembled binary on this host. "
            "machineView is objdump of <main> - the instruction encodings the CPU ran."
        )
    if lang == "binary":
        payload["binaryView"] = binary_source_view()
        payload["note"] = (
            "No source language on this rung: Run executes a real ELF built from C. "
            "The source panel is file(1) + the first 256 bytes of that executable (xxd)."
        )
    return payload


@app.on_event("startup")
def warm_builds() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    # Best-effort prebuild so first visitor click is fast.
    for lang in ("binary", "assembly", "c", "cpp", "rust", "go", "csharp"):
        try:
            ensure_built(lang)
        except Exception as exc:  # noqa: BLE001 - surface later on /health
            LANGS[lang]["_build_error"] = str(exc)


@app.get("/health")
def health() -> dict:
    tools = {
        "gcc": shutil.which("gcc", path=PATH_PREFIX),
        "g++": shutil.which("g++", path=PATH_PREFIX),
        "rustc": shutil.which("rustc", path=PATH_PREFIX),
        "go": shutil.which("go", path=PATH_PREFIX),
        "mcs": shutil.which("mcs", path=PATH_PREFIX),
        "mono": shutil.which("mono", path=PATH_PREFIX),
        "python3": shutil.which("python3", path=PATH_PREFIX),
        "node": shutil.which("node", path=PATH_PREFIX),
    }
    return {
        "status": "ok",
        "machine": platform.machine(),
        "system": platform.system(),
        "languages": list(LANGS.keys()),
        "tools": tools,
        "buildErrors": {
            k: v.get("_build_error") for k, v in LANGS.items() if v.get("_build_error")
        },
    }


@app.get("/languages")
def languages() -> list[dict]:
    out = []
    for key, meta in sorted(LANGS.items(), key=lambda kv: kv[1]["level"]):
        if key == "binary":
            try:
                source = binary_source_view()
            except Exception as exc:  # noqa: BLE001
                source = f"(binary view unavailable: {exc})"
        else:
            source_path = PROGRAMS / meta["source_file"]
            source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        out.append(
            {
                "id": key,
                "title": meta["title"],
                "level": meta["level"],
                "sourceFile": meta["source_file"],
                "source": source,
                "highlight": meta.get("highlight", "plaintext"),
            }
        )
    return out


@app.post("/run/{language}")
async def run_endpoint(language: str, request: Request, response: Response) -> dict:
    enforce_rate_limit(request)
    if language not in LANGS:
        raise HTTPException(status_code=404, detail=f"Unknown language: {language}")
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_language, language),
            timeout=BUILD_TIMEOUT_SECONDS + RUN_TIMEOUT_SECONDS + 2,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Run exceeded its time limit.") from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Process timed out.") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return result
