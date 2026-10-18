import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import placement as p


def fixture():
    host = {'host_uid': 'host:dev-01', 'ttl_seconds': 60, 'memory_reserve_bytes': 128,
            'root_reserve_bytes': 800, 'volumes': {
                'bulk20': {'reserve_bytes': 100, 'source': 'volume-a'},
                'backup4': {'reserve_bytes': 100, 'source': 'volume-b'}},
            'assets': [{'resource': 'data:a', 'representation': 'rep_a', 'data_class': 'closed_artifact',
                        'closed': True, 'bytes': 40, 'sha256': 'a' * 64},
                       {'resource': 'data:b', 'representation': 'rep_b', 'data_class': 'research_snapshot',
                        'closed': True, 'bytes': 40, 'sha256': 'b' * 64}]}
    graph = {'schema': 'usl-resource-graph/v1', 'resources': [
        {'id': 'data:a', 'locator': 'file://host/old', 'types': ['urn:test:Data'], 'metadata': {'revision': 'v1'}},
        {'id': 'data:b', 'locator': 'file://host/other', 'types': ['urn:test:Data']}],
        'meanings': [{'id': 'meaning:uses', 'description': 'original meaning'}],
        'links': [{'id': 'link:1', 'meaning': 'meaning:uses', 'participants': [
            {'role': 'input', 'resource': 'data:a'}, {'role': 'consumer', 'resource': 'data:b'}],
            'provenance': {'source': 'data:a'}}]}
    state = {'graph': graph, 'generation': 0}
    obs = {'schema': 'omc-hardware-observation/1', 'observed_at_epoch': 1000, 'host_uid': host['host_uid'],
           'config_digest': p.digest(host), 'boot_id': 'boot1', 'memory': {'available_bound_bytes': 1024},
           'root_available_bytes': 1000, 'guard': {'pool': {'data_percent': 90, 'metadata_percent': 4}},
           'volumes': {a: {'available_bytes': 200, 'available_inodes': 2000,
                          'source': v['source'], 'verified': True} for a, v in host['volumes'].items()}}
    request = {'schema': 'omc-placement-request/1', 'resources': ['data:a', 'data:b'], 'backup': True}
    return host, state, obs, request


def current_state(host, state, generation=0, operation=None):
    host['workspaces'] = {'source': '/registered/source'}
    bindings = {'schema': 'usl-resource-bindings/v1', 'resources': [
        {'id': asset['resource'], 'representations': [{'id': asset['representation'], 'relation': 'working-copy',
         'kind': 'workspace', 'workspace': 'source', 'path': asset['resource'] + '.bin',
         'digest': 'sha256:' + asset['sha256']}]} for asset in host['assets']
    ]}
    return {'schema': 'omc-placement-state/1', 'generation': generation, 'graph': state['graph'], 'bindings': bindings,
            'semantic_digest': p.semantic(state['graph']), 'last_operation': operation}


class PlacementTests(unittest.TestCase):
    def test_current_export_is_stable_committed_locator_contract(self):
        host, state, _, _ = fixture()
        with patch.object(p, 'pin', side_effect=AssertionError('export must not read content')):
            exported = p.current_placement(host, current_state(host, state))
        self.assertEqual(exported['schema'], 'omc-usl-placement-current/v1')
        self.assertEqual(exported['status'], 'CURRENT')
        self.assertEqual(exported['stateGeneration'], 0)
        self.assertEqual(exported['lastOperation'], None)
        self.assertIsNone(exported['operationDigest'])
        self.assertEqual(exported['registrationDigest'], p.digest(host))
        self.assertEqual([row['resource'] for row in exported['resources']], ['data:a', 'data:b'])
        self.assertEqual(exported['resources'][0]['contentDigest'], 'sha256:' + 'a' * 64)
        self.assertEqual(exported['resources'][0]['contentBytes'], 40)
        self.assertRegex(exported['provenance']['ownerImplementationDigest'], r'^sha256:[a-f0-9]{64}$')

    def test_current_export_rejects_semantic_or_binding_mutation(self):
        host, state, _, _ = fixture()
        for mutate in [
            lambda value: value.__setitem__('semantic_digest', 'sha256:' + '0' * 64),
            lambda value: value['bindings']['resources'][0]['representations'][0].__setitem__('workspace', 'unknown'),
            lambda value: value.__setitem__('generation', -1),
        ]:
            with self.subTest(mutate=mutate):
                broken = current_state(host, state)
                mutate(broken)
                with self.assertRaises(p.Refused):
                    p.current_placement(host, broken)

    def test_feasible_batch_preserves_identity_and_source(self):
        h, s, o, r = fixture()
        result = p.make_plan(h, s, o, r, 1005)
        self.assertEqual(result['status'], 'READY')
        self.assertEqual(result['transfer_bytes_upper_bound'], 160)
        self.assertEqual(result['semantic_digest'], p.semantic(s['graph']))
        self.assertTrue(result['source_retained'])
        self.assertEqual(result['space_reclaim_bytes'], 0)
        p.validate_plan(result)

    def test_shared_capacity_is_debited_for_entire_batch(self):
        h, s, o, r = fixture()
        o['volumes']['backup4']['available_bytes'] = 160
        result = p.make_plan(h, s, o, r, 1005)
        self.assertEqual(result['status'], 'NOT_READY')
        self.assertEqual(len(result['placements']), 1)
        with self.assertRaises(p.Refused):
            p.validate_plan(result)

    def test_ram_is_not_added_to_disk(self):
        h, s, o, r = fixture()
        o['memory']['available_bound_bytes'] = 0
        o['volumes']['bulk20']['available_bytes'] = 20 * 1024**4
        with self.assertRaisesRegex(p.Refused, 'memory'):
            p.make_plan(h, s, o, r, 1005)

    def test_stale_and_future_observations_refused(self):
        h, s, o, r = fixture()
        for now in [999, 1061]:
            with self.subTest(now=now), self.assertRaises(p.Refused):
                p.make_plan(h, s, o, r, now)

    def test_wrong_owner_and_config_refused(self):
        h, s, o, r = fixture()
        for field in ['host_uid', 'config_digest']:
            changed = copy.deepcopy(o); changed[field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(p.Refused):
                p.make_plan(h, s, changed, r, 1005)

    def test_wrong_mount_and_unverified_volume_refused(self):
        h, s, o, r = fixture()
        for field, value in [('source', 'other-disk'), ('verified', False)]:
            changed = copy.deepcopy(o); changed['volumes']['bulk20'][field] = value
            with self.subTest(field=field), self.assertRaises(p.Refused):
                p.make_plan(h, s, changed, r, 1005)

    def test_emergency_pool_and_root_refused(self):
        h, s, o, r = fixture()
        changed = copy.deepcopy(o); changed['guard']['pool']['data_percent'] = 98
        with self.assertRaises(p.Refused): p.make_plan(h, s, changed, r, 1005)
        changed = copy.deepcopy(o); changed['root_available_bytes'] = 799
        with self.assertRaises(p.Refused): p.make_plan(h, s, changed, r, 1005)

    def test_ai_cannot_supply_commands_roots_or_pins(self):
        h, s, o, r = fixture()
        for key in ['command', 'root', 'sha256']:
            with self.subTest(key=key), self.assertRaises(p.Refused):
                p.make_plan(h, s, o, {**r, key: 'arbitrary'}, 1005)

    def test_live_and_unclassified_data_excluded(self):
        for data_class in ['sqlite', 'credential', 'unknown']:
            h, s, o, r = fixture()
            h['assets'][0]['data_class'] = data_class; o['config_digest'] = p.digest(h)
            self.assertEqual(p.make_plan(h, s, o, r, 1005)['status'], 'NOT_READY')

    def test_unknown_and_duplicate_resource_refused(self):
        h, s, o, r = fixture()
        for resources in [['missing'], ['data:a', 'data:a']]:
            with self.subTest(resources=resources), self.assertRaises(p.Refused):
                p.make_plan(h, s, o, {**r, 'resources': resources}, 1005)

    def test_locator_only_change_is_accepted(self):
        _, s, _, _ = fixture()
        new = copy.deepcopy(s['graph']); new['resources'][0]['locator'] = 'file://host/new'
        p.invariant(s['graph'], new, {'data:a'})

    def test_unselected_locator_change_refused(self):
        _, s, _, _ = fixture()
        new = copy.deepcopy(s['graph']); new['resources'][1]['locator'] = 'file://host/new'
        with self.assertRaises(p.Refused): p.invariant(s['graph'], new, {'data:a'})

    def test_identity_roles_meanings_provenance_cannot_change(self):
        _, s, _, _ = fixture()
        changes = [lambda g: g['resources'][0].update(id='new-id'),
                   lambda g: g['resources'][0]['metadata'].update(revision='v2'),
                   lambda g: g['meanings'][0].update(description='different'),
                   lambda g: g['links'][0]['participants'][0].update(role='output'),
                   lambda g: g['links'][0].update(provenance={'source': 'data:b'})]
        for i, change in enumerate(changes):
            new = copy.deepcopy(s['graph']); change(new)
            with self.subTest(i=i), self.assertRaises(p.Refused): p.invariant(s['graph'], new, {'data:a'})

    def test_plan_tampering_detected(self):
        h, s, o, r = fixture()
        plan = p.make_plan(h, s, o, r, 1005); plan['placements'][0]['primary'] = 'backup4'
        with self.assertRaises(p.Refused): p.validate_plan(plan)

    def test_traversal_and_absolute_paths_refused(self):
        for path in ['/tmp/file', '../file', 'a/../b', 'a//b', 'a\\b', '']:
            with self.subTest(path=path), self.assertRaises(p.Refused): p.relative(path)

    def test_large_transfer_requires_a_live_managed_lease(self):
        with patch.dict(p.os.environ, {}, clear=True), self.assertRaises(p.Refused):
            p.managed_budget({'transfer_bytes_upper_bound': 101 * 1024**2})
        # A caller cannot qualify merely by naming an arbitrary artifact directory.
        with patch.dict(p.os.environ, {'STORAGE_ARTIFACT_DIR': '/not-managed/artifacts'}), self.assertRaises(p.Refused):
            p.managed_budget({'transfer_bytes_upper_bound': 101 * 1024**2})

    def test_rehashed_understated_copy_budget_refused(self):
        h, s, o, r = fixture()
        plan = p.make_plan(h, s, o, r, 1005)
        plan['transfer_bytes_upper_bound'] = 1
        plan['plan_digest'] = p.digest({k: v for k, v in plan.items() if k != 'plan_digest'})
        with self.assertRaises(p.Refused): p.validate_plan(plan)


class PlacementFilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_same_bytes_pin_and_size_limit(self):
        file = self.root / 'source'; file.write_bytes(b'stored memory')
        self.assertEqual(p.pin(file)['bytes'], 13)
        with self.assertRaises(p.Refused): p.pin(file, limit=4)

    def test_nested_symlink_escape_refused(self):
        owned = self.root / 'owned'; owned.mkdir()
        outside = self.root / 'outside'; outside.mkdir()
        (outside / 'file').write_text('outside')
        (owned / 'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(p.Refused): p.safe_path(owned, 'link/file')

    def test_file_symlink_not_followed(self):
        original = self.root / 'original'; original.write_text('memory')
        symlink = self.root / 'link'; symlink.symlink_to(original)
        with self.assertRaises(OSError): p.pin(symlink)

    def test_fifo_refused_without_blocking(self):
        import os
        fifo = self.root / 'pipe'; os.mkfifo(fifo)
        with self.assertRaises(p.Refused): p.pin(fifo)

    def test_atomic_state_survives_reopen(self):
        path = self.root / 'state.json'
        p.atomic(path, {'generation': 1, 'graph': {'id': 'stable'}})
        p.atomic(path, {'generation': 2, 'graph': {'id': 'stable'}})
        self.assertEqual(p.load(path), {'generation': 2, 'graph': {'id': 'stable'}})

    def test_control_plane_hardlink_alias_is_refused(self):
        import os
        workspace, state = self.root / 'workspace', self.root / 'state'
        workspace.mkdir(); state.mkdir()
        registry, control, alias = self.root / 'host.json', self.root / 'placement.py', workspace / 'artifact'
        registry.write_text('{}'); control.write_text('control'); os.link(control, alias)
        host = {'state_dir': str(state), 'workspaces': {'source': str(workspace)},
                'tool_pins': [{'path': str(control)}],
                'assets': [{'workspace': 'source', 'path': 'artifact'}]}
        with self.assertRaises(p.Refused):
            p.control_plane_assets(host, registry)
        alias.unlink(); alias.write_text('independent artifact')
        p.control_plane_assets(host, registry)

    def test_current_export_nonbootstrap_requires_matching_complete_receipt(self):
        host, raw, _, _ = fixture(); host['state_dir'] = str(self.root)
        state = current_state(host, raw, generation=1, operation='export-one')
        p.atomic(self.root / 'state.json', state)
        with self.assertRaises(p.Refused):
            p.current_placement(host, state)
        receipt = {'schema': 'omc-placement-result/1', 'status': 'COMPLETE', 'operation': 'export-one',
                   'state_digest': p.digest(state), 'semantic_digest_after': state['semantic_digest']}
        p.atomic(self.root / 'operations/export-one/result.json', receipt)
        exported = p.current_placement(host, state)
        self.assertEqual(exported['lastOperation'], 'export-one')
        self.assertEqual(exported['operationDigest'], p.digest(receipt))
        receipt['state_digest'] = 'sha256:' + '0' * 64
        p.atomic(self.root / 'operations/export-one/result.json', receipt)
        with self.assertRaises(p.Refused):
            p.current_placement(host, state)

    def test_completed_operation_never_calls_transport_again(self):
        h, state, obs, request = fixture()
        h['state_dir'] = str(self.root)
        obs['config_digest'] = p.digest(h)
        plan = p.make_plan(h, state, obs, request, 1005)
        current = {**state, 'last_operation': 'one', 'generation': 1}
        result = {'status': 'COMPLETE', 'plan_digest': plan['plan_digest'], 'state_digest': p.digest(current)}
        p.atomic(self.root / 'state.json', current)
        p.atomic(self.root / 'operations/one/intent.json', {'plan_digest': plan['plan_digest']})
        p.atomic(self.root / 'operations/one/result.json', result)
        with patch.object(p, 'command', return_value={'filesystems': [{'fstype': 'ext4'}]}) as command:
            self.assertEqual(p.apply(h, plan, 'one'), result)
            self.assertEqual(command.call_count, 1)  # Only local filesystem qualification.

    def test_recover_receipt_after_state_commit_does_not_reexecute(self):
        h, state, obs, request = fixture(); h['state_dir'] = str(self.root); obs['config_digest'] = p.digest(h)
        plan = p.make_plan(h, state, obs, request, 1005)
        current = {**state, 'last_operation': 'one', 'generation': 1}
        result = {'status': 'COMPLETE', 'plan_digest': plan['plan_digest'], 'state_digest': p.digest(current)}
        p.atomic(self.root / 'state.json', current)
        p.atomic(self.root / 'operations/one/intent.json', {'plan_digest': plan['plan_digest']})
        p.atomic(self.root / 'operations/one/prepared-result.json', result)
        with patch.object(p, 'command', return_value={'filesystems': [{'fstype': 'ext4'}]}), patch.object(p, 'observe', side_effect=AssertionError('must not execute')):
            with self.assertRaises(p.Refused): p.apply(h, plan, 'one')
            self.assertEqual(p.apply(h, plan, 'one', recover=True), result)
        self.assertEqual(p.load(self.root / 'state.json')['generation'], 1)
        self.assertEqual(p.load(self.root / 'operations/one/result.json'), result)

    def test_existing_unknown_operation_needs_explicit_recovery(self):
        h, state, obs, request = fixture(); h['state_dir'] = str(self.root); obs['config_digest'] = p.digest(h)
        plan = p.make_plan(h, state, obs, request, 1005)
        p.atomic(self.root / 'state.json', {**state, 'last_operation': None})
        p.atomic(self.root / 'operations/one/intent.json', {'plan_digest': plan['plan_digest']})
        with patch.object(p, 'command', return_value={'filesystems': [{'fstype': 'ext4'}]}):
            with self.assertRaisesRegex(p.Refused, 'incomplete operation'): p.apply(h, plan, 'one')

    def test_concurrent_writer_refused(self):
        host = {'state_dir': str(self.root)}
        with patch.object(p, 'command', return_value={'filesystems': [{'fstype': 'ext4'}]}):
            with p.locked(host), self.assertRaises(BlockingIOError):
                with p.locked(host): self.fail('Second writer admitted')

    def test_new_key_cannot_hide_an_unresolved_operation(self):
        h, state, obs, request = fixture(); h['state_dir'] = str(self.root); obs['config_digest'] = p.digest(h)
        for committed in (False, True):
            current = {**state, 'last_operation': 'one' if committed else None}
            plan = p.make_plan(h, current, obs, request, 1005)
            p.atomic(self.root / 'state.json', current)
            p.atomic(self.root / 'operations/one/intent.json', {'plan_digest': 'earlier-plan'})
            with self.subTest(committed=committed), patch.object(p, 'command', return_value={'filesystems': [{'fstype': 'ext4'}]}), patch.object(p, 'observe', side_effect=AssertionError('must not start another operation')):
                with self.assertRaisesRegex(p.Refused, 'Unresolved operation one'):
                    p.apply(h, plan, 'new-key')


if __name__ == '__main__':
    unittest.main()
