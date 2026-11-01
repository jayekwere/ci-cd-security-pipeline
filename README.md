# CI/CD Security Pipeline

A working example of scan gates, with an intentionally unsafe application fixture and tests proving that new findings and missing scan evidence fail the workflow. The fixture is for isolated analysis only and must not be deployed.

## What blocks a change

The [security workflow](.github/workflows/security.yml) runs on main pushes, pull requests and manual dispatch. No scan is skipped for dependency-update pull requests, and the blocking jobs need no repository secrets.

- Semgrep 1.182.1 runs the original `p/default` and `p/security-audit` packs plus two local regression rules. A strict scan must succeed, report no scanner errors and include the expected application source.
- [The gate](scripts/gate.py) rejects every finding outside the exact reviewed demonstration baseline. Each baseline entry binds rule, path, line range and the SHA-256 of the **entire source file**, including callers. Reviews last at most 30 days. Expired, stale, duplicate and unused entries fail as errors.
- The existing command-injection fixture produces two findings across the configured rules. Its [baseline](policy/sast-baseline.json) expires on **2026-11-26**. This scoped teaching fixture is the only SAST exception; it is not an acceptable application vulnerability.
- pip-audit 2.10.1 blocks reported vulnerabilities in the fully version-pinned application dependency closure. The old outdated dependency example was replaced with supported packages; earlier scan writeups remain historical.
- TruffleHog scans the event's commit range and fails on verified credentials. Its action source and scanner image are both pinned. Scanner errors fail their job. The final `gate` runs even after failure and requires all blocking jobs to have succeeded, so failed, skipped or cancelled scanners cannot become a green gate.

Action references use full commit SHAs. The default permission is `contents: read`; only the separate CodeQL analysis job can upload code-scanning results. Scan evidence is retained for 14 days, including failed runs.

## Passing and failing checks

Local checks on October 27, 2026:

| Check | Observed result |
| --- | --- |
| Gate regression suite | 15 tests passed |
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

[CodeQL](.github/workflows/codeql.yml) runs on pushes, pull requests and a weekly schedule. It uploads data-flow findings and remains report-only; this repository does not claim a CodeQL-based release gate. [ZAP](.github/workflows/dast-zap.yml) is manually dispatched against the disposable runner-local `app/server.py` target. There is no external target input. It runs a passive baseline and then an active scan if the baseline succeeds. Issue creation is disabled and neither job has issue-write permission. A web alert requires validation before claiming exploitability.

The [command-injection trace](docs/findings/cwe-78-command-injection.md), [tool comparison](docs/findings/semgrep-vs-codeql.md) and [dependency findings](docs/findings/sca-transitive-cves.md) document earlier runs. See [the gating policy](docs/gating-policy.md) for the current exception and failure behavior.

## Limits

Registry rule packs and vulnerability feeds can change; version-pinned scanners do not make those remote inputs immutable. A new rule can deliberately require baseline review. CI tool requirements pin direct scanner versions; their transitive installation is not a fully hashed lock. Action SHAs pin action source, not every binary or service used inside an action; the TruffleHog image is separately digest-pinned. Verified-only secret scanning can miss unverified or unsupported credentials, and event-range scans are not a full repository-history audit. Baseline and workflow edits require review by a trusted maintainer; repository writers can change these controls. Branch protection and a complete release/deployment system are not implemented here.

The first hosted security run caught a scanner invocation error: the action already supplies `--fail`, so passing it again was rejected. The final gate correctly failed when that scanner failed. The duplicate flag was removed and the scanner image was pinned to the digest observed in that run; a subsequent hosted result is recorded separately.

## Hosted verification

[Security run #40526501980](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/40526501980) passed all three jobs for implementation commit `7d9a5fa`: **8 gate tests**, **293 Semgrep rules with 2 exact baseline findings and 0 scanner errors**, **12 audited packages with 0 reported vulnerabilities**, and **0 verified credentials in the pushed commit range**. The unsafe-code and missing-report controls returned exits **1** and **2**, and the final gate required both scanner jobs to succeed. [CodeQL run #40526501959](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/40526501959) also passed its analysis job. Downloaded artifact hashes and scan scope are in [the exact record](docs/hosted-verification.json).

## Delivery evidence and trust boundaries

The safe application is `app/server.py`; the unsafe historical fixture is never packaged. Run `python3 scripts/delivery.py build` to create a deterministic ZIP, CycloneDX inventory and SHA-256 manifest in `artifacts/build`. Run `python3 scripts/delivery.py verify artifacts/build` to reject absent or modified evidence. The application uses only Python's standard library; the SBOM lists the application and does not claim to inventory the runner or Python distribution.

| Required job | Acceptance | Failure / unavailable |
| --- | --- | --- |
| scans | Strict Semgrep report, exact baseline, dependency audit, regression demonstrations | Any failed command blocks |
| secrets | Pinned TruffleHog verified-credential scan | Scanner failure blocks; unverified secrets remain a limitation |
| build | Compile safe source, reproducible ZIP, SBOM, verified digest manifest, successful upload | Missing or corrupt evidence blocks |
| gate | Exact required job set, every result success | Missing, skipped, cancelled or failed job blocks |

CodeQL and manual local ZAP are supplemental diagnostics, not release acceptance checks. No meaningful deployment IaC exists, so no IaC scanner is claimed. Artifact digests detect corruption but are not signed provenance. Releases require a verified exact commit, all required jobs successful, reviewed policy changes and verified artifacts. This repository does not yet automate signed release attestations.

The threat model includes malicious application changes, scanner failures, stale exceptions and missing artifacts. It assumes trusted GitHub runners, scanner publishers and maintainers. A writer who can modify workflow and gate code can bypass repository-local policy. On October 31, 2026, the GitHub API reported main as **not protected**. Configure required `gate` checks, strict branch updates, independent approving review, dismissal of stale reviews, restricted bypass and CODEOWNERS review before relying on this pipeline for production. These settings are requirements, not configured-control claims.

The original November 26, 2026 exception remains unchanged. Exact rule, path, line range and entire-file digest must match; a nonempty review reason and a review window of at most 30 days are mandatory. Expired, future, duplicate and unused exceptions fail. Baseline changes require an independent source review; never extend the date merely to make CI green.

Maintenance: review Dependabot updates, monitor scanner feeds, refresh evidence after policy changes, and review the fixture before its exception expires. Add `/app` to dependency update coverage when changing its lock. Historical findings under `docs/findings` describe earlier deliberately unsafe source and dependency versions, not current vulnerability counts.

An offline tracked-file token-shape check additionally blocks AWS access-key IDs and GitHub classic token shapes, including nonfunctional synthetic credentials. Tests construct synthetic values in memory. Unsupported credential formats remain outside this check. CI validates workflow syntax with actionlint 1.7.7.

## Current hosted verification — October 31, 2026

[Security run 41241785440](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/41241785440) passed all four required jobs on `3918ffe`: 15 tests, workflow validation, strict SAST, safe dependency audit, vulnerable dependency rejection, synthetic token checks and build evidence. [CodeQL](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/41241785449) passed. [Local-target ZAP](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/41241594676) passed passive and active jobs on the earlier implementation commit; the only subsequent DAST change renamed an unused readiness-loop variable.

Actual downloaded negative-gate and dependency reports are in [docs/examples](docs/examples). [The evidence record](docs/verification-2026-10-31.json) contains hashes of downloaded reports and build artifacts. These are generated outputs, not illustrative screenshots. The build manifest was verified again after download. [Run 41241665105](https://github.com/jayekwere/ci-cd-security-pipeline/actions/runs/41241665105) also demonstrates an actual validation failure propagating to a failed final gate; the corrected workflow passed.

## Protected delivery and signed provenance

The `independent-gate` job obtains the regression tests from the PR base commit, rather than trusting candidate tests. It runs those tests against candidate gate code without secrets or write permissions. This catches weakening the gate while editing its tests in the same PR. It is a regression boundary, not a proof against arbitrary malicious Python. Changes to the workflow itself require independent protected-branch review.

The main-only [provenance workflow](.github/workflows/provenance.yml) requires successful push security checks for the exact source commit, rebuilds the safe application, signs every delivery file using GitHub OIDC artifact attestations, verifies signer workflow and source digest, and demonstrates that a tampered ZIP fails verification. No signing credentials are stored. Signing permissions exist only in this job; pull request builds never receive them. This provides signed build provenance, not a SLSA Level 3 claim.

Verify a downloaded artifact with:

```sh
gh attestation verify application.zip --repo jayekwere/ci-cd-security-pipeline \
  --signer-workflow jayekwere/ci-cd-security-pipeline/.github/workflows/provenance.yml \
  --source-digest RELEASE_COMMIT_SHA
```

The protection rollout requires strict `gate` and `independent-gate` checks from GitHub Actions, one approving review, stale-review dismissal, approval of the latest push, resolved conversations, administrator enforcement, and disabled force pushes/deletions. With only one collaborator, subsequent merges require adding an authorized independent reviewer. Repository administrators retain the ability to edit protection settings; this is an unavoidable administrative trust boundary. Verify live settings through the GitHub API rather than treating this document as evidence of configuration.

---

**AI assistance:** AI tools helped with code or documentation.
