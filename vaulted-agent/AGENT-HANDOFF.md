# vaulted-agent v0.4.11 - handoff for agents on other hosts

Current release is **v0.4.11**.

## Upgrade

```bash
curl -fsSL https://vaultedagent.com/install.sh | bash
```

- Product: **https://vaultedagent.com/**
- Release: https://github.com/JacobStephens2/vaulted-agent-launcher/releases/tag/v0.4.11

## New in v0.4.11 (#62)

`va -m MANIFEST harness` launches a harness against another refs file for one session:

```bash
va -m readonly.env.tpl claude
```

- Flag before the harness name
- Replaces configured manifest (no merge)
- Missing file fails before agent start
- Refused under `*-conductor` (fixed entitlement)
- Allowed with `va -m … pick`

## Add one credential (quick)

1. Create the secret in the vault (Bitwarden SM or 1Password).
2. Map it: `va refresh` (interactive merge) or append one line under `/etc/vaulted-agent/manifests/`
   - Bitwarden: `OPENAI_API_KEY=name:openai-api-key`
   - 1Password: `OPENAI_API_KEY=op://Vault/item/field`
3. Ensure the harness conf has `manifest = that-file`.

Rotating a value in the vault needs no command. Adding a mapping needs refresh or a hand-edited line.

## Done when

- `vaulted-agent version` → 0.4.11
- `va -m … harness` works on the direct `va` path
