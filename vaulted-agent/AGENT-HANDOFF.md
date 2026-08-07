# vaulted-agent v0.4.7 - handoff for agents on other hosts

Current release is **v0.4.7**. Upgrade on that host and treat the behavior changes below as real, not optional docs.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
# or pin:
VAULTED_AGENT_VERSION=v0.4.7 curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product / install: **https://vaultedagent.com/**
- Repo: https://github.com/JacobStephens2/vaulted-agent-launcher
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.7

After install: `vaulted-agent version` → 0.4.7; run `va doctor`.

## New in v0.4.7 (#55 / #56 / #57)

1. **`va setup` asks who agents run as** — you (default) vs dedicated `service_user` (writes defaults.conf). Warns that `va run` is off unless `allow_run = yes`.

2. **`va setup` asks where agents start** — `workdir = caller` (default) vs a fixed path (writes harness confs). Warns when service account + caller meet a 0700 home.

3. **Launch checks workdir before exec** — if the effective user cannot traverse the resolved directory, you get a clear error (account, path, `setfacl -m u:<svc>:x <dir>`), not a bare exec EACCES.

## Earlier must-know (v0.4.3–v0.4.6)

- Unreadable token file ≠ missing (#51/#52); doctor three-state; no paste fallback on EACCES
- Doctor only flags malformed `op://` refs, not plain literals (#53/#54)
- Doctor runs as `service_user` when set (#44)
- 1Password `refresh` output injects without hand-editing (#48)
- Privilege hop is sudoers-matchable; `VAULTED_AGENT_CONFIG_DIR` does not cross hop (#45)
- Conductor `-p` is agent flag; prompt auth via `VAULTED_AGENT_PROMPT_AUTH=1` (#46)
- `va kimi` defaults to `--auto` (#47)
- Bare multi-line secrets (#43)
- Installer accepts either asset member name; preserves operator defaults (#50)

## Done when

- `vaulted-agent version` → 0.4.7
- `va doctor` honest about account, token files, and op refs
- Usual harnesses launch; workdir errors name setfacl when relevant
- If delegated: sudoers matches launcher; `va run` matches `allow_run`
