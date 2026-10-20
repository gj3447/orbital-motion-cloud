#!/usr/bin/env python3
"""Read-only disk, RAM and thin-pool observation across registered OMC hosts. Python stdlib only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

GIB = 1024 ** 3
MIN_FS_BYTES = GIB
WARN_PCT = 85.0
CRIT_PCT = 95.0
MEM_WARN_PCT = 10.0

# POSIX sh probe sent over stdin; prints one tagged record per line and changes nothing.
PROBE = r"""
df -P -B1 -l -x tmpfs -x devtmpfs -x squashfs -x overlay -x efivarfs 2>/dev/null | awk 'NR > 1 { print "fs", $6, $2, $3, $4 }'
free -b 2>/dev/null | awk '/^Mem:/ { print "mem", $2, $7 } /^Swap:/ { print "swap", $2, $3 }'
if command -v lvs >/dev/null 2>&1; then
  lvs --noheadings --separator ' ' -o vg_name,lv_name,data_percent,metadata_percent -S 'lv_attr=~^t' 2>/dev/null | awk '{ print "thin", $1 "/" $2, $3, $4 }'
fi
printf 'guard %s\n' "$(systemctl --user is-active omc-scratch-guard.timer 2>/dev/null || true)"
"""


def parse(text):
    out = {"filesystems": [], "memory": None, "swap": None, "thin_pools": [], "scratch_guard": None}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        tag, rest = parts[0], parts[1:]
        try:
            if tag == "fs" and len(rest) == 4:
                size, used, avail = (int(x) for x in rest[1:])
                if size >= MIN_FS_BYTES:
                    pct = 100.0 * used / (used + avail) if used + avail else 0.0
                    out["filesystems"].append({"mount": rest[0], "size": size, "avail": avail, "used_pct": round(pct, 1)})
            elif tag == "mem" and len(rest) == 2:
                total, avail = int(rest[0]), int(rest[1])
                out["memory"] = {"total": total, "avail": avail, "avail_pct": round(100.0 * avail / total, 1) if total else 0.0}
            elif tag == "swap" and len(rest) == 2:
                out["swap"] = {"total": int(rest[0]), "used": int(rest[1])}
            elif tag == "thin" and len(rest) == 3:
                out["thin_pools"].append({"pool": rest[0], "data_pct": float(rest[1]), "meta_pct": float(rest[2])})
            elif tag == "guard":
                out["scratch_guard"] = rest[0] if rest else "inactive"
        except ValueError:
            continue
    return out


def assess(obs):
    alerts = []

    def level(pct):
        return "critical" if pct >= CRIT_PCT else "warning" if pct >= WARN_PCT else None

    for fs in obs["filesystems"]:
        if lv := level(fs["used_pct"]):
            alerts.append({"level": lv, "kind": "filesystem", "target": fs["mount"], "used_pct": fs["used_pct"], "avail_gib": round(fs["avail"] / GIB, 1)})
    for pool in obs["thin_pools"]:
        pct = max(pool["data_pct"], pool["meta_pct"])
        if lv := level(pct):
            alerts.append({"level": lv, "kind": "thin_pool", "target": pool["pool"], "used_pct": pct})
    mem = obs["memory"]
    if mem and mem["avail_pct"] < MEM_WARN_PCT:
        alerts.append({"level": "warning", "kind": "memory", "target": "ram", "avail_pct": mem["avail_pct"]})
    return alerts


def observe(host, timeout):
    command = ["sh", "-s"] if host.get("ssh") is None else [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", host["ssh"], "sh -s"]
    started = time.monotonic()
    try:
        result = subprocess.run(command, input=PROBE, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"host": host["name"], "reachable": False, "error": "timeout", "alerts": []}
    if result.returncode != 0 and not result.stdout:
        return {"host": host["name"], "reachable": False, "error": result.stderr.strip()[-200:], "alerts": []}
    obs = parse(result.stdout)
    obs.update(host=host["name"], reachable=True, elapsed_s=round(time.monotonic() - started, 2))
    obs["alerts"] = assess(obs)
    return obs


def collect(args):
    hosts = json.loads(Path(args.hosts).read_text())["hosts"]
    report = {"schema": "omc-fleet-memory/1", "observed_at_epoch": int(time.time()),
              "hosts": [observe(h, args.timeout) for h in hosts]}
    for h in report["hosts"]:
        if not h["reachable"]:
            print(json.dumps({"level": "warning", "kind": "unreachable", "host": h["host"], "error": h["error"]}))
        for alert in h["alerts"]:
            print(json.dumps({"host": h["host"], **alert}))
    if args.state:
        state = Path(args.state)
        state.parent.mkdir(parents=True, exist_ok=True)
        tmp = state.with_suffix(".tmp")
        tmp.write_text(json.dumps(report, indent=1) + "\n")
        os.replace(tmp, state)
    critical = any(a["level"] == "critical" for h in report["hosts"] for a in h["alerts"])
    print(json.dumps({"summary": {h["host"]: len(h["alerts"]) if h["reachable"] else "unreachable" for h in report["hosts"]},
                      "critical": critical}))
    return 3 if critical else 0


def show(args):
    report = json.loads(Path(args.state).read_text())
    age = int(time.time()) - report["observed_at_epoch"]
    print(f"observed {age}s ago")
    for h in report["hosts"]:
        if not h["reachable"]:
            print(f"{h['host']:<14} UNREACHABLE {' '.join(h['error'].split())[:70]}")
            continue
        fs = ", ".join(f"{f['mount']} {f['used_pct']:.0f}%" for f in h["filesystems"])
        thin = ", ".join(f"{p['pool']} {p['data_pct']:.0f}%" for p in h["thin_pools"])
        mem = h["memory"]
        ram = f"RAM {mem['avail'] / GIB:.0f}/{mem['total'] / GIB:.0f}G free" if mem else "RAM ?"
        print(f"{h['host']:<14} {ram}; {fs}" + (f"; thin {thin}" if thin else "") + f"; guard {h['scratch_guard']}")
        for a in h["alerts"]:
            print(f"{'':<14} ! {a['level']} {a['kind']} {a['target']}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect", help="observe every registered host once")
    c.add_argument("--hosts", required=True, help="private omc-fleet-hosts/1 JSON: {\"hosts\": [{\"name\", \"ssh\"}]}; ssh null = local")
    c.add_argument("--state", help="write the latest report atomically to this file")
    c.add_argument("--timeout", type=int, default=30)
    s = sub.add_parser("show", help="print the latest stored report")
    s.add_argument("--state", required=True)
    args = parser.parse_args(argv)
    return collect(args) if args.command == "collect" else show(args)


if __name__ == "__main__":
    sys.exit(main())
