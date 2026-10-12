"""Hydrate the git-ignored upstream/ copy from the hash lock in acquisition.json.

Fetches each locked file at the pinned commit, verifies size, SHA-256 and Git
blob ID before writing, and skips files that already match. Default source is
the pinned raw GitHub URL; --git-dir reads the same commit from a local clone.

    python3 records/2026-10-10/post-client-server-kubernetes/hydrate.py
    python3 records/2026-10-10/post-client-server-kubernetes/hydrate.py --git-dir ~/src/kubernetes
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
LOCK = Path(__file__).resolve().parent / 'acquisition.json'


def matches(data, item):
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    return len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'] and blob == item['git_blob_oid']


def raw_url(upstream, commit, path):
    repo = upstream.removeprefix('https://github.com/')
    return f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'


def fetch(upstream, commit, path, git_dir):
    if git_dir:
        return subprocess.run(['git', '-C', git_dir, 'cat-file', 'blob', f'{commit}:{path}'],
                              check=True, capture_output=True).stdout
    with urllib.request.urlopen(raw_url(upstream, commit, path), timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--git-dir', help='local kubernetes clone containing the pinned commit')
    parser.add_argument('--replace', action='store_true', help='overwrite local files whose bytes mismatch the lock')
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text())
    counts = {'present': 0, 'hydrated': 0, 'failed': 0}
    for item in lock['files']:
        target = ROOT / item['local_path']
        if target.is_symlink() or not target.resolve().is_relative_to(ROOT):
            print('REFUSED (scope):', item['path'], file=sys.stderr)
            counts['failed'] += 1
            continue
        if target.is_file():
            if matches(target.read_bytes(), item):
                counts['present'] += 1
                continue
            if not args.replace:
                print('MISMATCH (use --replace):', item['path'], file=sys.stderr)
                counts['failed'] += 1
                continue
        try:
            data = fetch(lock['upstream'], lock['commit'], item['path'], args.git_dir)
        except (OSError, subprocess.CalledProcessError) as exc:
            print('FETCH FAILED:', item['path'], exc, file=sys.stderr)
            counts['failed'] += 1
            continue
        if not matches(data, item):
            print('FETCHED BYTES MISMATCH LOCK:', item['path'], file=sys.stderr)
            counts['failed'] += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + '.part')
        tmp.write_bytes(data)
        tmp.replace(target)
        counts['hydrated'] += 1
    print(json.dumps({'commit': lock['commit'], **counts, 'total': len(lock['files'])}))
    return 1 if counts['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
