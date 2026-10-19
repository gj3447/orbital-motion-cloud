#!/usr/bin/env python3
"""Reconcile one registered ORCA workspace-root placement into OMC current state.

This is an owner-local bridge: it reads one registered ORCA current pointer,
validates its completed relocation evidence, and publishes a pinned workspace
root for a USL consumer.  It never moves, scans, hashes, retires, or deletes a
directory tree.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import uuid
from contextlib import contextmanager

DIGEST = re.compile(r"sha256:[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\Z")
TXN = re.compile(r"[a-f0-9]{32}\Z")
SAFE_MAX = 9007199254740991
POINTER_SCHEMA = "orca-usl-workspace-current/v1"
EVENT_SCHEMA = "orca-usl-workspace-placement/v1"
CURRENT_SCHEMA = "omc-usl-workspace-current/v1"
CONFIG_SCHEMA = "omc-usl-workspace-host/v1"


class Refused(ValueError):
    pass


def require(value, message):
    if not value:
        raise Refused(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def raw_digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def implementation_digest():
    return "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def absolute_direct(value, label, directory=False):
    path = Path(value)
    require(path.is_absolute() and path.resolve() == path, f"{label} must be an absolute direct path")
    entry = os.lstat(path)
    require(not stat.S_ISLNK(entry.st_mode) and (stat.S_ISDIR(entry.st_mode) if directory else True),
            f"{label} must not be a symbolic link")
    return path


def relative(value, label):
    require(isinstance(value, str) and value and "\\" not in value and not value.startswith("/")
            and all(part not in ("", ".", "..") for part in value.split("/")), f"Invalid {label}")
    return value


def read_regular(path, limit=2 * 1024 * 1024):
    path = Path(path)
    entry = os.lstat(path)
    require(stat.S_ISREG(entry.st_mode) and not stat.S_ISLNK(entry.st_mode) and entry.st_size <= limit,
            "Expected bounded regular non-symlink file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        raw = bytearray()
        while True:
            block = os.read(fd, min(1024 * 1024, limit + 1 - len(raw)))
            if not block:
                break
            raw.extend(block)
            require(len(raw) <= limit, "File exceeds byte limit")
        after = os.fstat(fd)
        require(all(getattr(before, field) == getattr(after, field)
                    for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")),
                "File changed while being read")
        final = os.lstat(path)
        require((final.st_dev, final.st_ino) == (after.st_dev, after.st_ino), "File path changed while being read")
        return bytes(raw)
    finally:
        os.close(fd)


def read_outbox_event(root, transaction_id):
    """Open exactly placement-outbox/<txn>.json without following any component."""
    base = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        child = os.open("placement-outbox", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=base)
        try:
            fd = os.open(transaction_id + ".json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=child)
            try:
                info = os.fstat(fd); require(stat.S_ISREG(info.st_mode) and info.st_size <= 2 * 1024 * 1024, "Invalid outbox event")
                raw = bytearray()
                while len(raw) <= info.st_size:
                    block = os.read(fd, min(1024 * 1024, info.st_size + 1 - len(raw)))
                    if not block:
                        break
                    raw.extend(block)
                after = os.fstat(fd)
                require(len(raw) == info.st_size and all(getattr(info, field) == getattr(after, field)
                        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")),
                        "Outbox event changed while being read")
                raw = bytes(raw)
                return json.loads(raw), raw_digest(raw)
            finally: os.close(fd)
        finally: os.close(child)
    finally: os.close(base)


def load_regular(path):
    raw = read_regular(path)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Refused("Invalid JSON") from exc
    return value, raw_digest(raw)


def safe_integer(value, label):
    require(type(value) is int and 0 <= value <= SAFE_MAX, f"Invalid {label}")
    return value


def sha(value, label):
    require(isinstance(value, str) and DIGEST.fullmatch(value) is not None, f"Invalid {label}")
    return value


def config(path):
    value, _ = load_regular(path)
    expected = {"schema", "stateDir", "currentPointer", "outboxRoot", "workspace", "resourceId",
                "physicalRootBase", "expectedOrcaImplementationDigest", "expectedSemanticContractDigest"}
    require(isinstance(value, dict) and set(value) in (expected, expected | {"read"}) and value.get("schema") == CONFIG_SCHEMA,
            "Invalid workspace placement config")
    require(isinstance(value["workspace"], str) and IDENTIFIER.fullmatch(value["workspace"]) is not None,
            "Invalid registered workspace")
    require(isinstance(value["resourceId"], str) and value["resourceId"], "Invalid registered resource")
    for key in ("expectedOrcaImplementationDigest", "expectedSemanticContractDigest"):
        sha(value[key], key)
    for key, directory in (("stateDir", True), ("outboxRoot", True), ("physicalRootBase", True)):
        absolute_direct(value[key], key, directory)
    pointer = absolute_direct(value["currentPointer"], "currentPointer")
    require(pointer.is_file(), "currentPointer must be a regular file")
    if "read" in value:
        read = value["read"]
        require(isinstance(read, dict) and set(read) == {"registration", "registrationDigest", "uslRepository", "uslRuntimeDigest", "adapterDigest", "nodeRuntime", "ownerResourceId"},
                "Invalid registered read configuration")
        for key in ("registrationDigest", "uslRuntimeDigest", "adapterDigest"): sha(read[key], key)
        require(read["ownerResourceId"] == value["resourceId"], "Read owner resource registration mismatch")
        require(isinstance(read["nodeRuntime"], str) and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", read["nodeRuntime"]) is not None,
                "Invalid registered Node runtime")
        registration = absolute_direct(read["registration"], "read registration")
        require(registration.is_file(), "Read registration must be a regular file")
        repository = absolute_direct(read["uslRepository"], "USL repository", True)
    return value


def real_directory_beneath(base, candidate):
    base = absolute_direct(base, "physicalRootBase", True)
    candidate = Path(candidate)
    require(candidate.is_absolute() and candidate.is_relative_to(base), "Physical root escapes registered base")
    current = base
    for part in candidate.relative_to(base).parts:
        current = current / part
        entry = os.lstat(current)
        require(not stat.S_ISLNK(entry.st_mode), "Physical root traverses symbolic link")
    entry = os.lstat(candidate)
    require(stat.S_ISDIR(entry.st_mode) and not stat.S_ISLNK(entry.st_mode) and candidate.resolve() == candidate,
            "Physical root must be a direct directory")
    return candidate


def directory_identity(path):
    entry = os.lstat(path)
    require(stat.S_ISDIR(entry.st_mode) and not stat.S_ISLNK(entry.st_mode), "Physical root identity is invalid")
    return [entry.st_dev, entry.st_ino]


def event_from_pointer(host):
    pointer, pointer_digest = load_regular(host["currentPointer"])
    fields = {"schema", "ownerImplementationDigest", "semanticContractDigest", "resourceId",
              "workspace", "generation", "transactionId", "eventDigest", "previousEventDigest", "eventFile"}
    require(isinstance(pointer, dict) and set(pointer) == fields and pointer.get("schema") == POINTER_SCHEMA,
            "Invalid ORCA workspace current pointer")
    require(pointer["workspace"] == host["workspace"] and pointer["resourceId"] == host["resourceId"],
            "Pointer registration mismatch")
    safe_integer(pointer["generation"], "pointer generation")
    require(TXN.fullmatch(pointer["transactionId"]) is not None, "Invalid pointer transaction")
    for key in ("ownerImplementationDigest", "semanticContractDigest", "eventDigest"):
        sha(pointer[key], key)
    require(pointer["ownerImplementationDigest"] == host["expectedOrcaImplementationDigest"]
            and pointer["semanticContractDigest"] == host["expectedSemanticContractDigest"],
            "Pointer owner pin mismatch")
    require(pointer["previousEventDigest"] is None or DIGEST.fullmatch(pointer["previousEventDigest"]) is not None,
            "Invalid pointer previous event digest")
    require(pointer["eventFile"] == "placement-outbox/" + pointer["transactionId"] + ".json", "Unexpected pointer event file")
    outbox = absolute_direct(host["outboxRoot"], "outboxRoot", True)
    event, event_file_digest = read_outbox_event(outbox, pointer["transactionId"])
    fields = {"schema", "status", "owner", "transactionId", "workspace", "relation", "mapping",
              "resourceId", "sourceIdentity", "semanticContractDigest", "configDigest",
              "registryEvidenceDigest", "observedAt", "directoryProof", "sourceRetirement",
              "ownerImplementationDigest", "eventDigest"}
    require(isinstance(event, dict) and set(event) == fields and event.get("schema") == EVENT_SCHEMA
            and event.get("status") == "PENDING_OMC_RECONCILE" and event.get("owner") == "ORCA_SETTING/storage",
            "Invalid ORCA workspace relocation event")
    body = {key: value for key, value in event.items() if key != "eventDigest"}
    require(event["eventDigest"] == digest(body) == pointer["eventDigest"], "Event canonical digest mismatch")
    require(event["ownerImplementationDigest"] == host["expectedOrcaImplementationDigest"]
            and event["semanticContractDigest"] == host["expectedSemanticContractDigest"], "Event owner pin mismatch")
    require(event["workspace"] == host["workspace"] and event["resourceId"] == host["resourceId"]
            and event["transactionId"] == pointer["transactionId"] and TXN.fullmatch(event["transactionId"]) is not None,
            "Event registration mismatch")
    require(event["relation"] == "working-copy", "Invalid workspace relation")
    mapping = event["mapping"]
    require(isinstance(mapping, dict) and set(mapping) == {"kind", "logicalRoot", "physicalRoot", "compatibilityPath"}
            and mapping["kind"] == "workspace-root" and all(isinstance(mapping[key], str) and mapping[key]
            for key in ("logicalRoot", "physicalRoot", "compatibilityPath")), "Invalid workspace root mapping")
    require(isinstance(event["sourceIdentity"], list) and len(event["sourceIdentity"]) == 2
            and all(type(item) is int and item >= 0 for item in event["sourceIdentity"]), "Invalid source identity")
    for key in ("configDigest", "registryEvidenceDigest"):
        sha(event[key], key)
    proof = event["directoryProof"]
    require(isinstance(proof, dict) and set(proof) == {"kind", "manifestSha256", "sealDigest", "snapshotId", "fullRestoreVerifiedAt"}
            and proof["kind"] == "directory-manifest/v1" and isinstance(proof["snapshotId"], str) and proof["snapshotId"]
            and isinstance(proof["fullRestoreVerifiedAt"], str) and proof["fullRestoreVerifiedAt"], "Invalid directory proof")
    sha(proof["manifestSha256"], "manifest SHA"); sha(proof["sealDigest"], "seal digest")
    retirement = event["sourceRetirement"]
    require(isinstance(retirement, dict) and set(retirement) == {"status"} and retirement["status"] == "NOT_RETIRED",
            "Workspace publication requires source retention observation")
    physical = real_directory_beneath(host["physicalRootBase"], mapping["physicalRoot"])
    return pointer, pointer_digest, event, event_file_digest, physical


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + "." + uuid.uuid4().hex)
    try:
        with temp.open("xb") as stream:
            os.chmod(temp, 0o600)
            stream.write(canonical(value) + b"\n")
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def locked(host):
    root = Path(host["stateDir"])
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    absolute_direct(root, "stateDir", True)
    lock = root / "writer.lock"
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        entry = os.fstat(fd)
        require(stat.S_ISREG(entry.st_mode), "Invalid workspace writer lock")
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise Refused("Workspace reconcile busy") from exc
        yield root
    finally:
        os.close(fd)


def state_digest(state):
    return digest(state)


def expected_state(state, expected_generation, expected_digest):
    safe_integer(expected_generation, "expected generation")
    if state is None:
        require(expected_generation == 0 and expected_digest is None, "Expected bootstrap state mismatch")
    else:
        require(expected_generation == state["generation"] and expected_digest == state_digest(state),
                "Expected current state mismatch")


def receipt(host, state):
    operation_digest = digest({"schema": "omc-usl-workspace-reconcile-operation/v1",
                               "operation": state["lastOperation"], "generation": state["generation"],
                               "eventDigest": state["eventDigest"], "pointerDigest": state["pointerDigest"]})
    value = {"schema": "omc-usl-workspace-reconcile-result/v1", "status": "COMPLETE",
             "operation": state["lastOperation"], "stateGeneration": state["generation"],
             "stateDigest": state_digest(state), "eventDigest": state["eventDigest"],
             "pointerDigest": state["pointerDigest"], "completedAtEpoch": state["completedAtEpoch"]}
    value["operationDigest"] = operation_digest
    return value


def current(host, state):
    validate_saved_state(host, state)
    output = {"schema": CURRENT_SCHEMA, "status": "CURRENT", "stateGeneration": state["generation"],
              "stateDigest": state_digest(state), "semanticDigest": state["semanticContractDigest"],
              "registrationDigest": state["registrationDigest"], "lastOperation": state["lastOperation"],
              "operationDigest": state["operationDigest"], "workspace": state["workspace"],
              "resourceId": state["resourceId"], "physicalRoot": state["physicalRoot"],
              "directoryProof": {"digest": state["directoryProofDigest"]}, "pointerGeneration": state["pointerGeneration"],
              "pointerDigest": state["pointerDigest"], "eventDigest": state["eventDigest"],
              "provenance": {"ownerImplementationDigest": implementation_digest()}}
    return output


def load_state(root):
    path = root / "state.json"
    return load_regular(path)[0] if os.path.lexists(path) else None


def validate_saved_state(host, state):
    fields = {"schema", "generation", "registrationDigest", "workspace", "resourceId", "physicalRoot",
              "directoryProofDigest", "semanticContractDigest", "physicalRootIdentity", "pointerGeneration", "pointerDigest",
              "eventDigest", "eventFileDigest", "transactionId", "lastOperation", "operationDigest", "completedAtEpoch"}
    require(isinstance(state, dict) and set(state) == fields and state.get("schema") == "omc-usl-workspace-state/1",
            "Workspace state is unavailable or malformed")
    safe_integer(state["generation"], "state generation"); safe_integer(state["pointerGeneration"], "state pointer generation")
    for key in ("registrationDigest", "directoryProofDigest", "semanticContractDigest", "pointerDigest",
                "eventDigest", "eventFileDigest", "operationDigest"):
        sha(state[key], key)
    require(state["registrationDigest"] == digest(host) and state["workspace"] == host["workspace"]
            and state["resourceId"] == host["resourceId"] and state["semanticContractDigest"] == host["expectedSemanticContractDigest"],
            "Workspace state registration pin mismatch")
    require(TXN.fullmatch(state["transactionId"]) is not None and isinstance(state["lastOperation"], str)
            and isinstance(state["completedAtEpoch"], (int, float)), "Workspace state operation is invalid")
    real_directory_beneath(host["physicalRootBase"], state["physicalRoot"])
    require(state["physicalRootIdentity"] == directory_identity(state["physicalRoot"]), "Physical root identity changed")
    require(state["operationDigest"] == receipt(host, {key: value for key, value in state.items() if key != "operationDigest"})["operationDigest"],
            "Workspace state operation digest mismatch")


def state_matches_event(host, state, pointer, pointer_digest, event, event_file_digest, physical):
    validate_saved_state(host, state)
    require(state["pointerGeneration"] == pointer["generation"] and state["pointerDigest"] == pointer_digest
            and state["eventDigest"] == event["eventDigest"] and state["eventFileDigest"] == event_file_digest
            and state["transactionId"] == event["transactionId"] and state["physicalRoot"] == str(physical)
            and state["directoryProofDigest"] == digest(event["directoryProof"]), "Committed state/event mismatch")


def reconcile(host, expected_generation, expected_digest):
    with locked(host) as root:
        state = load_state(root)
        expected_state(state, expected_generation, expected_digest)
        if state is not None:
            # A pointer advance cannot relabel a committed workspace under a
            # modified registration.  The next host registration must begin
            # from an explicit, separately reviewed bootstrap/cutover.
            validate_saved_state(host, state)
        pointer, pointer_digest, event, event_file_digest, physical = event_from_pointer(host)
        if state is not None:
            if pointer["generation"] < state["pointerGeneration"]:
                raise Refused("ORCA pointer rollback")
            if pointer["generation"] == state["pointerGeneration"]:
                state_matches_event(host, state, pointer, pointer_digest, event, event_file_digest, physical)
                saved = root / "operations" / state["lastOperation"] / "result.json"
                if not os.path.lexists(saved):
                    atomic(saved, receipt(host, state))
                else:
                    load_regular(saved)
                return current(host, state)
            require(pointer["previousEventDigest"] == state["eventDigest"], "ORCA pointer chain mismatch")
        else:
            require(pointer["previousEventDigest"] is None, "Bootstrap pointer has prior event")
        operation = "workspace-reconcile-" + event["eventDigest"].split(":", 1)[1][:32]
        # ORCA does not share this lock.  Refuse, rather than committing a
        # snapshot that changed between validation and our local CAS.
        fresh = event_from_pointer(host)
        require((pointer, pointer_digest, event, event_file_digest, physical) == fresh,
                "ORCA pointer/event changed during reconcile")
        next_state = {"schema": "omc-usl-workspace-state/1", "generation": 1 if state is None else state["generation"] + 1,
                      "registrationDigest": digest(host), "workspace": host["workspace"], "resourceId": host["resourceId"], "physicalRoot": str(physical),
                      "directoryProofDigest": digest(event["directoryProof"]), "semanticContractDigest": event["semanticContractDigest"],
                      "physicalRootIdentity": directory_identity(physical),
                      "pointerGeneration": pointer["generation"], "pointerDigest": pointer_digest,
                      "eventDigest": event["eventDigest"], "eventFileDigest": event_file_digest,
                      "transactionId": event["transactionId"], "lastOperation": operation, "completedAtEpoch": time.time()}
        atomic(root / "operations" / operation / "intent.json",
               {"schema": "omc-usl-workspace-reconcile-intent/v1", "operation": operation,
                "previousStateDigest": None if state is None else state_digest(state), "eventDigest": event["eventDigest"],
                "pointerDigest": pointer_digest})
        next_state["operationDigest"] = receipt(host, next_state)["operationDigest"]
        atomic(root / "state.json", next_state)
        atomic(root / "operations" / operation / "result.json", receipt(host, next_state))
        return current(host, next_state)


def resolve_for_read(host):
    """Issue the owner-local current document and matching expectation per read.

    The expectation is generated only after the committed OMC state has passed
    its registry, ORCA pointer, event, and physical-root checks.  Static owner
    pins remain in the registered host/read configuration; callers never edit
    a per-generation expectation file.
    """
    with locked(host) as root:
        state = load_state(root)
        generation = 0 if state is None else state["generation"]
        state_pin = None if state is None else state_digest(state)
    value = reconcile(host, generation, state_pin)
    expectation = {"exportDigest": digest(value), "stateGeneration": value["stateGeneration"],
                   "stateDigest": value["stateDigest"], "semanticDigest": value["semanticDigest"],
                   "registrationDigest": value["registrationDigest"],
                   "ownerImplementationDigest": value["provenance"]["ownerImplementationDigest"],
                   "operationDigest": value["operationDigest"]}
    return {"current": value, "expectation": expectation}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("reconcile", "resolve"):
        item = sub.add_parser(name)
        item.add_argument("--expected-generation", type=int, required=True)
        item.add_argument("--expected-state-digest", default="null")
    sub.add_parser("export-current")
    sub.add_parser("resolve-for-read")
    args = parser.parse_args(argv)
    try:
        host = config(args.config)
        if args.command == "export-current":
            with locked(host) as root: result = current(host, load_state(root))
        elif args.command == "resolve-for-read":
            require("read" in host, "Registered read configuration required")
            result = resolve_for_read(host)
        else:
            expected = None if args.expected_state_digest == "null" else args.expected_state_digest
            require(expected is None or DIGEST.fullmatch(expected) is not None, "Invalid expected state digest")
            # resolve intentionally reconciles first on every invocation; it does
            # not access a child or follow compatibilityPath.
            result = reconcile(host, args.expected_generation, expected)
        if args.out: atomic(args.out, result)
        else: print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSED_OR_INCOMPLETE", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
