# vaulted-agent v0.4.8 - handoff for agents on other hosts

Current release is **v0.4.8**. Upgrade on that host and treat the behavior changes below as real, not optional docs.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
# or pin:
VAULTED_AGENT_VERSION=v0.4.8 curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product / install: **https://vaultedagent.com/**
- Repo: https://github.com/JacobStephens2/vaulted-agent-launcher
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.8

After install: `vaulted-agent version` → 0.4.8; run `va doctor`.

## New in v0.4.8 (#58 / #59)

**`doctor` probes workdir traversal** instead of always warning on `workdir=caller` + `service_user`. After `setfacl -m u:<svc>:x` on operator homes, doctor stays quiet. It still warns (and names the path + setfacl) when a real probe path fails.

## Earlier must-know (v0.4.3–v0.4.7)

- **v0.4.7:** setup asks who agents run as and where they start; launch checks workdir before exec with clear error (#55/#56)
- Unreadable token file ≠ missing (#51/#52)
- Doctor only flags malformed `op://` refs, not plain literals (#53/#54)
- Doctor runs as `service_user` when set (#44)
- 1Password `refresh` injects without hand-editing (#48)
- Privilege hop sudoers-matchable; `VAULTED_AGENT_CONFIG_DIR` does not cross hop (#45)
- Conductor `-p` is agent flag; prompt auth via `VAULTED_AGENT_PROMPT_AUTH=1` (#46)
- `va kimi` defaults to `--auto` (#47)
- Bare multi-line secrets (#43)
- Installer asset-name + preserves operator defaults (#50)

## Done when

- `vaulted-agent version` → 0.4.8
- `va doctor` silent on caller+service_user when ACLs grant traverse; warns only on real failures
- Usual harnesses launch
