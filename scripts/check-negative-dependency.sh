#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts
# Data-only input to pip-audit: never install this intentionally vulnerable package.
printf 'requests==2.19.1\n' > artifacts/vulnerable-requirements.txt
set +e
pip-audit -r artifacts/vulnerable-requirements.txt --no-deps --disable-pip --format json --output artifacts/negative-dependency.json
status=$?
set -e
test "$status" = 1
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('artifacts/negative-dependency.json').read_text())
assert any(d['name'] == 'requests' and d['version'] == '2.19.1' and d['vulns'] for d in report['dependencies'])
print('PASS pinned vulnerable dependency rejected without installation')
PY
