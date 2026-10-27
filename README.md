# CI/CD Security Pipeline

A working example of scan gates, with an intentionally unsafe application fixture and tests proving that new findings and missing scan evidence fail the workflow. The fixture is for isolated analysis only and must not be deployed.

## What blocks a change

The [security workflow](.github/workflows/security.yml) runs on main pushes, pull requests and manual dispatch. No scan is skipped for dependency-update pull requests, and the blocking jobs need no repository secrets.

- Semgrep 1.182.1 runs the original `p/default` and `p/security-audit` packs plus two local regression rules. A strict scan must succeed, report no scanner errors and include the expected application source.
- [The gate](scripts/gate.py) rejects every finding outside the exact reviewed demonstration baseline. Each baseline entry binds rule, path, line range and the SHA-256 of the **entire source file**, including callers. Reviews last at most 30 days. Expired, stale, duplicate and unused entries fail as errors.
- The existing command-injection fixture produces two findings across the configured rules. Its [baseline](policy/sast-baseline.json) expires on **2026-11-26**. This scoped teaching fixture is the only SAST exception; it is not an acceptable application vulnerability.
- pip-audit 2.10.1 blocks reported vulnerabilities in the fully version-pinned application dependency closure. The old outdated dependency example was replaced with supported packages; earlier scan writeups remain historical.
- TruffleHog scans the event's commit range and fails on verified credentials. Its action source and scanner image are both pinned. Scanner errors fail their job. The final `gate` runs even after failure and requires both blocking jobs to have succeeded, so failed, skipped or cancelled scanners cannot become a green gate.

Action references use full commit SHAs. The default permission is `contents: read`; only the separate CodeQL analysis job can upload code-scanning results. Scan evidence is retained for 14 days, including failed runs.

## Passing and failing checks

Local checks on October 27, 2026:

| Check | Observed result |
| --- | --- |
| Gate regression suite | 8 tests passed |
| Semgrep against the actual app | 293 rules, 3 scanned files, 2 expected fixture findings; source-bound baseline passed |
| New `eval(input())` fixture | Scanner found it; gate exited 1 |
| Missing scanner report | Gate exited 2 |
| Locked application dependency audit | 12 packages, no known vulnerabilities reported |
| Workflow syntax and action references | actionlint passed; all action references use commit SHAs |

Exit codes: `0` accepted, `1` unreviewed finding, `2` missing, invalid or stale evidence. A clean scan and an execution error are different outcomes. CI repeats the gate tests and actual scans, rather than relying on this table.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-ci.txt
python -m unittest discover -v
mkdir -p artifacts
semgrep scan --config p/default --config p/security-audit --config policy/semgrep.yml \
  --strict --metrics=off --disable-version-check --json --output artifacts/semgrep.json app
python scripts/gate.py --report artifacts/semgrep.json --baseline policy/sast-baseline.json \
  --require-target app/vuln.py
bash scripts/check-negative-gate.sh
pip-audit --requirement app/requirements.txt --no-deps --disable-pip --format json
```

## Other analysis

[CodeQL](.github/workflows/codeql.yml) runs on pushes, pull requests and a weekly schedule. It uploads data-flow findings and remains report-only; this repository does not claim a CodeQL-based release gate. [ZAP](.github/workflows/dast-zap.yml) is manually dispatched against an explicitly supplied, authorized test target. It runs a passive baseline and then an active scan if the baseline succeeds. Issue creation is disabled and neither job has issue-write permission. A web alert requires validation before claiming exploitability.

The [command-injection trace](docs/findings/cwe-78-command-injection.md), [tool comparison](docs/findings/semgrep-vs-codeql.md) and [dependency findings](docs/findings/sca-transitive-cves.md) document earlier runs. See [the gating policy](docs/gating-policy.md) for the current exception and failure behavior.

## Limits

Registry rule packs and vulnerability feeds can change; version-pinned scanners do not make those remote inputs immutable. A new rule can deliberately require baseline review. CI tool requirements pin direct scanner versions; their transitive installation is not a fully hashed lock. Action SHAs pin action source, not every binary or service used inside an action; the TruffleHog image is separately digest-pinned. Verified-only secret scanning can miss unverified or unsupported credentials, and event-range scans are not a full repository-history audit. Baseline and workflow edits require review by a trusted maintainer; repository writers can change these controls. Branch protection and a complete release/deployment system are not implemented here.

The first hosted security run caught a scanner invocation error: the action already supplies `--fail`, so passing it again was rejected. The final gate correctly failed when that scanner failed. The duplicate flag was removed and the scanner image was pinned to the digest observed in that run; a subsequent hosted result is recorded separately.

## Hosted verification

[Security run #40526501980](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/40526501980) passed all three jobs for implementation commit `7d9a5fa`: **8 gate tests**, **293 Semgrep rules with 2 exact baseline findings and 0 scanner errors**, **12 audited packages with 0 reported vulnerabilities**, and **0 verified credentials in the pushed commit range**. The unsafe-code and missing-report controls returned exits **1** and **2**, and the final gate required both scanner jobs to succeed. [CodeQL run #40526501959](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/40526501959) also passed its analysis job. Downloaded artifact hashes and scan scope are in [the exact record](docs/hosted-verification.json).
