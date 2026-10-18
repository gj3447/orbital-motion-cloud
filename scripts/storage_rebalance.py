#!/usr/bin/env python3
"""Plan the data-01 containerd relocation; never stop services or move bytes.

The private observation comes from the storage owner. The OMC operator reads
this plan before a maintenance decision. It is not an execution permit, a
canonical HSWM export, or proof of reclaimed thin-pool blocks.
"""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import time

from placement import Refused, digest, load, require

GIB = 1024 ** 3
SOURCE = '/var/lib/containerd'

# Fixed owner transport and paths, not commands supplied by a graph or model.
# Inspect only identity and state fields; never collect container environments.
COLLECT = r'''
import json, os, subprocess, time, tomllib
def run(args):
    return subprocess.check_output(args, text=True, timeout=120).strip()
began = time.time()
source = registration['source_path']
target = registration['target_path']
def mount(path):
    return json.loads(run(['findmnt','-J','-T',path,'-o','TARGET,SOURCE,FSTYPE,UUID']))['filesystems'][0]
src, dst = mount(source), mount(registration['target_mount'])
allocated = int(run(['sudo','-n','du','-sx','-B1',source]).split()[0])
ids = run(['sudo','-n','docker','ps','-aq','--no-trunc']).splitlines()
template = '{"id":{{json .Id}},"name":{{json .Name}},"image_id":{{json .Image}},"running":{{json .State.Running}}}'
rows = [json.loads(line) for line in run(['sudo','-n','docker','inspect','--format',template,*ids]).splitlines()] if ids else []
for row in rows: row['name'] = row['name'].lstrip('/')
driver = json.loads(run(['sudo','-n','docker','info','--format','{{json .DriverStatus}}']))
configuration = tomllib.loads(run(['sudo','-n','containerd','config','dump']))
print(json.dumps({
    'schema':'omc-storage-owner-observation/1','epoch':time.time(),'collection_started_epoch':began,
    'boot_id':run(['cat','/proc/sys/kernel/random/boot_id']),
    'source':{'host_uid':'host:data-01','path':source,'mount_target':src['target'],
              'device':src['source'],'fstype':src['fstype'],'allocated_bytes':allocated},
    'target':{'host_uid':'host:data-01','path':target,'mount_target':dst['target'],
              'device':dst['source'],'fstype':dst['fstype'],'filesystem_uuid':dst['uuid'],
              'available_bytes':int(run(['df','-B1','--output=avail',registration['target_mount']]).splitlines()[-1]),
              'destination_absent':not os.path.lexists(target),'path_resolves_exactly':os.path.realpath(target)==target},
    'containers':rows,
    'image_ids':sorted(set(run(['sudo','-n','docker','image','ls','-aq','--no-trunc']).splitlines())),
    'containerd_namespaces':sorted(run(['sudo','-n','ctr','namespaces','list','--quiet']).splitlines()),
    'containerd_root':configuration.get('root'),'containerd_state':configuration.get('state'),
    'driver':dict(driver).get('driver-type'),
    'live_restore_enabled':json.loads(run(['sudo','-n','docker','info','--format','{{json .LiveRestoreEnabled}}']))
}))
'''


def check_registration(registration):
    require(registration.get('schema') == 'omc-storage-owner-host/1' and
            registration['host_uid'] == 'host:data-01' and registration['source_path'] == SOURCE,
            'Wrong owner scope')
    require(re.fullmatch(r'[a-z_][a-z0-9_-]*@[A-Za-z0-9][A-Za-z0-9.-]*', registration['ssh_target']),
            'Invalid owner SSH target')
    for key in ('target_path', 'target_mount', 'source_device', 'target_device'):
        path = Path(registration[key])
        require(path.is_absolute() and '..' not in path.parts, 'Invalid registered path')
    require(Path(registration['target_path']).is_relative_to(registration['target_mount']) and
            registration['target_path'] != registration['target_mount'], 'Target outside registered volume')
    require(registration['source_device'] != registration['target_device'] and
            registration['pool_uuid'] and registration['bulk_uuid'], 'Missing separate volume identities')


def collect_observation(registration):
    check_registration(registration)
    program = 'import json\nregistration=json.loads(' + repr(json.dumps(registration)) + ')\n' + COLLECT
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                             '-o', 'ConnectTimeout=8', registration['ssh_target'], 'python3 -'],
                            input=program, capture_output=True, text=True, timeout=240)
    require(result.returncode == 0, 'Owner observation failed; no migration attempted')
    require(len(result.stdout) <= 1024 * 1024, 'Owner observation exceeds budget')
    value = json.loads(result.stdout)
    status = json.loads(subprocess.check_output(['storage-guard', 'status'], text=True, timeout=30))
    value['pool'] = status['pool']
    return value


def positive(value, label):
    require(type(value) is int and value > 0, 'Invalid positive bytes: ' + label)
    return value


def protected_states(placement_path, runtime_path):
    result = {}
    graphs = []
    for name, path in [('placement', placement_path), ('runtime', runtime_path)]:
        value = load(path)
        graph = value['graph'] if name == 'placement' else value['semantic_context']['usl_graph']
        require(graph.get('schema') == 'usl-resource-graph/v1', 'Wrong USL graph schema')
        require(graph.get('resources') and graph.get('meanings') and graph.get('links'),
                'Missing semantic graph; an empty graph cannot prove preservation')
        # Keep locators, revisions, participant order, qualifiers and unknown
        # future fields. No semantic whitelist that could silently omit data.
        graphs.append(graph)
        result[name] = {'state_digest': digest(value), 'graph_digest': digest(graph)}
    require(graphs[0] == graphs[1], 'Placement and runtime USL graphs differ')
    return result


def make_plan(observation, protected, registration, now=None):
    check_registration(registration)
    now = time.time() if now is None else now
    require(observation.get('schema') == 'omc-storage-owner-observation/1', 'Unknown observation')
    epoch = observation['epoch']
    require(type(epoch) in (int, float) and math.isfinite(epoch) and 0 <= now - epoch <= 300,
            'Storage observation is stale or from the future')
    pool = observation['pool']
    require(pool['pool_uuid'] == registration['pool_uuid'], 'Unexpected thin pool')
    require(type(pool['epoch']) in (int, float) and math.isfinite(pool['epoch']) and
            0 <= now - pool['epoch'] <= 300, 'Thin-pool observation is stale or from the future')
    size = positive(pool['size_bytes'], 'pool')
    percent = pool['data_percent']
    require(type(percent) in (int, float) and math.isfinite(percent) and 0 <= percent <= 100,
            'Invalid pool percentage')
    source, target = observation['source'], observation['target']
    require(source['host_uid'] == 'host:data-01' and source['path'] == SOURCE,
            'Only the selected data-01 containerd root is supported')
    require(source['mount_target'] == '/' and source['fstype'] == 'ext4' and
            source['device'] == registration['source_device'],
            'Source is no longer the observed SSD root')
    require(target['host_uid'] == source['host_uid'] and target['path'] == registration['target_path'] and
            target['mount_target'] == registration['target_mount'] and target['fstype'] == 'ext4' and
            target['filesystem_uuid'] == registration['bulk_uuid'] and
            target['device'] == registration['target_device'],
            'Target must be the separate local 20TB filesystem, never provider-owned NFS')
    require(target['destination_absent'] is True, 'Destination exists; reconcile instead of overwriting')
    require(target['path_resolves_exactly'] is True, 'Destination traverses an unexpected symlink')
    allocated = positive(source['allocated_bytes'], 'source allocation')
    require(allocated <= size, 'Source allocation exceeds the pool')
    free = positive(target['available_bytes'], 'target available')
    require(free - allocated >= 100 * GIB, '20TB reserve would be violated')
    require(observation['containerd_namespaces'] == ['moby'], 'Unknown containerd consumers')
    require(observation['containerd_root'] == SOURCE and observation['containerd_state'] == '/run/containerd',
            'Effective containerd storage configuration differs')
    require(observation['driver'] == 'io.containerd.snapshotter.v1', 'Unexpected Docker storage driver')
    require(observation['image_ids'] and len(set(observation['image_ids'])) == len(observation['image_ids']),
            'Missing or duplicate image identity inventory')
    containers = observation['containers']
    require(containers and len(containers) <= 128, 'Missing or unbounded container inventory')
    require(len({c['id'] for c in containers}) == len(containers), 'Duplicate container IDs')
    for container in containers:
        require(container['name'] and container['image_id'] and type(container['running']) is bool,
                'Incomplete container identity')
    running = sorted(c['name'] for c in containers if c['running'])
    reasons = ['OWNER_MAINTENANCE_EXECUTION_NOT_PERFORMED', 'COPY_AND_RECOVERY_VERIFICATION_PENDING',
               'REMOTE_GROWTH_ACCOUNTING_NOT_REGISTERED', 'THIN_POOL_RECLAIM_NOT_MEASURED']
    if running:
        reasons.insert(0, 'RUNNING_SERVICES_REQUIRE_MAINTENANCE_DECISION')
    if percent >= 98:
        reasons.insert(0, 'STORAGE_GUARD_EMERGENCY_NO_LARGE_WRITER')
    used = size * percent / 100
    needed = math.ceil(max(0, used - size * .85))
    estimate = max(0, used - allocated) * 100 / size
    result = {
        'schema': 'omc-storage-rebalance-plan/1', 'status': 'NOT_EXECUTABLE',
        'owner': 'gj3447/ORCA_SETTING/storage-toolkit', 'capability': 'omc:placement:capability',
        'observation_digest': digest(observation), 'registration_digest': digest(registration),
        'observed_at_epoch': epoch,
        'protected_states': protected, 'effect': 'PROPOSED_PHYSICAL_BIND_MOUNT_ONLY',
        'logical_path': SOURCE, 'proposed_physical_path': registration['target_path'],
        'preserve': ['USL graph including locators', 'HSWM semantic context and revisions',
                     'container IDs and image IDs', 'all images including rollback versions',
                     'volume and application bind paths', 'UID/GID, mode, ACL, xattr, hardlinks, sparse files'],
        'running_services': running, 'container_count': len(containers),
        'container_identity_digest': digest(sorted(containers, key=lambda row: row['id'])),
        'image_identity_digest': digest(sorted(observation['image_ids'])),
        'observed_pool_percent': percent, 'target_pool_percent': 85,
        'bytes_needed_for_target': needed, 'candidate_allocated_bytes': allocated,
        'estimated_pool_percent_if_all_blocks_reclaimed': estimate,
        'estimated_remaining_bytes': max(0, needed - allocated),
        'estimate_basis': 'du allocation; not exclusive thin blocks; concurrent writes and sharing are unmeasured',
        'actual_reclaimed_bytes': None, 'execution_performed': False, 'reasons': reasons,
        'hswm_execution': 'NOT_PERFORMED',
    }
    result['digest'] = digest(result)
    return result


def compare_protected(before, current):
    require(before['protected_states'] == current, 'Protected USL/HSWM state changed; replan required')
    return {'status': 'UNCHANGED', 'scope': 'selected owner state JSON, including every graph field',
            'canonical_hswm_store_verified': False, 'relocation_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True, help='Explicit private owner transport and volume mapping')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--observation', type=Path)
    mode.add_argument('--collect', action='store_true', help='Read fixed data-01 owner paths over existing SSH')
    parser.add_argument('--placement-state', type=Path, required=True)
    parser.add_argument('--runtime-state', type=Path, required=True)
    parser.add_argument('--verify-before', type=Path,
                        help='Refuse if either selected owner state changed since this plan')
    args = parser.parse_args()
    try:
        protected = protected_states(args.placement_state, args.runtime_state)
        registration = load(args.host)
        observation = collect_observation(registration) if args.collect else load(args.observation)
        require(protected == protected_states(args.placement_state, args.runtime_state),
                'Owner state changed during observation')
        result = make_plan(observation, protected, registration)
        if args.collect:
            # One private plan carries its reproducible owner input. This does
            # not publish private hosts or registrations in a portable graph.
            result['owner_observation'] = observation
        if args.verify_before:
            result['preservation_check'] = compare_protected(load(args.verify_before), protected)
        result.pop('digest')
        result['digest'] = digest(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Refused, KeyError, TypeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
