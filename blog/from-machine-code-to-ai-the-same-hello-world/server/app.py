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
from pydantic import BaseModel, Field

POST_DIR = Path(__file__).resolve().parent.parent
PROGRAMS = POST_DIR / "programs"
CACHE = POST_DIR / "cache"
GITHUB_TREE = (
    "https://github.com/JacobStephens2/stephens.page/tree/main/"
    "blog/from-machine-code-to-ai-the-same-hello-world"
)
GITHUB_BLOB_PROGRAMS = (
    "https://github.com/JacobStephens2/stephens.page/blob/main/"
    "blog/from-machine-code-to-ai-the-same-hello-world/programs"
)
GITHUB_BLOB_SERVER = (
    "https://github.com/JacobStephens2/stephens.page/blob/main/"
    "blog/from-machine-code-to-ai-the-same-hello-world/server"
)

RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60
BENCH_RATE_LIMIT = 4
BENCH_RATE_WINDOW_SECONDS = 300
RUN_TIMEOUT_SECONDS = 3
BUILD_TIMEOUT_SECONDS = 60
BENCH_SAMPLES_MIN = 1
BENCH_SAMPLES_MAX = 100
BENCH_TOTAL_TIMEOUT_SECONDS = 420

PATH_PREFIX = os.environ.get(
    "HELLO_LADDER_PATH",
    "/home/jacob/.cargo/bin:/usr/local/go/bin:/usr/bin:/bin",
)

_requests: dict[str, deque[float]] = defaultdict(deque)
_bench_requests: dict[str, deque[float]] = defaultdict(deque)

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
        "blurb": "Raw opcodes - and a hand-entry hex sheet for how people loaded them before assemblers.",
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
        "era": "1970–1985",
        "hides": "Hides instruction selection; still close to the machine model.",
        "blurb": "Pascal, C, and C++ - structured systems programming with a thin runtime.",
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
        "title": "Machine code (objdump)",
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
    "handcode": {
        "title": "Hand-entered hex",
        "year": "c. 1940s–50s",
        "year_note": "front panels, paper tape, absolute hex before assemblers",
        "band": "machine",
        "source_file": "hand-entry.txt",
        "kind": "handcode",
        "highlight": "plaintext",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
        "build_source": "hello.s",
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
    "pascal": {
        "title": "Pascal",
        "year": "1970",
        "year_note": "Niklaus Wirth; namesake of PascalCase",
        "band": "systems",
        "source_file": "hello.pas",
        "kind": "native",
        "highlight": "plaintext",
        "binary": "hello-pascal",
        "build": [
            "fpc",
            "-O1",
            f"-FE{CACHE}",
            f"-FU{CACHE}",
            f"-o{CACHE / 'hello-pascal'}",
            str(PROGRAMS / "hello.pas"),
        ],
        "run": [str(CACHE / "hello-pascal")],
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


def _read_first(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def hardware_info() -> dict:
    """Facts about the production host that executes allowlisted programs."""
    model = ""
    cpus = os.cpu_count() or 0
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        model = platform.processor() or "unknown"

    mem_total_kib = 0
    try:
        with open("/proc/meminfo", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    mem_total_kib = int(parts[1])
                    break
    except (OSError, ValueError, IndexError):
        mem_total_kib = 0

    pretty = ""
    for line in _read_first("/etc/os-release").splitlines():
        if line.startswith("PRETTY_NAME="):
            pretty = line.split("=", 1)[1].strip().strip('"')
            break

    return {
        "provider": "DigitalOcean droplet",
        "model": model or "DO-Premium-AMD (reported)",
        "architecture": platform.machine(),
        "cpus": cpus,
        "memoryGiB": round(mem_total_kib / (1024 * 1024), 1) if mem_total_kib else None,
        "os": pretty or f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "note": (
            "Times measure wall clock for a short allowlisted Hello World on this shared "
            "host - not microbenchmarks. Other services run on the same machine."
        ),
    }


def _host() -> dict:
    hw = hardware_info()
    return {
        "machine": hw["architecture"],
        "system": platform.system(),
        "python": hw["python"],
        "cpus": hw["cpus"],
        "model": hw["model"],
        "memoryGiB": hw["memoryGiB"],
    }


def _stats(samples_ms: list[float]) -> dict:
    n = len(samples_ms)
    if n == 0:
        return {"samples": 0, "avgMs": None, "minMs": None, "maxMs": None, "stdevMs": None}
    avg = sum(samples_ms) / n
    mn = min(samples_ms)
    mx = max(samples_ms)
    if n > 1:
        var = sum((x - avg) ** 2 for x in samples_ms) / (n - 1)
        stdev = var**0.5
    else:
        stdev = 0.0
    return {
        "samples": n,
        "avgMs": round(avg, 3),
        "minMs": round(mn, 3),
        "maxMs": round(mx, 3),
        "stdevMs": round(stdev, 3),
    }


def run_language_once(lang: str) -> dict:
    """Single execution (build if needed). Used by /run and multi-sample benches."""
    return run_language(lang)


def run_language_samples(lang: str, samples: int) -> dict:
    """Run allowlisted program `samples` times after one build; return avg stats."""
    if lang not in LANGS:
        raise KeyError(lang)
    samples = max(BENCH_SAMPLES_MIN, min(BENCH_SAMPLES_MAX, int(samples)))

    # Build once (untimed), then time execute-only samples.
    build_lang = {
        "machine": "assembly",
        "handcode": "handcode",
        "binary": "binary",
    }.get(lang, lang)
    meta = LANGS[lang]
    if meta.get("build"):
        ensure_built(build_lang)

    times: list[float] = []
    last: dict | None = None
    stdout_set: set[str] = set()
    exit_codes: set[int] = set()
    for i in range(samples):
        # Full detail only on the last sample (objdump / ELF view once).
        last = run_language(lang, detail=(i == samples - 1))
        times.append(float(last.get("wallMs") or 0.0))
        stdout_set.add((last.get("displayStdout") or last.get("stdout") or "").strip())
        exit_codes.add(int(last.get("exitCode") or 0))

    assert last is not None
    stats = _stats(times)
    last["samples"] = stats["samples"]
    last["avgMs"] = stats["avgMs"]
    last["minMs"] = stats["minMs"]
    last["maxMs"] = stats["maxMs"]
    last["stdevMs"] = stats["stdevMs"]
    last["sampleMs"] = [round(t, 3) for t in times]
    last["wallMs"] = stats["avgMs"]  # primary displayed timing is the average
    last["stdoutConsistent"] = len(stdout_set) == 1
    last["exitCodes"] = sorted(exit_codes)
    last["stdoutVariants"] = sorted(stdout_set)
    last["host"] = _host()
    if samples > 1:
        last["note"] = (
            (last.get("note") + " " if last.get("note") else "")
            + f"Timing is mean of {samples} server-side runs "
            f"(min {stats['minMs']} ms, max {stats['maxMs']} ms, stdev {stats['stdevMs']} ms)."
        )
    return last


class BenchmarkRequest(BaseModel):
    samples: int = Field(default=10, ge=BENCH_SAMPLES_MIN, le=BENCH_SAMPLES_MAX)
    languages: list[str] | None = None


def run_language(lang: str, *, detail: bool = True) -> dict:
    if lang not in LANGS:
        raise KeyError(lang)
    meta = LANGS[lang]
    started = time.perf_counter()
    band_level = next(b["level"] for b in BANDS if b["id"] == meta["band"])

    if meta["kind"] == "ai-standin":
        wall_ms = (time.perf_counter() - started) * 1000
        payload = {
            "language": lang,
            "title": meta["title"],
            "year": meta.get("year"),
            "level": band_level,
            "stdout": "Hello, World!\n",
            "stderr": "",
            "exitCode": 0,
            "wallMs": round(wall_ms, 3),
            "host": _host() if detail else {},
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "plaintext"),
            "displayStdout": "Hello, World!",
            "note": (
                "Deterministic stand-in for an LLM: the server does not call a model. "
                "It returns the exact one-line output the engineered prompt asks for."
            ),
        }
        if detail:
            payload["prompt"] = (PROGRAMS / "ai-prompt.txt").read_text(encoding="utf-8")
        return payload

    if meta["kind"] == "vibe-standin":
        result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
        wall_ms = (time.perf_counter() - started) * 1000
        stdout = (result.stdout or "").replace("\r\n", "\n")
        payload = {
            "language": lang,
            "title": meta["title"],
            "year": meta.get("year"),
            "level": band_level,
            "stdout": stdout,
            "stderr": result.stderr,
            "exitCode": result.returncode,
            "wallMs": round(wall_ms, 3),
            "host": _host() if detail else {},
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "markdown"),
            "command": meta["run"],
            "displayStdout": stdout.strip() or "(empty stdout)",
            "note": (
                "Vibe coding stand-in: chat transcript is the process; "
                "Run executes programs/vibe-hello.py. No live model."
            ),
        }
        if detail:
            payload["session"] = (PROGRAMS / meta["source_file"]).read_text(encoding="utf-8")
        return payload

    build_lang = {
        "machine": "assembly",
        "handcode": "handcode",
        "binary": "binary",
    }.get(lang, lang)
    ensure_built(build_lang)
    # Time only the execute step after build is warm.
    started = time.perf_counter()
    result = _run_cmd(meta["run"], RUN_TIMEOUT_SECONDS)
    wall_ms = (time.perf_counter() - started) * 1000

    stdout = (result.stdout or "").replace("\r\n", "\n")
    payload: dict = {
        "language": lang,
        "title": meta["title"],
        "year": meta.get("year"),
        "level": band_level,
        "stdout": stdout,
        "stderr": result.stderr,
        "exitCode": result.returncode,
        "wallMs": round(wall_ms, 3),
        "host": _host() if detail else {},
        "sourceFile": meta["source_file"],
        "highlight": meta.get("highlight", "plaintext"),
        "command": meta["run"],
        "displayStdout": stdout.strip() or "(empty stdout)",
    }
    if not detail:
        return payload
    if lang == "machine":
        payload["machineView"] = machine_hex_snippet()
        payload["note"] = (
            "stdout is from executing the assembled binary. "
            "machineView is objdump of <main>. For hand-keyed hex, carousel to Hand-entered hex."
        )
    if lang == "handcode":
        payload["note"] = (
            "Executed the same ELF as Assembly/Machine. The source sheet is a teaching "
            "re-enactment of absolute hex entry (front panel / paper tape style) - not a 1949 ISA."
        )
    if lang == "binary":
        payload["binaryView"] = binary_source_view()
        payload["note"] = (
            "Executed a real ELF (chmod +x style program). "
            "Stdout is the program output; the source dump is the file format, not what you type by hand."
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
    src_name = meta["source_file"]
    return {
        "id": key,
        "title": meta["title"],
        "year": meta.get("year"),
        "yearNote": meta.get("year_note", ""),
        "sourceFile": src_name,
        "source": source,
        "highlight": meta.get("highlight", "plaintext"),
        "runnable": True,
        "githubUrl": f"{GITHUB_BLOB_PROGRAMS}/{src_name}",
    }


@app.on_event("startup")
def warm_builds() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for lang in (
        "binary",
        "assembly",
        "pascal",
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
        "fpc": shutil.which("fpc", path=PATH_PREFIX),
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
        "hardware": hardware_info(),
        "defaultSamples": 10,
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
                "githubTree": GITHUB_TREE,
                "githubPrograms": GITHUB_BLOB_PROGRAMS,
                "githubServer": GITHUB_BLOB_SERVER,
            }
        )
    return result


@app.post("/run/{language}")
async def run_endpoint(
    language: str,
    request: Request,
    response: Response,
    samples: int = 10,
) -> dict:
    """Run an allowlisted program. Default samples=10 (mean wall time)."""
    enforce_rate_limit(request)
    if language not in LANGS:
        raise HTTPException(status_code=404, detail=f"Unknown language: {language}")
    samples = max(BENCH_SAMPLES_MIN, min(BENCH_SAMPLES_MAX, int(samples)))
    timeout = BUILD_TIMEOUT_SECONDS + (RUN_TIMEOUT_SECONDS + 1) * samples + 5
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_language_samples, language, samples),
            timeout=timeout,
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


@app.post("/benchmark")
async def benchmark_endpoint(
    payload: BenchmarkRequest,
    request: Request,
    response: Response,
) -> dict:
    """Run every (or selected) language N times server-side; return a comparison table."""
    enforce_bench_rate_limit(request)
    samples = payload.samples
    if payload.languages:
        langs = [x for x in payload.languages if x in LANGS]
        unknown = [x for x in payload.languages if x not in LANGS]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown languages: {unknown}")
    else:
        # Prefer one representative per band for speed, plus all unique langs.
        # Full matrix is intentional for the comparison table.
        langs = list(LANGS.keys())

    def _bench_all() -> list[dict]:
        rows: list[dict] = []
        for lang in langs:
            try:
                result = run_language_samples(lang, samples)
                rows.append(
                    {
                        "id": lang,
                        "title": result.get("title"),
                        "year": result.get("year"),
                        "level": result.get("level"),
                        "avgMs": result.get("avgMs"),
                        "minMs": result.get("minMs"),
                        "maxMs": result.get("maxMs"),
                        "stdevMs": result.get("stdevMs"),
                        "samples": result.get("samples"),
                        "stdout": (result.get("displayStdout") or result.get("stdout") or "").strip(),
                        "stdoutConsistent": result.get("stdoutConsistent"),
                        "exitCodes": result.get("exitCodes"),
                        "ok": result.get("exitCode") == 0,
                        "error": None,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    {
                        "id": lang,
                        "title": LANGS[lang]["title"],
                        "year": LANGS[lang].get("year"),
                        "level": next(
                            b["level"] for b in BANDS if b["id"] == LANGS[lang]["band"]
                        ),
                        "avgMs": None,
                        "minMs": None,
                        "maxMs": None,
                        "stdevMs": None,
                        "samples": samples,
                        "stdout": "",
                        "stdoutConsistent": False,
                        "exitCodes": [],
                        "ok": False,
                        "error": str(exc),
                    }
                )
        rows.sort(key=lambda r: (r["avgMs"] is None, r["avgMs"] if r["avgMs"] is not None else 0))
        return rows

    try:
        rows = await asyncio.wait_for(
            asyncio.to_thread(_bench_all),
            timeout=BENCH_TOTAL_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Benchmark exceeded the global time limit.",
        ) from exc

    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return {
        "samples": samples,
        "hardware": hardware_info(),
        "count": len(rows),
        "rows": rows,
    }
