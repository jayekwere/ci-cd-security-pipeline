# CI/CD Security Pipeline — Secure Developer Workflow Tooling

A hardened GitHub Actions pipeline that runs **SAST, SCA, secrets scanning, and DAST**
on every push and pull request, with supply-chain hardening and a scan-gating policy
designed to keep signal meaningful instead of perpetually red.

Built to answer a practical question: *what does it actually take to wire the full
shift-left toolchain into CI so it catches real, exploitable issues — and not just
generate dashboard noise developers learn to ignore?*

---

## What this pipeline does

| Stage | Tool | What it catches |
|-------|------|-----------------|
| SAST (pattern) | [Semgrep](https://semgrep.dev) | Pattern-based code flaws, custom rules |
| SAST (semantic) | [CodeQL](https://codeql.github.com) | Data-flow / taint issues across functions (e.g. CWE-78) |
| SCA | [Snyk](https://snyk.io) | Direct **and** transitive dependency CVEs, by reachability |
| Secrets | [TruffleHog](https://github.com/trufflesecurity/trufflehog) | Committed credentials across **full git history**, verified live |
| DAST | [OWASP ZAP](https://www.zaproxy.org) | Runtime issues — headers, CORS, XSS — proven exploitable |
| Dep updates | [Dependabot](https://docs.github.com/code-security/dependabot) | Automated dependency + Actions-pin remediation |

Workflows live in [`.github/workflows/`](.github/workflows/).

---

## Design principles

**1. Least-privilege by default.**
Every workflow declares `permissions:` explicitly and scopes the `GITHUB_TOKEN` to the
minimum each job needs (`contents: read`, `security-events: write` only where SARIF is
uploaded). No workflow inherits the default broad token.

**2. Supply-chain hardening via SHA-pinning.**
Third-party actions are pinned to immutable commit SHAs, not mutable tags — mitigating
the tag-hijack attack class (e.g. the `tj-actions/changed-files` compromise, where a
mutable `v` tag was repointed at malicious code). Pins are managed, not hand-typed:
[`scripts/pin-actions.sh`](scripts/pin-actions.sh) resolves each action's release tag to
its **source-verified** SHA, and Dependabot keeps them fresh. See
[Supply-chain hardening](#supply-chain-hardening) below.

**3. Gate on what's actionable, report on what isn't.**
A pipeline that fails on every pre-existing finding gets disabled within a week. The
gating policy blocks on **new-code SAST findings** and runs **report-only** for
known-deferred dependencies — so a failed build means *you introduced something*, which
keeps the gate trusted. See [`docs/gating-policy.md`](docs/gating-policy.md).

**4. AI-suggested fixes are reviewed, not auto-applied.**
Copilot Autofix suggestions are evaluated on correctness before merge. Automated
*detection* with human-reviewed *remediation* — the same principle applied to Dependabot
PRs, which are triaged by breaking-change risk rather than auto-merged.

---

## Findings & writeups

Concrete results from running this against real codebases. Each is a short, honest
writeup — methodology, what was found, and what it taught about the tool's limits.

- **[CWE-78 command injection — data-flow trace](docs/findings/cwe-78-command-injection.md)**
  CodeQL traced untrusted input from source to a dangerous sink across multiple
  functions. Pattern-based scanning missed it. A worked example of why semantic
  analysis earns its slower runtime.

- **[Semgrep vs CodeQL on identical code](docs/findings/semgrep-vs-codeql.md)**
  Same codebase, both engines. Where pattern-matching wins (speed, custom rules) and
  where taint-tracking wins (cross-function flows), and how to choose query suites by
  precision-vs-coverage.

- **[Transitive CVEs the local scan hid](docs/findings/sca-transitive-cves.md)**
  SCA on a clean CI runner surfaced 11 dependency CVEs (8 transitive) that local
  scanning masked due to environment drift — and why transitive fixes mean
  *pin-with-compatibility-test*, not a blind upgrade.

---

## Supply-chain hardening

Actions in this repo are tag-pinned in source for readability. To convert them to
verified SHA pins (the production posture):

```bash
# Resolves every `uses: org/action@tag` to org/action@<sha>  # tag
# using the action's published release commit, verified against the source repo.
./scripts/pin-actions.sh .github/workflows/security.yml
```

The script intentionally fails loudly if a tag cannot be resolved to a source-verified
SHA — the lesson from debugging a failed pin: **SHA-pinning is only as good as the hash
you verified against the source.** A pin to the wrong SHA is worse than a tag, because
it looks safe.

Dependabot (`.github/dependabot.yml`) then keeps both dependencies and Action pins
current, opening PRs that are triaged — not auto-merged — by breaking-change risk.

---

## Run it yourself

1. **Fork / clone** this repo.
2. **Add secrets** (Settings → Secrets and variables → Actions):
   - `SNYK_TOKEN` — for the SCA job ([free token](https://app.snyk.io/account)).
   - Semgrep and TruffleHog run without secrets on public repos.
3. **Push or open a PR.** All workflows run automatically; results land in the
   **Security → Code scanning** tab as SARIF.
4. **(Optional) DAST:** [`dast-zap.yml`](.github/workflows/dast-zap.yml) needs a running
   target URL — point it at a deployed staging instance or a local container.

---

## What I'd build next

- **API-aware DAST.** ZAP's traditional spider misses dynamically-loaded SPA endpoints;
  the next iteration imports an OpenAPI spec and runs authenticated active scans so
  coverage matches the real attack surface.
- **Reachability-gated SCA.** Move from "is this CVE present" to "is the vulnerable
  function actually called," to cut transitive-dependency noise further.
- **Policy-as-code gating.** Express the gate rules (block vs report-only) as a
  versioned policy file rather than per-job conditionals.

---

*Author: Jonathan (Jay) Ekwere · [github.com/jayekwere](https://github.com/jayekwere)*
