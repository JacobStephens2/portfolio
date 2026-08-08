# vaulted-agent — short handoff

**Full agent contract:** [AGENTS.md](./AGENTS.md) (also https://vaultedagent.com/AGENTS.md)

Current pin: **v0.4.13**

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
vaulted-agent version
va doctor
va secrets validate
```

Product: https://vaultedagent.com/ · Repo README: https://github.com/JacobStephens2/vaulted-agent-launcher#readme

v0.4.13 (#64): `va secrets validate` resolves every ref against the vault (same path as a launch). Fails closed without a manager token. `--offline` keeps shape-only. Doctor stays offline by design.
