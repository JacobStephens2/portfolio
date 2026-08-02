from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Sequence

class UnknownLanguage(KeyError):
    """Raised when language id is not in the allowlist."""

class ExecuteError(RuntimeError):
    """Raised when build or execution fails."""

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
DEFAULT_SAMPLES = 10
BENCH_TOTAL_TIMEOUT_SECONDS = 420

# Include Swift (/opt/swift), Dart SDK (/opt/dart-sdk), and standard tool locations.
PATH_PREFIX = os.environ.get(
    "HELLO_LADDER_PATH",
    "/opt/dart-sdk/bin:/opt/swift/usr/bin:/home/jacob/.elan/bin:/home/jacob/.cargo/bin:/usr/local/go/bin:/usr/bin:/bin",
)

# Abstraction bands (ordered). Each band may hold multiple language variants.
BANDS: list[dict] = [
    {
        "id": "binary",
        "level": 0,
        "title": "Absolute machine program",
        "era": "c. 1945",
        "hides": "No symbolic source - instruction and data words only.",
        "blurb": "What people actually entered: absolute words (hex/octal), not a modern ELF shipping crate.",
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
        "blurb": "Pascal, C, Objective-C, and C++ - structured systems programming with a thin runtime.",
    },
    {
        "id": "managed",
        "level": 5,
        "title": "Managed / safe systems",
        "era": "1995–2015",
        "hides": "Hides more memory/safety details behind a runtime or type system.",
        "blurb": "Java, C#, Kotlin, Dart, Go, Swift, Rust, Lean - GC, VMs, ownership, or dependent types as machinery.",
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
        "title": "AI Engineering",
        "era": "c. 2022–2025",
        "hides": "Code behind a natural-language interface to a model.",
        "blurb": "Same machinery, two disciplines: a tight prompt contract vs a casual vibe one-liner (Karpathy).",
    },
]

def _as_ld_build(stem: str, source_s: str) -> list[str]:
    """Assemble + link a no-libc absolute program (as + ld)."""
    obj = CACHE / f"{stem}.o"
    out = CACHE / stem
    src = PROGRAMS / source_s
    return [
        "sh",
        "-c",
        f"as -o {obj} {src} && ld -o {out} {obj}",
    ]


# language_id -> runnable variant metadata
LANGS: dict[str, dict] = {
    "absolute": {
        "title": "Absolute machine words",
        "year": "c. 1945",
        "year_note": "instruction + data words people entered; live objdump of _start (sys_write + sys_exit, no libc) - not ELF headers",
        "band": "binary",
        "source_file": "absolute-words.txt",
        "kind": "absolute",
        "highlight": "plaintext",
        "binary": "hello-raw",
        "build": _as_ld_build("hello-raw", "hello_raw.s"),
        "run": [str(CACHE / "hello-raw")],
        "build_source": "hello_raw.s",
    },
    "tabulate": {
        "title": "Numerical job (sum 1..10)",
        "year": "c. 1950",
        "year_note": "tables and totals were typical early work - not greetings; live objdump of sum 1..10 → SUM=55",
        "band": "binary",
        "source_file": "tabulate-words.txt",
        "kind": "tabulate",
        "highlight": "plaintext",
        "binary": "hello-sum",
        "build": _as_ld_build("hello-sum", "hello_sum.s"),
        "run": [str(CACHE / "hello-sum")],
        "build_source": "hello_sum.s",
    },
    "elf": {
        "title": "Modern ELF packaging",
        "year": "c. 1985",
        "year_note": "OS file format (ELF) around the absolute program - shipping crate, not handwritten invoice; xxd of first 256 bytes",
        "band": "binary",
        "source_file": "elf-note.txt",
        "kind": "elf",
        "highlight": "plaintext",
        "binary": "hello-raw",
        "build": _as_ld_build("hello-raw", "hello_raw.s"),
        "run": [str(CACHE / "hello-raw")],
        "build_source": "hello_raw.s",
    },
    "machine": {
        "title": "Machine code (objdump)",
        "year": "c. 1940s",
        "year_note": "live objdump of <main> opcodes; plugboards and binary programs predate assemblers",
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
        "year_note": "front panels / paper tape / absolute hex before assemblers; teaching re-enactment of form, not a 1949 ISA",
        "band": "machine",
        "source_file": "hand-entry.txt",
        "kind": "handcode",
        "highlight": "plaintext",
        "binary": "hello-asm",
        "build": ["gcc", "-O0", "-o", str(CACHE / "hello-asm"), str(PROGRAMS / "hello.s")],
        "run": [str(CACHE / "hello-asm")],
        "build_source": "hello.s",
    },
    "punchcard": {
        "title": "Punch cards (sim)",
        "year": "c. 1890–1970s",
        "year_note": "Hollerith → unit record → source/data decks; 80-col teaching stand-in (not a live card reader)",
        "band": "machine",
        "source_file": "punch-card.txt",
        "kind": "punchcard-sim",
        "highlight": "plaintext",
        "build": None,
        "run": None,
    },
    "assembly": {
        "title": "Assembly (x86_64 Linux)",
        "year": "c. 1949",
        "year_note": "symbolic assembly (e.g. EDSAC era); dialect here is modern GAS on Linux x86_64 via libc puts (amd64 host, not Apple Silicon ARM64)",
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
        "year_note": "John Backus / IBM; free-form Fortran 90+; explicit (A) format (list-directed write inserts a leading space)",
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
        "year_note": "CODASYL; free-format source; business data processing",
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
    "objc": {
        "title": "Objective-C",
        "year": "1984",
        "year_note": "Brad Cox / Stepstone; NeXT and Apple later; GNU runtime without Cocoa/GNUstep Foundation on this host",
        "band": "systems",
        "source_file": "hello.m",
        "kind": "native",
        "highlight": "objectivec",
        "binary": "hello-objc",
        "build": [
            "gcc",
            "-x",
            "objective-c",
            "-O0",
            "-o",
            str(CACHE / "hello-objc"),
            str(PROGRAMS / "hello.m"),
            "-lobjc",
        ],
        "run": [str(CACHE / "hello-objc")],
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
    "kotlin": {
        "title": "Kotlin",
        "year": "2011",
        "year_note": "JetBrains; 1.0 in 2016; JVM-first with null-safety; bytecode via kotlinc on this host",
        "band": "managed",
        "source_file": "hello.kt",
        "kind": "kotlin",
        "highlight": "kotlin",
        "binary": "hello-kotlin.jar",
        "build": [
            "kotlinc",
            str(PROGRAMS / "hello.kt"),
            "-include-runtime",
            "-d",
            str(CACHE / "hello-kotlin.jar"),
        ],
        "run": ["java", "-jar", str(CACHE / "hello-kotlin.jar")],
    },
    "dart": {
        "title": "Dart",
        "year": "2011",
        "year_note": "Google; 1.0 in 2013; client-first (web/Flutter); AOT via dart compile exe on this host",
        "band": "managed",
        "source_file": "hello.dart",
        "kind": "native",
        "highlight": "dart",
        "binary": "hello-dart",
        "build": [
            "dart",
            "compile",
            "exe",
            "-o",
            str(CACHE / "hello-dart"),
            str(PROGRAMS / "hello.dart"),
        ],
        "run": [str(CACHE / "hello-dart")],
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
    "swift": {
        "title": "Swift",
        "year": "2014",
        "year_note": "Apple; open source 2015; systems/app language with C interop; swiftc Linux toolchain on this host",
        "band": "managed",
        "source_file": "hello.swift",
        "kind": "native",
        "highlight": "swift",
        "binary": "hello-swift",
        "build": [
            "swiftc",
            "-O",
            "-o",
            str(CACHE / "hello-swift"),
            str(PROGRAMS / "hello.swift"),
        ],
        "run": [str(CACHE / "hello-swift")],
    },
    "lean": {
        "title": "Lean",
        "year": "2013",
        "year_note": "Leonardo de Moura / Microsoft Research; Lean 4 on this host (lean-lang.org) - theorem prover and general-purpose language with dependent types",
        "band": "managed",
        "source_file": "hello.lean",
        "kind": "interp",
        "highlight": "plaintext",
        "build": None,
        "run": ["lean", "--run", str(PROGRAMS / "hello.lean")],
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
        "title": "Tight contract",
        "year": "2022",
        "year_note": "LLM-as-interface; live GPT-5.6 Luna (reasoning low) on this host",
        "band": "ai",
        "source_file": "ai-prompt.txt",
        "kind": "ai-llm",
        "highlight": "plaintext",
        "build": None,
        "run": None,
        "llm_mode": "ai-engineering",
    },
    "vibe": {
        "title": "Vibe coding",
        "year": "2025",
        "year_note": "Karpathy coinage; same LLM band as AI engineering, casual one-line prompt",
        "band": "ai",
        "source_file": "vibe-session.md",
        "kind": "vibe-llm",
        "highlight": "plaintext",
        "build": None,
        "run": None,
        "llm_mode": "vibe-coding",
        "artifact": "vibe-hello.py",
    },
}


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

def _objdump_symbol(binary: Path, symbol: str, max_lines: int = 20) -> str:
    raw = _run_cmd(["objdump", "-d", str(binary)], timeout=5)
    if raw.returncode != 0:
        return raw.stderr.strip() or "(objdump unavailable)"
    lines = raw.stdout.splitlines()
    out: list[str] = []
    capture = False
    pat = re.compile(rf"<{re.escape(symbol)}>:")
    for line in lines:
        if pat.search(line):
            capture = True
            out.append(line)
            continue
        if capture:
            if line.startswith(" ") or line.startswith("\t") or re.match(r"^[0-9a-f]+:", line):
                out.append(line)
                if len(out) >= max_lines:
                    break
            elif out and not line.strip():
                break
            elif out and re.search(r"<.+>:", line):
                break
    return "\n".join(out) if out else "(symbol not found in objdump)"


def absolute_source_view() -> str:
    """Live _start dump + ASCII payload hex (no narrative comments in the panel)."""
    ensure_built("absolute")
    path = CACHE / "hello-raw"
    dump = _objdump_symbol(path, "_start", max_lines=16)
    # "Hello, World!\n" as absolute data words - shape people entered, not ELF magic
    payload = "48 65 6c 6c 6f 2c 20 57 6f 72 6c 64 21 0a"
    return f"{dump}\n\n{payload}\n"


def tabulate_source_view() -> str:
    """Live _start dump for the sum 1..10 job (no narrative comments)."""
    ensure_built("tabulate")
    path = CACHE / "hello-sum"
    return _objdump_symbol(path, "_start", max_lines=28) + "\n"


def elf_source_view() -> str:
    """Modern packaging dump only - xxd of on-disk container, no prose comments."""
    ensure_built("elf")
    path = CACHE / "hello-raw"
    file_out = _run_cmd(["file", "-b", str(path)], timeout=5)
    size = path.stat().st_size if path.exists() else 0
    xxd = _run_cmd(["xxd", "-g", "1", "-l", "256", str(path)], timeout=5)
    header = f"cache/hello-raw  {size} bytes\n{file_out.stdout.strip()}\n\n"
    return header + (xxd.stdout or "(xxd unavailable)")


def binary_source_view() -> str:
    """Back-compat alias used by older notes; prefer absolute/elf views."""
    return elf_source_view()

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

def run_samples(
    language: str,
    samples: int = 10,
    *,
    detail: bool = True,
    history_source: str = "run",
) -> dict:
    """Run allowlisted program `samples` times after one build; return avg stats."""
    if language not in LANGS:
        raise UnknownLanguage(language)
    samples = max(BENCH_SAMPLES_MIN, min(BENCH_SAMPLES_MAX, int(samples)))
    meta = LANGS[language]
    # Live LLM / punch sim: single shot (don't multiply API spend or fake multi-runs).
    if meta.get("kind") in ("ai-llm", "vibe-llm", "punchcard-sim"):
        samples = 1

    # Build once (untimed), then time execute-only samples.
    build_lang = {
        "machine": "assembly",
        "handcode": "handcode",
        "elf": "absolute",
    }.get(language, language)
    if meta.get("build"):
        ensure_built(build_lang)

    times: list[float] = []
    last: dict | None = None
    stdout_set: set[str] = set()
    exit_codes: set[int] = set()
    for i in range(samples):
        # Full detail only on the last sample (objdump / ELF view once).
        last = run_language(language, detail=bool(detail and i == samples - 1))
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

    # Durable all-visitor aggregate (no PII)
    try:
        import run_history

        ok = int(last.get("exitCode") or 0) == 0
        run_history.record_run(
            language=language,
            title=str(last.get("title") or meta.get("title") or language),
            year=str(last.get("year") or meta.get("year") or ""),
            avg_ms=stats.get("avgMs"),
            min_ms=stats.get("minMs"),
            max_ms=stats.get("maxMs"),
            stdev_ms=stats.get("stdevMs"),
            samples=samples,
            exit_code=int(last.get("exitCode") or 0),
            ok=ok,
            stdout=str(last.get("displayStdout") or last.get("stdout") or ""),
            source=history_source if history_source in ("run", "benchmark") else "run",
        )
    except Exception:  # noqa: BLE001 - never fail a visitor run for stats I/O
        pass

    return last

def _run_llm_rung(lang: str, meta: dict, band_level: int, *, detail: bool) -> dict:
    """Live GPT-5.6 Luna (reasoning low) for AI engineering / vibe coding."""
    import llm_client
    from llm_spend import read_spend

    prompt_path = PROGRAMS / meta["source_file"]
    source_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    if meta["kind"] == "ai-llm":
        system = (
            "You are a precise program. Follow the user's specification exactly. "
            "Output only what is required - no markdown fences unless asked."
        )
        user = source_text.strip() or "Print one line: Hello, World!"
        mode = "ai-engineering"
    else:
        system = (
            "You are a casual coding agent in a vibe-coding chat. "
            "Be brief. Prefer a single working line of output the user can run or see."
        )
        user = source_text.strip() or "say hello world"
        mode = "vibe-coding"

    started = time.perf_counter()
    try:
        llm = llm_client.complete(mode=mode, system=system, user=user)
        err = ""
        exit_code = 0
    except Exception as exc:  # noqa: BLE001
        wall_ms = (time.perf_counter() - started) * 1000
        spend = read_spend()
        return {
            "language": lang,
            "title": meta["title"],
            "year": meta.get("year"),
            "level": band_level,
            "stdout": "",
            "stderr": str(exc),
            "exitCode": 1,
            "wallMs": round(wall_ms, 3),
            "host": _host() if detail else {},
            "sourceFile": meta["source_file"],
            "highlight": meta.get("highlight", "plaintext"),
            "displayStdout": f"(LLM error: {exc})",
            "costUsd": 0.0,
            "spendTotalUsd": float(spend.get("total_usd") or 0),
            "model": llm_client.MODEL,
            "reasoningEffort": llm_client.REASONING_EFFORT,
            "note": f"Live LLM call failed: {exc}",
            "samples": 1,
            "avgMs": round(wall_ms, 3),
            "minMs": round(wall_ms, 3),
            "maxMs": round(wall_ms, 3),
            "stdevMs": 0.0,
        }

    wall_ms = llm.get("llmWallMs") or ((time.perf_counter() - started) * 1000)
    display = llm["displayStdout"]
    payload = {
        "language": lang,
        "title": meta["title"],
        "year": meta.get("year"),
        "level": band_level,
        "stdout": llm.get("stdout") or (display + "\n"),
        "stderr": err,
        "exitCode": exit_code,
        "wallMs": round(float(wall_ms), 3),
        "host": _host() if detail else {},
        "sourceFile": meta["source_file"],
        "highlight": meta.get("highlight", "plaintext"),
        "displayStdout": display,
        "costUsd": llm.get("costUsd"),
        "spendTotalUsd": llm.get("spendTotalUsd"),
        "spendRequestCount": llm.get("spendRequestCount"),
        "inputTokens": llm.get("inputTokens"),
        "outputTokens": llm.get("outputTokens"),
        "cachedInputTokens": llm.get("cachedInputTokens"),
        "model": llm.get("model"),
        "reasoningEffort": llm.get("reasoningEffort"),
        "note": (
            f"Live OpenAI {llm.get('model')} with reasoning.effort="
            f"{llm.get('reasoningEffort')}. This request ~${float(llm.get('costUsd') or 0):.6f}; "
            f"ladder cumulative LLM spend ${float(llm.get('spendTotalUsd') or 0):.4f} "
            f"({llm.get('spendRequestCount')} requests)."
        ),
        "samples": 1,
        "avgMs": round(float(wall_ms), 3),
        "minMs": round(float(wall_ms), 3),
        "maxMs": round(float(wall_ms), 3),
        "stdevMs": 0.0,
    }
    if detail and meta["kind"] == "ai-llm":
        payload["prompt"] = source_text
    if detail and meta["kind"] == "vibe-llm":
        payload["session"] = source_text
        payload["prompt"] = user
    return payload


def run_language(lang: str, *, detail: bool = True) -> dict:
    if lang not in LANGS:
        raise UnknownLanguage(lang)
    meta = LANGS[lang]
    started = time.perf_counter()
    band_level = next(b["level"] for b in BANDS if b["id"] == meta["band"])

    if meta["kind"] in ("ai-llm", "vibe-llm"):
        return _run_llm_rung(lang, meta, band_level, detail=detail)

    if meta["kind"] == "punchcard-sim":
        wall_ms = (time.perf_counter() - started) * 1000
        out = "HELLO, WORLD!\n"
        return {
            "language": lang,
            "title": meta["title"],
            "year": meta.get("year"),
            "level": band_level,
            "stdout": out,
            "stderr": "",
            "exitCode": 0,
            "wallMs": round(wall_ms, 3),
            "host": _host() if detail else {},
            "sourceFile": meta["source_file"],
            "highlight": "plaintext",
            "displayStdout": "HELLO, WORLD!",
            "costUsd": 0.0,
            "note": (
                "Simulated card-deck job: period systems often printed fixed-width "
                "lines or punched result cards - not a modern interactive terminal. "
                "See source sheet for history. Not a live card reader."
            ),
            "samples": 1,
            "avgMs": round(wall_ms, 3),
            "minMs": round(wall_ms, 3),
            "maxMs": round(wall_ms, 3),
            "stdevMs": 0.0,
        }

    if meta["kind"] in ("ai-standin", "vibe-standin"):
        # Legacy kinds kept for tests; prefer ai-llm / vibe-llm in LANGS.
        wall_ms = (time.perf_counter() - started) * 1000
        return {
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
            "costUsd": 0.0,
            "note": "Legacy deterministic stand-in (no live model).",
        }

    build_lang = {
        "machine": "assembly",
        "handcode": "handcode",
        "elf": "absolute",
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
    if lang == "absolute":
        payload["binaryView"] = absolute_source_view()
        payload["note"] = (
            "Executed a minimal absolute program (sys_write + sys_exit, no libc). "
            "Source shows instruction/data words + live objdump of _start - not ELF headers."
        )
    if lang == "tabulate":
        payload["binaryView"] = tabulate_source_view()
        payload["note"] = (
            "Period-flavored numerical job: sum 1..10, print SUM=55. "
            "Early machines spent more time on tables and totals than greetings."
        )
    if lang == "elf":
        payload["binaryView"] = elf_source_view()
        payload["note"] = (
            "Same Hello World job as Absolute machine words. "
            "Source dump is modern ELF packaging (crate), not what operators keyed in 1945."
        )
    return payload

def _variant_payload(key: str) -> dict:
    meta = LANGS[key]
    try:
        if key == "absolute":
            source = absolute_source_view()
        elif key == "tabulate":
            source = tabulate_source_view()
        elif key == "elf":
            source = elf_source_view()
        elif key == "machine":
            source = machine_hex_snippet()
        else:
            source_path = PROGRAMS / meta["source_file"]
            source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    except Exception as exc:  # noqa: BLE001
        source = f"(source view unavailable: {exc})"
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

def warm_builds() -> dict[str, str]:
    """Prebuild native binaries. Returns map of lang -> error string (empty = ok)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    errors: dict[str, str] = {}
    for lang in (
        "absolute",
        "tabulate",
        "assembly",
        "pascal",
        "c",
        "objc",
        "cpp",
        "fortran",
        "cobol",
        "java",
        "kotlin",
        "dart",
        "rust",
        "go",
        "swift",
        "csharp",
    ):
        if lang not in LANGS:
            continue
        try:
            ensure_built(lang)
            errors[lang] = ""
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            LANGS[lang]["_build_error"] = msg
            errors[lang] = msg
    return errors

def known_languages() -> list[str]:
    return list(LANGS.keys())

def tools_present() -> dict[str, str | None]:
    return {
        "as": shutil.which("as", path=PATH_PREFIX),
        "ld": shutil.which("ld", path=PATH_PREFIX),
        "lean": shutil.which("lean", path=PATH_PREFIX),
        "gcc": shutil.which("gcc", path=PATH_PREFIX),
        "g++": shutil.which("g++", path=PATH_PREFIX),
        "swiftc": shutil.which("swiftc", path=PATH_PREFIX),
        "kotlinc": shutil.which("kotlinc", path=PATH_PREFIX),
        "dart": shutil.which("dart", path=PATH_PREFIX),
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

def catalog_languages() -> list[dict]:
    """Flat language list for clients."""
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

def catalog_levels() -> list[dict]:
    """Grouped bands with ordered variants for carousel rendering."""
    result = []
    for band in BANDS:
        variants = [
            _variant_payload(key)
            for key, meta in LANGS.items()
            if meta["band"] == band["id"]
        ]
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

def benchmark(
    samples: int = 10,
    languages: Sequence[str] | None = None,
) -> dict:
    """Run each language `samples` times; return comparison rows sorted by avgMs."""
    samples = max(BENCH_SAMPLES_MIN, min(BENCH_SAMPLES_MAX, int(samples)))
    if languages is not None:
        langs = list(languages)
        unknown = [x for x in langs if x not in LANGS]
        if unknown:
            raise UnknownLanguage(f"Unknown languages: {unknown}")
    else:
        langs = list(LANGS.keys())

    rows: list[dict] = []
    for lang in langs:
        try:
            result = run_samples(lang, samples, history_source="benchmark")
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
    return {
        "samples": samples,
        "hardware": hardware_info(),
        "count": len(rows),
        "rows": rows,
    }
