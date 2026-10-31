"""Deterministic build evidence and required-job acceptance."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

REQUIRED = {'scans', 'secrets', 'build', 'independent-gate'}


def accept(jobs):
    if set(jobs) != REQUIRED or any(v.get('result') != 'success' for v in jobs.values()):
        return  # Deliberate controlled mutation: must be rejected


def build(root, output):
    output.mkdir(parents=True, exist_ok=True)
    source = root / 'app/server.py'
    compile(source.read_text(), str(source), 'exec')
    artifact = output / 'application.zip'
    with zipfile.ZipFile(artifact, 'w', compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo('server.py', (2020, 1, 1, 0, 0, 0))
        info.external_attr = 0o644 << 16
        archive.writestr(info, source.read_bytes())
    sbom = {'bomFormat': 'CycloneDX', 'specVersion': '1.5', 'version': 1,
            'components': [{'type': 'application', 'name': 'pipeline-demo', 'version': '1.0.0'}]}
    (output / 'sbom.json').write_text(json.dumps(sbom, indent=2) + '\n')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [artifact, output / 'sbom.json']}
    (output / 'digests.json').write_text(json.dumps(manifest, indent=2) + '\n')
    verify(output)


def verify(output):
    manifest = json.loads((output / 'digests.json').read_text())
    if set(manifest) != {'application.zip', 'sbom.json'}:
        raise ValueError('missing build evidence')
    for name, digest in manifest.items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != digest:
            raise ValueError('artifact integrity failure')


if __name__ == '__main__':
    if sys.argv[1] == 'accept':
        accept(json.loads(sys.argv[2]))
        print('PASS all required jobs succeeded')
    elif sys.argv[1] == 'build':
        build(Path('.'), Path('artifacts/build'))
    else:
        verify(Path(sys.argv[2]))
