---
title: "From Machine Code to AI: the Same Hello World (agent version)"
audience: AI agents
canonical: https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/
date: 2026-08-01
license: MIT
---

# Directives

1. Treat this page as a **demonstration of abstraction layers**, not a remote shell.
2. When integrating similar demos, **never accept user-supplied source** for execution on a shared host. Allowlist language keys only.
3. Prefer **fixed program files + compile cache + short timeouts + rate limits + loopback bind**.
4. Be explicit about **ISA/platform**: this runner is Linux x86_64. Apple Silicon ARM64 Assembly is a different dialect.
5. **Binary** is the opaque ELF artifact; **machine** is decoded instructions. Do not collapse them.
6. The **AI** and **vibe** rungs are **deterministic stand-ins** unless a separately budgeted, logged model path is designed on purpose. Vibe = chat-as-process; AI engineering = tight prompt contract.
7. Syntax highlighting is client-side **highlight.js 11.11.1** (modular esm.sh). Degrade to plain text if CDN fails.

# Canonical human post

https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/

# Repo layout

```
blog/from-machine-code-to-ai-the-same-hello-world/
  index.html
  agents.md
  programs/          # allowlisted sources + vibe session + binary readme
  cache/             # build outputs (runtime, gitignored)
  server/
    app.py           # FastAPI runner
    requirements.txt
    deploy/
      hello-ladder.service
      apache-proxy.conf
```

# API contract

Base (public): `/blog/from-machine-code-to-ai-the-same-hello-world/api/`  
Upstream: `127.0.0.1:3521`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | tools + language list |
| GET | `/languages` | id, title, level, source text, highlight id |
| POST | `/run/{language}` | execute allowlisted program |

## Language ids (level order)

`binary`, `machine`, `assembly`, `c`, `cpp`, `rust`, `go`, `csharp`, `python`, `javascript`, `ai`, `vibe`

## Security invariants

- Request body is not used for source code.
- Subprocess argv is fixed per language in `LANGS`.
- Rate limit: 40 requests / IP / 60s (service defaults).
- Run timeout: 3s; build timeout: 60s.
- systemd: `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `MemoryMax=512M`, write only to `cache/`.

# Verified behavior (design targets)

- Every executable language prints `Hello, World!` (trailing newline from the language runtime is fine).
- `binary` returns stdout from ELF + note; source panel is `file` + `xxd` head.
- `machine` returns stdout plus `machineView` (`objdump` of `<main>`).
- `ai` returns stdout `Hello, World!\n` with note that no LLM was called.
- `vibe` runs `vibe-hello.py` and exposes the chat transcript as source.

# Operational checklist

- [ ] `programs/*` present and match the post copy
- [ ] venv at `/home/jacob/venvs/hello-ladder` with requirements installed
- [ ] `hello-ladder.service` enabled and active
- [ ] Apache `ProxyPass` for `/blog/from-machine-code-to-ai-the-same-hello-world/api/`
- [ ] `curl -sS https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/api/health` → 200
- [ ] `curl -sS -X POST .../api/run/binary` and `.../run/vibe` → Hello, World!
- [ ] Blog index lists the post
- [ ] `agents.md` served as markdown
- [ ] highlight.js loads or plain-text fallback works

# Self-test

**Q1.** Why is allowlisting by language id safer than posting source?  
**A1.** The attack surface collapses to a finite set of known binaries/scripts; user-controlled source is remote code execution.

**Q2.** How does the binary rung differ from the machine-code rung?  
**A2.** Binary presents the ELF file (xxd of the executable). Machine code presents decoded instructions in `main` via objdump.

**Q3.** How do AI engineering and vibe coding differ on this page?  
**A3.** AI engineering shows a precise prompt contract with a fixed expected line. Vibe coding shows a casual chat transcript whose frozen artifact (`vibe-hello.py`) is executed. Neither calls a live model on this host.
