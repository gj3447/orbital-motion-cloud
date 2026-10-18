import json
from pathlib import Path
import sys
import tempfile
import unittest

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


class StorageRebalanceTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
