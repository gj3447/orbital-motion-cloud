#!/usr/bin/env python3
"""OMC owner adapter for registered, persistent native systemd workloads.

The root-owned registration is the owner's admission decision. This adapter
does not schedule arbitrary jobs, pool memory, infer grants from observations,
or replace the existing bounded-work broker. No container engine is used.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import stat
import subprocess


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(path, *, secret=False):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'An absolute direct path is required')
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0, 'Owner file must be root-owned and regular')
    require(not info.st_mode & 0o022, 'Owner file must not be group/world writable')
    if secret:
        require(stat.S_IMODE(info.st_mode) == 0o600, 'Secret/registration requires mode 600')
    return path


def path_value(value):
    require(isinstance(value, str) and re.fullmatch(r'/[A-Za-z0-9_./@+-]+', value), 'Unsafe native path')
    require('..' not in Path(value).parts and str(Path(value)) == value, 'Noncanonical native path')
    return value


def validate(value):
    require(isinstance(value, dict) and value.get('schema') == 'omc/native-service@1', 'Unknown service contract')
    allowed = {'schema', 'uid', 'owner', 'release', 'architecture', 'user', 'group', 'cwd', 'argv',
               'environment', 'environmentFiles', 'writePaths', 'binds', 'resources', 'bundleManifest'}
    require(set(value) == allowed, 'Unexpected or missing service fields')
    require(re.fullmatch(r'[a-z][a-z0-9-]{1,55}', value['uid']), 'Invalid workload UID')
    require(isinstance(value['owner'], str) and re.fullmatch(r'[A-Za-z0-9_:/.-]+', value['owner']), 'Missing owner')
    require(re.fullmatch(r'[a-f0-9]{40,64}', value['release']), 'Release must be immutable')
    require(value['architecture'] in ('x86_64', 'aarch64'), 'Unregistered architecture')
    require(all(type(value[k]) is int and 1 <= value[k] < 65534 for k in ('user', 'group')), 'Nonroot service identity required')
    path_value(value['cwd'])
    require(isinstance(value['argv'], list) and 1 <= len(value['argv']) <= 16, 'Invalid argv')
    path_value(value['argv'][0])
    require(all(isinstance(a, str) and a and not any(c in a for c in '\n\r\x00') for a in value['argv']), 'Unsafe argv')
    require(isinstance(value['environment'], dict), 'Invalid environment')
    require(all(re.fullmatch(r'[A-Z][A-Z0-9_]*', k) and isinstance(v, str) and not any(c in v for c in '\n\r\x00')
                for k, v in value['environment'].items()), 'Invalid environment value')
    require(len(value['environmentFiles']) <= 12 and len(value['writePaths']) <= 12 and len(value['binds']) <= 12, 'Path bound exceeded')
    for path in value['environmentFiles'] + value['writePaths']:
        path_value(path)
    for bind in value['binds']:
        require(set(bind) == {'source', 'target', 'readOnly'} and type(bind['readOnly']) is bool, 'Invalid bind')
        path_value(bind['source']); path_value(bind['target'])
    resources = value['resources']
    require(set(resources) == {'memoryBytes', 'cpuPercent', 'tasks', 'restartBurst'}, 'Invalid resource contract')
    for key, low, high in [('memoryBytes', 16 * 1024**2, 8 * 1024**3), ('cpuPercent', 1, 800), ('tasks', 8, 512), ('restartBurst', 1, 5)]:
        require(type(resources[key]) is int and low <= resources[key] <= high, 'Resource budget outside supported bounds')
    pin = value['bundleManifest']
    require(set(pin) == {'path', 'sha256'}, 'Bundle pin required')
    path_value(pin['path']); require(re.fullmatch('[a-f0-9]{64}', pin['sha256']), 'Invalid bundle pin')
    return value


def verify_bundle(value):
    pin = value['bundleManifest']
    manifest = regular(pin['path'])
    require(sha(manifest) == pin['sha256'], 'Bundle manifest changed')
    bundle = json.loads(manifest.read_text())
    require(bundle['schema'] == 'omc/native-bundle@1' and bundle['release'] == value['release'], 'Bundle release mismatch')
    root = manifest.parent
    require(isinstance(bundle['files'], dict) and 0 < len(bundle['files']) <= 30000, 'Bundle file bound exceeded')
    expected = set()
    for name, digest in bundle['files'].items():
        require(name != 'bundle.json' and not Path(name).is_absolute() and '..' not in Path(name).parts and str(Path(name)) == name, 'Unsafe bundle member')
        path = regular(root / name)
        require(path.is_relative_to(root) and re.fullmatch('[a-f0-9]{64}', digest), 'Invalid member pin')
        require(sha(path) == digest, 'Native bundle bytes changed: ' + name)
        expected.add(name)
    actual = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Bundle contains a symlink')
        if path.is_file() and path != manifest:
            actual.add(str(path.relative_to(root)))
    require(actual == expected, 'Unmanifested bundle files')
    for path in [value['cwd'], value['argv'][0]]:
        require(Path(path).resolve().is_relative_to(root), 'Execution leaves the verified bundle')
    require(os.access(value['argv'][0], os.X_OK), 'Native executable is not executable')
    require(platform.machine() == value['architecture'], 'Hardware architecture mismatch')
    for path in value['environmentFiles']:
        regular(path, secret=True)
    for path in value['writePaths'] + [b['source'] for b in value['binds']]:
        require(Path(path).exists() and Path(path).resolve() == Path(path), 'Missing or indirect registered data path')
    return root


def quote(value):
    # systemd command lines are not shell command lines. Disable specifier and
    # environment expansion in argv; all substitutions belong to owner config.
    return '"' + value.replace('%', '%%').replace('\\', '\\\\').replace('"', '\\"') + '"'


def unit_text(value, registration_sha):
    validate(value)
    r = value['resources']
    lines = [f'# OMC registration SHA-256: {registration_sha}', '[Unit]',
             f'Description=OMC native workload {value["uid"]} ({value["release"][:12]})',
             'After=network-online.target', 'Wants=network-online.target',
             f'StartLimitIntervalSec=60', f'StartLimitBurst={r["restartBurst"]}', '[Service]',
             'Type=exec', f'User={value["user"]}', f'Group={value["group"]}',
             f'WorkingDirectory={value["cwd"]}', 'ExecStart=:' + ' '.join(quote(a) for a in value['argv']),
             'Restart=on-failure', 'RestartSec=3', 'TimeoutStopSec=30', 'KillMode=control-group',
             'NoNewPrivileges=yes', 'CapabilityBoundingSet=', 'AmbientCapabilities=',
             'ProtectSystem=strict', 'ProtectHome=yes', 'PrivateTmp=yes', 'PrivateDevices=yes',
             'ProtectKernelTunables=yes', 'ProtectKernelModules=yes', 'ProtectControlGroups=yes',
             'RestrictSUIDSGID=yes', 'RestrictRealtime=yes', 'LockPersonality=yes', 'UMask=0077',
             'RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6',
             f'MemoryMax={r["memoryBytes"]}', f'CPUQuota={r["cpuPercent"]}%', f'TasksMax={r["tasks"]}',
             'MemoryAccounting=yes', 'CPUAccounting=yes', 'OOMPolicy=stop',
             'StandardOutput=journal', 'StandardError=journal', 'LogRateLimitIntervalSec=30s', 'LogRateLimitBurst=200']
    lines += ['Environment=' + quote(k + '=' + v) for k, v in sorted(value['environment'].items())]
    lines += ['EnvironmentFile=' + p for p in value['environmentFiles']]
    lines += ['ReadWritePaths=' + p for p in value['writePaths']]
    lines += [('BindReadOnlyPaths=' if b['readOnly'] else 'BindPaths=') + b['source'] + ':' + b['target'] for b in value['binds']]
    return '\n'.join(lines + ['[Install]', 'WantedBy=multi-user.target', ''])


def command(*argv):
    return subprocess.check_output(argv, text=True, timeout=45).strip()


def status(value):
    unit = 'omc-' + value['uid'] + '.service'
    keys = ['LoadState', 'ActiveState', 'SubState', 'MainPID', 'Result', 'FragmentPath', 'ControlGroup',
            'MemoryCurrent', 'MemoryPeak', 'MemoryMax', 'CPUUsageNSec', 'CPUQuotaPerSecUSec', 'TasksCurrent', 'TasksMax']
    rows = command('systemctl', 'show', unit, '--property=' + ','.join(keys))
    observed = dict(row.split('=', 1) for row in rows.splitlines() if '=' in row)
    pid = int(observed.get('MainPID', 0))
    observed['executableMatches'] = pid > 0 and os.path.realpath(f'/proc/{pid}/exe') == value['argv'][0]
    observed['bootId'] = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    observed['architecture'] = platform.machine()
    return {'schema': 'omc/native-service-observation@1', 'uid': value['uid'], 'owner': value['owner'],
            'release': value['release'], 'unit': unit, 'observed': observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'install', 'start', 'stop', 'restart', 'status', 'enable', 'disable'])
    parser.add_argument('--registration', required=True)
    parser.add_argument('--sha256', required=True, help='Exact owner registration digest, including for readback')
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Native service effects require the host owner')
    path = regular(args.registration, secret=True)
    require(sha(path) == args.sha256, 'Registration changed')
    value = validate(json.loads(path.read_text()))
    lock = Path('/run/lock') / ('omc-native-' + value['uid'] + '.lock')
    require(not lock.is_symlink(), 'Indirect lifecycle lock')
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        unit = 'omc-' + value['uid'] + '.service'
        target = Path('/etc/systemd/system') / unit
        text = unit_text(value, args.sha256)
        if args.action in ('verify', 'install', 'start', 'restart'):
            verify_bundle(value)
        if args.action == 'install':
            require(not target.is_symlink(), 'Indirect service unit')
            if target.exists() and target.read_text() != text:
                require(command('systemctl', 'show', unit, '--property=ActiveState', '--value') not in ('active', 'activating', 'deactivating'), 'Stop old owner workload before replacing its registration')
            temporary = target.with_suffix('.new.service')
            require(not temporary.exists(), 'Unresolved unit installation')
            temporary.write_text(text); temporary.chmod(0o644)
            try:
                command('systemd-analyze', 'verify', str(temporary))
                temporary.replace(target)
                command('systemctl', 'daemon-reload')
            finally:
                temporary.unlink(missing_ok=True)
        elif args.action in ('start', 'restart', 'stop', 'enable', 'disable'):
            require(regular(target).read_text() == text, 'Installed unit differs from owner registration')
            command('systemctl', args.action, unit)
        result = status(value)
        result['registrationSha256'] = args.sha256
        result['action'] = args.action
        print(json.dumps(result))


if __name__ == '__main__':
    main()
