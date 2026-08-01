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
5. The AI rung is a **deterministic stand-in** unless a separately budgeted, logged model path is designed on purpose.

# Canonical human post

https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/

# Repo layout

```
blog/from-machine-code-to-ai-the-same-hello-world/
  index.html
  agents.md
  programs/          # allowlisted sources
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
| GET | `/languages` | id, title, level, source text |
| POST | `/run/{language}` | execute allowlisted program |

## Language ids (level order)

`machine`, `assembly`, `c`, `cpp`, `rust`, `go`, `csharp`, `python`, `javascript`, `ai`

## Security invariants

- Request body is not used for source code.
- Subprocess argv is fixed per language in `LANGS`.
- Rate limit: 40 requests / IP / 60s (service defaults).
- Run timeout: 3s; build timeout: 60s.
- systemd: `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `MemoryMax=512M`, write only to `cache/`.

# Verified behavior (design targets)

- Every non-AI language prints `Hello, World!` (trailing newline from the language runtime is fine).
- `machine` returns `stdout` plus `machineView` (`objdump` of `<main>`).
- `ai` returns stdout `Hello, World!\n` with `note` explaining no LLM was called.

# Operational checklist

- [ ] `programs/*` present and match the post copy
- [ ] venv at `/home/jacob/venvs/hello-ladder` with requirements installed
- [ ] `hello-ladder.service` enabled and active
- [ ] Apache `ProxyPass` for `/blog/from-machine-code-to-ai-the-same-hello-world/api/`
- [ ] `curl -sS https://stephens.page/blog/from-machine-code-to-ai-the-same-hello-world/api/health` → 200
- [ ] `curl -sS -X POST .../api/run/python` → Hello, World!
- [ ] Blog index lists the post
- [ ] `agents.md` served as markdown

# Self-test

**Q1.** Why is allowlisting by language id safer than posting source?  
**A1.** The attack surface collapses to a finite set of known binaries/scripts; user-controlled source is remote code execution.

**Q2.** Why is the Assembly on this page not the same as an Apple Silicon teach lab?  
**A2.** Different ISA and OS ABI (x86_64 Linux vs ARM64 Darwin).

**Q3.** What does the AI rung prove if it does not call a model?  
**A3.** That the *interface* can be natural language while the *execution path* remains a lower layer; calling a model is optional product cost, not required for the ladder metaphor.
