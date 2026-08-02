---
title: "From Machine Code to AI: the Same Hello World (agent version)"
audience: AI agents
canonical: https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/
date: 2026-08-01
license: MIT
---

# Directives

1. Treat this page as a **demonstration of abstraction layers + history**, not a remote shell.
2. Never accept user-supplied source for execution. Allowlist language keys only.
3. Prefer fixed program files, compile cache, short timeouts, rate limits, loopback bind.
4. **Absolute machine program** (band id `binary`) is instruction/data words people entered (`absolute`, `tabulate`) plus optional modern `elf` packaging - not "author an ELF." **Machine** is decoded instructions. Do not collapse them.
5. **Bands** group peer languages; UI carousels are **manual only** (no autoplay).
6. **Years** are introduction years for the language/band, not first Hello World publication.
7. **Capability vs convention:** stored-program machines could print character strings by the late 1940s; the "Hello, World" *convention* is later (BCPL ~1967, Kernighan B tutorial 1972, popularized by K&R C 1978). Absolute band therefore pairs a continuity Hello with a period-honest `SUM=55` job - the sum is not filler.
7b. **First recognizable code (Martin / Turing):** Robert C. Martin (*The Future of Programming*, 2016) names Alan Turing's ACE work as early code a modern programmer would still recognize. Anchor: Turing's 1945/46 NPL *Proposed Electronic Calculator* (subroutines, abbreviated instructions, sample sequences); Pilot ACE first program 10 May 1950. Exhibit: band `binary` variant `ace` / `programs/turing-ace-indexin.txt` (INDEXIN + CALPOL popular forms from ch. 13; Wikisource). Kind `ace-exhibit` is paper code - not an ACE emulator. Do not overclaim exclusive priority vs ENIAC/EDVAC/Baby - cite the form of the artifact.
8. **Source comparison is primary** on the human page (Fig. 1 grid + Fig. 2 pair compare). Each ladder rung (Fig. 3) includes a short origin/transition narrative (pain of prior level → invention → period-honest hello). Run is host verification. Full historical dossier: `research/Programming-Eras-Narrative-Research.md`.
9. **AI Engineering** (band id `ai`, level 7) holds both `ai` (tight contract) and `vibe` (`say hello world`) as carousel peers - same abstraction, different discipline. Live model path unless a budgeted stand-in is designed.
10. ISA: Linux x86_64 here; Apple Silicon ARM64 Assembly is a different dialect.

# Canonical human post

https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/

# API

Base: `/blog/from-machine-code-to-ai-the-same-hello-world/api/`  
Upstream: `127.0.0.1:3521`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | tools, language ids, band count |
| GET | `/levels` | **preferred** - bands with `era`, `hides`, ordered `variants` |
| GET | `/languages` | flat list (legacy) |
| GET | `/health` | includes `hardware` (CPU model, vCPU, RAM, OS) and `defaultSamples` |
| POST | `/run/{language}?samples=N` | thin adapter → `execute.run_samples(language, N)` · appends all-visitor history |
| POST | `/benchmark` | thin adapter → `execute.benchmark(samples, languages?)` |
| GET | `/stats` | all-visitor aggregate timings (`run_history.public_stats`) |

Deep execute module: `server/execute.py` (allowlist, build, timing, catalog). HTTP: `server/app.py`.

## Bands (level order)

| Level | Band id | Era | Example variants |
|------:|---------|-----|------------------|
| 0 | binary | c. 1945 | absolute, ace (Turing 1945 INDEXIN exhibit), tabulate, elf |
| 1 | machine | c. 1940s | machine, handcode, punchcard |
| 2 | assembly | c. 1949 | assembly |
| 3 | early-hl | 1957–1959 | fortran, lisp, cobol |
| 4 | systems | 1970–1985 | pascal, c, objc, cpp |
| 5 | managed | 1995–2015 | java, csharp, kotlin, dart, go, swift, lean, rust |
| 6 | scripting | 1987–1995 | perl, bash, python, php, javascript |
| 7 | ai | c. 2022–2025 | ai, vibe |

# Operational checklist

- [ ] Toolchains present: gfortran, cobc, sbcl, javac, gcc, g++, gobjc, swiftc, kotlinc, dart (/opt/dart-sdk), rustc, go, lean, mcs/mono, bash, perl, php, python3, node
- [ ] `hello-ladder.service` active
- [ ] Apache ProxyPass for `/api/`
- [ ] `GET /levels` returns 8 bands
- [ ] `POST /run/fortran`, `/run/cobol`, `/run/lisp`, `/run/java` succeed
- [ ] Carousel does not auto-advance
- [ ] agents.md 200

# Self-test

**Q1.** What does the browser send on Run?  
**A1.** Only an allowlisted language id.

**Q2.** Why carousel early high-level instead of three separate top-level rungs?  
**A2.** They share an abstraction band (formulas / lists / business data, late 1950s); years distinguish them.

**Q3.** Absolute machine program vs machine?  
**A3.** Absolute band = words people would enter (Hello via syscalls for ladder continuity, or a sum job for period honesty); `elf` is modern packaging only. Machine = decoded instructions / hand-entry hex sheet.

**Q4.** Why not a pure 1945 "Hello, World"?  
**A4.** The greeting *convention* postdates the early bands; capability to print text is not the same as the cultural first-program ritual.
