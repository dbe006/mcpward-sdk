# mcpward-verify

Stand-alone CLI to verify Ed25519-signed audit log records produced by the [mcpward](https://mcpward.redfleet.fr) gateway.

Lets you (or any third party) verify that an audit record has not been altered, without contacting the gateway operator.

## Install

```bash
pipx install mcpward-verify
```

(Or `pip install mcpward-verify` if you prefer.)

## Usage

```bash
# Single record
mcpward-verify --pubkey ed25519.pub --record record.json

# Batch (JSONL, one record per line)
mcpward-verify --pubkey ed25519.pub --batch records.jsonl

# From stdin
cat records.jsonl | mcpward-verify --pubkey ed25519.pub --stdin

# JSON output (for scripting)
mcpward-verify --pubkey ed25519.pub --batch records.jsonl --format json
```

## Public key

The hosted gateway publishes its Ed25519 public key at:

    https://mcpward.redfleet.fr/v1/pubkey

Download once, then verify any number of audit records offline.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All records valid |
| 1 | One or more records have invalid signatures |
| 2 | Usage error (missing file, bad arguments) |

## Record format

See [`../schemas/audit_log_v1.json`](../schemas/audit_log_v1.json) for the JSON Schema describing the record format.

## License

MIT
