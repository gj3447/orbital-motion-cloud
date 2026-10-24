#!/usr/bin/env python3
"""Keep the OMC owner on DW; expose only its authenticated protocol to HOH.
The remote side uses installed socket/stat utilities, not copied OMC programs.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
from browser_contribution import read_json, require

REMOTE_SOCKET = '/srv/hoh-main/omc/owner.sock'
CLEANUP = r'''set -eu
p=/srv/hoh-main/omc/owner.sock
if [ -e "$p" ]; then
  test -S "$p"
  test "$(stat -c %u "$p")" = "$(id -u)"
  identity=$(stat -c '%d:%i:%Z' "$p")
  listeners=$(ss -xlH)
  if printf '%s\n' "$listeners" | awk -v path="$p" '{ for (i=1;i<=NF;i++) if ($i==path) found=1 } END { exit !found }'; then
    echo 'OMC socket still has a listener; refusing replacement' >&2
    exit 73
  fi
  test "$(stat -c '%d:%i:%Z' "$p")" = "$identity"
  rm -- "$p"
fi
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = read_json(args.config, 2048)
    require(set(config) == {'host'}, 'Only the operator SSH host is configurable')
    host = config['host']
    require(isinstance(host, str) and re.fullmatch(r'[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+', host), 'Invalid SSH destination')
    base = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
    subprocess.run([*base, host, CLEANUP], check=True, timeout=20)
    os.execvp('ssh', [*base, '-NT', '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=20',
                     '-o', 'ServerAliveCountMax=3', '-R', REMOTE_SOCKET + ':127.0.0.1:19128', host])


if __name__ == '__main__': main()
