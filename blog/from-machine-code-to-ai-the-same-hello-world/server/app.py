"""Allowlisted Hello World runner for the abstraction-ladder post.

Security model: the client may only pick a language key. Source is never taken
from the request body. Programs are fixed files under ../programs. Compiled
artifacts live under ../cache. Subprocesses have timeouts and no shell.

Languages are grouped into abstraction *bands* (levels). The UI may carousel
multiple variants within a band; each variant still runs via POST /run/{id}.
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

# Abstraction bands (ordered). Each band may hold multiple language variants.
BANDS: list[dict] = [
    {
        "id": "binary",
        "level": 0,
        "title": "Binary program",
        "era": "c. 1945",
        "hides": "Hides all source. The program is an executable file.",
        "blurb": "Stored-program computers and the opaque binary you ship.",
    },
    {
        "id": "machine",
        "level": 1,
        "title": "Machine code",
        "era": "c. 1940s",
        "hides": "Hides almost nothing: instruction encodings the CPU runs.",
        "blurb": "Raw opcodes - the only language the execution units ultimately care about.",
    },
    {
        "id": "assembly",
        "level": 2,
        "title": "Assembly",
        "era": "c. 1949",
        "hides": "Hides bit encodings; still names registers and calls.",
        "blurb": "Symbolic mnemonics for machine instructions (this host: x86_64 Linux GAS).",
    },
    {
        "id": "early-hl",
        "level": 3,
        "title": "Early high-level",
        "era": "1957–1959",
        "hides": "Hides registers; you write formulas, business data, or lists.",
        "blurb": "FORTRAN (science), Lisp (lists/AI), COBOL (business) - the first mass high-level languages.",
    },
    {
        "id": "systems",
        "level": 4,
        "title": "Systems languages",
        "era": "1972–1985",
        "hides": "Hides instruction selection; still close to the machine model.",
        "blurb": "C and C++ - portable systems programming with a thin runtime.",
    },
    {
        "id": "managed",
        "level": 5,
        "title": "Managed / safe systems",
        "era": "1995–2015",
        "hides": "Hides more memory/safety details behind a runtime or type system.",
        "blurb": "Java, C#, Go, Rust - GC, VMs, or ownership as compile-time machinery.",
    },
    {
        "id": "scripting",
        "level": 6,
        "title": "Scripting / dynamic",
        "era": "1987–1995",
        "hides": "Almost the entire machine; interpreters, VMs, and huge libraries.",
        "blurb": "Bash, Perl, Python, PHP, JavaScript - glue, web, and everyday automation.",
    },
    {
        "id": "ai",
        "level": 7,
        "title": "AI engineering",
        "era": "c. 2022",
        "hides": "Code behind a precise natural-language contract.",
        "blurb": "Intent as the interface - still bottoms out in lower layers.",
    },
    {
        "id": "vibe",
        "level": 8,
        "title": "Vibe coding",
        "era": "2025",
        "hides": "Even the contract - chat is the process; accept and run.",
        "blurb": "Casual agent chat as the workflow (Karpathy's coinage), not a tight prompt spec.",
    },
]

# language_id -> runnable variant metadata
LANGS: dict[str, dict] = {
    "binary": {
        "title": "ELF binary",
        "year": "c. 1945",
        "year_note": "stored-program era; this file is a modern Linux ELF",
        "band": "binary",
        "source_file": "binary-readme.txt",
        "kind": "binary",
        "highlight": "plaintext",
        "binary": "hello-binary",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-binary"), str(PROGRAMS / "hello.c")],
        "run": [str(CACHE / "hello-binary")],
        "build_source": "hello.c",
    },
    "machine": {
        "title": "Machine code",
        "year": "c. 1940s",
        "year_note": "plugboards and binary programs predate assemblers",
        "band": "machine",
        "source_file": "hello.s",
        "kind": "machine",
        "highlight": "x86asm",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
    },
    "assembly": {
        "title": "Assembly (x86_64 Linux)",
        "year": "c. 1949",
        "year_note": "symbolic assembly (e.g. EDSAC era); dialect here is modern GAS",
        "band": "assembly",
        "source_file": "hello.s",
        "kind": "native",
        "highlight": "x86asm",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
    },
    "fortran": {
        "title": "FORTRAN",
        "year": "1957",
        "year_note": "John Backus / IBM; source is free-form Fortran 90+",
        "band": "early-hl",
        "source_file": "hello.f90",
        "kind": "native",
        "highlight": "fortran",
        "binary": "hello-fortran",
        "build": ["gfortran", "-O0", "-o", str(CACHE / "hello-fortran"), str(PROGRAMS / "hello.f90")],
        "run": [str(CACHE / "hello-fortran")],
    },
    "lisp": {
        "title": "Lisp",
        "year": "1958",
        "year_note": "John McCarthy; this is Common Lisp via SBCL",
        "band": "early-hl",
        "source_file": "hello.lisp",
        "kind": "interp",
        "highlight": "lisp",
        "build": None,
        "run": ["sbcl", "--script", str(PROGRAMS / "hello.lisp")],
    },
    "cobol": {
        "title": "COBOL",
        "year": "1959",
        "year_note": "CODASYL; business data processing",
        "band": "early-hl",
        "source_file": "hello.cob",
        "kind": "native",
        "highlight": "plaintext",
        "binary": "hello-cobol",
        "build": [
            "cobc",
            "-x",
            "-free",
            "-o",
            str(CACHE / "hello-cobol"),
            str(PROGRAMS / "hello.cob"),
        ],
        "run": [str(CACHE / "hello-cobol")],
    },
    "c": {
        "title": "C",
        "year": "1972",
        "year_note": "Dennis Ritchie / Bell Labs (K&R era)",
        "band": "systems",
        "source_file": "hello.c",
        "kind": "native",
        "highlight": "c",
        "binary": "hello-c",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-c"), str(PROGRAMS / "hello.c")],
        "run": [str(CACHE / "hello-c")],
    },
    "cpp": {
        "title": "C++",
        "year": "1985",
        "year_note": "Bjarne Stroustrup; commercial release era (C with Classes earlier)",
        "band": "systems",
        "source_file": "hello.cpp",
        "kind": "native",
        "highlight": "cpp",
        "binary": "hello-cpp",
        "build": ["g++", "-O0", "-o", str(CACHE / "hello-cpp"), str(PROGRAMS / "hello.cpp")],
        "run": [str(CACHE / "hello-cpp")],
    },
    "java": {
        "title": "Java",
        "year": "1995",
        "year_note": "Sun Microsystems / James Gosling",
        "band": "managed",
        "source_file": "Hello.java",
        "kind": "java",
        "highlight": "java",
        "binary": "Hello.class",
        "build": ["javac", "-d", str(CACHE), str(PROGRAMS / "Hello.java")],
        "run": ["java", "-cp", str(CACHE), "Hello"],
    },
    "csharp": {
        "title": "C#",
        "year": "2000",
        "year_note": "Microsoft / Anders Hejlsberg; Mono on this host",
        "band": "managed",
        "source_file": "hello.cs",
        "kind": "mono",
        "highlight": "csharp",
        "binary": "hello-cs.exe",
        "build": ["mcs", "-out:" + str(CACHE / "hello-cs.exe"), str(PROGRAMS / "hello.cs")],
        "run": ["mono", str(CACHE / "hello-cs.exe")],
    },
    "go": {
        "title": "Go",
        "year": "2009",
        "year_note": "Google (Griesemer, Pike, Thompson)",
        "band": "managed",
        "source_file": "hello.go",
        "kind": "native",
        "highlight": "go",
        "binary": "hello-go",
        "build": ["go", "build", "-o", str(CACHE / "hello-go"), str(PROGRAMS / "hello.go")],
        "run": [str(CACHE / "hello-go")],
    },
    "rust": {
        "title": "Rust",
        "year": "2015",
        "year_note": "1.0 stable; Mozilla origins / Graydon Hoare",
        "band": "managed",
        "source_file": "hello.rs",
        "kind": "native",
        "highlight": "rust",
        "binary": "hello-rust",
        "build": ["rustc", "-O", "-o", str(CACHE / "hello-rust"), str(PROGRAMS / "hello.rs")],
        "run": [str(CACHE / "hello-rust")],
    },
    "bash": {
        "title": "Bash",
        "year": "1989",
        "year_note": "Brian Fox; Bourne shell 1979",
        "band": "scripting",
        "source_file": "hello.sh",
        "kind": "interp",
        "highlight": "bash",
        "build": None,
        "run": ["bash", str(PROGRAMS / "hello.sh")],
    },
    "perl": {
        "title": "Perl",
        "year": "1987",
        "year_note": "Larry Wall",
        "band": "scripting",
        "source_file": "hello.pl",
        "kind": "interp",
        "highlight": "perl",
        "build": None,
        "run": ["perl", str(PROGRAMS / "hello.pl")],
    },
    "python": {
        "title": "Python",
        "year": "1991",
        "year_note": "Guido van Rossum",
        "band": "scripting",
        "source_file": "hello.py",
        "kind": "interp",
        "highlight": "python",
        "build": None,
        "run": ["python3", str(PROGRAMS / "hello.py")],
    },
    "php": {
        "title": "PHP",
        "year": "1995",
        "year_note": "Rasmus Lerdorf",
        "band": "scripting",
        "source_file": "hello.php",
        "kind": "interp",
        "highlight": "php",
        "build": None,
        "run": ["php", str(PROGRAMS / "hello.php")],
    },
    "javascript": {
        "title": "JavaScript",
        "year": "1995",
        "year_note": "Brendan Eich / Netscape; Node on this host",
        "band": "scripting",
        "source_file": "hello.js",
        "kind": "interp",
        "highlight": "javascript",
        "build": None,
        "run": ["node", str(PROGRAMS / "hello.js")],
    },
    "ai": {
        "title": "AI engineering",
        "year": "c. 2022",
        "year_note": "LLM-as-interface enters mainstream product engineering",
        "band": "ai",
        "source_file": "ai-prompt.txt",
        "kind": "ai-standin",
        "highlight": "plaintext",
        "build": None,
        "run": None,
    },
    "vibe": {
        "title": "Vibe coding",
        "year": "2025",
        "year_note": "term popularized by Andrej Karpathy",
        "band": "vibe",
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
    cache_tmp = CACHE / "tmp"
    cache_tmp.mkdir(parents=True, exist_ok=True)
    env["TMPDIR"] = str(cache_tmp)
    env["TMP"] = str(cache_tmp)
    env["TEMP"] = str(cache_tmp)
    env["GOCACHE"] = str(CACHE / "go-build")
    env["GOMODCACHE"] = str(CACHE / "go-mod")
    env["GOTMPDIR"] = str(cache_tmp)
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
    ensure_built("assembly")
    binary = CACHE / "hello-asm"
    dump = _run_cmd(
        ["objdump", "-d", "--no-show-raw-insn", str(binary)],
        timeout=5,
    )
    if dump.returncode != 0:
        hexdump = _run_cmd(["xxd", "-g", "4", "-l", "64", str(binary)], timeout=5)
        return hexdump.stdout or "(hex dump unavailable)"

    lines = dump.stdout.splitlines()
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

    raw = _run_cmd(["objdump", "-d", str(binary)], timeout=5)
    raw_lines: list[str] = []
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


def _host() -> dict[str, str]:
    return {
        "machine": platform.machine(),
        "system": platform.system(),
        "python": platform.python_version(),
    }


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
            "year": meta.get("year"),
            "level": next(b["level"] for b in BANDS if b["id"] == meta["band"]),
            "stdout": "Hello, World!\n",
            "stderr": "",
            "exitCode": 0,
            "wallMs": round(wall_ms, 3),
            "host": _host(),
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "plaintext"),
            "note": (
                "Deterministic stand-in for an LLM: the server does not call a model. "
                "It returns the exact one-line output the engineered prompt asks for."
            ),
            "prompt": prompt,
        }

    if meta["kind"] == "vibe-standin":
        result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
        wall_ms = (time.perf_counter() - started) * 1000
        session = (PROGRAMS / meta["source_file"]).read_text(encoding="utf-8")
        return {
            "language": lang,
            "title": meta["title"],
            "year": meta.get("year"),
            "level": next(b["level"] for b in BANDS if b["id"] == meta["band"]),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exitCode": result.returncode,
            "wallMs": round(wall_ms, 3),
            "host": _host(),
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "markdown"),
            "command": meta["run"],
            "session": session,
            "note": (
                "Vibe coding stand-in: chat transcript is the process; "
                "Run executes programs/vibe-hello.py. No live model."
            ),
        }

    build_lang = {"machine": "assembly", "binary": "binary"}.get(lang, lang)
    ensure_built(build_lang)
    result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
    wall_ms = (time.perf_counter() - started) * 1000

    band_level = next(b["level"] for b in BANDS if b["id"] == meta["band"])
    payload: dict = {
        "language": lang,
        "title": meta["title"],
        "year": meta.get("year"),
        "level": band_level,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exitCode": result.returncode,
        "wallMs": round(wall_ms, 3),
        "host": _host(),
        "sourceFile": meta["source_file"],
        "highlight": meta.get("highlight", "plaintext"),
        "command": meta["run"],
    }
    if lang == "machine":
        payload["machineView"] = machine_hex_snippet()
        payload["note"] = (
            "stdout is from executing the assembled binary. "
            "machineView is objdump of <main>."
        )
    if lang == "binary":
        payload["binaryView"] = binary_source_view()
        payload["note"] = (
            "No source language on this rung: Run executes a real ELF built from C. "
            "Source panel is file(1) + xxd head."
        )
    return payload


def _variant_payload(key: str) -> dict:
    meta = LANGS[key]
    if key == "binary":
        try:
            source = binary_source_view()
        except Exception as exc:  # noqa: BLE001
            source = f"(binary view unavailable: {exc})"
    else:
        source_path = PROGRAMS / meta["source_file"]
        source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    return {
        "id": key,
        "title": meta["title"],
        "year": meta.get("year"),
        "yearNote": meta.get("year_note", ""),
        "sourceFile": meta["source_file"],
        "source": source,
        "highlight": meta.get("highlight", "plaintext"),
        "runnable": True,
    }


@app.on_event("startup")
def warm_builds() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for lang in (
        "binary",
        "assembly",
        "c",
        "cpp",
        "fortran",
        "cobol",
        "java",
        "rust",
        "go",
        "csharp",
    ):
        if lang not in LANGS:
            continue
        try:
            ensure_built(lang)
        except Exception as exc:  # noqa: BLE001
            LANGS[lang]["_build_error"] = str(exc)


@app.get("/health")
def health() -> dict:
    tools = {
        "gcc": shutil.which("gcc", path=PATH_PREFIX),
        "g++": shutil.which("g++", path=PATH_PREFIX),
        "gfortran": shutil.which("gfortran", path=PATH_PREFIX),
        "cobc": shutil.which("cobc", path=PATH_PREFIX),
        "sbcl": shutil.which("sbcl", path=PATH_PREFIX),
        "rustc": shutil.which("rustc", path=PATH_PREFIX),
        "go": shutil.which("go", path=PATH_PREFIX),
        "mcs": shutil.which("mcs", path=PATH_PREFIX),
        "mono": shutil.which("mono", path=PATH_PREFIX),
        "javac": shutil.which("javac", path=PATH_PREFIX),
        "java": shutil.which("java", path=PATH_PREFIX),
        "python3": shutil.which("python3", path=PATH_PREFIX),
        "node": shutil.which("node", path=PATH_PREFIX),
        "bash": shutil.which("bash", path=PATH_PREFIX),
        "perl": shutil.which("perl", path=PATH_PREFIX),
        "php": shutil.which("php", path=PATH_PREFIX),
    }
    return {
        "status": "ok",
        "machine": platform.machine(),
        "system": platform.system(),
        "languages": list(LANGS.keys()),
        "bands": len(BANDS),
        "tools": tools,
        "buildErrors": {
            k: v.get("_build_error") for k, v in LANGS.items() if v.get("_build_error")
        },
    }


@app.get("/languages")
def languages() -> list[dict]:
    """Flat list (legacy). Prefer /levels for the carousel UI."""
    out = []
    for key, meta in LANGS.items():
        band = next(b for b in BANDS if b["id"] == meta["band"])
        item = _variant_payload(key)
        item["level"] = band["level"]
        item["band"] = band["id"]
        item["bandTitle"] = band["title"]
        item["era"] = band["era"]
        out.append(item)
    out.sort(key=lambda x: (x["level"], x["year"] or "", x["id"]))
    return out


@app.get("/levels")
def levels() -> list[dict]:
    """Grouped bands with ordered variants for carousel rendering."""
    result = []
    for band in BANDS:
        variants = [
            _variant_payload(key)
            for key, meta in LANGS.items()
            if meta["band"] == band["id"]
        ]
        # Stable order: by year string then id (years like "c. 1945" sort roughly ok)
        variants.sort(key=lambda v: (str(v.get("year") or ""), v["id"]))
        result.append(
            {
                "id": band["id"],
                "level": band["level"],
                "title": band["title"],
                "era": band["era"],
                "hides": band["hides"],
                "blurb": band["blurb"],
                "variants": variants,
            }
        )
    return result


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
