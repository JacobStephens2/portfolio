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
7. AI and vibe rungs are deterministic stand-ins unless a budgeted model path is designed.
8. ISA: Linux x86_64 here; Apple Silicon ARM64 Assembly is a different dialect.

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
| POST | `/run/{language}?samples=N` | thin adapter → `execute.run_samples(language, N)` |
| POST | `/benchmark` | thin adapter → `execute.benchmark(samples, languages?)` |

Deep execute module: `server/execute.py` (allowlist, build, timing, catalog). HTTP: `server/app.py`.

## Bands (level order)

| Level | Band id | Era | Example variants |
|------:|---------|-----|------------------|
| 0 | binary | c. 1945 | absolute, tabulate, elf |
| 1 | machine | c. 1940s | machine, handcode, punchcard |
| 2 | assembly | c. 1949 | assembly |
| 3 | early-hl | 1957–1959 | fortran, lisp, cobol |
| 4 | systems | 1970–1985 | pascal, c, cpp |
| 5 | managed | 1995–2015 | java, csharp, go, lean, rust |
| 6 | scripting | 1987–1995 | perl, bash, python, php, javascript |
| 7 | ai | c. 2022 | ai |
| 8 | vibe | 2025 | vibe |

# Operational checklist

- [ ] Toolchains present: gfortran, cobc, sbcl, javac, gcc, g++, rustc, go, lean, mcs/mono, bash, perl, php, python3, node
- [ ] `hello-ladder.service` active
- [ ] Apache ProxyPass for `/api/`
- [ ] `GET /levels` returns 9 bands
- [ ] `POST /run/fortran`, `/run/cobol`, `/run/lisp`, `/run/java` succeed
- [ ] Carousel does not auto-advance
- [ ] agents.md 200

# Self-test

**Q1.** What does the browser send on Run?  
**A1.** Only an allowlisted language id.

**Q2.** Why carousel early high-level instead of three separate top-level rungs?  
**A2.** They share an abstraction band (formulas / lists / business data, late 1950s); years distinguish them.

**Q3.** Absolute machine program vs machine?  
**A3.** Absolute band = words people would enter (Hello via syscalls, or a sum job); `elf` is modern packaging only. Machine = decoded instructions / hand-entry hex sheet.
