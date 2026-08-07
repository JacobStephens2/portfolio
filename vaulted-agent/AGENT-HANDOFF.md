# vaulted-agent v0.4.10 - handoff for agents on other hosts

Current release is **v0.4.10**.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
# or pin:
VAULTED_AGENT_VERSION=v0.4.10 curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product: **https://vaultedagent.com/**
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.10

## New in v0.4.10 (#61)

Doctor legacy-name warning for 1Password `*_ADD_MORE_*` variables:

- Counts as a real warning in the summary (no more `0 warning(s)` under a printed WARN)
- Samples the first few names plus “and N more” instead of dumping every name
- Once per shared manifest, not once per harness pointing at it

## Earlier (v0.4.9 #60)

1Password refresh: drop default “add more” from env names, merge dedupe, `--exclude`. Re-run `va refresh` if you still have old names; see MIGRATION.md.

## Done when

- `vaulted-agent version` → 0.4.10
- `va doctor` summary matches printed warnings; legacy-name lines stay short
