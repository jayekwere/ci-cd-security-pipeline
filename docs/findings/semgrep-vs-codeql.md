# Semgrep vs CodeQL on identical code

Both engines, same codebase. The point isn't "which is better" — it's *when each wins*,
so you can run both deliberately instead of treating SAST as one undifferentiated step.

## The two analysis models

| | Semgrep | CodeQL |
|---|---------|--------|
| Model | Pattern / AST matching | Semantic data-flow (taint tracking) |
| Catches | Known-bad code shapes, secrets, config | Source-to-sink flows across functions |
| Speed | Fast | Slower (builds a queryable code database) |
| Custom rules | Easy, readable YAML-ish patterns | Powerful but steeper (QL language) |
| Best for | Custom org rules, fast PR feedback | Injection/flow classes pattern-matching misses |

## What each found that the other didn't

- **CodeQL caught a cross-function command injection (CWE-78)** that Semgrep's default
  rules missed, because the source and sink were several hops apart — a flow problem, not
  a shape problem. See [cwe-78-command-injection.md](cwe-78-command-injection.md).
- **Semgrep caught org-specific and config-shaped issues faster**, and let me author a
  custom rule for an internal pattern in minutes — something that's possible in CodeQL but
  far heavier to write.

## How to choose

Not either/or. The practical split:

- **Run Semgrep on every PR** for fast feedback and custom-rule enforcement.
- **Run CodeQL** (on push + scheduled) for the deeper flow analysis you don't want
  gating every PR on, but do want catching injection-class bugs before release.
- **Tune CodeQL query suites** by the precision-vs-coverage tradeoff: `security-extended`
  for higher-confidence findings, `security-and-quality` when you want maximum coverage
  and have the triage capacity.

## Takeaway

Pattern-matching answers *"does this code look dangerous?"* Data-flow answers
*"can untrusted data actually reach somewhere dangerous?"* Different questions — running
both, at the right pipeline stage, is how you cover both.
