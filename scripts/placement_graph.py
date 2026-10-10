#!/usr/bin/env python3
"""Validate the owner-local placement graph and emit its USL projection."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(graph, contract, root=ROOT):
    errors = []
    def need(ok, message):
        if not ok: errors.append(message)
    need(graph.get('schema') == 'omc-hardware-placement/1', 'Wrong graph schema')
    nodes = {}
    for n in graph['nodes']:
        need(n['uid'] not in nodes, 'Duplicate node ' + n['uid'])
        nodes[n['uid']] = n
        need(n['type'] in contract['node_types'], 'Unknown node type')
        need(n['authority'] in ('USER_PRIMARY', 'SECONDARY_AI', 'SOURCE_DOCUMENT'), 'Unknown authority')
        if n['type'] != 'Source':
            need(n['authority'] == 'SECONDARY_AI', 'AI graph interpretation promoted to user source')
            need(bool(n.get('source_refs')), 'Missing provenance: ' + n['uid'])
        else:
            p = Path(n['path'])
            need(not p.is_absolute() and '..' not in p.parts, 'Source escapes repository')
            if p.is_absolute() or '..' in p.parts: continue
            target = root / p
            allowed = target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root.resolve())
            need(allowed, 'Missing/escaped source ' + str(p))
            if allowed:
                need(hashlib.sha256(target.read_bytes()).hexdigest() == n['sha256'], 'Stale source ' + str(p))
    for n in nodes.values():
        for ref in n.get('source_refs', []):
            need(nodes.get(ref, {}).get('type') == 'Source', 'Missing source reference ' + ref)
    seen, triples, counts, incoming = set(), set(), Counter(), Counter()
    for e in graph['edges']:
        need(e['uid'] not in seen and e['uid'] not in nodes, 'Duplicate edge ID')
        seen.add(e['uid'])
        triple = (e['type'], e['source'], e['target'])
        need(triple not in triples, 'Duplicate edge'); triples.add(triple)
        spec = contract['predicates'].get(e['type'])
        need(spec is not None, 'Unknown predicate')
        need(e['source'] in nodes and e['target'] in nodes, 'Missing endpoint')
        need(e.get('authority') == 'SECONDARY_AI', 'Edge authority invalid')
        if spec and e['source'] in nodes and e['target'] in nodes:
            need(nodes[e['source']]['type'] in spec['domain'] and nodes[e['target']]['type'] in spec['range'], 'Domain/range violation')
            counts[e['source'], e['type']] += 1
            incoming[e['target'], e['type']] += 1
    for predicate, spec in contract['predicates'].items():
        for uid, n in nodes.items():
            if n['type'] in spec['domain']:
                count = counts[uid, predicate]
                need(count >= spec['out_min'] and (spec['out_max'] is None or count <= spec['out_max']), 'Cardinality violation ' + uid)
            if n['type'] in spec['range']:
                count = incoming[uid, predicate]
                need(count >= spec['in_min'] and (spec['in_max'] is None or count <= spec['in_max']), 'Incoming cardinality violation ' + uid)
    qids = set()
    for q in graph['competency_questions']:
        need(q['id'] not in qids, 'Duplicate query'); qids.add(q['id'])
        current = {q['start']}
        for predicate in q['via']:
            need(predicate in contract['predicates'], 'Unknown query predicate')
            current = {e['target'] for e in graph['edges'] if e['source'] in current and e['type'] == predicate}
        need(current == set(q['expected']), 'Wrong competency answer ' + q['id'])
    return errors


def project(graph):
    # Private host paths are absent from this portable declaration projection.
    return {'schema': 'usl-resource-graph/v1', 'resources': [
        {'id': n['uid'], 'types': ['urn:omc:placement:' + n['type']],
         'locator': 'https://github.com/gj3447/orbital-motion-cloud/blob/main/' + (n['path'] if n['type'] == 'Source' else 'graph/placement.json'),
         'metadata': {k: v for k, v in n.items() if k not in ('uid', 'type')}} for n in graph['nodes']],
        'meanings': [{'id': 'omc:placement:predicate:' + key, 'description': value['meaning']}
                     for key, value in graph['predicate_contracts'].items()],
        'links': [{'id': e['uid'], 'meaning': 'omc:placement:predicate:' + e['type'],
                   'participants': [{'role': 'source', 'resource': e['source']}, {'role': 'target', 'resource': e['target']}],
                   'metadata': {'authority': e['authority']}} for e in graph['edges']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'render', 'query'])
    args = parser.parse_args()
    graph = json.loads((ROOT / 'graph/placement.json').read_text())
    contract = json.loads((ROOT / 'graph/placement-contract.json').read_text())
    errors = validate(graph, contract)
    if graph['predicate_contracts'] != contract['predicates']: errors.append('Predicate contract mismatch')
    output = ROOT / 'graph/placement.usl.json'
    projection = json.dumps(project(graph), ensure_ascii=False, indent=2) + '\n'
    if not errors and args.command == 'render': output.write_text(projection)
    if not errors and args.command == 'check' and (not output.is_file() or output.read_text() != projection):
        errors.append('USL projection is stale')
    print(json.dumps({'ok': not errors, 'errors': errors, 'nodes': len(graph['nodes']), 'edges': len(graph['edges']),
                      'competency_questions': graph['competency_questions'] if args.command == 'query' else len(graph['competency_questions']),
                      'scope': 'OWNER_LOCAL_TYPED_PROPERTY_GRAPH_NOT_EXTERNAL_STANDARDS_CERTIFICATION'}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__': raise SystemExit(main())
