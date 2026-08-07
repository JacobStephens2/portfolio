# vaulted-agent v0.4.9 - handoff for agents on other hosts

Current release is **v0.4.9**. Upgrade on that host and treat the behavior changes below as real, not optional docs.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
# or pin:
VAULTED_AGENT_VERSION=v0.4.9 curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product / install: **https://vaultedagent.com/**
- Repo: https://github.com/JacobStephens2/vaulted-agent-launcher
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.9
- Migration notes: see MIGRATION.md in the repo (1Password variable renames)

After install: `vaulted-agent version` → 0.4.9; run `va doctor`.

## New in v0.4.9 (#60)

1Password `va refresh` naming and merge:

1. **Default section label “add more” no longer reaches variable names** - references still include the section for `op inject`; only the env var name is cleaned (`ANTHROPIC_CONDUCTOR_API_KEY` not `ANTHROPIC_ADD_MORE_CONDUCTOR_API_KEY`).
2. **Merge dedupe** - a curated `op://V/item/field` and a generated `op://V/item/add more/field` are one field; merge no longer appends a second name for the same secret.
3. **`va refresh --exclude PATTERN`** - skip variable names (`*` / `?`, case-insensitive); patterns persist as `# exclude:` in the manifest.
4. **Doctor** warns when a manifest still carries the old `*_ADD_MORE_*` form for a default-section field (see MIGRATION.md).

**If anything reads the old `*_ADD_MORE_*` names**, re-run refresh and update those consumers at the same time - nothing renames variables in place.

## Earlier must-know (v0.4.3–v0.4.8)

- Doctor probes workdir traversal (#58/#59); launch checks workdir before exec (#56)
- Setup asks who agents run as and where they start (#55)
- Unreadable token file ≠ missing (#51/#52)
- Doctor only flags malformed `op://` refs (#53/#54)
- Privilege hop, kimi `--auto`, bare multi-line secrets, installer fixes (#43–#50)

## Done when

- `vaulted-agent version` → 0.4.9
- After `va refresh`, no unwanted `*_ADD_MORE_*` names; no double-mapped secrets
- `doctor` clean (or only true warnings)
