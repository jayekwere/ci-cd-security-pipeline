"""Offline token-shape check complements verified credential scanning."""
from pathlib import Path
import re
import subprocess

PATTERN = re.compile(rb'(?:AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36})')


def check(raw):
    return bool(PATTERN.search(raw))


if __name__ == '__main__':
    paths = subprocess.check_output(['git', 'ls-files', '-z']).split(b'\0')
    denied = []
    for raw in paths:
        if raw:
            path = Path(raw.decode())
            if path.is_file() and check(path.read_bytes()):
                denied.append(str(path))
    if denied:
        raise SystemExit('DENY token-shaped credential in: ' + ', '.join(denied))
    print('PASS tracked files contain no supported token-shaped credentials')
