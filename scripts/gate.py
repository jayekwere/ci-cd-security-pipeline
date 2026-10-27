"""Reject findings outside a reviewed, source-bound demonstration baseline."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sys


def findings(report, root):
    if not isinstance(report, dict) or not isinstance(report.get("results"), list):
        raise ValueError("missing Semgrep results")
    if report.get("errors"):
        raise ValueError("scanner reported errors")
    result = set()
    for item in report["results"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("finding path must stay inside the repository")
        raw = (root / relative).read_bytes()
        # Bind the entire fixture, including its callers, not just the sink line.
        key = (item["check_id"], relative.as_posix(),
               hashlib.sha256(raw).hexdigest(), item["start"]["line"], item["end"]["line"])
        result.add(key)
    return result


def assess(report, baseline, root, today=None):
    today = today or date.today()
    actual = findings(report, root)
    if baseline.get("schemaVersion") != 1 or not isinstance(baseline.get("findings"), list):
        raise ValueError("invalid baseline")
    accepted = set()
    for entry in baseline["findings"]:
        expiry = date.fromisoformat(entry["expires"])
        reviewed = date.fromisoformat(entry["reviewed"])
        if not reviewed <= today <= expiry or not 0 <= (expiry - reviewed).days <= 30:
            raise ValueError("baseline review missing, expired or longer than 30 days")
        if not entry.get("reason", "").strip():
            raise ValueError("baseline needs a reason")
        key = (entry["rule"], entry["path"], entry["fileSHA256"], entry["startLine"], entry["endLine"])
        if key in accepted:
            raise ValueError("duplicate baseline finding")
        accepted.add(key)
    if accepted - actual:
        raise ValueError("baseline no longer matches scanned source; review it")
    return actual - accepted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--require-target")
    args = parser.parse_args()
    try:
        report = json.loads(Path(args.report).read_text())
        if args.require_target and args.require_target not in report.get("paths", {}).get("scanned", []):
            raise ValueError("required source file was not scanned")
        denied = assess(report,
                        json.loads(Path(args.baseline).read_text()), Path(args.root))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if denied:
        for rule, path, _, first, _ in sorted(denied):
            print(f"DENY {rule} {path}:{first}")
        return 1
    print("PASS scan completed; no unreviewed findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
