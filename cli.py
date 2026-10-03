#!/usr/bin/env python3
"""Read apostle identity and validate local declarations; no agent runtime."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = ("README.md", "AGENTS.md", "docs/WHAT_IS.md", "docs/HOW_TO.md", "APOSTLE_MODULE.json")


def errors(data):
    problems = []
    if not isinstance(data, dict) or data.get("schema") != "apostle-module/1":
        return ["Unsupported manifest schema"]
    identity = data.get("identity", {})
    position = identity.get("position")
    if type(position) is not int or not 1 <= position <= 12:
        problems.append("Position must be an integer from 1 to 12")
    elif identity.get("slot_uid") != f"metahumotonic:apostle-slot:{position:02d}":
        problems.append("Slot UID must match position")
    if not isinstance(identity.get("korean_name"), str) or not identity["korean_name"].strip():
        problems.append("Korean name is required")
    pending = identity.get("selection_state") == "CONFLICT_PENDING"
    if pending:
        if identity.get("stable_entity_uid") is not None or identity.get("english_name") is not None:
            problems.append("Pending slot cannot select a persona or English name")
        if not data.get("candidates") or data.get("repository_role", {}).get("state") != "SLOT_WORKSPACE":
            problems.append("Pending slot needs candidates and a neutral workspace role")
    elif any(not isinstance(identity.get(key), str) or not identity[key].strip()
             for key in ("stable_entity_uid", "english_name")):
        problems.append("Selected identity needs an entity UID and English name")
    pins = data.get("source_pins")
    if not isinstance(pins, list) or not pins:
        problems.append("Source pins are required")
    else:
        for pin in pins:
            if not isinstance(pin, dict):
                problems.append("Invalid source pin")
                continue
            snapshot, original = pin.get("dashboard_snapshot", {}), pin.get("original_source", {})
            if not isinstance(snapshot, dict) or not isinstance(original, dict):
                problems.append("Source and snapshot locators are required")
                continue
            digest, revision = snapshot.get("sha256"), original.get("revision")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                problems.append("Snapshot SHA-256 is invalid")
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
                problems.append("Original source Git revision is invalid")
            if any(not isinstance(original.get(key), str) or not original[key] for key in ("owner", "repository", "path")):
                problems.append("Original source locator is incomplete")
    role = data.get("runtime_role", {})
    if role.get("state") == "UNASSIGNED":
        if role.get("authority") != "UNASSIGNED" or role.get("label") is not None:
            problems.append("Unassigned role cannot claim an assignment")
    elif role.get("state") == "USER_ASSIGNED":
        if pending or role.get("authority") != "USER_PRIMARY" or not isinstance(role.get("label"), str) or not role["label"].strip():
            problems.append("Assigned role needs a selected identity and user authority")
    else:
        problems.append("Unknown runtime role state")
    return problems


def main():
    command = sys.argv[1] if len(sys.argv) == 2 else ""
    if command not in {"identity", "show", "check"}:
        raise SystemExit("usage: cli.py identity|show|check")
    try:
        raw = (ROOT / "APOSTLE_MODULE.json").read_bytes()
        data = json.loads(raw)
        if command == "check":
            problems = errors(data) + ["Missing file: " + path for path in REQUIRED if not (ROOT / path).is_file()]
            value = {"ok": not problems, "errors": problems, "schema": data.get("schema"),
                     "identity": data.get("identity"), "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                     "pin_verification": "PIN_METADATA_ONLY"}
        else:
            value = data["identity"] if command == "identity" else data
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if command != "check" or value["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
