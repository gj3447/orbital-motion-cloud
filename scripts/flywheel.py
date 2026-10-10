#!/usr/bin/env python3
"""Validate and read the OMC design graph; does not run an economic simulation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_inputs(root=ROOT):
    return tuple(json.loads((root / name).read_text()) for name in
                 ("graph/flywheel.json", "graph/flywheel-contract.json"))


def answers(graph):
    nodes = {n["uid"]: n for n in graph["nodes"]}
    result = []
    for q in graph["competency_questions"]:
        current = {q["start"]}
        for predicate in q["via"]:
            current = {e["target"] for e in graph["edges"]
                       if e["source"] in current and e["type"] == predicate}
        result.append({"id": q["id"], "question": q["question"],
                       "answers": [nodes[u] for u in sorted(current)]})
    return result


def validate(graph, contract, root=ROOT):
    errors = []

    def require(ok, message):
        if not ok:
            errors.append(message)

    require(graph.get("schema") == contract["graph_schema"], "graph schema mismatch")
    require(graph.get("scope") == "OWNER_LOCAL_DESIGN_GRAPH", "scope must remain owner-local")
    nodes = {}
    for n in graph["nodes"]:
        u, kind = n["uid"], n["type"]
        require(u not in nodes, "duplicate node UID: " + u)
        nodes[u] = n
        require(kind in contract["node_types"], "unregistered node type: " + kind)
        for key in contract["common_required"] + contract["node_types"].get(kind, []):
            require(key in n, f"missing {key}: {u}")
        require(bool(n.get("label")), "empty label: " + u)
        if kind != "Source":
            require(n.get("authority") == "SECONDARY_AI" and n.get("record_lifecycle") == "PROPOSED",
                    "local design authority/lifecycle changed: " + u)
        if kind == "Claim":
            require(n.get("authority") == contract["claim_authority"], "AI claim promoted to user authority: " + u)
            require(n.get("epistemic_state") == contract["claim_state"], "unobserved claim promoted: " + u)
        elif kind == "Evaluation":
            require(n.get("status") == contract["evaluation_status"] and n.get("result") is None,
                    "evaluation needs a new observation contract before reporting results: " + u)
            require(bool(n.get("conditions")), "missing evaluation conditions: " + u)
        elif kind == "Source":
            path = Path(n["path"])
            require(not path.is_absolute() and ".." not in path.parts, "source path escapes owner: " + u)
            target = root / path
            if path.is_absolute() or ".." in path.parts:
                continue
            if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
                errors.append("source unavailable: " + u)
            else:
                require(hashlib.sha256(target.read_bytes()).hexdigest() == n["sha256"], "source digest mismatch: " + u)
            require(n["digest_scope"] == "FILE_BYTES", "unknown digest scope: " + u)
            require(n["authority"] in {"USER_PRIMARY", "SECONDARY_AI", "SOURCE_DOCUMENT"}, "unknown source authority: " + u)
    edge_ids, triples = set(), set()
    outgoing, incoming = Counter(), Counter()
    for n in nodes.values():
        if "source_refs" in n:
            require(bool(n["source_refs"]), "empty source refs: " + n["uid"])
            for ref in n["source_refs"]:
                require(nodes.get(ref, {}).get("type") == "Source", "missing source ref: " + ref)
    for e in graph["edges"]:
        u, p, a, b = e["uid"], e["type"], e["source"], e["target"]
        require(u not in edge_ids and u not in nodes, "duplicate edge UID: " + u)
        require((p, a, b) not in triples, "duplicate relationship: " + u)
        edge_ids.add(u)
        triples.add((p, a, b))
        require(e.get("authority") == contract["edge_authority"] and e.get("status") == contract["edge_status"],
                "relationship authority/status changed: " + u)
        spec = contract["predicates"].get(p)
        require(spec is not None, "unregistered predicate: " + p)
        require(a in nodes and b in nodes, "missing endpoint: " + u)
        if spec is None or a not in nodes or b not in nodes:
            continue
        require(nodes[a]["type"] in spec["domain"] and nodes[b]["type"] in spec["range"], "domain/range violation: " + u)
        outgoing[a, p] += 1
        incoming[b, p] += 1
        if p == "MAY_ENABLE":
            require(nodes.get(e.get("claim_uid"), {}).get("type") == "Claim", "missing conditional claim: " + u)
            require(bool(e.get("label")), "missing mechanism label: " + u)
    for p, spec in contract["predicates"].items():
        for u, n in nodes.items():
            for side, domain, counts in [("out", "domain", outgoing), ("in", "range", incoming)]:
                if n["type"] in spec[domain]:
                    count = counts[u, p]
                    maximum = spec[side + "_max"]
                    require(count >= spec[side + "_min"] and (maximum is None or count <= maximum),
                            f"{side} cardinality violation: {u} {p}")
    for p in contract["acyclic_predicates"]:
        visiting, visited = set(), set()

        def visit(u):
            if u in visiting:
                return False
            if u in visited:
                return True
            visiting.add(u)
            ok = all(visit(e["target"]) for e in graph["edges"] if e["type"] == p and e["source"] == u)
            visiting.remove(u)
            visited.add(u)
            return ok

        require(all(visit(u) for u in nodes), "forbidden dependency cycle: " + p)
    for cycle in graph["cycles"]:
        path = cycle["stages"]
        require(len(path) >= 3 and path[0] == path[-1], "cycle is not closed: " + cycle["id"])
        for a, b in zip(path, path[1:]):
            require(("MAY_ENABLE", a, b) in triples, "missing cycle step: " + cycle["id"])
    question_ids = [q["id"] for q in graph["competency_questions"]]
    require(len(question_ids) == len(set(question_ids)), "duplicate competency question")
    for q in graph["competency_questions"]:
        require(q["start"] in nodes and all(u in nodes for u in q["expected"]), "missing query node: " + q["id"])
        require(bool(q["via"]) and all(p in contract["predicates"] for p in q["via"]), "unregistered query predicate: " + q["id"])
    if not errors:
        for q, answer in zip(graph["competency_questions"], answers(graph)):
            require({n["uid"] for n in answer["answers"]} == set(q["expected"]), "competency query mismatch: " + q["id"])
    return errors


def render(graph):
    stages = [n for n in graph["nodes"] if n["type"] == "Stage"]
    aliases = {n["uid"]: f"s{i}" for i, n in enumerate(stages)}

    def safe(label):
        return label.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ")

    lines = ["# 입체운행구름 플라이휠 그래프", "", "동일 모델과 총토큰에서 더 유용한 답변을 얻는다는 전제로 연결한 조건부 순환이다.",
             "모든 화살표는 SECONDARY_AI 설계 가설이며 성능·경제 효과는 미검증이다.", "", "```mermaid", "flowchart LR"]
    for n in stages:
        lines.append(f'    {aliases[n["uid"]]}["{safe(n["label"])}"]')
    for e in graph["edges"]:
        if e["type"] == "MAY_ENABLE":
            lines.append(f'    {aliases[e["source"]]} -->|"{safe(e["label"])}"| {aliases[e["target"]]}')
    lines += ["```", "", "## 원문에서 평가까지", "", "| 가설 | 검증할 내용 | 상태 |", "|---|---|---|"]
    for n in graph["nodes"]:
        if n["type"] == "Claim":
            lines.append(f'| {n["label"]} | {n["qualification"]} | HYPOTHESIS |')
    lines += ["", "[설계와 총토큰 회계](FLYWHEEL.md) · [그래프 정본](../graph/flywheel.json) · [관계 계약](../graph/flywheel-contract.json)", "",
              "이 그림은 `python3 scripts/flywheel.py render`로 생성한다. 원문을 바꾸면 해시와 그래프를 함께 갱신한다.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "query", "render"])
    args = parser.parse_args()
    try:
        graph, contract = read_inputs()
        errors = validate(graph, contract)
        output = ROOT / "docs/FLYWHEEL_GRAPH.md"
        if not errors and args.command == "check":
            if not output.is_file() or output.read_text() != render(graph):
                errors.append("diagram is stale; run render")
        if errors:
            print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False))
            return 1
        if args.command == "render":
            output.write_text(render(graph))
        value = answers(graph) if args.command == "query" else {
            "ok": True, "scope": "GRAPH_AND_SOURCE_INTEGRITY_ONLY", "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]), "competency_questions": len(graph["competency_questions"]),
            "cycles": len(graph["cycles"]), "performance_observed": False}
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
