import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("monitor", Path(__file__).parents[1] / "scripts/monitor.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class MonitorTests(unittest.TestCase):
    def sample(self, epoch=100, tokens=40):
        return {"observed_at_epoch": epoch, "boot_id": "boot", "services": [
            {"uid": "main", "container_id": "container", "container_started_at": "start", "models": [{"root": "model"}],
             "metrics": {"output_tokens": tokens}}]}

    def test_exact_metric_names_do_not_double_count_waiting_reasons(self):
        text = '\n'.join([
            'vllm:num_requests_waiting{engine="0"} 2',
            'vllm:num_requests_waiting_by_reason{reason="capacity"} 2',
            'vllm:request_success_total{finished_reason="stop"} 10',
            'vllm:request_success_total{finished_reason="abort"} 1',
            'vllm:kv_cache_usage_perc{engine="0"} 0.2',
            'vllm:kv_cache_usage_perc{engine="1"} 0.4',
            'vllm:generation_tokens_total 1.5e3',
        ])
        self.assertEqual(m.parse_metrics(text), {"waiting": 2, "finished_requests": 11, "kv_fraction": 0.4, "output_tokens": 1500})

    def test_unavailable_is_not_zero(self):
        for value in ("[N/A]", "NaN", "Inf", "-1", None):
            self.assertIsNone(m.number(value))
        self.assertEqual(m.parse_metrics("vllm:generation_tokens_total NaN"), {})
        self.assertEqual(m.number("0"), 0)

    def test_aliases_are_one_loaded_root(self):
        groups = m.model_groups({"data": [{"id": x, "root": "Qwen/new", "max_model_len": 65536} for x in ["new", "Qwen/new", "old-alias"]]})
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["aliases"]), 3)

    def test_stopped_model_is_inventory_not_ready(self):
        row = m.container_record({"Id": "old", "Name": "/backup", "Config": {"Cmd": ["--model", "Qwen/old", "--api-key", "NEVER_EXPORT"], "Env": ["TOKEN=NEVER_EXPORT"]},
                                  "State": {"Status": "exited", "StartedAt": "old", "Running": False}, "HostConfig": {"Memory": 0}})
        self.assertEqual(row["state"], "exited")
        self.assertIsNone(row["memory_limit_bytes"])
        self.assertNotIn("NEVER_EXPORT", json.dumps(row))

    def test_stale_future_and_boundary(self):
        self.assertEqual(m.status(self.sample(), now=100)["freshness"], "CURRENT")
        self.assertEqual(m.status(self.sample(), now=190)["freshness"], "CURRENT")
        for now in [99, 191]:
            self.assertEqual(m.status(self.sample(), now=now)["freshness"], "STALE_OR_FUTURE")

    def test_rate_and_reset(self):
        previous = self.sample()
        current = self.sample(130, 100)
        m.add_rates(current, previous)
        self.assertEqual(current["services"][0]["output_tokens_per_second"], 2)
        for current in [self.sample(130, 2), self.sample(99, 100), self.sample(300, 100)]:
            m.add_rates(current, previous)
            self.assertIsNone(current["services"][0]["output_tokens_per_second"])

    def test_restarts_or_model_changes_invalidate_rates(self):
        for key, value in [("container_id", "changed"), ("container_id", None), ("container_started_at", "changed"), ("models", [])]:
            current = self.sample(130, 100)
            current["services"][0][key] = value
            m.add_rates(current, self.sample())
            self.assertIsNone(current["services"][0]["output_tokens_per_second"])
        current = self.sample(130, 100)
        current["boot_id"] = "new"
        m.add_rates(current, self.sample())
        self.assertIsNone(current["services"][0]["output_tokens_per_second"])

    def test_retention_and_failed_write_preserve_last_observation(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE samples(id INTEGER PRIMARY KEY, epoch REAL NOT NULL, body TEXT NOT NULL)")
        with patch.object(m, "MAX_ROWS", 3):
            for t in range(6):
                m.save(conn, self.sample(t))
            self.assertEqual(conn.execute("SELECT count(*) FROM samples").fetchone()[0], 3)
            m.save(conn, self.sample(50000))
            self.assertEqual(conn.execute("SELECT count(*) FROM samples").fetchone()[0], 1)
            too_big = self.sample(50030)
            too_big["extra"] = "x" * m.MAX_BYTES
            with self.assertRaises(ValueError):
                m.save(conn, too_big)
            self.assertEqual(m.latest(conn)["observed_at_epoch"], 50000)
        conn.close()

    def test_endpoint_failure_is_partial_and_no_generation_request(self):
        config = {"host_uid": "host:dgx", "services": [{"uid": "main", "container": "vllm", "port": 8000}]}
        with patch.object(m, "hardware", return_value={}), patch.object(m, "gpu", return_value=[]), patch.object(m, "inventory", return_value=[]), patch.object(m, "get", side_effect=OSError("offline")) as get:
            result = m.observe(config, "digest")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["services"][0]["state"], "UNAVAILABLE")
        self.assertEqual(result["services"][0]["metrics"], {})
        self.assertTrue(all(c.args[1] in ["/health", "/v1/models", "/metrics"] for c in get.call_args_list))


if __name__ == "__main__":
    unittest.main()
