import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fleet_memory  # noqa: E402

GIB = 1024 ** 3
SAMPLE = "\n".join([
    f"fs / {930 * GIB} {915 * GIB} {15 * GIB}",
    f"fs /data {3600 * GIB} {2900 * GIB} {700 * GIB}",
    f"fs /boot/efi {400 * 1024 ** 2} {80 * 1024 ** 2} {320 * 1024 ** 2}",
    f"mem {128 * GIB} {6 * GIB}",
    f"swap {8 * GIB} {8 * GIB}",
    "thin pve/data 88.20 3.65",
    "guard active",
    "garbage line",
])


class FleetMemoryTest(unittest.TestCase):
    def test_parse_and_assess(self):
        obs = fleet_memory.parse(SAMPLE)
        self.assertEqual([f["mount"] for f in obs["filesystems"]], ["/", "/data"])
        self.assertEqual(obs["scratch_guard"], "active")
        alerts = {(a["kind"], a["target"]): a["level"] for a in fleet_memory.assess(obs)}
        self.assertEqual(alerts, {("filesystem", "/"): "critical", ("thin_pool", "pve/data"): "warning",
                                  ("memory", "ram"): "warning"})

    def test_collect_local_host_writes_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            hosts = Path(tmp) / "hosts.json"
            hosts.write_text(json.dumps({"hosts": [{"name": "local", "ssh": None}]}))
            state = Path(tmp) / "state" / "fleet.json"
            code = fleet_memory.main(["collect", "--hosts", str(hosts), "--state", str(state)])
            report = json.loads(state.read_text())
            self.assertIn(code, (0, 3))
            self.assertTrue(report["hosts"][0]["reachable"])
            self.assertTrue(report["hosts"][0]["filesystems"])
            self.assertEqual(fleet_memory.main(["show", "--state", str(state)]), 0)


if __name__ == "__main__":
    unittest.main()
