#!/usr/bin/env python3
"""Read a source-pinned apostle module; this is not an agent runtime."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent; REQUIRED=("README.md","AGENTS.md","docs/WHAT_IS.md","docs/HOW_TO.md","APOSTLE_MODULE.json")
def load(): return json.loads((ROOT/"APOSTLE_MODULE.json").read_text(encoding="utf-8"))
def check(d):
 i,p=d.get("identity",{}),d.get("source_pins"); return {"ok":d.get("schema")=="apostle-module/1" and all(isinstance(i.get(k),(str,int)) and i.get(k) not in ("",0) for k in ("stable_entity_uid","slot_uid","position","korean_name","english_name")) and isinstance(p,list) and bool(p) and all((ROOT/x).is_file() for x in REQUIRED),"schema":d.get("schema"),"identity":i,"source_pins":p,"required_files":list(REQUIRED),"manifest_sha256":hashlib.sha256((ROOT/"APOSTLE_MODULE.json").read_bytes()).hexdigest()}
def main():
 c=sys.argv[1] if len(sys.argv)==2 else "";
 if c not in {"identity","show","check"}: raise SystemExit("usage: cli.py identity|show|check")
 d=load();v=d["identity"] if c=="identity" else (check(d) if c=="check" else d);print(json.dumps(v,ensure_ascii=False,sort_keys=True));return 0 if c!="check" or v["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
