# Scan-gating policy

The `security` workflow requires completed SAST, dependency and verified-secret scans. The final `gate` runs with `if: always()` and accepts only successful blocking jobs. No scanner failure, absent report, skip or cancellation counts as a clean scan.

Semgrep retains the default and security-audit packs and adds local regression rules. Every finding blocks unless its rule, path, line range and entire source-file hash match the checked baseline. The intentionally non-deployable command-injection fixture has two recorded findings, reviewed on 2026-10-27 and expiring on 2026-11-26. The review window is at most 30 days. Stale, future-dated, expired, duplicate and unused entries fail. Any change to the fixture or its callers invalidates that whole-file exception.

Application dependencies are fully version-pinned and audited without an ignore list. Verified secrets block. CodeQL remains report-only and requires manual review. ZAP is manual against an authorized target, with issue writing disabled. These are workflow checks; no release gate or protected-branch configuration is claimed.

The regression suite checks clean input, new findings, exact baseline matching, source changes, expiry, scanner errors, missing report structure, traversal and unused entries. The workflow also scans new unsafe code and requires gate exit 1, then omits a report and requires exit 2. Tests do not call a scanner timeout a policy rejection.
