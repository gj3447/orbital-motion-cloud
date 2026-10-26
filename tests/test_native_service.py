import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('native_service', Path(__file__).parents[1] / 'scripts/native_service.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def registration():
    return {'schema': 'omc/native-service@1', 'uid': 'hoh-main', 'owner': 'gj3447/HOH',
            'release': 'a' * 40, 'architecture': 'x86_64', 'user': 1000, 'group': 1000,
            'cwd': '/srv/hoh/native/app', 'argv': ['/srv/hoh/native/bin/node', '/srv/hoh/native/app/main.js'],
            'environment': {'NODE_ENV': 'production'}, 'environmentFiles': ['/srv/hoh/model.env'],
            'writePaths': ['/data'], 'binds': [{'source': '/srv/hoh/data', 'target': '/data', 'readOnly': False}],
            'resources': {'memoryBytes': 536870912, 'cpuPercent': 100, 'tasks': 128, 'restartBurst': 3},
            'bundleManifest': {'path': '/srv/hoh/native/bundle.json', 'sha256': 'b' * 64}}


class NativeServiceTests(unittest.TestCase):
    def test_owner_budget_and_native_identity_are_preserved(self):
        text = native.unit_text(registration(), 'c' * 64)
        for required in ['MemoryMax=536870912', 'CPUQuota=100%', 'TasksMax=128', 'User=1000',
                         'ProtectSystem=strict', 'NoNewPrivileges=yes', 'KillMode=control-group',
                         'EnvironmentFile=/srv/hoh/model.env', 'BindPaths=/srv/hoh/data:/data']:
            self.assertIn(required, text)
        self.assertNotIn('docker', text)

    def test_owner_file_references_do_not_embed_secret_bytes(self):
        text = native.unit_text(registration(), 'c' * 64)
        self.assertIn('/srv/hoh/model.env', text)
        self.assertNotIn('API_KEY', text)

    def test_rejects_root_unbounded_resources_and_unit_injection(self):
        for key, bad in [('user', 0), ('group', 0), ('uid', '../../docker'), ('uid', 'x\nExecStart=bad'),
                         ('cwd', '/srv/../etc'), ('cwd', '/srv/hoh%h'), ('release', 'latest'),
                         ('architecture', 'unknown')]:
            value = registration(); value[key] = bad
            with self.subTest(key=key, value=bad), self.assertRaises(ValueError):
                native.validate(value)
        for key, bad in [('memoryBytes', 0), ('cpuPercent', 0), ('tasks', 99999), ('restartBurst', 100)]:
            value = registration(); value['resources'][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                native.validate(value)

    def test_rejects_newline_in_environment_and_argv(self):
        for field, payload in [('environment', {'X': 'x\nExecStart=/evil'}),
                               ('argv', ['/usr/bin/node', 'x\nExecStart=/evil'])]:
            value = registration(); value[field] = payload
            with self.subTest(field=field), self.assertRaises(ValueError):
                native.validate(value)

    def test_literal_specifiers_and_variables_in_argv(self):
        value = registration(); value['argv'].append('$HOME %n "literal"')
        text = native.unit_text(value, 'c' * 64)
        self.assertIn('ExecStart=:', text)
        self.assertIn('$HOME %%n \\"literal\\"', text)

    def test_unknown_fields_cannot_silently_change_execution(self):
        value = registration(); value['shell'] = 'sudo anything'
        with self.assertRaises(ValueError):
            native.validate(value)


if __name__ == '__main__':
    unittest.main()
