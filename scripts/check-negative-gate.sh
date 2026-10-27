#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/negative
printf 'eval(input())\n' > artifacts/negative/untrusted.py
semgrep scan --config policy/semgrep.yml --strict --metrics=off --disable-version-check \
  --no-git-ignore --json --output artifacts/negative.json artifacts/negative/untrusted.py
set +e
python scripts/gate.py --report artifacts/negative.json --baseline policy/empty-baseline.json > artifacts/negative-gate.txt 2>&1
status=$?
set -e
cat artifacts/negative-gate.txt
test "$status" = 1
set +e
python scripts/gate.py --report artifacts/missing-report.json --baseline policy/empty-baseline.json > artifacts/missing-report-gate.txt 2>&1
status=$?
set -e
test "$status" = 2
printf 'PASS new unsafe code rejected (exit 1); absent report rejected (exit 2)\n'
