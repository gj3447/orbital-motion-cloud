#!/usr/bin/env python3
"""Read a source-pinned apostle module; this is not an agent runtime."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent; REQUIRED=("README.md","AGENTS.md","docs/WHAT_IS.md","docs/HOW_TO.md","APOSTLE_MODULE.json")
def load(): return json.loads((ROOT/"APOSTLE_MODULE.json").read_text(encoding="utf-8"))
def check(d):
 i,p=d.get("identity",{}),d.get("source_pins"); return {"ok":d.get("schema")=="apostle-module/1" and all(isinstance(i.get(k),(str,int)) and i.get(k) not in ("",0) for k in ("stable_entity_uid","slot_uid","position","korean_name","english_name")) and isinstance(p,list) and bool(p) and all((ROOT/x).is_file() for x in REQUIRED),"schema":d.get("schema"),"identity":i,"source_pins":p,"required_files":list(REQUIRED),"manifest_sha256":hashlib.sha256((ROOT/"APOSTLE_MODULE.json").read_bytes()).hexdigest()}
def strict(d):
 i=d.get("identity",{});p=i.get("position"); pins=d.get("source_pins",[]); role=d.get("runtime_role",{}); return isinstance(p,int) and 1<=p<=12 and i.get("slot_uid")==f"metahumotonic:apostle-slot:{p:02d}" and all(isinstance(i.get(k),str) and i[k] for k in ("stable_entity_uid","korean_name","english_name")) and isinstance(pins,list) and bool(pins) and all(isinstance(x,dict) and re.fullmatch(r"[0-9a-f]{64}",x.get("dashboard_snapshot",{}).get("sha256","")) and re.fullmatch(r"[0-9a-f]{40}",x.get("original_source",{}).get("revision","")) and all(isinstance(x.get("original_source",{}).get(k),str) and x["original_source"][k] for k in ("owner","repository","path")) for x in pins) and ((role.get("state")=="UNASSIGNED" and role.get("label") is None and role.get("authority")=="UNASSIGNED") or (role.get("state")=="USER_ASSIGNED" and isinstance(role.get("label"),str) and role.get("authority")=="USER_PRIMARY"))
def main():
 c=sys.argv[1] if len(sys.argv)==2 else "";
 if c not in {"identity","show","check"}: raise SystemExit("usage: cli.py identity|show|check")
 d=load();v=d["identity"] if c=="identity" else (check(d) if c=="check" else d);v.update({"ok":bool(v["ok"] and strict(d)),"pin_verification":"PIN_METADATA_ONLY"}) if c=="check" else None;print(json.dumps(v,ensure_ascii=False,sort_keys=True));return 0 if c!="check" or v["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
