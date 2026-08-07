# vaulted-agent v0.4.6 - handoff for agents on other hosts

Current release is **v0.4.6**. Upgrade on that host and treat the behavior changes below as real, not optional docs.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
# or pin:
VAULTED_AGENT_VERSION=v0.4.6 curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product / install: **https://vaultedagent.com/** (stephens.page/vaulted-agent 301s here)
- Repo: https://github.com/JacobStephens2/vaulted-agent-launcher
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.6

After install: `vaulted-agent version` should report 0.4.6; run `va doctor` and re-check sudoers if you use `service_user`.

## Changes since v0.4.2 (must-know)

### Doctor and token files (v0.4.5–v0.4.6)

1. **Unreadable ≠ missing** (#51/#52) - `op.env` / `bws.env` that exist but are EACCES (typical `root:service_user` 0640) no longer print as "missing" and no longer fall through to pasting a vault service-account token. Message names the effective user and hints when `service_user` is unset. Doctor reports `present` / `missing` / `unreadable`.

2. **Doctor only flags bad `op://` refs** (#53/#54) - plain literals (region, URL, phone) in a 1Password template are fine. Only values starting with `op://` that fail the scanner are errors.

3. **Doctor runs as `service_user`** (#44) - same hop as a launch; report says `checked as: …`.

### 1Password refresh (v0.4.4)

4. **`va refresh` output injects without hand-editing** (#48) - skips NOTES fields, falls back to item id when titles break `op`'s scanner, header comment has no sample `op://` that would abort inject. Re-run `va refresh --all --replace` if old refs were poison.

### Privilege hop and install (v0.4.3–v0.4.4)

5. **Sudoers-matchable hop** (#45) - re-exec is `sudo -u svc vaulted-agent …`, not via `env`. With `service_user` set, **`va run` is off** unless `allow_run = yes`. `VAULTED_AGENT_CONFIG_DIR` does not cross the hop.

6. **Conductor `-p`** (#46) - under `*-conductor`, `-p` is the agent's flag. Prompt auth: `VAULTED_AGENT_PROMPT_AUTH=1`. On `va …`, `-p` still forces prompt auth.

7. **`va kimi` defaults to `--auto`** (#47).

8. **Bare multi-line secrets** (#43) - PEMs / unquoted multi-line injects parse.

9. **Installer** (#50) - accepts hand-cut or CI asset member names; reinstall preserves operator `defaults.conf` keys (`service_user`, `allow_run`, …).

## Done when

- `vaulted-agent version` → 0.4.6
- `va doctor` - correct account; token files not falsely "missing"; literals not falsely bad refs
- Usual harnesses launch
- If delegated: sudoers matches the launcher binary; `va run` matches `allow_run`
