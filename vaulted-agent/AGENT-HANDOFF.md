# vaulted-agent — short handoff

**Full agent contract:** [AGENTS.md](./AGENTS.md) (also https://vaultedagent.com/AGENTS.md)

Current pin: **v0.4.15**

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
vaulted-agent version
va doctor
va secrets validate
```

Product: https://vaultedagent.com/ · Repo README: https://github.com/JacobStephens2/vaulted-agent-launcher#readme

v0.4.15 (#67): harness `alias = TARGET = SOURCE` copies an injected secret onto another name in that harness's child env only (fail closed if source missing).
