# The transitive CVEs the local scan hid

**Tool:** Snyk (SCA) · **Finding:** 11 dependency CVEs (8 transitive) · **Root cause:** environment drift

## What happened

Running SCA on a **clean CI runner** surfaced 11 dependency CVEs that a local scan on my
own machine had not. Eight of them were **transitive** — pulled in by dependencies of my
dependencies, not anything in the direct requirements.

The gap was **environment drift**: my local environment had a different, partially-newer
set of resolved package versions than a fresh install from the lockfile produced on the
runner. The local scan was, in effect, scanning a different dependency tree than the one
that would actually ship.

## Why the clean runner is the source of truth

A CI runner installs from scratch, from the committed manifest/lockfile, every time. That
is the dependency tree that gets built and deployed — so it's the one worth scanning.
Local environments accumulate drift (manual upgrades, leftover versions, cached wheels)
and quietly hide or mask real exposure. **Scan where you build, not where you code.**

## Direct vs transitive remediation

These are not the same fix:

- **Direct dependency CVE** → upgrade the package you declared. Straightforward.
- **Transitive CVE** → you don't control that version directly. The fix is a
  **version pin / override with a compatibility test** (e.g. pinning `urllib3` pulled in
  via `requests`), *not* a blind bump — bumping the parent may not move the transitive
  dependency, and forcing the transitive version can break the parent. Pin, then test.

## Prioritization

Triaged by **reachability and exploitability**, not raw CVSS:

- Is the vulnerable function actually reachable from our code paths?
- Is there a known exploit / is it in CISA KEV?
- Only then, the CVSS base score.

This keeps remediation effort on genuinely exploitable exposure instead of chasing every
high-CVSS finding that the code never actually calls.

## Takeaway

- **Run SCA on a clean runner** — local results lie when the environment has drifted.
- **Transitive ≠ direct.** Pin-with-compatibility-test, don't blind-upgrade.
- **Reachability over raw severity** for what to fix first.
