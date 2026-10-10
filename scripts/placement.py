#!/usr/bin/env python3
"""OMC: observe hardware, plan bounded copies, verify and rebind stable resources.

The owner supplies a private host registry and an existing USL resource graph.
AI requests select resources; they cannot supply commands, roots or new pins.
Transfers use THE GREAT FLOW's existing shared_storage CLI. Original files are
retained. Large mutable directories remain with their owner migration worker.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
JSON_LIMIT = 2 * 1024 * 1024
FILE_LIMIT = 64 * 1024 * 1024
BATCH_LIMIT = 256 * 1024 * 1024
SAFE_CLASSES = {'closed_artifact', 'research_snapshot', 'memory_snapshot'}


class Refused(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def implementation_digest():
    return 'sha256:' + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def load(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= JSON_LIMIT,
            'JSON must be a bounded regular non-symlink file: ' + str(p))
    return json.loads(p.read_bytes())


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            os.chmod(temporary, 0o600)
            stream.write(canonical(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


def relative(value):
    require(isinstance(value, str) and value and '\\' not in value and
            not value.startswith('/') and all(x not in ('', '.', '..') for x in value.split('/')),
            'Invalid relative path')
    return value


def safe_path(root, path):
    root = Path(root)
    require(root.is_absolute() and root.resolve() == root and root.is_dir(), 'Invalid workspace root')
    target = root / relative(path)
    require(target.resolve().is_relative_to(root), 'Workspace escape')
    for item in [target, *target.parents]:
        require(not item.is_symlink(), 'Symlink in selected path')
        if item == root:
            break
    return target


def pin(path, limit=FILE_LIMIT):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'Not a bounded regular file')
        h, total = hashlib.sha256(), 0
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            total += len(block)
            require(total <= limit, 'File grew beyond budget')
            h.update(block)
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        require(all(getattr(before, k) == getattr(after, k) for k in fields), 'File changed during read')
        require(os.stat(path, follow_symlinks=False).st_ino == after.st_ino, 'Path changed during read')
        return {'bytes': total, 'sha256': h.hexdigest()}
    finally:
        os.close(fd)


def command(argv, cwd=None, timeout=30):
    # argv is built by this module, never taken from a graph or AI request.
    env = {k: v for k, v in os.environ.items() if k != 'METAHUMOTONIC_SHARED_ROOT'}
    env['TSX_DISABLE_CACHE'] = '1'
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    require(len(result.stdout) <= JSON_LIMIT and len(result.stderr) <= JSON_LIMIT, 'CLI output budget exceeded')
    require(result.returncode == 0, 'CLI failed: ' + result.stderr.decode(errors='replace')[:1000])
    return json.loads(result.stdout)


def host_config(path):
    host = load(path)
    require(host.get('schema') == 'omc-placement-host/1', 'Unknown host schema')
    require(host['host_uid'] == 'host:dev-01', 'This live adapter is scoped to dev-01')
    require(set(host['volumes']) == {'bulk20', 'backup4'}, 'Expected separately identified storage tiers')
    require(len({v['source'] for v in host['volumes'].values()}) == 2, 'Aliased storage pools')
    require(host['volumes']['bulk20']['root'] == '/mnt/development/METAHUMOTONIC_SHARED', 'Unexpected owner store')
    require(host['volumes']['bulk20']['source'] == '192.168.0.25:/srv/expansion20tb/pool/Development', 'Wrong 20TB export')
    require(host['volumes']['backup4']['mount'] == '/mnt/bulk' and
            host['volumes']['backup4']['source'] == '192.168.0.25:/srv/dgx4tb/nas/hswm', 'Wrong 4TB export')
    backup = host['volumes']['backup4']
    require(backup['transport'] == 'owner_ssh' and backup['provider_host'] == 'data-01' and
            backup['provider_mount'] == '/srv/dgx4tb' and
            backup['provider_root'] == '/srv/dgx4tb/nas/hswm/omc-replicas' and
            backup['provider_uuid'] == '57bc2272-c87a-48f9-bc8a-fb6c4d8b1148' and
            backup['root'] == '/mnt/bulk/omc-replicas', 'Unregistered backup transport/provider')
    for alias, volume in host['volumes'].items():
        require(Path(volume['root']).is_relative_to(volume['mount']), 'Store root outside declared mount')
        require(volume['reserve_bytes'] >= 100 * 1024**3, 'Storage reserve below 100 GiB')
    require(1 <= host['ttl_seconds'] <= 300, 'Observation TTL outside supported range')
    require(host['memory_reserve_bytes'] >= 128 * 1024**2, 'Memory reserve too small')
    require(host['root_reserve_bytes'] >= 8 * 1024**3, 'Root reserve too small')
    require(0 < len(host['assets']) <= 64, 'Asset limit exceeded')
    require(len({a['resource'] for a in host['assets']}) == len(host['assets']), 'Duplicate asset ID')
    require(len({a['representation'] for a in host['assets']}) == len(host['assets']), 'Duplicate representation ID')
    for asset in host['assets']:
        require(asset['workspace'] in host['workspaces'], 'Unregistered source workspace')
        relative(asset['path'])
        require(type(asset['bytes']) is int and 0 <= asset['bytes'] <= FILE_LIMIT, 'Asset exceeds file budget')
        require(re.fullmatch('[a-f0-9]{64}', asset['sha256']) is not None, 'Missing owner content pin')
        require(re.fullmatch('[A-Za-z_][A-Za-z0-9_.-]*', asset['representation']) is not None, 'Invalid representation ID')
    for item in host['tool_pins']:
        require(pin(item['path'], JSON_LIMIT)['sha256'] == item['sha256'], 'Owner CLI changed; refresh reviewed registration')
    required_tools = {str(Path(host['owner_repository']) / 'scripts' / name) for name in ('shared_storage.py', 'fleet.py')}
    required_tools |= {str(Path(host['usl_repository']) / 'src' / name) for name in ('cli.ts', 'resource-bindings.ts')}
    require(required_tools <= {x['path'] for x in host['tool_pins']}, 'Missing invoked CLI source pins')
    for key in ('state_dir', 'usl_repository', 'owner_repository'):
        require(Path(host[key]).is_absolute() and Path(host[key]).resolve() == Path(host[key]), 'Invalid registered local root')
    return host


def mount(host, alias):
    v = host['volumes'][alias]
    result = command(['findmnt', '-J', '-T', v['mount'], '-o', 'TARGET,SOURCE,FSTYPE,OPTIONS'])
    rows = result.get('filesystems', [])
    require(len(rows) == 1, 'Missing mount')
    row = rows[0]
    options = set(row['options'].split(','))
    require(row['target'] == v['mount'] and row['source'] == v['source'] and
            row['fstype'] == 'nfs4' and 'rw' in options, 'Unexpected mount identity/options')
    if alias == 'bulk20':
        require('hard' in options, 'Primary store requires the existing hard NFS mount')
    else:
        provider = command([sys.executable, str(Path(host['owner_repository']) / 'scripts/fleet.py'),
                            'exec', v['provider_host'], '--', 'findmnt', '-J', '-T', v['provider_mount'],
                            '-o', 'TARGET,FSTYPE,UUID'])['filesystems'][0]
        require(provider['target'] == v['provider_mount'] and provider['fstype'] == 'ext4' and
                provider['uuid'] == v['provider_uuid'], 'Backup provider identity mismatch')
    s = os.statvfs(v['mount'])
    return {'uid': v['uid'], 'source': row['source'], 'available_bytes': s.f_bavail * s.f_frsize,
            'available_inodes': s.f_favail, 'verified': True,
            'write_transport': 'owner_ssh_provider_local' if alias == 'backup4' else 'owner_cli_hard_nfs',
            'client_nfs_options': row['options']}


def memory():
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        if key in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'):
            values[key] = int(value.split()[0]) * 1024
    cgroup = Path('/sys/fs/cgroup')
    entries = Path('/proc/self/cgroup').read_text().splitlines()
    own = next((x[3:] for x in entries if x.startswith('0::')), None)
    rows = []
    if own is not None:
        leaf = cgroup / own.lstrip('/')
        for directory in [leaf, *leaf.parents]:
            if not directory.is_relative_to(cgroup):
                break
            if (directory / 'memory.max').exists():
                limit = (directory / 'memory.max').read_text().strip()
                current = int((directory / 'memory.current').read_text())
                rows.append({'path': str(directory), 'max_bytes': None if limit == 'max' else int(limit),
                             'current_bytes': current,
                             'cpu_max': (directory / 'cpu.max').read_text().strip()})
    headrooms = [values['MemAvailable']] + [max(0, r['max_bytes'] - r['current_bytes']) for r in rows if r['max_bytes'] is not None]
    return {'os_visible': values, 'visible_cgroups': rows, 'available_bound_bytes': min(headrooms),
            'outside_namespace_constraints': 'UNKNOWN', 'basis': 'OS_VISIBLE_AND_VISIBLE_LIMITS_ONLY'}


def observe(host):
    guard = command(['storage-guard', 'status'])
    return {'schema': 'omc-hardware-observation/1', 'observed_at_epoch': time.time(),
            'host_uid': host['host_uid'], 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'config_digest': digest(host), 'memory': memory(), 'cpu': {'logical_count': os.cpu_count(), 'load_average': list(os.getloadavg())},
            'root_available_bytes': guard['root']['available_bytes'], 'guard': guard,
            'volumes': {alias: mount(host, alias) for alias in host['volumes']},
            'hardware_allocation_authorized': False}


def semantic(graph):
    """Only resource locators may vary. Everything else, including order, is pinned."""
    result = copy.deepcopy(graph)
    for resource in result['resources']:
        resource.pop('locator', None)
    return digest(result)


def invariant(before, after, selected):
    require(semantic(before) == semantic(after), 'Semantic graph changed')
    for old, new in zip(before['resources'], after['resources'], strict=True):
        if old['id'] not in selected:
            require(old == new, 'Unselected resource changed')


def usl(host, *args):
    return command(['node', '--import', 'tsx', 'src/cli.ts', *args], cwd=host['usl_repository'], timeout=30)


def stored_pin(host, target, key):
    if target == 'bulk20':
        path = safe_path(host['volumes'][target]['root'], key)
        return pin(path) if path.exists() else None
    v = host['volumes'][target]
    remote = Path(v['provider_root']) / relative(key)
    # Read back on the writing host. The existing soft NFS client can retain
    # negative directory-cache entries after a file was published over SSH.
    program = '''import os,stat,hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); base=Path(sys.argv[2])
assert p.is_relative_to(base) and p.resolve()==p and base.resolve()==base
if not p.exists():
 print('null'); raise SystemExit(0)
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 before=os.fstat(fd); assert stat.S_ISREG(before.st_mode) and before.st_size<=67108864
 h=hashlib.sha256(); total=0
 while True:
  b=os.read(fd,1048576)
  if not b: break
  total+=len(b); assert total<=67108864; h.update(b)
 after=os.fstat(fd)
 assert all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns'))
 assert p.stat().st_ino==after.st_ino
 print(json.dumps({'bytes':total,'sha256':h.hexdigest()}))
finally: os.close(fd)
'''
    return command([sys.executable, str(Path(host['owner_repository']) / 'scripts/fleet.py'),
                    'exec', v['provider_host'], '--', 'python3', '-c', program, str(remote), v['provider_root']])


@contextmanager
def locked(host):
    directory = Path(host['state_dir'])
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(directory.resolve() == directory, 'State directory must be local and direct')
    require(command(['findmnt', '-J', '-T', str(directory), '-o', 'FSTYPE'])['filesystems'][0]['fstype'] in ('ext4', 'xfs', 'btrfs', 'tmpfs'),
            'State lock/CAS requires local storage')
    with (directory / 'writer.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield directory


def initialize(host, graph_path):
    graph = load(graph_path)
    require(graph.get('schema') == 'usl-resource-graph/v1', 'Expected native USL resource graph')
    ids = [r['id'] for r in graph['resources']]
    require(len(ids) == len(set(ids)), 'Duplicate resource ID')
    assets = host['assets']
    for a in assets:
        require(a['resource'] in ids, 'Owner asset is absent from semantic graph')
        source = safe_path(host['workspaces'][a['workspace']], a['path'])
        require(pin(source) == {'bytes': a['bytes'], 'sha256': a['sha256']}, 'Owner content pin mismatch')
    usl(host, 'adapt', '--format', 'resource-graph', '--graph', str(Path(graph_path).absolute()),
        '--namespace', 'omc.placement', '--operation', 'check')
    bindings = {'schema': 'usl-resource-bindings/v1', 'resources': [
        {'id': a['resource'], 'representations': [{'id': a['representation'], 'relation': 'working-copy',
         'kind': 'workspace', 'workspace': a['workspace'], 'path': a['path'], 'digest': 'sha256:' + a['sha256']}]}
        for a in assets]}
    with locked(host) as directory:
        path = directory / 'state.json'
        require(not path.exists(), 'Owner state already exists')
        state = {'schema': 'omc-placement-state/1', 'generation': 0, 'graph': graph, 'bindings': bindings,
                 'semantic_digest': semantic(graph), 'last_operation': None}
        atomic(path, state)
        return {'status': 'INITIALIZED', 'state_digest': digest(state), 'semantic_digest': semantic(graph)}


def ready(host, observation, now=None):
    now = time.time() if now is None else now
    require(observation['schema'] == 'omc-hardware-observation/1', 'Unknown observation')
    require(0 <= now - observation['observed_at_epoch'] <= host['ttl_seconds'], 'Stale/future observation')
    require(observation['host_uid'] == host['host_uid'] and observation['config_digest'] == digest(host), 'Wrong host/config observation')
    require(observation['memory']['available_bound_bytes'] >= host['memory_reserve_bytes'], 'Insufficient observed memory')
    require(observation['root_available_bytes'] >= host['root_reserve_bytes'], 'Root reserve exhausted')
    require(observation['guard']['pool']['data_percent'] < 98, 'Thinpool emergency threshold')
    require(observation['guard']['pool']['metadata_percent'] < 80, 'Thinpool metadata threshold')
    require(set(observation['volumes']) == set(host['volumes']), 'Missing volume observations')


def make_plan(host, state, observation, request, now=None):
    ready(host, observation, now)
    require(request.get('schema') == 'omc-placement-request/1' and set(request) <= {'schema', 'resources', 'backup', 'reason'}, 'Unknown request fields/schema')
    wanted = request['resources']
    require(isinstance(wanted, list) and 0 < len(wanted) <= 16 and len(wanted) == len(set(wanted)), 'Invalid selected resources')
    require(type(request.get('backup', False)) is bool, 'backup must be boolean')
    require(set(wanted) <= {a['resource'] for a in host['assets']}, 'Unregistered resource request')
    remaining = {alias: observation['volumes'][alias]['available_bytes'] - v['reserve_bytes'] for alias, v in host['volumes'].items()}
    rows, rejected, used = [], [], 0
    for a in sorted(host['assets'], key=lambda a: (-a['bytes'], a['resource'])):
        if a['resource'] not in wanted:
            continue
        if a['data_class'] not in SAFE_CLASSES or a.get('closed') is not True:
            rejected.append({'resource': a['resource'], 'reason': 'LIVE_OR_UNCLASSIFIED_DATA'}); continue
        targets = ['bulk20'] + (['backup4'] if request.get('backup') else [])
        cost = a['bytes'] * len(targets)
        if used + cost > BATCH_LIMIT or any(remaining[t] < a['bytes'] or observation['volumes'][t]['available_inodes'] < 1000 for t in targets):
            rejected.append({'resource': a['resource'], 'reason': 'CAPACITY_OR_BATCH_BUDGET'}); continue
        for t in targets:
            require(observation['volumes'][t]['verified'] and observation['volumes'][t]['source'] == host['volumes'][t]['source'], 'Unverified target')
            remaining[t] -= a['bytes']
        used += cost
        rows.append({'resource': a['resource'], 'representation': a['representation'], 'bytes': a['bytes'], 'sha256': a['sha256'],
                     'primary': 'bulk20', 'copies': targets, 'key': 'omc/objects/' + a['sha256'] + '/' + hashlib.sha256(a['resource'].encode()).hexdigest()[:20]})
    value = {'schema': 'omc-placement-plan/1', 'status': 'READY' if rows and not rejected else 'NOT_READY',
             'implementation_digest': implementation_digest(),
             'config_digest': digest(host), 'state_digest': digest(state), 'semantic_digest': semantic(state['graph']),
             'observation_digest': digest(observation), 'boot_id': observation['boot_id'], 'request': request,
             'placements': rows, 'rejected': rejected, 'transfer_bytes_upper_bound': used,
             'source_retained': True, 'space_reclaim_bytes': 0, 'optimization': 'DETERMINISTIC_FEASIBLE_BATCH_NOT_GLOBAL_OPTIMUM',
             'ai_authority': 'CANDIDATE_SELECTION_ONLY'}
    value['plan_digest'] = digest(value)
    return value


def validate_plan(plan):
    value = {k: v for k, v in plan.items() if k != 'plan_digest'}
    require(plan['plan_digest'] == digest(value), 'Plan digest mismatch')
    require(plan['status'] == 'READY', 'Plan is not executable')
    require(plan['transfer_bytes_upper_bound'] == sum(row['bytes'] * len(row['copies']) for row in plan['placements']),
            'Transfer budget does not match placements')


def managed_budget(plan):
    """Require the deployed runner's live job group for larger transfers."""
    if plan['transfer_bytes_upper_bound'] <= 100 * 1024**2:
        return
    artifact = Path(os.environ.get('STORAGE_ARTIFACT_DIR', ''))
    require(artifact.is_absolute() and artifact.is_relative_to('/mnt/development/managed-dev') and
            artifact.name == 'artifacts' and artifact.is_dir(), 'Large transfer requires proxmox-scratch')
    run_id = artifact.parent.name.rsplit('-', 1)[-1]
    require(re.fullmatch('[a-f0-9]{32}', run_id) is not None, 'Invalid managed run identity')
    lease = load(Path.home() / '.local/state/storage-guard/leases' / (run_id + '.json'))
    require(lease['id'] == run_id and lease['tier'] == 'bulk' and
            lease['project'] == artifact.parents[2].name and
            lease['budget_bytes'] >= plan['transfer_bytes_upper_bound'] and
            lease['child_pid'] == os.getpgrp(), 'Managed lease does not cover this process/budget')
    require(lease['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'Stale managed lease')
    process = Path('/proc') / str(lease['pid']) / 'stat'
    start_ticks = int(process.read_text().rsplit(')', 1)[1].split()[19])
    require(start_ticks == int(lease['start_ticks']), 'Managed supervisor identity changed')


def apply(host, plan, operation, recover=False, reviewed_implementation=None):
    validate_plan(plan)
    managed_budget(plan)
    changed_implementation = plan['implementation_digest'] != implementation_digest()
    require(not changed_implementation or (recover and reviewed_implementation == implementation_digest()),
            'Planner/executor implementation changed; recovery needs its explicitly reviewed digest')
    require(re.fullmatch('[a-z0-9][a-z0-9-]{0,62}', operation) is not None, 'Invalid operation key')
    with locked(host) as directory:
        current = load(directory / 'state.json')
        op = directory / 'operations' / operation
        intent_path = op / 'intent.json'
        if intent_path.exists():
            intent = load(intent_path)
            require(intent['plan_digest'] == plan['plan_digest'], 'Operation key conflict')
            if current['last_operation'] == operation:
                # A crash between the state CAS and the final receipt must not
                # repeat the transfer or increment the generation again.
                result_path = op / 'result.json'
                result = load(result_path if result_path.exists() else op / 'prepared-result.json')
                require(result['state_digest'] == digest(current) and result['plan_digest'] == plan['plan_digest'], 'Committed result mismatch')
                if not result_path.exists():
                    require(recover, 'Committed state has no final receipt; recover the same operation')
                    atomic(result_path, result)
                return result
            require(recover, 'Existing incomplete operation; use recover with the same plan/key')
        else:
            require(not recover, 'No operation to recover')
        if changed_implementation:
            atomic(op / ('recovery-' + implementation_digest().split(':')[1] + '.json'),
                   {'original_implementation': plan['implementation_digest'], 'reviewed_implementation': reviewed_implementation,
                    'original_plan_digest': plan['plan_digest'], 'reviewed_at_epoch': time.time()})
        require(digest(current) == plan['state_digest'] and digest(host) == plan['config_digest'], 'STALE state/config')
        fresh = observe(host)
        require(fresh['boot_id'] == plan['boot_id'], 'Host rebooted; make a new plan')
        replanned = make_plan(host, current, fresh, plan['request'])
        require(replanned['status'] == 'READY' and replanned['placements'] == plan['placements'], 'Fresh hardware no longer admits plan')
        if not intent_path.exists():
            atomic(intent_path, {'schema': 'omc-placement-intent/1', 'plan_digest': plan['plan_digest'], 'plan': plan,
                                 'started_at_epoch': time.time(), 'status': 'INTENT_DURABLE'})
        tools_path = Path(host['owner_repository']) / 'scripts/shared_storage.py'
        next_state = copy.deepcopy(current)
        transfers = []
        for row in plan['placements']:
            a = next(a for a in host['assets'] if a['resource'] == row['resource'])
            source = safe_path(host['workspaces'][a['workspace']], a['path'])
            expected = {'bytes': row['bytes'], 'sha256': row['sha256']}
            require(pin(source) == expected, 'Source changed since registration')
            for target in row['copies']:
                mount(host, target)
                atomic(op / 'progress.json', {'operation': operation, 'transfers': transfers,
                                               'state_committed': False})
                root = Path(host['volumes'][target]['root'])
                require(root.is_dir(), 'Registered target root must already exist')
                dest = safe_path(root, row['key'])
                existing = stored_pin(host, target, row['key'])
                if existing is not None:
                    require(existing == expected, 'Existing target content mismatch')
                    transfers.append({'target': target, 'status': 'EXISTING_BYTES_VERIFIED', **expected})
                else:
                    argv = [sys.executable, str(tools_path)]
                    if target == 'bulk20':
                        argv += ['put', '--source', str(source), row['key']]
                    else:
                        v = host['volumes'][target]
                        remote_dest = Path(v['provider_root']) / row['key']
                        # Only mkdir for this registered object's parent; no
                        # arbitrary shell or request-provided command is used.
                        program = ('from pathlib import Path\nimport json,sys\n'
                                   'base=Path(sys.argv[2]); p=Path(sys.argv[1])\n'
                                   'assert base.is_dir() and base.resolve()==base\n'
                                   'assert p.is_absolute() and p.resolve()==p and p.is_relative_to(base)\n'
                                   'current=base\n'
                                   'for part in p.relative_to(base).parts:\n'
                                   ' current=current/part\n'
                                   ' current.mkdir(exist_ok=True,mode=0o750)\n'
                                   ' assert not current.is_symlink()\n'
                                   'print(json.dumps({"parent_ready":True}))')
                        command([sys.executable, str(Path(host['owner_repository']) / 'scripts/fleet.py'),
                                 'exec', v['provider_host'], '--', 'python3', '-c', program, str(remote_dest.parent), v['provider_root']])
                        argv += ['get', row['key'], '--host', v['provider_host'], '--destination', str(remote_dest)]
                    receipt = command(argv, cwd=host['owner_repository'], timeout=120)
                    require(receipt.get('mount', {}).get('verified') is True, 'Unverified owner transport')
                    require({'bytes': receipt['bytes'], 'sha256': receipt['sha256']} == expected, 'Transport pin mismatch')
                    require(stored_pin(host, target, row['key']) == expected, 'Destination readback mismatch')
                    transfers.append({'target': target, 'status': 'COPIED_AND_READBACK_VERIFIED', 'owner_receipt': receipt})
                mount(host, target)
            require(pin(source) == expected, 'Source changed during transfer')
            bound = next(r for r in next_state['bindings']['resources'] if r['id'] == row['resource'])
            rep = next(r for r in bound['representations'] if r['id'] == row['representation'])
            rep.update(workspace='bulk20', path=row['key'])
        workspaces = {**host['workspaces'], **{k: v['root'] for k, v in host['volumes'].items()}}
        atomic(op / 'bindings.json', next_state['bindings'])
        atomic(op / 'before.json', current['graph'])
        atomic(op / 'host.json', {'schema': 'usl-cli-host/v1', 'bindings': 'bindings.json', 'workspaces': workspaces,
                                  'maxSourceBytes': JSON_LIMIT, 'actions': []})
        selections = [{'resource': r['resource'], 'representation': r['representation']} for r in plan['placements']]
        atomic(op / 'selections.json', selections)
        rebound = usl(host, 'bind-graph', '--config', str(op / 'host.json'), '--graph', str(op / 'before.json'),
                      '--selections', str(op / 'selections.json'))
        invariant(current['graph'], rebound['graph'], {r['resource'] for r in plan['placements']})
        atomic(op / 'after.json', rebound['graph'])
        checked = usl(host, 'adapt', '--format', 'resource-graph', '--graph', str(op / 'after.json'),
                      '--namespace', 'omc.placement', '--operation', 'check')
        for row in plan['placements']:
            for target in row['copies']:
                require(stored_pin(host, target, row['key']) == {'bytes': row['bytes'], 'sha256': row['sha256']}, 'Copy changed before commit')
        require(digest(load(directory / 'state.json')) == plan['state_digest'], 'CAS conflict')
        next_state.update(graph=rebound['graph'], generation=current['generation'] + 1, last_operation=operation)
        result = {'schema': 'omc-placement-result/1', 'operation': operation, 'status': 'COMPLETE',
                  'plan_digest': plan['plan_digest'], 'previous_state_digest': digest(current), 'state_digest': digest(next_state),
                  'semantic_digest_before': semantic(current['graph']), 'semantic_digest_after': semantic(next_state['graph']),
                  'source_retained': True, 'space_reclaim_bytes': 0, 'transfers': transfers,
                  'binding_receipt': rebound['bindingReceipt'], 'usl_check': checked['result'], 'completed_at_epoch': time.time()}
        result['implementation_digest'] = implementation_digest()
        atomic(op / 'prepared-result.json', result)
        atomic(directory / 'state.json', next_state)
        atomic(op / 'result.json', result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, help='Private owner registry; not an AI proposal')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--graph', required=True)
    sub.add_parser('observe')
    plan = sub.add_parser('plan'); plan.add_argument('--observation', required=True); plan.add_argument('--request', required=True)
    for name in ('apply', 'recover'):
        run = sub.add_parser(name); run.add_argument('--plan', required=True); run.add_argument('--operation', required=True)
        if name == 'recover': run.add_argument('--reviewed-implementation', help='Exact new code digest after an explicitly reviewed recovery fix')
    sub.add_parser('status')
    parser.add_argument('--out', help='Save result JSON atomically')
    args = parser.parse_args(argv)
    try:
        host = host_config(args.host)
        if args.command == 'init':
            result = initialize(host, args.graph)
        elif args.command == 'observe':
            result = observe(host)
        elif args.command == 'plan':
            result = make_plan(host, load(Path(host['state_dir']) / 'state.json'), load(args.observation), load(args.request))
        elif args.command in ('apply', 'recover'):
            result = apply(host, load(args.plan), args.operation, args.command == 'recover', getattr(args, 'reviewed_implementation', None))
        else:
            state = load(Path(host['state_dir']) / 'state.json')
            result = {'generation': state['generation'], 'state_digest': digest(state),
                      'semantic_digest': semantic(state['graph']), 'last_operation': state['last_operation']}
        if args.out:
            atomic(args.out, result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'REFUSED_OR_INCOMPLETE', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
