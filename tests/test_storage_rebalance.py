import json
from pathlib import Path
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import stat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import storage_rebalance as rebalance


def registration():
    return {'schema':'omc-storage-owner-host/1','host_uid':'host:data-01',
            'ssh_target':'operator@data-01.example','pool_uuid':'fixture-pool','bulk_uuid':'fixture-bulk',
            'source_path':rebalance.SOURCE,'source_device':'/dev/sda1',
            'target_path':'/srv/fixture/containerd','target_mount':'/srv/fixture','target_device':'/dev/sdc2'}


def observation():
    return {
        'schema': 'omc-storage-owner-observation/1', 'epoch': 1000,
        'pool': {'pool_uuid': 'fixture-pool', 'epoch': 1000,
                 'size_bytes': 390070272000, 'data_percent': 97.48},
        'source': {'host_uid': 'host:data-01', 'path': rebalance.SOURCE, 'mount_target': '/',
                   'fstype': 'ext4', 'device': '/dev/sda1', 'allocated_bytes': 34058149888},
        'target': {'host_uid': 'host:data-01', 'path': '/srv/fixture/containerd',
                   'mount_target': '/srv/fixture', 'fstype': 'ext4',
                   'filesystem_uuid': 'fixture-bulk', 'device': '/dev/sdc2',
                   'destination_absent': True, 'path_resolves_exactly': True, 'available_bytes': 19 * 10**12},
        'containerd_namespaces': ['moby'], 'driver': 'io.containerd.snapshotter.v1',
        'containerd_root': rebalance.SOURCE, 'containerd_state': '/run/containerd',
        'image_ids': ['sha256:fixture'],
        'containers': [{'id': 'container:fixture', 'name': 'database', 'image_id': 'sha256:fixture',
                        'running': True}],
    }


def adaptive_inputs(now=1000):
    plan = {'schema': 'storage-adaptive-plan/v1', 'registry_digest': 'a' * 64,
            'semantic_digest': 'b' * 64, 'decisions': [
                {'id': 'storage:archive-a', 'action': 'DEMOTE', 'reason': 'COLD_SEALED_WITH_MEASURED_CAPACITY_BENEFIT',
                 'reclaimable_bytes': 4096, 'seal_digest': 'c' * 64},
                {'id': 'storage:archive-b', 'action': 'KEEP', 'reason': 'ALREADY_ON_BULK'},
            ]}
    context = {'schema': 'storage-agent-context/v1', 'plan': plan, 'expires_epoch': now + 100,
               'allowed_actions': ['RANK_ADMITTED_COLD_IDS', 'DEFER'], 'actor_authority': 'SECONDARY_AI'}
    context['digest'] = rebalance.adaptive_hash(context)
    current = {'schema': 'omc-usl-placement-current/v1', 'status': 'CURRENT', 'stateGeneration': 3,
               'stateDigest': 'sha256:' + '1' * 64, 'semanticDigest': 'sha256:' + '2' * 64,
               'registrationDigest': 'sha256:' + '3' * 64, 'lastOperation': 'placement-fixture',
               'operationDigest': 'sha256:' + '4' * 64, 'resources': [
                   {'resource': 'data:a', 'representation': 'rep-a', 'relation': 'working-copy',
                    'workspace': 'fixture-workspace', 'path': 'archive/a',
                    'contentDigest': 'sha256:' + 'a' * 64, 'contentBytes': 1},
                   {'resource': 'data:b', 'representation': 'rep-b', 'relation': 'working-copy',
                    'workspace': 'fixture-workspace', 'path': 'archive/b',
                    'contentDigest': 'sha256:' + 'b' * 64, 'contentBytes': 2},
               ], 'provenance': {'stateSchema': 'omc-placement-state/1', 'graphSchema': 'usl-resource-graph/v1',
                                  'bindingsSchema': 'usl-resource-bindings/v1',
                                  'ownerImplementationDigest': 'sha256:' + '5' * 64}}
    bindings = {'schema': 'omc-usl-storage-bindings/v1', 'authority': 'EXPLICIT_OWNER_MAPPING',
                'expectedRegistryDigest': plan['registry_digest'], 'expectedSemanticDigest': plan['semantic_digest'],
                'placementExpectation': {'exportDigest': rebalance.digest(current),
                                         'stateGeneration': current['stateGeneration'],
                                         'stateDigest': current['stateDigest'], 'semanticDigest': current['semanticDigest'],
                                         'registrationDigest': current['registrationDigest'],
                                         'ownerImplementationDigest': current['provenance']['ownerImplementationDigest'],
                                         'operationDigest': current['operationDigest'],
                                         'previous': {'stateGeneration': 3, 'stateDigest': current['stateDigest']}},
                'bindings': [
                    {'storageId': 'storage:archive-a', 'uslResourceId': 'data:a', 'uslRepresentationId': 'rep-a'},
                    {'storageId': 'storage:archive-b', 'uslResourceId': 'data:b', 'uslRepresentationId': 'rep-b'},
                ]}
    return context, bindings, current


def native_storage_graph():
    source = {'uid': 'source:fixture', 'sha256': 'a' * 64, 'authority': 'SOURCE_DECLARED'}
    return {'schema': 'storage-adaptive-graph/v1', 'logical_identity_mutation': False,
            'shared_kg_published': False, 'hswm_execution': False, 'sources': [source],
            'nodes': [{'uid': 'storage-policy:fixture', 'type': 'PlacementPolicy', 'authority': 'SOURCE_DECLARED'},
                      {'uid': 'omc:placement:capability', 'type': 'CapabilityReference', 'authority': 'SOURCE_DECLARED'},
                      {'uid': 'storage:fixture:a', 'type': 'Dataset', 'authority': 'SOURCE_DECLARED'},
                      {'uid': 'storage:fixture:b', 'type': 'Dataset', 'authority': 'SOURCE_DECLARED'}],
            'edges': [{'type': 'HOST_ADAPTER_FOR', 'source': 'storage-policy:fixture', 'target': 'omc:placement:capability'},
                      {'type': 'MANAGES', 'source': 'storage-policy:fixture', 'target': 'storage:fixture:a'},
                      {'type': 'MANAGES', 'source': 'storage-policy:fixture', 'target': 'storage:fixture:b'}]}


class StorageRebalanceTests(unittest.TestCase):
    def test_native_registry_projects_real_management_without_placement_or_hoh_identity(self):
        value = rebalance.adaptive_registry_usl_graph(native_storage_graph())
        self.assertEqual(value['status'], 'OBSERVED_NO_EXECUTION')
        self.assertEqual(value['hohRelation'], 'UNRESOLVED_NO_NATIVE_STORAGE_RELATION')
        self.assertEqual(value['execution'], 'NOT_REQUESTED')
        ids = {row['id'] for row in value['graph']['resources']}
        self.assertTrue({'storage:fixture:a', 'storage:fixture:b', 'storage-policy:fixture', 'omc:placement:capability'} <= ids)
        self.assertEqual(sum(row['meaning'] == 'owner-manages-storage-dataset' for row in value['graph']['links']), 2)
        broken = native_storage_graph(); broken['edges'].pop()
        with self.assertRaises(rebalance.Refused): rebalance.adaptive_registry_usl_graph(broken)

    def test_registry_graph_cli_private_output_is_new_and_not_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            source, output = Path(root) / 'native.json', Path(root) / 'private.json'
            source.write_text(json.dumps(native_storage_graph()))
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts' / 'storage_rebalance.py'),
                       'usl-adaptive', '--storage-graph', str(source), '--out', str(output), 'registry-graph']
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(json.loads(output.read_text())['status'], 'OBSERVED_NO_EXECUTION')
            output.write_text('unrelated-owner-content')
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(output.read_text(), 'unrelated-owner-content')
    def test_below_trigger_does_not_mean_pressure_released(self):
        value = observation()
        value['pool']['data_percent'] = 84.55
        plan = rebalance.make_plan(value, {}, registration(), now=1000)
        self.assertEqual(plan['pressure_start_pool_percent'], 85)
        self.assertEqual(plan['target_pool_percent'], 80)
        self.assertEqual(plan['target_comparison'], 'STRICTLY_BELOW')
        self.assertGreater(plan['bytes_needed_for_target'], 17_000_000_000)
        self.assertLess(plan['bytes_needed_for_target'], 18_000_000_000)
        for percent, needed in ((80, 1), (79.99, 0)):
            value['pool']['data_percent'] = percent
            self.assertEqual(rebalance.make_plan(value, {}, registration(), now=1000)
                             ['bytes_needed_for_target'], needed)

    def test_continuity_consent_does_not_permit_quiescing_running_dependencies(self):
        policy = {'schema': 'omc-storage-maintenance-policy/1',
                  'registration_digest': rebalance.digest(registration()),
                  'decision': 'AUTHORIZED_WITHOUT_SERVICE_INTERRUPTION',
                  'source_ref': 'local:operator-decision'}
        for live_restore in (False, True):
            value = observation()
            value['live_restore_enabled'] = live_restore
            value['pool']['data_percent'] = 98.01
            plan = rebalance.make_plan(value, {}, registration(), now=1000, maintenance_policy=policy)
            self.assertEqual(plan['relocation_decision'], 'HOLD_SERVICE_CONTINUITY')
            self.assertEqual(plan['status'], 'NOT_EXECUTABLE')
            self.assertFalse(plan['execution_performed'])
            self.assertIn('SERVICE_CONTINUITY_REQUIRED_NO_FAILOVER_VERIFIED', plan['reasons'])
            self.assertIn('STORAGE_GUARD_EMERGENCY_NO_LARGE_WRITER', plan['reasons'])
            self.assertNotIn('RUNNING_SERVICES_REQUIRE_MAINTENANCE_DECISION', plan['reasons'])
        for change in ({'registration_digest': 'sha256:wrong'}, {'decision': 'AUTHORIZED_STOP'},
                       {'failover_verified': True}, {'source_ref': ''}):
            with self.subTest(change=change), self.assertRaises(rebalance.Refused):
                rebalance.make_plan(value, {}, registration(), now=1000,
                                    maintenance_policy={**policy, **change})

    def test_large_candidate_is_estimate_and_still_requires_maintenance(self):
        plan = rebalance.make_plan(observation(), {}, registration(), now=1000)
        self.assertAlmostEqual(plan['estimated_pool_percent_if_all_blocks_reclaimed'], 88.7487, places=3)
        self.assertGreater(plan['estimated_remaining_bytes'], 14 * 10**9)
        self.assertIsNone(plan['actual_reclaimed_bytes'])
        self.assertFalse(plan['execution_performed'])
        self.assertEqual(plan['status'], 'NOT_EXECUTABLE')
        self.assertIn('RUNNING_SERVICES_REQUIRE_MAINTENANCE_DECISION', plan['reasons'])

    def test_refuses_stale_source_and_pool_independently(self):
        for field in ('source', 'pool'):
            value = observation()
            if field == 'source': value['epoch'] = 699
            else: value['pool']['epoch'] = 699
            with self.subTest(field=field), self.assertRaises(rebalance.Refused):
                rebalance.make_plan(value, {}, registration(), now=1000)

    def test_refuses_provider_nfs_and_same_disk(self):
        for changes in ({'fstype': 'nfs4'}, {'device': '/dev/sda1'}, {'filesystem_uuid': 'wrong'}):
            value = observation(); value['target'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(rebalance.Refused):
                rebalance.make_plan(value, {}, registration(), now=1000)

    def test_refuses_low_capacity_existing_destination_unknown_consumer(self):
        for mutate in (lambda d: d['target'].update(available_bytes=100 * rebalance.GIB),
                       lambda d: d['target'].update(destination_absent=False),
                       lambda d: d.update(containerd_namespaces=['moby', 'k8s.io'])):
            value = observation(); mutate(value)
            with self.assertRaises(rebalance.Refused): rebalance.make_plan(value, {}, registration(), now=1000)

    def test_emergency_not_cleared_by_large_potential_reclaim(self):
        value = observation(); value['pool']['data_percent'] = 98.01
        plan = rebalance.make_plan(value, {}, registration(), now=1000)
        self.assertIn('STORAGE_GUARD_EMERGENCY_NO_LARGE_WRITER', plan['reasons'])

    def test_refuses_parent_symlink_and_different_effective_root(self):
        for mutate in (lambda d: d['target'].update(path_resolves_exactly=False),
                       lambda d: d.update(containerd_root='/other-root')):
            value = observation(); mutate(value)
            with self.assertRaises(rebalance.Refused): rebalance.make_plan(value, {}, registration(), now=1000)

    def test_identity_comparison_catches_nested_hswm_changes(self):
        graph = {'schema': 'usl-resource-graph/v1', 'resources': [{'id': 'a', 'locator': 'file://a'}],
                 'meanings': [{'id': 'meaning', 'description': 'original'}],
                 'links': [{'id': 'link', 'participants': [{'resource': 'a', 'role': 'source'}]}]}
        with tempfile.TemporaryDirectory() as root:
            placement, runtime = Path(root)/'placement.json', Path(root)/'runtime.json'
            placement.write_text(json.dumps({'graph': graph, 'bindings': {'alias': 'unchanged'}}))
            state = {'semantic_context': {'usl_graph': graph, 'hswm_read_set': {'revision': 1}}}
            runtime.write_text(json.dumps(state))
            before = rebalance.protected_states(placement, runtime)
            self.assertEqual(rebalance.compare_protected({'protected_states': before}, before)['status'], 'UNCHANGED')
            state['semantic_context']['hswm_read_set']['revision'] = 2
            runtime.write_text(json.dumps(state))
            with self.assertRaises(rebalance.Refused):
                rebalance.compare_protected({'protected_states': before}, rebalance.protected_states(placement, runtime))
            state['semantic_context']['usl_graph']['links'][0]['participants'][0]['role'] = 'executor'
            runtime.write_text(json.dumps(state))
            with self.assertRaises(rebalance.Refused): rebalance.protected_states(placement, runtime)

    def test_invalid_numeric_observations_fail_closed(self):
        for percent in (True, float('nan'), -1, 101):
            value = observation(); value['pool']['data_percent'] = percent
            with self.subTest(percent=percent), self.assertRaises(rebalance.Refused):
                rebalance.make_plan(value, {}, registration(), now=1000)

    def test_adaptive_context_projects_native_storage_ids_without_a_move(self):
        context, bindings, current = adaptive_inputs()
        value = rebalance.adaptive_usl_graph(context, bindings, current, now=1000)
        self.assertEqual(value['schema'], 'omc-storage-rebalance-usl/v1')
        self.assertEqual(value['status'], 'READY_FOR_OWNER_SUBMIT')
        resources = {row['id']: row for row in value['graph']['resources']}
        self.assertEqual({row for row in resources if row.startswith('storage:')}, {'storage:archive-a', 'storage:archive-b'})
        mappings = [row for row in resources.values() if 'urn:omc:ExplicitOwnerMapping' in row['types']]
        self.assertEqual(len(mappings), 2)
        self.assertEqual({row['metadata']['nativeOmcResourceId'] for row in mappings}, {'data:a', 'data:b'})
        self.assertTrue(all(row['metadata']['storageNativeId'] in {'storage:archive-a', 'storage:archive-b'} for row in mappings))
        self.assertTrue(all(row['locator'].startswith('kg://omc-placement-mapping/') and
                            row['metadata']['locatorStatus'] == 'DECLARED_SYMBOLIC_UNRESOLVED'
                            for row in mappings))
        self.assertTrue(all(row['metadata']['locatorStatus'] == 'DECLARED_SYMBOLIC_UNRESOLVED'
                            for key, row in resources.items() if key.startswith('storage:')))
        mapping_links = [row for row in value['graph']['links'] if row['meaning'] == 'explicit-owner-storage-mapping']
        self.assertEqual(len(mapping_links), 2)
        self.assertTrue(all({item['role'] for item in row['participants']} == {'storage_dataset', 'omc_logical_mapping'}
                            for row in mapping_links))
        tasks = {row['storageId']: row for row in value['tasks']}
        self.assertEqual(tasks['storage:archive-a']['nativeId'], 'storage:archive-a')
        self.assertEqual(tasks['storage:archive-a']['status'], 'READY_FOR_OWNER_SUBMIT')
        self.assertEqual(tasks['storage:archive-b']['status'], 'NOT_READY')
        self.assertEqual(tasks['storage:archive-a']['estimatedReclaimableBytes'], 4096)
        self.assertEqual(tasks['storage:archive-a']['reclaimEstimateBasis'],
                         'storage-tier adaptive plan estimate; physical reclaim is not observed')
        self.assertIsNone(tasks['storage:archive-b']['estimatedReclaimableBytes'])
        self.assertTrue(all(row['execution'] == 'NOT_REQUESTED' for row in value['tasks']))

    def test_adaptive_all_keep_context_is_not_ready_and_does_not_claim_reclaim(self):
        context, bindings, current = adaptive_inputs()
        context['plan']['decisions'][0].update(action='KEEP', reason='ALREADY_ON_BULK')
        context['digest'] = rebalance.adaptive_hash({key: value for key, value in context.items() if key != 'digest'})
        value = rebalance.adaptive_usl_graph(context, bindings, current, now=1000)
        self.assertEqual(value['status'], 'NOT_READY')
        self.assertTrue(all(task['status'] == 'NOT_READY' for task in value['tasks']))
        self.assertTrue(all(task['estimatedReclaimableBytes'] is None for task in value['tasks']))
        self.assertTrue(all(task['execution'] == 'NOT_REQUESTED' for task in value['tasks']))

    def test_adaptive_submit_and_lease_are_only_existing_owner_protocol_payloads(self):
        context, bindings, current = adaptive_inputs()
        proposal = rebalance.adaptive_submit(context, bindings, current, ['data:a'], [], 'omc', 'fixture', 'cold sealed archive', 1050, now=1000)
        self.assertEqual(set(proposal), {'schema', 'context_digest', 'actor', 'model', 'rationale', 'expires_epoch', 'ranked_ids', 'defer_ids'})
        self.assertEqual(proposal['ranked_ids'], ['storage:archive-a'])
        lease = rebalance.adaptive_lease(context, bindings, current, 'data:b', 60, now=1000)
        self.assertEqual(lease['execution'], 'NOT_REQUESTED')
        self.assertEqual(lease['argv'], ['storage-tier', 'adaptive', 'use', 'storage:archive-b', '--pin-seconds', '60'])
        self.assertIn('protective use lease', lease['scope'])
        # storage-tier adaptive use leases any registered dataset. KEEP is a
        # protective pin and does not become a DEMOTE/reclaim admission.
        with self.assertRaises(rebalance.Refused):
            rebalance.adaptive_submit(context, bindings, current, ['data:b'], [], 'omc', 'fixture', 'reason', 1050, now=1000)

    def test_adaptive_bridge_rejects_stale_or_unregistered_identity_and_authority_expansion(self):
        context, bindings, current = adaptive_inputs()
        cases = [
            lambda c, b, p: c.__setitem__('expires_epoch', 999),
            lambda c, b, p: b.__setitem__('expectedRegistryDigest', '0' * 64),
            lambda c, b, p: b.__setitem__('authority', 'CALLER_GRANTED'),
            lambda c, b, p: b.__setitem__('grant', {'write': True}),
            lambda c, b, p: b['bindings'][0].__setitem__('storageId', 'storage:unknown'),
            lambda c, b, p: b['bindings'][1].__setitem__('uslResourceId', 'data:a'),
            lambda c, b, p: p['resources'].pop(),
            lambda c, b, p: p['resources'][0].__setitem__('path', 'tampered-without-envelope-change'),
            lambda c, b, p: b['placementExpectation'].__setitem__('stateDigest', 'sha256:' + '0' * 64),
            lambda c, b, p: b['placementExpectation']['previous'].__setitem__('stateDigest', 'sha256:' + '6' * 64),
            lambda c, b, p: b['placementExpectation']['previous'].__setitem__('stateGeneration', 4),
        ]
        for mutate in cases:
            c, b, p = copy.deepcopy(context), copy.deepcopy(bindings), copy.deepcopy(current)
            mutate(c, b, p)
            if 'digest' in c: c['digest'] = rebalance.adaptive_hash({key: value for key, value in c.items() if key != 'digest'})
            with self.subTest(mutate=mutate), self.assertRaises(rebalance.Refused):
                rebalance.adaptive_usl_graph(c, b, p, now=1000)
        with self.assertRaises(rebalance.Refused):
            rebalance.adaptive_submit(context, bindings, current, ['data:unknown'], [], 'omc', 'fixture', 'reason', 1050, now=1000)
        c, b, p = copy.deepcopy(context), copy.deepcopy(bindings), copy.deepcopy(current)
        c['allowed_actions'] = ['DEFER']
        c['digest'] = rebalance.adaptive_hash({key: value for key, value in c.items() if key != 'digest'})
        with self.assertRaises(rebalance.Refused):
            rebalance.adaptive_submit(c, b, p, ['data:a'], [], 'omc', 'fixture', 'reason', 1050, now=1000)

    def test_adaptive_bridge_refuses_unsealed_demote_and_unsafe_exporter_numbers(self):
        context, bindings, current = adaptive_inputs()
        context['plan']['decisions'][0]['seal_digest'] = 'not-a-seal'
        context['digest'] = rebalance.adaptive_hash({key: value for key, value in context.items() if key != 'digest'})
        with self.assertRaises(rebalance.Refused):
            rebalance.adaptive_usl_graph(context, bindings, current, now=1000)
        context, bindings, current = adaptive_inputs()
        current['resources'][0]['contentBytes'] = 9007199254740992
        with self.assertRaises(rebalance.Refused):
            rebalance.adaptive_usl_graph(context, bindings, current, now=1000)

    def test_adaptive_cli_reads_explicit_files_and_emits_only_a_graph_observation(self):
        context, bindings, current = adaptive_inputs(now=time.time())
        with tempfile.TemporaryDirectory() as root:
            paths = [Path(root) / name for name in ('context.json', 'bindings.json', 'current.json')]
            for path, value in zip(paths, (context, bindings, current)):
                path.write_text(json.dumps(value))
            result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts' / 'storage_rebalance.py'),
                                     'usl-adaptive', '--context', str(paths[0]), '--bindings', str(paths[1]),
                                     '--placement-current', str(paths[2]), 'graph'], text=True, capture_output=True, check=True)
            value = json.loads(result.stdout)
            self.assertEqual(value['execution'], 'NOT_REQUESTED')
            self.assertEqual(value['graph']['schema'], 'usl-resource-graph/v1')

    @unittest.skipUnless(os.environ.get('OMC_USL_RESOURCE_GRAPH_TEST') == '1',
                         'set OMC_USL_RESOURCE_GRAPH_TEST=1 with OMC_USL_ROOT for the opt-in USL adapter check')
    def test_opt_in_usl_resource_graph_adapter_preserves_storage_native_ids(self):
        root = Path(os.environ['OMC_USL_ROOT'])
        self.assertTrue(root.is_absolute() and root.is_dir() and not root.is_symlink() and root.resolve() == root)
        self.assertTrue((root / 'src' / 'integrations' / 'resource-graph.ts').is_file())
        node = shutil.which('node')
        self.assertIsNotNone(node)
        context, bindings, current = adaptive_inputs()
        graph = rebalance.adaptive_usl_graph(context, bindings, current, now=1000)['graph']
        program = '''import { readFileSync } from "node:fs";
import { Either } from "effect";
import { adaptResourceGraph } from "./src/integrations/resource-graph.ts";
const graph = readFileSync(0, "utf8");
const adapted = Either.getOrThrow(adaptResourceGraph(graph, { namespace: "omc.storage.adapter.fixture" }));
const nativeIds = Object.keys(adapted.identities.resources).sort();
const mappings = nativeIds.filter(id => id.startsWith("omc-owner-map-"));
console.log(JSON.stringify({ adapter: adapted.source.adapter, nativeIds, mappingCount: mappings.length }));'''
        result = subprocess.run([node, '--max-old-space-size=64', '--import', 'tsx', '--input-type=module', '-e', program],
                                input=json.dumps(graph), text=True, capture_output=True, cwd=root, timeout=15,
                                env={'PATH': str(Path(node).parent) + ':/usr/bin:/bin', 'TSX_DISABLE_CACHE': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(result.stdout.encode()), 4096)
        output = json.loads(result.stdout)
        self.assertEqual(output['adapter'], 'resource-graph/v1')
        self.assertEqual({item for item in output['nativeIds'] if item.startswith('storage:')},
                         {'storage:archive-a', 'storage:archive-b'})
        self.assertEqual(output['mappingCount'], 2)


if __name__ == '__main__':
    unittest.main()
