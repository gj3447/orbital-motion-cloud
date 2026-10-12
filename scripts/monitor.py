#!/usr/bin/env python3
"""Bounded, read-only hardware/model observations for OMC. Python stdlib only."""
import argparse
import csv
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
import urllib.request

GIB = 1024 ** 3
TTL = 90
MAX_ROWS = 1440
MAX_BYTES = 16384
METRICS = {
    "num_requests_running": "running", "num_requests_waiting": "waiting",
    "kv_cache_usage_perc": "kv_fraction", "gpu_cache_usage_perc": "kv_fraction",
    "prompt_tokens_total": "prompt_tokens", "generation_tokens_total": "output_tokens",
    "request_success_total": "finished_requests",
}


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (ValueError, TypeError):
        return None


def run(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=6)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} exit {result.returncode}")
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError("command output exceeds bound")
    return result.stdout


def get(port, path):
    # Fixed loopback path; never follows a server redirect or proxy to another host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(f"http://127.0.0.1:{port}{path}", timeout=2) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("HTTP response exceeds bound")
    return data.decode()


def parse_metrics(text):
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r'vllm:(\w+)(?:\{.*\})?\s+(\S+)(?:\s+\S+)?', line)
        if not match or match[1] not in METRICS:
            continue
        value = number(match[2])
        if value is None:
            continue
        key = METRICS[match[1]]
        # Gauges are summed across engines; KV occupancy uses the busiest engine.
        values[key] = max(values.get(key, 0), value) if key == "kv_fraction" else values.get(key, 0) + value
    return values


def model_groups(data):
    groups = {}
    for model in data.get("data", []):
        root = model.get("root") or model["id"]
        row = groups.setdefault(root, {"root": root, "aliases": [], "max_context": model.get("max_model_len")})
        row["aliases"].append(model["id"])
    return list(groups.values())


def option(argv, key):
    for index, value in enumerate(argv):
        if value == key and index + 1 < len(argv):
            return argv[index + 1]
        if value.startswith(key + "="):
            return value.split("=", 1)[1]
    return None


def container_record(raw):
    config, state, limits = raw["Config"], raw["State"], raw["HostConfig"]
    argv = config.get("Cmd") or []
    model = option(argv, "--model")
    # vLLM's positional `serve MODEL` form.
    if not model and "serve" in argv:
        index = argv.index("serve")
        if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
            model = argv[index + 1]
    if not model:
        return None
    record = {
        "name": raw["Name"].lstrip("/"), "id": raw["Id"],
        "state": state["Status"], "started_at": state["StartedAt"],
        "configured_model": model, "revision": option(argv, "--revision"),
        "memory_limit_bytes": limits.get("Memory") or None,
        "cpu_limit": (limits.get("NanoCpus") or 0) / 1e9 or None,
        "pids_limit": limits.get("PidsLimit"), "memory_current_bytes": None,
    }
    if state.get("Running") and state.get("Pid"):
        try:
            relative = Path(f'/proc/{state["Pid"]}/cgroup').read_text().split("0::", 1)[1].strip()
            base = Path("/sys/fs/cgroup").resolve()
            cgroup = (base / relative.lstrip("/")).resolve()
            if not cgroup.is_relative_to(base):
                raise ValueError("cgroup escaped root")
            record["memory_current_bytes"] = int((cgroup / "memory.current").read_text())
        except (OSError, ValueError, IndexError):
            record["memory_observation"] = "UNAVAILABLE"
    return record


def inventory():
    ids = run(["docker", "ps", "-aq"]).split()
    if len(ids) > 32:
        raise ValueError("Docker inventory exceeds 32 containers")
    if not ids:
        return []
    result = []
    for raw in json.loads(run(["docker", "inspect", *ids])):
        record = container_record(raw)
        if record:
            result.append(record)
    return result


def hardware():
    mem = {line.split(":")[0]: int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()}
    def cpu():
        # guest times are already included in user/nice, so exclude fields 9+.
        return list(map(int, Path("/proc/stat").read_text().splitlines()[0].split()[1:9]))
    before = cpu()
    time.sleep(0.2)
    after = cpu()
    delta = [b - a for a, b in zip(before, after)]
    cpu_percent = 100 * (sum(delta) - delta[3] - delta[4]) / sum(delta) if sum(delta) > 0 else None
    disk = shutil.disk_usage("/")
    return {
        "memory_total_bytes": mem["MemTotal"], "memory_available_bytes": mem["MemAvailable"],
        "memory_unavailable_bytes": mem["MemTotal"] - mem["MemAvailable"],
        "swap_total_bytes": mem["SwapTotal"], "swap_free_bytes": mem["SwapFree"],
        "cpu_percent": cpu_percent, "cpu_sample_seconds": 0.2,
        "disk_total_bytes": disk.total, "disk_available_bytes": disk.free,
        "memory_pressure": Path("/proc/pressure/memory").read_text().strip(),
        "memory_accounting": "Host MemAvailable; container memory overlaps host; GPU memory is not added.",
    }


def gpu():
    fields = "name,uuid,utilization.gpu,memory.total,memory.used,temperature.gpu,power.draw"
    rows = csv.reader(io.StringIO(run(["nvidia-smi", "--query-gpu=" + fields, "--format=csv,noheader,nounits"])))
    result = []
    for row in rows:
        name, uid, util, total, used, temp, power = [x.strip() for x in row]
        result.append({"name": name, "uuid": uid, "utilization_percent": number(util),
                       "memory_total_mib": number(total), "memory_used_mib": number(used),
                       "temperature_c": number(temp), "power_w": number(power),
                       "memory_note": "UNAVAILABLE_AS_DEDICATED_VRAM" if number(total) is None else "DRIVER_REPORTED"})
    return result


def load_config(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    if config.get("schema") != "omc-monitor-host/1" or config.get("host_uid") != "host:dgx":
        raise ValueError("unsupported host registration")
    services = config["services"]
    if not 1 <= len(services) <= 4 or len({s["uid"] for s in services}) != len(services):
        raise ValueError("invalid/duplicate services")
    for service in services:
        if type(service["port"]) is not int or not 1024 <= service["port"] <= 65535:
            raise ValueError("invalid loopback port")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", service["container"]):
            raise ValueError("invalid container registration")
    return config, hashlib.sha256(raw).hexdigest()


def observe(config, digest):
    now = time.time()
    snapshot = {"schema": "omc-runtime-observation/1", "authority": "OBSERVED",
                "host_uid": config["host_uid"], "observed_at_epoch": now,
                "observed_at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
                "ttl_seconds": TTL, "registration_sha256": digest,
                "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                "hardware": {}, "gpus": [], "containers": [], "services": [], "errors": []}
    for key, reader in [("hardware", hardware), ("gpus", gpu), ("containers", inventory)]:
        try:
            snapshot[key] = reader()
        except Exception as error:
            snapshot["errors"].append({"source": key, "error": type(error).__name__})
    containers = {row["name"]: row for row in snapshot["containers"]}
    for registration in config["services"]:
        item = {**registration, "models": [], "metrics": {}, "state": "UNAVAILABLE"}
        container = containers.get(registration["container"])
        item["container_id"] = container["id"] if container else None
        item["container_started_at"] = container["started_at"] if container else None
        try:
            get(item["port"], "/health")
            item["models"] = model_groups(json.loads(get(item["port"], "/v1/models")))
            if not item["models"]:
                raise ValueError("empty model list")
            item["state"] = "READY"
        except Exception as error:
            snapshot["errors"].append({"source": item["uid"] + ":health/models", "error": type(error).__name__})
        try:
            item["metrics"] = parse_metrics(get(item["port"], "/metrics"))
            if not all(k in item["metrics"] for k in ("running", "waiting", "output_tokens")):
                raise ValueError("required metrics unavailable")
        except Exception as error:
            snapshot["errors"].append({"source": item["uid"] + ":metrics", "error": type(error).__name__})
        snapshot["services"].append(item)
    snapshot["status"] = "PARTIAL" if snapshot["errors"] else "OK"
    snapshot["collection_seconds"] = round(time.time() - now, 3)
    snapshot["coverage"] = "Host /proc, NVIDIA driver, Docker --model/serve inventory, registered loopback vLLM endpoints; no cache scan or process-wide AI discovery."
    return snapshot


def rate(current, previous, key):
    a, b = current.get("metrics", {}).get(key), previous.get("metrics", {}).get(key)
    if a is None or b is None or a < b:
        return None
    return a - b


def add_rates(snapshot, previous):
    prior = {s["uid"]: s for s in previous.get("services", [])} if previous else {}
    elapsed = snapshot["observed_at_epoch"] - previous["observed_at_epoch"] if previous else 0
    for service in snapshot["services"]:
        service["output_tokens_per_second"] = None
        old = prior.get(service["uid"])
        if not old or not 0 < elapsed <= TTL or snapshot["boot_id"] != previous["boot_id"]:
            continue
        if not service.get("container_id") or any(service.get(k) != old.get(k) for k in ("container_id", "container_started_at", "models")):
            continue
        delta = rate(service, old, "output_tokens")
        if delta is not None:
            service["output_tokens_per_second"] = delta / elapsed


def status(snapshot, now=None):
    age = (time.time() if now is None else now) - snapshot["observed_at_epoch"]
    return {**snapshot, "age_seconds": round(age, 1), "freshness": "CURRENT" if 0 <= age <= TTL else "STALE_OR_FUTURE"}


def database(state, create=False):
    path = state / "observations.sqlite3"
    if create:
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        connection = sqlite3.connect(path, timeout=2)
        connection.execute("PRAGMA max_page_count=8192")  # 32 MiB at the default 4 KiB page size.
        connection.execute("CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY, epoch REAL NOT NULL, body TEXT NOT NULL)")
        return connection
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)


def latest(connection):
    row = connection.execute("SELECT body FROM samples ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else None


def save(connection, snapshot):
    raw = json.dumps(snapshot, ensure_ascii=False)
    if len(raw.encode()) > MAX_BYTES:
        raise ValueError("snapshot exceeds 16 KiB")
    with connection:
        connection.execute("DELETE FROM samples WHERE epoch < ?", (snapshot["observed_at_epoch"] - 12 * 3600,))
        connection.execute("DELETE FROM samples WHERE id NOT IN (SELECT id FROM samples ORDER BY id DESC LIMIT ?)", (MAX_ROWS - 1,))
        connection.execute("INSERT INTO samples(epoch,body) VALUES (?,?)", (snapshot["observed_at_epoch"], raw))


def collect(config, digest, state):
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / "collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        connection = database(state, create=True)
        try:
            snapshot = observe(config, digest)
            add_rates(snapshot, latest(connection))
            save(connection, snapshot)
            return status(snapshot)
        finally:
            connection.close()


def fmt(value, suffix=""):
    return "?" if value is None else f"{value:.1f}{suffix}"


def display(snapshot):
    hw = snapshot["hardware"]
    def gib(key):
        value = hw.get(key)
        return fmt(value / GIB if value is not None else None, " GiB")
    print(f'OMC / {snapshot["host_uid"]}  {snapshot["observed_at"]}  {snapshot["freshness"]} ({snapshot["age_seconds"]}s) / {snapshot["status"]}')
    print(f'Memory available {gib("memory_available_bytes")} / {gib("memory_total_bytes")} | CPU {fmt(hw.get("cpu_percent"), "%")} | Disk available {gib("disk_available_bytes")}')
    for row in snapshot["gpus"]:
        print(f'GPU {row["name"]}: {fmt(row["utilization_percent"], "%")} | {fmt(row["temperature_c"], " C")} | {fmt(row["power_w"], " W")} | dedicated VRAM {fmt(row["memory_used_mib"], " MiB")}')
    for service in snapshot["services"]:
        metric = service["metrics"]
        names = ", ".join(g["aliases"][0] for g in service["models"]) or "unknown model"
        kv = metric.get("kv_fraction")
        print(f'{service["uid"]}: {names} [{service["state"]}] :{service["port"]}')
        print(f'  running={fmt(metric.get("running"))} waiting={fmt(metric.get("waiting"))} KV={fmt(kv * 100 if kv is not None else None, "%")} | output={fmt(service.get("output_tokens_per_second"), " tok/s")} (sample interval)')
        print(f'  since server start: prompt={fmt(metric.get("prompt_tokens"))} output={fmt(metric.get("output_tokens"))} finished={fmt(metric.get("finished_requests"))}')
    for row in snapshot["containers"]:
        memory = row["memory_current_bytes"]
        limit = row["memory_limit_bytes"]
        print(f'Container {row["name"]}: {row["state"]} | {row["configured_model"]} | cgroup={fmt(memory / GIB if memory is not None else None, " GiB")} / limit={fmt(limit / GIB if limit else None, " GiB")}')
    warnings = [e["source"] + ": " + e["error"] for e in snapshot["errors"]]
    if hw.get("memory_available_bytes", 8 * GIB) < 8 * GIB:
        warnings.append("memory available below 8 GiB")
    if hw.get("disk_available_bytes", 0) < 100 * GIB:
        warnings.append("root disk available below 100 GiB")
    if any(s["metrics"].get("waiting", 0) > 0 for s in snapshot["services"]):
        warnings.append("requests are waiting")
    if warnings:
        print("Attention: " + "; ".join(warnings))
    print("GB10 UMA: host memory and container memory overlap; never add them. '?' means unavailable. No inference requests are sent.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/omc/monitor.json")
    parser.add_argument("--state", type=Path, default=Path.home() / ".local/state/omc-monitor")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("once", "collect", "status", "history", "watch"):
        p = sub.add_parser(command)
        p.add_argument("--json", action="store_true")
        if command == "history":
            p.add_argument("--limit", type=int, default=10)
        if command == "watch":
            p.add_argument("--seconds", type=int, default=3600)
            p.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    os.umask(0o077)
    if args.command == "watch" and not (30 <= args.interval <= 300 and 1 <= args.seconds <= 7200):
        parser.error("watch interval must be 30..300 and seconds 1..7200")
    if args.command == "history" and not 1 <= args.limit <= 100:
        parser.error("history limit must be 1..100")
    config, digest = load_config(args.config)
    if args.command in ("once", "collect"):
        snapshot = status(observe(config, digest)) if args.command == "once" else collect(config, digest, args.state)
        print(json.dumps(snapshot, ensure_ascii=False)) if args.json else display(snapshot)
        return 0 if snapshot["status"] == "OK" else 2
    end = time.monotonic() + getattr(args, "seconds", 0)
    while True:
        connection = database(args.state.resolve())
        try:
            if args.command == "history":
                rows = connection.execute("SELECT body FROM samples ORDER BY id DESC LIMIT ?", (args.limit,)).fetchall()
                records = [status(json.loads(row[0])) for row in rows]
                if args.json:
                    print(json.dumps(records, ensure_ascii=False))
                else:
                    for record in reversed(records):
                        display(record)
                return 0
            snapshot = latest(connection)
        finally:
            connection.close()
        if not snapshot:
            raise ValueError("no observations; start the collector or use once")
        snapshot = status(snapshot)
        if snapshot["registration_sha256"] != digest:
            snapshot["freshness"] = "REGISTRATION_CHANGED"
        if args.command == "watch" and sys.stdout.isatty():
            print("\033[2J\033[H", end="")
        print(json.dumps(snapshot, ensure_ascii=False)) if args.json else display(snapshot)
        if args.command != "watch":
            return 0 if snapshot["freshness"] == "CURRENT" and snapshot["status"] == "OK" else 2
        remaining = end - time.monotonic()
        if remaining <= args.interval:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:
        print(f"omc-monitor: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
