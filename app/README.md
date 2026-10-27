# Intentionally unsafe scanner fixture

`vuln.py` contains a command-injection example and an argument-list counterpart. Use it only for isolated static analysis; do not deploy it.

The current dependency file contains a fully version-pinned, audited package closure. Earlier outdated-package findings remain historical writeups under `docs/findings/`.

Semgrep records two findings for the unsafe fixture. The main README explains its exact source-bound, expiring baseline. New or modified findings fail the gate. CodeQL separately uploads its data-flow analysis to code scanning; other scan evidence is retained as workflow artifacts.
