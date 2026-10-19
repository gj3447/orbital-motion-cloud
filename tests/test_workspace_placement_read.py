import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from scripts import workspace_placement as bridge
from tests.test_workspace_placement import event, pointer, write


ROOT = Path(__file__).resolve().parents[1]
USL = ROOT.parent / "USL"
NODE = shutil.which("node")


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_digest():
    result = subprocess.run([NODE, str(ROOT / "scripts" / "workspace_placement_read.mjs"), "--runtime-digest",
                             "--usl-repository", str(USL)], text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


@unittest.skipUnless(NODE and (USL / "node_modules" / "tsx").is_dir(), "USL tsx runtime unavailable")
class WorkspacePlacementReadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base = self.root / "physical"; self.base.mkdir()
        self.target_a = self.base / "destination-a"; self.target_a.mkdir()
        self.target_b = self.base / "destination-b"; self.target_b.mkdir()
        self.payload_a = b"closed workspace payload a\n"
        # A relocation changes the physical root, never the registered child
        # content pin.  The same closed bytes prove the new root is consumed.
        self.payload_b = self.payload_a
        (self.target_a / "policy.json").write_bytes(self.payload_a)
        (self.target_b / "policy.json").write_bytes(self.payload_b)
        self.outbox = self.root / "adaptive"; (self.outbox / "placement-outbox").mkdir(parents=True)
        self.state = self.root / "state"; self.state.mkdir()
        self.pointer_path = self.root / "current.json"
        self.owner = "sha256:" + "1" * 64
        self.semantic = "sha256:" + "2" * 64
        self.workspace, self.owner_resource = "tier_root", "storage:workspace-fixture"
        self.txn_a = "a" * 32
        self.event_a = event(self.txn_a, self.workspace, self.owner_resource, self.target_a, self.owner, self.semantic)
        write(self.outbox / "placement-outbox" / (self.txn_a + ".json"), self.event_a)
        write(self.pointer_path, pointer(self.txn_a, self.workspace, self.owner_resource, 0, self.event_a, self.owner, self.semantic))
        self.registration = self.root / "read-registration.json"
        self.write_registration(self.payload_a)
        self.config_path = self.root / "host.json"
        self.write_config()

    def tearDown(self):
        self.temp.cleanup()

    def write_registration(self, payload):
        document = {
            "schema": "omc-usl-workspace-read-registration/v1",
            "bindings": {"schema": "usl-resource-bindings/v1", "resources": [{
                "id": "usl:fixture-child", "representations": [{
                    "id": "fixture_policy", "relation": "working-copy", "kind": "workspace",
                    "workspace": self.workspace, "path": "policy.json",
                    "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                }],
            }]},
            "selection": {"resource": "usl:fixture-child", "representation": "fixture_policy"},
            "allowedRoots": [str(self.base)], "maxBytes": 1024,
        }
        write(self.registration, document)

    def write_config(self):
        config = {"schema": "omc-usl-workspace-host/v1", "stateDir": str(self.state),
                  "currentPointer": str(self.pointer_path), "outboxRoot": str(self.outbox),
                  "workspace": self.workspace, "resourceId": self.owner_resource,
                  "physicalRootBase": str(self.base), "expectedOrcaImplementationDigest": self.owner,
                  "expectedSemanticContractDigest": self.semantic,
                  "read": {"registration": str(self.registration), "registrationDigest": sha(self.registration),
                           "uslRepository": str(USL), "uslRuntimeDigest": runtime_digest(),
                           "adapterDigest": sha(ROOT / "scripts" / "workspace_placement_read.mjs"),
                           "nodeRuntime": subprocess.run([NODE, "--version"], text=True, capture_output=True, check=True).stdout.strip(),
                           "ownerResourceId": self.owner_resource}}
        write(self.config_path, config)

    def read(self):
        return subprocess.run([NODE, "--import", "tsx", str(ROOT / "scripts" / "workspace_placement_read.mjs"),
                               "--config", str(self.config_path)], cwd=USL, text=True, capture_output=True,
                              env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}, timeout=30)

    def test_per_read_refreshes_two_generations_and_refuses_tamper_or_rollback(self):
        registered_config = self.config_path.read_bytes()
        registered_bindings = self.registration.read_bytes()
        first = self.read()
        self.assertEqual(first.returncode, 0, first.stderr)
        first_value = json.loads(first.stdout)
        self.assertEqual((first_value["status"], first_value["contentBytes"], first_value["checkpoint"]["stateGeneration"]),
                         ("PASS", len(self.payload_a), 1))

        txn_b = "b" * 32
        event_b = event(txn_b, self.workspace, self.owner_resource, self.target_b, self.owner, self.semantic)
        write(self.outbox / "placement-outbox" / (txn_b + ".json"), event_b)
        write(self.pointer_path, pointer(txn_b, self.workspace, self.owner_resource, 1, event_b, self.owner, self.semantic,
                                         previous=self.event_a["eventDigest"]))
        second = self.read()
        self.assertEqual(second.returncode, 0, second.stderr)
        second_value = json.loads(second.stdout)
        self.assertEqual((second_value["status"], second_value["contentBytes"], second_value["checkpoint"]["stateGeneration"]),
                         ("PASS", len(self.payload_b), 2))
        self.assertEqual(self.config_path.read_bytes(), registered_config)
        self.assertEqual(self.registration.read_bytes(), registered_bindings)

        self.registration.write_text("{}\n")
        tampered = self.read()
        self.assertNotEqual(tampered.returncode, 0)
        self.write_registration(self.payload_b); self.write_config()
        write(self.pointer_path, pointer(self.txn_a, self.workspace, self.owner_resource, 0, self.event_a, self.owner, self.semantic))
        stale = self.read()
        self.assertEqual(stale.returncode, 0, stale.stderr)
        self.assertEqual(json.loads(stale.stdout), {"status": "HOLD", "reason": "OWNER_CURRENT_UNAVAILABLE"})


if __name__ == "__main__":
    unittest.main()
