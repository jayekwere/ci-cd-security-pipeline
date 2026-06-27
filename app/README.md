# Sample target app (intentionally vulnerable)

This directory is a **deliberately insecure** test fixture so the pipeline's scanners
have real code to analyze. It is not production code and must not be deployed.

| File | What it's for |
|------|----------------|
| `vuln.py` | A real CWE-78 command injection (cross-function source→sink) for CodeQL/Semgrep to catch, plus a safe counterpart. |
| `requirements.txt` | Outdated pins (`flask`, `requests`) that pull known-vulnerable dependencies, including transitive ones, for Snyk SCA to flag. |

The findings these produce are written up in [`../docs/findings/`](../docs/findings/).
After a pipeline run, the alerts appear under the repo's **Security → Code scanning** tab.
