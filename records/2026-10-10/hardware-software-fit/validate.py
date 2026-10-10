"""Read-only validation of the hardware-fit design; does not run workloads."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
GRAPH = ROOT / "graph/hardware-software-fit.proposal.json"
NS = "omc:hardware-fit:"
TYPES = {"Source", "Subject", "Capability", "Proposal", "IntegrationTarget",
         "Invariant", "Dimension", "Stage", "Gate"}
PRIMARY = {
    "records/2026-10-10/hardware-software-fit/user-verbatim.txt",
    "records/2026-10-10/hardware-software-fit/chu-os-user-verbatim.txt",
    "records/2026-10-10/hardware-adaptive-placement/user-verbatim.txt",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(graph):
    require(graph["schema"] == "omc-hardware-software-fit-proposal/1", "schema")
    require(graph["scope"] == "OWNER_LOCAL_DESIGN_ONLY", "scope")
    require(graph["authority"] == "SECONDARY_AI" and graph["state"] == "PROPOSED", "authority")
    require(graph["shared_kg_written"] is False and graph["runtime_deployed"] is False, "effects")
    nodes = {n["uid"]: n for n in graph["nodes"]}
    require(len(nodes) == len(graph["nodes"]), "duplicate node")
    sources = {uid for uid, n in nodes.items() if n["type"] == "Source"}
    for uid, n in nodes.items():
        require(n["type"] in TYPES and n.get("label") and n.get("state"), "node fields")
        if n["type"] == "Source":
            if n["authority"] == "USER_PRIMARY":
                require(n.get("path") in PRIMARY, "primary source boundary")
            if "path" in n:
                path = ROOT / n["path"]
                require(path.resolve().is_relative_to(ROOT) and not path.is_symlink(), "source scope")
                data = path.read_bytes()
                require(hashlib.sha256(data).hexdigest() == n["sha256"], "source digest: " + n["path"])
                require(len(data) == n["bytes"], "source bytes")
                require(n["revision"] is None or re.fullmatch(r"[a-f0-9]{40}", n["revision"]), "revision")
            else:
                require(n["url"].startswith("https://kubernetes.io/") and n["sha256"] is None, "external source")
        else:
            require(n["authority"] == "SECONDARY_AI", "interpretation promoted to canon")
            require(n.get("sources") and set(n["sources"]) <= sources, "node provenance")
            if n["type"] == "Stage":
                require(n["state"] == "PLANNED", "unexecuted phase marked complete")
            if n["type"] == "Gate":
                require(n["state"] == "NOT_EVALUATED", "unexecuted gate marked evaluated")
    edge_ids = set()
    triples = set()
    contracts = graph["predicate_contracts"]
    for e in graph["edges"]:
        require(e["uid"] not in edge_ids, "duplicate edge UID")
        edge_ids.add(e["uid"])
        triple = (e["source"], e["type"], e["target"])
        require(triple not in triples, "duplicate edge triple")
        triples.add(triple)
        require(e["source"] in nodes and e["target"] in nodes, "missing endpoint")
        require(e["type"] in contracts, "unknown predicate")
        c = contracts[e["type"]]
        require(nodes[e["source"]]["type"] in c["domain"], "domain")
        require(nodes[e["target"]]["type"] in c["range"], "range")
        require(e["authority"] == "SECONDARY_AI" and e["state"] == "PROPOSED", "edge authority/state")
        require(e.get("sources") and set(e["sources"]) <= sources, "edge provenance")
    for predicate, c in contracts.items():
        require(c["direction"] == "source_to_target" and c["meaning"], "predicate meaning")
        for uid, n in nodes.items():
            for end, type_key, prefix in (("source", "domain", "out"), ("target", "range", "in")):
                if n["type"] not in c[type_key]:
                    continue
                count = sum(e["type"] == predicate and e[end] == uid for e in graph["edges"])
                require(count >= c[prefix + "_min"], "minimum cardinality")
                maximum = c[prefix + "_max"]
                require(maximum is None or count <= maximum, "maximum cardinality")
        if c["acyclic"]:
            visiting, visited = set(), set()

            def visit(uid):
                require(uid not in visiting, "dependency cycle")
                if uid in visited:
                    return
                visiting.add(uid)
                for e in graph["edges"]:
                    if e["type"] == predicate and e["source"] == uid:
                        visit(e["target"])
                visiting.remove(uid)
                visited.add(uid)

            for uid in nodes:
                visit(uid)
    answers = {}
    for q in graph["competency_questions"]:
        require(q["id"] not in answers, "duplicate CQ")
        actual = sorted(e["target"] for e in graph["edges"]
                        if e["source"] == q["start"] and e["type"] == q["predicate"])
        require(actual == sorted(q["expected"]), "wrong CQ answer: " + q["id"])
        for uid, properties in q.get("expected_properties", {}).items():
            require(all(nodes[uid].get(k) == v for k, v in properties.items()), "CQ properties")
        answers[q["id"]] = actual
    require(set(answers) == {"CQ1", "CQ2", "CQ3", "CQ4", "CQ5", "CQ6"}, "CQ coverage")
    runtime = graph["runtime_contract"]
    require(runtime["state"] == "PROPOSED_SCHEMA_ONLY" and runtime["instances"] == [], "fake runtime instances")
    for fields in runtime["required_fields"].values():
        require("uid" in fields and len(fields) == len(set(fields)), "runtime field declaration")
    for c in runtime["predicate_contracts"].values():
        require(set(c["domain"] + c["range"]) <= set(runtime["required_fields"]), "runtime type declaration")
        require(c["direction"] == "source_to_target" and c["meaning"], "runtime meaning")
        for prefix in ("in", "out"):
            require(c[prefix + "_min"] >= 0, "runtime minimum")
            require(c[prefix + "_max"] is None or c[prefix + "_max"] >= c[prefix + "_min"], "runtime maximum")
    manifest = json.loads((Path(__file__).parent / "sources.json").read_text())
    require({s["uid"]: s for s in manifest["sources"]} == {uid: nodes[uid] for uid in sources}, "source manifest mismatch")
    return {"status": "PASS", "nodes": len(nodes), "edges": len(edge_ids), "answers": answers,
            "scope": "DESIGN_GRAPH_ONLY; runtime schema declaration checked, runtime instances not evaluated"}


if __name__ == "__main__":
    print(json.dumps(validate(json.loads(GRAPH.read_text())), ensure_ascii=False, indent=2))
