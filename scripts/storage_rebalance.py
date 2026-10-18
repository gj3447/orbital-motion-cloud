#!/usr/bin/env python3
"""Plan the data-01 containerd relocation; never stop services or move bytes.

The private observation comes from the storage owner. The OMC operator reads
this plan before a maintenance decision. It is not an execution permit, a
canonical HSWM export, or proof of reclaimed thin-pool blocks.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote

from placement import Refused, digest, load, require

GIB = 1024 ** 3
SOURCE = '/var/lib/containerd'
# ORCA_SETTING storage_adaptive.DEFAULT_POLICY: start and release differ.
# This estimate does not replace the owner's root-headroom/hysteresis checks.
POOL_START_PERCENT = 85
POOL_RELEASE_PERCENT = 80

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


def maintenance_decision(policy, registration):
    if policy is None:
        return {'status': 'NOT_RECORDED', 'no_service_interruption': None}
    require(isinstance(policy, dict) and set(policy) == {
        'schema', 'registration_digest', 'decision', 'source_ref'}, 'Invalid maintenance policy fields')
    require(policy['schema'] == 'omc-storage-maintenance-policy/1' and
            policy['decision'] == 'AUTHORIZED_WITHOUT_SERVICE_INTERRUPTION',
            'Unsupported maintenance decision')
    require(policy['registration_digest'] == digest(registration),
            'Maintenance decision belongs to another host registration')
    require(isinstance(policy['source_ref'], str) and 0 < len(policy['source_ref']) <= 512,
            'Missing bounded maintenance decision source')
    # A local record preserves the user's constraint; it grants no executor,
    # failover, storage admission or canonical HSWM authority.
    return {'status': policy['decision'], 'no_service_interruption': True,
            'policy_digest': digest(policy), 'source_ref': policy['source_ref']}


def make_plan(observation, protected, registration, now=None, maintenance_policy=None):
    check_registration(registration)
    maintenance = maintenance_decision(maintenance_policy, registration)
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
        reasons.insert(0, 'SERVICE_CONTINUITY_REQUIRED_NO_FAILOVER_VERIFIED'
                       if maintenance['no_service_interruption'] else
                       'RUNNING_SERVICES_REQUIRE_MAINTENANCE_DECISION')
    if percent >= 98:
        reasons.insert(0, 'STORAGE_GUARD_EMERGENCY_NO_LARGE_WRITER')
    used = size * percent / 100
    # Release requires strictly below 80%, not merely below the 85% trigger.
    needed = max(0, math.floor(used - size * POOL_RELEASE_PERCENT / 100) + 1)
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
        'maintenance': maintenance,
        'relocation_decision': ('HOLD_SERVICE_CONTINUITY'
                                if running and maintenance['no_service_interruption'] else
                                'OWNER_PREFLIGHT_REQUIRED'),
        'container_identity_digest': digest(sorted(containers, key=lambda row: row['id'])),
        'image_identity_digest': digest(sorted(observation['image_ids'])),
        'observed_pool_percent': percent, 'pressure_start_pool_percent': POOL_START_PERCENT,
        'target_pool_percent': POOL_RELEASE_PERCENT, 'target_comparison': 'STRICTLY_BELOW',
        'target_scope': 'pool only; adaptive release also requires owner root-headroom checks',
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


# This adapter deliberately translates only owner-local storage-tier observations.
# It does not open the storage registry, create a placement, or invoke its CLI.
ADAPTIVE_CONTEXT_SCHEMA = 'storage-agent-context/v1'
ADAPTIVE_PLAN_SCHEMA = 'storage-adaptive-plan/v1'
ADAPTIVE_BINDINGS_SCHEMA = 'omc-usl-storage-bindings/v1'
PLACEMENT_CURRENT_SCHEMA = 'omc-usl-placement-current/v1'
ADAPTIVE_GRAPH_SCHEMA = 'storage-adaptive-graph/v1'


def adaptive_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def _text(value, label):
    require(isinstance(value, str) and value, 'Invalid ' + label)
    return value


def _safe_integer(value, label):
    # JSON integers outside this range cannot be represented exactly by a JS
    # USL consumer, so accepting them would weaken a cross-runtime pin.
    require(type(value) is int and 0 <= value <= 9007199254740991, 'Invalid safe integer ' + label)
    return value


def _sha256(value, label):
    require(isinstance(value, str) and re.fullmatch(r'sha256:[a-f0-9]{64}', value) is not None,
            'Invalid OMC placement ' + label)
    return value


def _adaptive_context(value, now):
    require(isinstance(value, dict) and value.get('schema') == ADAPTIVE_CONTEXT_SCHEMA,
            'Unknown adaptive context')
    require(isinstance(value.get('plan'), dict) and value['plan'].get('schema') == ADAPTIVE_PLAN_SCHEMA,
            'Adaptive context lacks a storage-tier plan')
    require(isinstance(value.get('expires_epoch'), (int, float)) and math.isfinite(value['expires_epoch']) and
            now <= value['expires_epoch'], 'Adaptive context expired')
    supplied = value.get('digest')
    require(isinstance(supplied, str) and supplied == adaptive_hash({k: v for k, v in value.items() if k != 'digest'}),
            'Adaptive context digest mismatch')
    plan = value['plan']
    for key in ('registry_digest', 'semantic_digest'):
        require(re.fullmatch(r'[a-f0-9]{64}', plan.get(key, '')) is not None,
                'Adaptive plan has invalid ' + key)
    decisions = plan.get('decisions')
    require(isinstance(decisions, list), 'Adaptive plan decisions missing')
    by_id = {}
    for decision in decisions:
        require(isinstance(decision, dict), 'Invalid adaptive decision')
        storage_id = _text(decision.get('id'), 'storage decision ID')
        require(storage_id.startswith('storage:'), 'Unregistered storage decision ID')
        require(storage_id not in by_id and isinstance(decision.get('action'), str) and
                isinstance(decision.get('reason'), str), 'Duplicate or incomplete adaptive decision')
        if decision['action'] == 'DEMOTE':
            require(re.fullmatch(r'[a-f0-9]{64}', decision.get('seal_digest', '')) is not None,
                    'Admitted DEMOTE lacks a valid storage-tier seal_digest')
        by_id[storage_id] = decision
    return plan, by_id


def _placement_current(value):
    expected = {'schema', 'status', 'stateGeneration', 'stateDigest', 'semanticDigest',
                'registrationDigest', 'lastOperation', 'operationDigest', 'resources', 'provenance'}
    require(isinstance(value, dict) and set(value) == expected and value.get('schema') == PLACEMENT_CURRENT_SCHEMA and
            value.get('status') == 'CURRENT', 'OMC placement current export must have the frozen owner schema')
    _safe_integer(value.get('stateGeneration'), 'generation')
    for key in ('stateDigest', 'semanticDigest', 'registrationDigest'):
        _sha256(value.get(key), key)
    generation = value['stateGeneration']
    if generation == 0:
        require(value['lastOperation'] is None and value['operationDigest'] is None,
                'Bootstrap placement operation fields are invalid')
    else:
        require(isinstance(value['lastOperation'], str) and
                re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', value['lastOperation']) is not None,
                'Committed placement operation is invalid')
        _sha256(value['operationDigest'], 'operationDigest')
    provenance = value.get('provenance')
    require(isinstance(provenance, dict) and set(provenance) == {'stateSchema', 'graphSchema', 'bindingsSchema',
            'ownerImplementationDigest'} and provenance['stateSchema'] == 'omc-placement-state/1' and
            provenance['graphSchema'] == 'usl-resource-graph/v1' and provenance['bindingsSchema'] == 'usl-resource-bindings/v1',
            'OMC placement provenance is invalid')
    _sha256(provenance['ownerImplementationDigest'], 'ownerImplementationDigest')
    rows = value.get('resources')
    require(isinstance(rows, list), 'OMC placement resources missing')
    current = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'resource', 'representation', 'relation', 'workspace', 'path',
                'contentDigest', 'contentBytes'} and row.get('relation') == 'working-copy',
                'Invalid OMC placement resource')
        resource, representation = _text(row.get('resource'), 'OMC resource'), _text(row.get('representation'), 'OMC representation')
        _text(row.get('workspace'), 'OMC workspace')
        _text(row.get('path'), 'OMC path')
        _sha256(row.get('contentDigest'), 'contentDigest')
        _safe_integer(row.get('contentBytes'), 'contentBytes')
        require((resource, representation) not in current, 'Duplicate OMC placement resource')
        current[resource, representation] = row
    return current, value


def _bindings(value, plan, decisions, current, exported):
    require(isinstance(value, dict) and set(value) == {'schema', 'authority', 'expectedRegistryDigest',
            'expectedSemanticDigest', 'placementExpectation', 'bindings'} and value['schema'] == ADAPTIVE_BINDINGS_SCHEMA,
            'Unknown or widened storage binding input')
    require(value['authority'] == 'EXPLICIT_OWNER_MAPPING', 'Storage binding source authority is not owner mapping')
    require(value['expectedRegistryDigest'] == plan['registry_digest'] and
            value['expectedSemanticDigest'] == plan['semantic_digest'], 'Storage binding pin differs from adaptive plan')
    expectation = value['placementExpectation']
    core = {'exportDigest', 'stateGeneration', 'stateDigest', 'semanticDigest', 'registrationDigest',
            'ownerImplementationDigest', 'operationDigest'}
    require(isinstance(expectation, dict) and set(expectation) in (core, core | {'previous'}),
            'Storage binding lacks an exact caller-owned placement expectation')
    _safe_integer(expectation['stateGeneration'], 'expected placement generation')
    for key in ('stateDigest', 'semanticDigest', 'registrationDigest', 'ownerImplementationDigest', 'exportDigest'):
        _sha256(expectation[key], 'expected ' + key)
    if expectation['stateGeneration'] == 0:
        require(expectation['operationDigest'] is None, 'Bootstrap expected operation digest is invalid')
    else:
        _sha256(expectation['operationDigest'], 'expected operationDigest')
    actual = {'stateGeneration': exported['stateGeneration'], 'stateDigest': exported['stateDigest'],
              'semanticDigest': exported['semanticDigest'], 'registrationDigest': exported['registrationDigest'],
              'ownerImplementationDigest': exported['provenance']['ownerImplementationDigest'],
              'operationDigest': exported['operationDigest'], 'exportDigest': digest(exported)}
    require(all(expectation[key] == actual[key] for key in core),
            'Caller placement expectation does not match the trusted exporter document')
    if 'previous' in expectation:
        prior = expectation['previous']
        require(isinstance(prior, dict) and set(prior) == {'stateGeneration', 'stateDigest'},
                'Prior placement checkpoint is invalid')
        _safe_integer(prior['stateGeneration'], 'prior placement generation')
        _sha256(prior['stateDigest'], 'prior stateDigest')
        require(actual['stateGeneration'] >= prior['stateGeneration'] and
                (actual['stateGeneration'] != prior['stateGeneration'] or actual['stateDigest'] == prior['stateDigest']),
                'Placement exporter rollback or fork is not accepted')
    require(isinstance(value['bindings'], list) and value['bindings'], 'Storage bindings missing')
    result = {}
    used_resources, used_representations = set(), set()
    for row in value['bindings']:
        require(isinstance(row, dict) and set(row) == {'storageId', 'uslResourceId', 'uslRepresentationId'},
                'Invalid storage binding row')
        storage_id = _text(row['storageId'], 'storage binding ID')
        resource = _text(row['uslResourceId'], 'USL resource ID')
        representation = _text(row['uslRepresentationId'], 'USL representation ID')
        require(storage_id in decisions, 'Storage binding is not registered in adaptive context')
        require(storage_id not in result and resource not in used_resources and representation not in used_representations,
                'Storage binding would merge independent identities')
        require((resource, representation) in current, 'Storage binding is not registered in current OMC placement')
        result[storage_id] = dict(storageId=storage_id, uslResourceId=resource, uslRepresentationId=representation)
        used_resources.add(resource); used_representations.add(representation)
    return result


def load_adaptive_inputs(context, bindings, placement_current, now=None):
    now = time.time() if now is None else now
    plan, decisions = _adaptive_context(context, now)
    current, exported = _placement_current(placement_current)
    return plan, decisions, _bindings(bindings, plan, decisions, current, exported), current


def adaptive_usl_graph(context, bindings, placement_current, now=None):
    plan, decisions, mapped, _ = load_adaptive_inputs(context, bindings, placement_current, now)
    resources, links, tasks = [], [], []
    for storage_id, mapping in sorted(mapped.items()):
        decision = decisions[storage_id]
        admitted = decision['action'] == 'DEMOTE'
        state = 'READY_FOR_OWNER_SUBMIT' if admitted else 'NOT_READY'
        task = {**mapping, 'nativeId': storage_id, 'status': state, 'action': decision['action'],
                'reason': decision['reason'], 'execution': 'NOT_REQUESTED',
                'estimatedReclaimableBytes': decision.get('reclaimable_bytes') if admitted else None,
                'reclaimEstimateBasis': ('storage-tier adaptive plan estimate; physical reclaim is not observed'
                                         if admitted else None)}
        mapping_id = 'omc-owner-map-' + hashlib.sha256(
            json.dumps([storage_id, mapping['uslResourceId'], mapping['uslRepresentationId']],
                       ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()[:24]
        resources.append({'id': storage_id, 'types': ['urn:omc:StorageTierDataset'],
                          # The native storage ID stays the resource ID.  This is
                          # a scoped storage-tier locator, not a claim that an
                          # OMC asset and a storage dataset share an identity.
                          'locator': 'kg://storage-tier/' + quote(storage_id, safe=''),
                          'metadata': {'uslResourceId': mapping['uslResourceId'],
                                       'uslRepresentationId': mapping['uslRepresentationId'],
                                       'registryDigest': plan['registry_digest'],
                                       'semanticDigest': plan['semantic_digest'],
                                       'status': state, 'action': decision['action'], 'reason': decision['reason'],
                                       'locatorStatus': 'DECLARED_SYMBOLIC_UNRESOLVED'}})
        # This node names the owner-declared logical OMC mapping.  It is
        # deliberately distinct from the storage native ID and never asserts
        # same-as, a shared registration, or a physical path.
        resources.append({'id': mapping_id, 'types': ['urn:omc:ExplicitOwnerMapping'],
                          'locator': 'kg://omc-placement-mapping/' + quote(mapping_id, safe=''),
                          'metadata': {'authority': 'EXPLICIT_OWNER_MAPPING',
                                       'nativeOmcResourceId': mapping['uslResourceId'],
                                       'nativeOmcRepresentationId': mapping['uslRepresentationId'],
                                       'storageNativeId': storage_id,
                                       'locatorStatus': 'DECLARED_SYMBOLIC_UNRESOLVED'}})
        links.append({'id': 'storage-task-' + hashlib.sha256(storage_id.encode()).hexdigest()[:24],
                      'meaning': 'storage-tier-candidate', 'participants': [{'role': 'dataset', 'resource': storage_id}],
                      'metadata': {'status': state, 'action': decision['action'], 'reason': decision['reason']}})
        links.append({'id': 'owner-storage-map-' + hashlib.sha256(mapping_id.encode()).hexdigest()[:24],
                      'meaning': 'explicit-owner-storage-mapping', 'participants': [
                          {'role': 'storage_dataset', 'resource': storage_id},
                          {'role': 'omc_logical_mapping', 'resource': mapping_id},
                      ], 'metadata': {'authority': 'EXPLICIT_OWNER_MAPPING', 'execution': 'NOT_REQUESTED'}})
        tasks.append(task)
    overall = 'READY_FOR_OWNER_SUBMIT' if any(task['status'] == 'READY_FOR_OWNER_SUBMIT' for task in tasks) else 'NOT_READY'
    return {'schema': 'omc-storage-rebalance-usl/v1', 'status': overall, 'execution': 'NOT_REQUESTED',
            'contextDigest': context['digest'], 'expiresEpoch': context['expires_epoch'],
            'registryDigest': plan['registry_digest'], 'semanticDigest': plan['semantic_digest'],
            'graph': {'schema': 'usl-resource-graph/v1', 'resources': resources,
                      'meanings': [
                          {'id': 'storage-tier-candidate', 'description': 'Owner storage-tier candidate observation'},
                          {'id': 'explicit-owner-storage-mapping',
                           'description': 'Explicit owner mapping between separate storage and OMC logical identities'},
                      ],
                      'links': links}, 'tasks': tasks}


def adaptive_registry_usl_graph(value):
    """Project only the storage owner's proven management edges; no mover call."""
    require(isinstance(value, dict) and value.get('schema') == ADAPTIVE_GRAPH_SCHEMA and
            value.get('logical_identity_mutation') is False and value.get('shared_kg_published') is False and
            value.get('hswm_execution') is False, 'Native storage graph is not a read-only identity-preserving export')
    nodes, edges, sources = value.get('nodes'), value.get('edges'), value.get('sources')
    require(all(isinstance(x, list) for x in (nodes, edges, sources)), 'Native storage graph fields missing')
    by_uid = {node.get('uid'): node for node in nodes if isinstance(node, dict) and isinstance(node.get('uid'), str)}
    require(len(by_uid) == len(nodes), 'Native storage graph duplicate node')
    capability = by_uid.get('omc:placement:capability')
    require(isinstance(capability, dict) and capability.get('type') == 'CapabilityReference', 'OMC capability missing')
    policies = {edge.get('source') for edge in edges if isinstance(edge, dict) and edge.get('type') == 'HOST_ADAPTER_FOR' and edge.get('target') == capability['uid']}
    require(len(policies) == 1 and by_uid.get(next(iter(policies)), {}).get('type') == 'PlacementPolicy', 'Storage policy lacks OMC owner adapter')
    policy = next(iter(policies))
    datasets = sorted(node['uid'] for node in nodes if node.get('type') == 'Dataset' and node.get('authority') == 'SOURCE_DECLARED')
    managed = {edge.get('target') for edge in edges if isinstance(edge, dict) and edge.get('type') == 'MANAGES' and edge.get('source') == policy}
    require(datasets and set(datasets) == managed, 'Storage datasets are not exactly owner-managed by the OMC adapter policy')
    source_digest = digest(value)
    symbolic = 'DECLARED_SYMBOLIC_UNRESOLVED'
    resources = [
        {'id': policy, 'types': ['urn:omc:StoragePolicy'], 'locator': 'kg://storage-tier-policy/' + quote(policy, safe=''), 'metadata': {'locatorStatus': symbolic, 'authority': 'SOURCE_DECLARED'}},
        {'id': capability['uid'], 'types': ['urn:omc:PlacementCapability'], 'locator': 'kg://omc-placement/capability', 'metadata': {'locatorStatus': symbolic, 'authority': 'SOURCE_DECLARED'}},
    ]
    links = [{'id': 'storage-policy-omc-capability', 'meaning': 'owner-provides-omc-placement-capability', 'participants': [{'role': 'policy', 'resource': policy}, {'role': 'capability', 'resource': capability['uid']}], 'metadata': {'authority': 'SOURCE_DECLARED', 'execution': 'NOT_REQUESTED'}}]
    for storage_id in datasets:
        resources.append({'id': storage_id, 'types': ['urn:omc:StorageTierDataset'], 'locator': 'kg://storage-tier/' + quote(storage_id, safe=''), 'metadata': {'locatorStatus': symbolic, 'authority': 'SOURCE_DECLARED', 'nativeId': storage_id}})
        links.append({'id': 'storage-managed-' + hashlib.sha256(storage_id.encode()).hexdigest()[:24], 'meaning': 'owner-manages-storage-dataset', 'participants': [{'role': 'policy', 'resource': policy}, {'role': 'dataset', 'resource': storage_id}], 'metadata': {'authority': 'SOURCE_DECLARED', 'execution': 'NOT_REQUESTED'}})
    return {'schema': 'omc-storage-registry-usl/v1', 'status': 'OBSERVED_NO_EXECUTION', 'execution': 'NOT_REQUESTED', 'sourceDigest': source_digest, 'hohRelation': 'UNRESOLVED_NO_NATIVE_STORAGE_RELATION', 'graph': {'schema': 'usl-resource-graph/v1', 'resources': resources, 'meanings': [{'id': 'owner-provides-omc-placement-capability', 'description': 'Owner storage policy provides the declared OMC placement capability'}, {'id': 'owner-manages-storage-dataset', 'description': 'Owner storage policy manages the declared storage dataset'}], 'links': links}}


def adaptive_submit(context, bindings, placement_current, ranked_resources, deferred_resources,
                    actor, model, rationale, expires_epoch, now=None):
    now = time.time() if now is None else now
    _, decisions, mapped, _ = load_adaptive_inputs(context, bindings, placement_current, now)
    require(context.get('actor_authority') == 'SECONDARY_AI' and
            context.get('allowed_actions') == ['RANK_ADMITTED_COLD_IDS', 'DEFER'],
            'Adaptive context does not grant the existing ranked/deferred proposal capability')
    require(all(isinstance(items, list) for items in (ranked_resources, deferred_resources)), 'Selected resources must be arrays')
    selected = ranked_resources + deferred_resources
    require(all(isinstance(item, str) for item in selected) and len(selected) == len(set(selected)),
            'Duplicate or invalid selected USL resource')
    by_resource = {row['uslResourceId']: storage_id for storage_id, row in mapped.items()}
    require(set(selected) <= set(by_resource), 'USL selected resource is not explicitly mapped')
    storage_ranked = [by_resource[item] for item in ranked_resources]
    storage_deferred = [by_resource[item] for item in deferred_resources]
    admitted = {storage_id for storage_id, decision in decisions.items() if decision['action'] == 'DEMOTE'}
    require(set(storage_ranked + storage_deferred) <= admitted, 'Selected resource is not an admitted adaptive candidate')
    for label, value in [('actor', actor), ('model', model), ('rationale', rationale)]:
        require(isinstance(value, str) and 0 < len(value) <= 4000, 'Invalid ' + label)
    require(isinstance(expires_epoch, (int, float)) and math.isfinite(expires_epoch) and
            now <= expires_epoch <= context['expires_epoch'], 'Submit expiry is outside adaptive context')
    return {'schema': 'storage-agent-proposal/v1', 'context_digest': context['digest'], 'actor': actor,
            'model': model, 'rationale': rationale, 'expires_epoch': expires_epoch,
            'ranked_ids': storage_ranked, 'defer_ids': storage_deferred}


def adaptive_lease(context, bindings, placement_current, selected_resource, pin_seconds, now=None):
    _, _, mapped, _ = load_adaptive_inputs(context, bindings, placement_current, now)
    require(isinstance(selected_resource, str), 'Invalid selected USL resource')
    matches = [row for row in mapped.values() if row['uslResourceId'] == selected_resource]
    require(len(matches) == 1, 'USL selected resource is not explicitly mapped')
    require(isinstance(pin_seconds, int) and 1 <= pin_seconds <= 86400, 'Lease must be 1..86400 seconds')
    row = matches[0]
    return {'schema': 'omc-storage-rebalance-lease-proposal/v1', 'status': 'NOT_REQUESTED',
            'execution': 'NOT_REQUESTED', 'storageId': row['storageId'], 'uslResourceId': selected_resource,
            'uslRepresentationId': row['uslRepresentationId'],
            'scope': 'REGISTERED_MAPPED_RESOURCE_ONLY; protective use lease, not relocation admission or reclaim proof',
            'argv': ['storage-tier', 'adaptive', 'use', row['storageId'], '--pin-seconds', str(pin_seconds)]}


def adaptive_main(argv):
    parser = argparse.ArgumentParser(description='Translate pinned owner storage-tier observations without moving data.')
    parser.add_argument('--context', type=Path)
    parser.add_argument('--bindings', type=Path)
    parser.add_argument('--placement-current', type=Path)
    parser.add_argument('--storage-graph', type=Path)
    parser.add_argument('--out', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('graph')
    submit = sub.add_parser('submit')
    submit.add_argument('--ranked-resource', action='append', default=[])
    submit.add_argument('--defer-resource', action='append', default=[])
    submit.add_argument('--actor', required=True); submit.add_argument('--model', required=True)
    submit.add_argument('--rationale', required=True); submit.add_argument('--expires-epoch', type=float, required=True)
    lease = sub.add_parser('lease')
    lease.add_argument('--resource', required=True); lease.add_argument('--pin-seconds', type=int, default=3600)
    sub.add_parser('registry-graph')
    args = parser.parse_args(argv)
    try:
        if args.command == 'registry-graph':
            require(args.storage_graph is not None, '--storage-graph is required for registry-graph')
            result = adaptive_registry_usl_graph(load(args.storage_graph))
        else:
            require(all(item is not None for item in (args.context, args.bindings, args.placement_current)), 'context, bindings and placement-current are required')
            context, bindings, current = load(args.context), load(args.bindings), load(args.placement_current)
            if args.command == 'graph': result = adaptive_usl_graph(context, bindings, current)
            elif args.command == 'submit': result = adaptive_submit(context, bindings, current, args.ranked_resource,
            args.defer_resource, args.actor, args.model, args.rationale, args.expires_epoch)
            else: result = adaptive_lease(context, bindings, current, args.resource, args.pin_seconds)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (Refused, KeyError, TypeError, ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')


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
    parser.add_argument('--maintenance-policy', type=Path,
                        help='Private recorded user constraint; never an execution or failover permit')
    args = parser.parse_args()
    try:
        protected = protected_states(args.placement_state, args.runtime_state)
        registration = load(args.host)
        observation = collect_observation(registration) if args.collect else load(args.observation)
        require(protected == protected_states(args.placement_state, args.runtime_state),
                'Owner state changed during observation')
        policy = load(args.maintenance_policy) if args.maintenance_policy else None
        result = make_plan(observation, protected, registration, maintenance_policy=policy)
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
    if len(sys.argv) > 1 and sys.argv[1] == 'usl-adaptive':
        raise SystemExit(adaptive_main(sys.argv[2:]))
    main()
