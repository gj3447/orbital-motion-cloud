#!/usr/bin/env python3
"""Install the first OMC monitor release through the existing fleet DGX transport.

Refuses conflicting existing files. Does not install packages or restart models.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import base64,hashlib,json,os,pathlib,subprocess
os.umask(0o077)
home=pathlib.Path.home()
release=home/".local/share/omc-monitor/releases"/payload["release"]
files={
 str(release/"monitor.py"):payload["script"],
 str(home/".config/omc/monitor.json"):payload["config"],
 str(home/".config/systemd/user/omc-monitor.service"):payload["service"],
 str(home/".config/systemd/user/omc-monitor.timer"):payload["timer"],
}
wrapper=("#!/bin/sh\n# OMC managed DGX monitor\nexec /usr/bin/python3 -B \""+str(release/"monitor.py")+"\" \"$@\"\n").encode()
files[str(home/".local/bin/omc-monitor")]=base64.b64encode(wrapper).decode()
decoded={pathlib.Path(p):base64.b64decode(v) for p,v in files.items()}
for path,data in decoded.items():
 if path.is_symlink() or (path.exists() and path.read_bytes()!=data):
  raise RuntimeError("Refusing conflicting existing file: "+str(path))
for path,data in decoded.items():
 path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 if not path.exists():
  with path.open("xb") as f: f.write(data)
 path.chmod(0o700 if path.name=="omc-monitor" else 0o600)
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True,timeout=40)
 if p.returncode: raise RuntimeError(str(argv)+": "+p.stderr[-2000:])
 return p.stdout
run(["systemd-analyze","--user","verify",str(home/".config/systemd/user/omc-monitor.service"),str(home/".config/systemd/user/omc-monitor.timer")])
observation=json.loads(run([str(home/".local/bin/omc-monitor"),"once","--json"]))
assert observation["status"]=="OK",observation["errors"]
run(["systemctl","--user","daemon-reload"])
run(["systemctl","--user","enable","--now","omc-monitor.timer"])
run(["systemctl","--user","start","omc-monitor.service"])
state=home/".local/state/omc-monitor"
receipt={"status":"INSTALLED","release":payload["release"],"files_sha256":{str(p):hashlib.sha256(d).hexdigest() for p,d in decoded.items()},"initial_observation":observation}
receipt_path=state/("installation-"+payload["release"]+".json")
if not receipt_path.exists(): receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(receipt,ensure_ascii=False))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fleet-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = {"script": "scripts/monitor.py", "config": "deploy/dgx-monitor.example.json",
             "service": "deploy/omc-monitor.service", "timer": "deploy/omc-monitor.timer"}
    payload = {key: base64.b64encode((root / path).read_bytes()).decode() for key, path in paths.items()}
    payload["release"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    code = "payload=" + repr(payload) + "\n" + REMOTE
    # Exclusive local receipt: preserve prior deployment evidence on retries.
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x") as output:
        result = subprocess.run(["python3", str(args.fleet_root / "scripts/fleet.py"), "exec", "dgx", "--", "python3", "-c", code],
                                cwd=args.fleet_root, capture_output=True, text=True, timeout=65)
        if result.returncode:
            json.dump({"status": "FAILED", "exit_code": result.returncode, "stderr": result.stderr[-4000:]}, output, indent=2)
            raise SystemExit(result.returncode)
        receipt = json.loads(result.stdout)
        json.dump(receipt, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"status": receipt["status"], "release": receipt["release"], "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
