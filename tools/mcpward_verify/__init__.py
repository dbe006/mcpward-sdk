"""mcpward audit log verifier — verify Ed25519 signatures of audit records.

Stand-alone CLI. Install with:

    pipx install mcpward-verify

Usage:

    mcpward-verify --pubkey ed25519.pub --record record.json
    mcpward-verify --pubkey ed25519.pub --batch records.jsonl
    cat records.jsonl | mcpward-verify --pubkey ed25519.pub --stdin
    mcpward-verify --pubkey ed25519.pub --batch records.jsonl --format json

Exit codes:
    0 — all records valid
    1 — one or more records have invalid signatures
    2 — usage error
"""

from __future__ import annotations

__version__ = "0.1.0"

import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_public_key


def verify_record(record: dict, public_key) -> bool:
    """Verify Ed25519 signature of a single audit record."""
    sig_str = record.get("signature", "")
    if not sig_str.startswith("ed25519:"):
        return False

    try:
        signature = base64.b64decode(sig_str.removeprefix("ed25519:"))
    except Exception:
        return False

    payload = {k: v for k, v in record.items() if k != "signature"}
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    try:
        public_key.verify(signature, message)
        return True
    except Exception:
        return False


def load_public_key(path: Path):
    """Load Ed25519 public key from PEM file."""
    if not path.exists():
        print(f"Error: public key file not found: {path}", file=sys.stderr)
        sys.exit(2)
    return load_pem_public_key(path.read_bytes())


def format_result_text(results: list[dict]) -> str:
    lines = []
    for r in results:
        status = "  OK " if r["valid"] else " FAIL"
        lines.append(f"{status} {r['id']}")
    valid = sum(1 for r in results if r["valid"])
    invalid = len(results) - valid
    lines.append(f"\n{valid} valid, {invalid} invalid out of {len(results)} records.")
    return "\n".join(lines)


def format_result_json(results: list[dict]) -> str:
    valid = sum(1 for r in results if r["valid"])
    invalid = len(results) - valid
    output = {
        "total": len(results),
        "valid": valid,
        "invalid": invalid,
        "all_valid": invalid == 0,
        "records": results,
    }
    return json.dumps(output, indent=2)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="mcpward-verify",
        description="Verify Ed25519 signatures of mcpward audit log records.",
    )
    parser.add_argument(
        "--pubkey", required=True, type=Path, help="Path to Ed25519 public key (PEM)"
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument(
        "--version", action="version", version=f"mcpward-verify {__version__}"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", type=Path, help="Single JSON record file")
    group.add_argument("--batch", type=Path, help="JSONL file with one record per line")
    group.add_argument("--stdin", action="store_true", help="Read records from stdin (JSONL)")
    args = parser.parse_args()

    public_key = load_public_key(args.pubkey)

    records: list[dict] = []
    if args.record:
        if not args.record.exists():
            print(f"Error: file not found: {args.record}", file=sys.stderr)
            sys.exit(2)
        records.append(json.loads(args.record.read_text()))
    elif args.batch:
        if not args.batch.exists():
            print(f"Error: file not found: {args.batch}", file=sys.stderr)
            sys.exit(2)
        for line in args.batch.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    elif args.stdin:
        for line in sys.stdin:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        print("No records to verify.", file=sys.stderr)
        sys.exit(2)

    results: list[dict] = []
    for i, record in enumerate(records):
        record_id = record.get("id", f"record_{i}")
        valid = verify_record(record, public_key)
        results.append({"id": record_id, "valid": valid})

    if args.format == "json":
        print(format_result_json(results))
    else:
        print(format_result_text(results))

    has_invalid = any(not r["valid"] for r in results)
    sys.exit(1 if has_invalid else 0)


if __name__ == "__main__":
    main()
