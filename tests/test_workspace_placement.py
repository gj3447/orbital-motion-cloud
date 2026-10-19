import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts import workspace_placement as bridge


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bridge.canonical(value) + b"\n")
    os.chmod(path, 0o600)


def event(txn, workspace, resource, root, owner, semantic):
    value = {
        "schema": "orca-usl-workspace-placement/v1", "status": "PENDING_OMC_RECONCILE",
        "owner": "ORCA_SETTING/storage", "transactionId": txn, "workspace": workspace,
        "relation": "working-copy", "mapping": {"kind": "workspace-root", "logicalRoot": "/logical/root",
        "physicalRoot": str(root), "compatibilityPath": "/logical/root"},
        "resourceId": resource, "sourceIdentity": [1, 2], "semanticContractDigest": semantic,
        "configDigest": "sha256:" + "a" * 64, "registryEvidenceDigest": "sha256:" + "b" * 64,
        "observedAt": "2026-10-19T00:00:00Z",
        "directoryProof": {"kind": "directory-manifest/v1", "manifestSha256": "sha256:" + "c" * 64,
                           "sealDigest": "sha256:" + "d" * 64, "snapshotId": "snapshot-1",
                           "fullRestoreVerifiedAt": "2026-10-19T00:00:00Z"},
        "sourceRetirement": {"status": "NOT_RETIRED"}, "ownerImplementationDigest": owner,
    }
    value["eventDigest"] = bridge.digest(value)
    return value


def pointer(txn, workspace, resource, generation, event_value, owner, semantic, previous=None):
    return {
        "schema": "orca-usl-workspace-current/v1", "ownerImplementationDigest": owner,
        "semanticContractDigest": semantic, "resourceId": resource,
        "workspace": workspace, "generation": generation, "transactionId": txn,
        "eventDigest": event_value["eventDigest"], "previousEventDigest": previous,
        "eventFile": "placement-outbox/" + txn + ".json",
    }


class WorkspacePlacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base = self.root / "physical"; self.base.mkdir()
        self.target = self.base / "destination-a"; self.target.mkdir()
        self.outbox = self.root / "outbox"; (self.outbox / "placement-outbox").mkdir(parents=True)
        self.state = self.root / "state"; self.state.mkdir()
        self.pointer_path = self.root / "current.json"
        self.owner = "sha256:" + "1" * 64
        self.semantic = "sha256:" + "2" * 64
        self.workspace = "tier_root"; self.resource = "storage:closed-a"
        self.txn = "e" * 32
        self.first_event = event(self.txn, self.workspace, self.resource, self.target, self.owner, self.semantic)
        write(self.outbox / "placement-outbox" / (self.txn + ".json"), self.first_event)
        write(self.pointer_path, pointer(self.txn, self.workspace, self.resource, 0, self.first_event, self.owner, self.semantic))
        self.config_path = self.root / "config.json"
        self.config = {"schema": "omc-usl-workspace-host/v1", "stateDir": str(self.state),
                       "currentPointer": str(self.pointer_path), "outboxRoot": str(self.outbox),
                       "workspace": self.workspace, "resourceId": self.resource,
                       "physicalRootBase": str(self.base), "expectedOrcaImplementationDigest": self.owner,
                       "expectedSemanticContractDigest": self.semantic}
        write(self.config_path, self.config)

    def tearDown(self):
        self.temp.cleanup()

    def test_reconcile_and_per_read_resolve_preserve_proof_boundary(self):
        host = bridge.config(self.config_path)
        current = bridge.reconcile(host, 0, None)
        self.assertEqual(set(current), {"schema", "status", "stateGeneration", "stateDigest", "semanticDigest",
                         "registrationDigest", "lastOperation", "operationDigest", "workspace", "resourceId",
                         "physicalRoot", "directoryProof", "pointerGeneration", "pointerDigest", "eventDigest", "provenance"})
        self.assertEqual(current["stateGeneration"], 1)
        self.assertEqual(current["pointerGeneration"], 0)
        self.assertEqual(current["physicalRoot"], str(self.target))
        self.assertEqual(set(current["directoryProof"]), {"digest"})
        self.assertNotEqual(current["directoryProof"]["digest"], self.first_event["directoryProof"]["sealDigest"])
        repeat = bridge.reconcile(host, current["stateGeneration"], current["stateDigest"])
        self.assertEqual(repeat, current)
        self.assertTrue((self.state / "operations" / current["lastOperation"] / "result.json").is_file())

    def test_new_pointer_requires_chain_and_advances_omc_state_independently(self):
        host = bridge.config(self.config_path)
        first = bridge.reconcile(host, 0, None)
        target = self.base / "destination-b"; target.mkdir()
        txn = "f" * 32
        second = event(txn, self.workspace, self.resource, target, self.owner, self.semantic)
        write(self.outbox / "placement-outbox" / (txn + ".json"), second)
        write(self.pointer_path, pointer(txn, self.workspace, self.resource, 1, second, self.owner, self.semantic,
                                         previous=self.first_event["eventDigest"]))
        updated = bridge.reconcile(host, first["stateGeneration"], first["stateDigest"])
        self.assertEqual((updated["stateGeneration"], updated["pointerGeneration"]), (2, 1))
        self.assertEqual(updated["physicalRoot"], str(target))
        self.assertEqual(updated["eventDigest"], second["eventDigest"])

    def test_tamper_fork_and_symlink_are_refused_without_state_mutation(self):
        host = bridge.config(self.config_path)
        first = bridge.reconcile(host, 0, None)
        bad = copy.deepcopy(self.first_event); bad["directoryProof"]["snapshotId"] = "mutated"
        write(self.outbox / "placement-outbox" / (self.txn + ".json"), bad)
        with self.assertRaises(bridge.Refused): bridge.reconcile(host, first["stateGeneration"], first["stateDigest"])
        self.assertEqual(bridge.current(host, bridge.load_state(self.state))["eventDigest"], first["eventDigest"])
        # Restore a valid event but replace the root with a symlink under the allowed base.
        os.unlink(self.outbox / "placement-outbox" / (self.txn + ".json"))
        link = self.base / "symlink-root"; link.symlink_to(self.target, target_is_directory=True)
        bad = event(self.txn, self.workspace, self.resource, link, self.owner, self.semantic)
        write(self.outbox / "placement-outbox" / (self.txn + ".json"), bad)
        with self.assertRaises(bridge.Refused): bridge.reconcile(host, first["stateGeneration"], first["stateDigest"])
        # Same pointer generation with a changed raw pointer is a fork.
        write(self.outbox / "placement-outbox" / (self.txn + ".json"), self.first_event)
        fork = pointer(self.txn, self.workspace, self.resource, 0, self.first_event, self.owner, self.semantic)
        fork["previousEventDigest"] = "sha256:" + "9" * 64
        write(self.pointer_path, fork)
        with self.assertRaises(bridge.Refused): bridge.reconcile(host, first["stateGeneration"], first["stateDigest"])

    def test_stale_callback_and_mapping_mismatch_are_refused(self):
        host = bridge.config(self.config_path)
        current = bridge.reconcile(host, 0, None)
        with self.assertRaises(bridge.Refused): bridge.reconcile(host, 0, None)
        changed = copy.deepcopy(self.config); changed["resourceId"] = "storage:other"
        write(self.config_path, changed)
        changed_host = bridge.config(self.config_path)
        with self.assertRaises(bridge.Refused): bridge.reconcile(changed_host, current["stateGeneration"], current["stateDigest"])

    def test_export_rejects_forged_state_or_replaced_root(self):
        host = bridge.config(self.config_path)
        current = bridge.reconcile(host, 0, None)
        state_path = self.state / "state.json"
        original = state_path.read_bytes()
        forged = json.loads(state_path.read_text()); forged["physicalRoot"] = str(self.base)
        write(state_path, forged)
        with self.assertRaises(bridge.Refused): bridge.current(host, bridge.load_state(self.state))
        # Restore through a fresh fixture state then replace the committed directory inode.
        state_path.write_bytes(original)
        os.rmdir(self.target); self.target.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(bridge.Refused): bridge.current(host, bridge.load_state(self.state))


if __name__ == "__main__":
    unittest.main()
