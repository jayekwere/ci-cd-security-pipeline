# CI/CD Security Pipeline

Example workflows for code analysis, dependency scanning, secret scanning and web-application scanning. The repository includes an intentionally vulnerable demonstration app and writeups showing how the tools report its findings. Use an isolated test environment for that app.

## Current workflow behavior

| Workflow | When it runs | What it does |
| --- | --- | --- |
| [Security](.github/workflows/security.yml) | Pushes and pull requests targeting main | Runs Semgrep, Snyk and TruffleHog; uploads available SARIF results |
| [CodeQL](.github/workflows/codeql.yml) | Pushes, pull requests and a weekly schedule | Runs Python analysis with the security-extended query suite |
| [ZAP](.github/workflows/dast-zap.yml) | Manual dispatch with a target URL | Runs a passive baseline scan, followed by an active scan if the baseline job succeeds |

Scan jobs exclude Dependabot-triggered runs. Snyk needs its API token stored as a repository secret. ZAP needs a running target that you are authorized to scan.

## Gates and limitations

The current workflows are a demonstration, not a complete blocking security gate:

- Semgrep uses `|| true`, so its scan exit code does not block the job. There is no implemented comparison that blocks only newly introduced findings.
- Snyk runs with `continue-on-error` and is excluded from the final Gate job's dependencies. SARIF upload is skipped if no report was produced.
- The Gate job depends on the Semgrep and secret-scanning jobs, then prints a completion message. It does not evaluate findings or enforce the proposed new-code policy.
- CodeQL uploads analysis results. The repository does not implement a release gate based on those findings.
- TruffleHog scans full history with the verified-only filter. Its job status is a dependency of the Gate job.
- Most action references are mutable tags or branches. This includes `@master` and `@main`; the workflows are not currently pinned throughout to commit SHAs.

The [gating-policy document](docs/gating-policy.md) describes the intended policy. Its blocking-SAST claim is ahead of the implementation above.

## Action pinning

The repository includes a helper for resolving action tags to commit SHAs:

```bash
# Resolves every `uses: org/action@tag` to org/action@<sha>  # tag
# using the action's published release commit, verified against the source repo.
./scripts/pin-actions.sh .github/workflows/security.yml
```

It requires an authenticated GitHub CLI, Bash and GNU-compatible sed. It edits the file in place and stops if a tag cannot be resolved. The current helper looks up tags, so branch references such as `@master` and `@main` need separate handling. Review the diff before committing. Providing this script does not mean its output has already been applied to the workflows.

## Documented examples

- [Command-injection data flow](docs/findings/cwe-78-command-injection.md), tracing input to a shell sink in the demonstration app.
- [Semgrep and CodeQL comparison](docs/findings/semgrep-vs-codeql.md), comparing pattern matching and data-flow analysis.
- [Transitive dependency findings](docs/findings/sca-transitive-cves.md), recording differences between a local environment and a clean CI runner.

These writeups describe their recorded runs. A dependency finding alone does not establish application reachability, and a passive web-scan alert alone does not prove exploitation.

## Run it

1. Clone or fork the repository.
2. Add `SNYK_TOKEN` to repository Actions secrets if you want the Snyk job to run successfully.
3. Push to main or open a pull request to run the automatic workflows. Review workflow results and available code-scanning reports.
4. Run ZAP separately through its manual workflow, supplying an authorized test URL. It is not part of every push or pull request.

## Next steps

Implement and test a findings-based gate, pin action dependencies, and distinguish scanner failure from a clean scan. Add baseline comparisons for new findings and an authenticated API-aware DAST example. Reachability-aware dependency evaluation remains future work.

Author: Jonathan (Jay) Ekwere, [github.com/jayekwere](https://github.com/jayekwere).
