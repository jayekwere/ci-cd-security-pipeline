# Scan-gating policy

A security gate that fails on every pre-existing finding gets disabled within a week.
The goal is a gate developers *trust* — where a red build means "you introduced
something," not "the repo has a backlog."

## The policy

| Stage | Mode | Rationale |
|-------|------|-----------|
| SAST (Semgrep) | **Block on new-code findings** | New issues are cheap to fix at PR time; this is where shift-left pays off |
| SAST (CodeQL) | Report to code scanning; review before release | Deeper flow analysis; don't gate every PR on it, but don't let it ship |
| SCA (Snyk) | **Report-only** for known-deferred deps | Transitive CVEs often need pin-with-test or upstream fixes — blocking would stall delivery on issues the team can't immediately fix |
| Secrets (TruffleHog) | **Block on verified secrets** | A live, verified credential in history is always actionable and always serious |

## Why "block on new, report on old"

The distinction that makes the gate sustainable:

- **New-code findings** are introduced by the PR under review. The author has full
  context and the fix is cheapest now. Blocking here is fair and effective.
- **Pre-existing / known-deferred findings** (especially transitive deps awaiting an
  upstream fix) are tracked and reported, not used to block unrelated PRs. Otherwise the
  gate punishes every developer for a backlog they didn't create — and gets turned off.

## Verified-only secrets

TruffleHog runs with `--only-verified`: it attempts to authenticate found credentials and
reports only the live ones. This cuts the false-positive noise (expired keys, example
values) that makes secret scanners get ignored — so when it fails the build, it means a
real, working credential is exposed.
