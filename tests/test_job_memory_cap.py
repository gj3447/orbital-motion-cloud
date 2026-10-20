import importlib.machinery
import importlib.util
from pathlib import Path
import re
import unittest

PATH = Path(__file__).resolve().parents[1] / "deploy" / "omc-job-memory-cap"
loader = importlib.machinery.SourceFileLoader("job_memory_cap", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
cap = importlib.util.module_from_spec(spec)
loader.exec_module(cap)

DAEMON = "/user.slice/user-1001.slice/user@1001.service/app.slice/orca-daemon-d13139e9-3264.scope"
BOX = "/user.slice/user-1001.slice/user@1001.service/app.slice/omc-jobcap-500-777.scope"
GIB_KIB = 1048576
PROTECT = re.compile(r"pyright|isaacsim|orca-ide")


def proc(pid, ppid, comm, gib=0.0, cgroup=DAEMON, cmdline=None):
    return pid, {"pid": pid, "ppid": ppid, "comm": comm, "anon_kib": int(gib * GIB_KIB),
                 "cgroup": cgroup, "cmdline": cmdline or comm, "start": pid * 10}


def table(*rows):
    return dict(proc(*r) if isinstance(r, tuple) else r for r in rows)


class JobMemoryCapTest(unittest.TestCase):
    def test_boxes_large_agent_job_tree_only(self):
        procs = table(
            (1, 0, "orca-ide", 1, DAEMON, "orca-ide daemon"),
            (10, 1, "bash"), (11, 10, "claude", 0.6),
            (12, 11, "bash"), (13, 12, "timeout"),
            (14, 13, "python", 0.1, DAEMON, "python collect.py"),
            (15, 14, "python", 6.0), (16, 14, "python", 5.0),
            (17, 11, "node", 9.0, DAEMON, "node pyright-langserver --stdio"),
            (18, 12, "python", 2.0, DAEMON, "python small.py"),
            (19, 11, "isaacsim", 20.0, DAEMON, "/srv/sim/envs/isaacsim/bin/isaacsim"),
            (20, 1, "python", 30.0, DAEMON, "python not-under-an-agent.py"),
            (21, 11, "python", 12.0, "/user.slice/user-1001.slice/user@1001.service/app.slice/run-p1.scope"),
        )
        boxes, stragglers = cap.plan(procs, 8 * GIB_KIB, PROTECT)
        self.assertEqual([(root, pids) for root, pids, _ in boxes], [(14, [14, 15, 16])])
        self.assertEqual(stragglers, [])

    def test_small_jobs_and_codex_agents_are_left_alone(self):
        procs = table((30, 1, "codex", 1.2, DAEMON, "/data/kjra/.codex/packages/standalone/codex resume"),
                      (31, 30, "bash"), (32, 31, "python", 7.9))
        self.assertEqual(cap.plan(procs, 8 * GIB_KIB, PROTECT), ([], []))
        procs.update(table((33, 32, "python", 0.2)))
        boxes, _ = cap.plan(procs, 8 * GIB_KIB, PROTECT)
        self.assertEqual([(root, pids) for root, pids, _ in boxes], [(32, [32, 33])])

    def test_children_forked_after_boxing_join_the_same_box(self):
        procs = table((11, 1, "claude"), (500, 11, "python", 9.0, BOX),
                      (501, 500, "python", 4.0, BOX), (502, 500, "python", 0.5), (503, 502, "bash"))
        boxes, stragglers = cap.plan(procs, 8 * GIB_KIB, PROTECT)
        self.assertEqual(boxes, [])
        self.assertEqual(stragglers, [("omc-jobcap-500-777.scope", [502, 503])])

    def test_box_request_caps_memory_without_swap_and_keeps_siblings(self):
        calls = []
        cap.run = calls.append
        unit = cap.box(14, [14, 15], 140, 0, 40 * 1024 ** 3)
        self.assertEqual(unit, "omc-jobcap-14-140.scope")
        args = calls[0]
        self.assertIn("StartTransientUnit", args)
        for name, value in [("MemoryMax", str(40 * 1024 ** 3)), ("MemorySwapMax", "0"),
                            ("OOMPolicy", "continue"), ("Delegate", "true")]:
            self.assertEqual(args[args.index(name) + 2], value)
        self.assertEqual(args[args.index("PIDs") + 2:args.index("PIDs") + 5], ["2", "14", "15"])
        self.assertNotIn("MemoryHigh", args)  # throttling without swap stalls instead of failing


if __name__ == "__main__":
    unittest.main()
