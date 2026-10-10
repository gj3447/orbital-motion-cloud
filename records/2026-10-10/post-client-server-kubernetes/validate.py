"""Read-only checks for recorded evidence and graph contracts; no workloads run."""
from pathlib import Path
import copy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
RECORD = Path(__file__).resolve().parent
NS = 'omc:post-client-server:'
PIN = '841d8db7236e660f53ee9df91133b58a780c8e7f'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_local(path):
    p = ROOT / path
    require(not p.is_symlink() and p.resolve().is_relative_to(ROOT), 'source scope')
    return p.read_bytes()


def validate(graph, evidence, acquisition):
    require(graph['schema'] == 'omc-post-client-server-knowledge/1', 'graph schema')
    require(graph['authority'] == 'SECONDARY_AI' and graph['state'] == 'PROPOSED', 'proposal authority')
    require(graph['scope'] == 'OWNER_LOCAL_RESEARCH_PROPOSAL', 'graph scope')
    require(graph['runtime_deployed'] is False and graph['shared_kg_written'] is False, 'effects')
    require(graph['upstream_commit'] == evidence['commit'] == acquisition['commit'] == PIN, 'pin')
    for obj in (evidence, acquisition):
        require(all(obj[k] == 'NOT_RUN' for k in ('upstream_build', 'upstream_tests', 'cluster_execution')), 'unexecuted work promoted')
    files = {f['path']: f for f in acquisition['files']}
    require(len(files) == len(acquisition['files']) == 27, 'acquisition set')
    for path, item in files.items():
        data = read_local(item['local_path'])
        require(len(data) == item['bytes'] and digest(data) == item['sha256'], 'source bytes: ' + path)
        require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['git_blob_oid'], 'Git blob: ' + path)
    spans = {s['uid']: s for s in evidence['read_spans']}
    require(len(spans) == len(evidence['read_spans']), 'duplicate span')
    for span in spans.values():
        require(span['path'] in files and span['commit'] == PIN, 'span source')
        lines = read_local(files[span['path']]['local_path']).splitlines(keepends=True)
        start, end = span['start_line'], span['end_line']
        require(1 <= start <= end <= len(lines), 'span bounds')
        require(digest(b''.join(lines[start-1:end])) == span['sha256'], 'span digest')
        require(span['state'] == 'READ_STATIC' and span['authority'] == 'SOURCE_DOCUMENT', 'span state')
    claims = {c['id']: c for c in evidence['claims']}
    require(set(claims) == {f'C{i:02}' for i in range(1, 16)}, 'claim set')
    for c in claims.values():
        require(c['authority'] == 'SECONDARY_AI' and c['state'] == 'STATIC_CODE_ANALYSIS', 'claim authority')
        require(c['read_spans'] and set(c['read_spans']) <= set(spans), 'claim evidence')
    nodes = {n['uid']: n for n in graph['nodes']}
    require(len(nodes) == len(graph['nodes']), 'duplicate node')
    types = {'Subject', 'Source', 'Proposal', 'Knowledge', 'PlannedArtifact', 'Invariant', 'CodeClaim', 'ReadSpan'}
    for uid, node in nodes.items():
        require(node['type'] in types and node['label'] and node['state'], 'node fields')
        if node['type'] == 'Subject':
            require(uid == 'sym:Character:입체운행구름' and node['state'] == 'EXISTING_IDENTITY_REFERENCE', 'subject identity')
        elif node['type'] == 'Source':
            require(digest(read_local(node['path'])) == node['sha256'], 'source digest')
            require(node['authority'] == ('USER_PRIMARY' if uid == NS+'user' else 'SECONDARY_AI'), 'source authority')
        elif node['type'] == 'ReadSpan':
            require(uid in spans and all(node[k] == v for k, v in spans[uid].items()), 'span graph divergence')
        else:
            require(node['authority'] == 'SECONDARY_AI', 'AI promoted to canon')
            if node['type'] == 'CodeClaim':
                c = claims[node['claim_id']]
                require(node['label'] == c['statement'] and node['state'] == c['state'], 'claim divergence')
                actual = {e['target'] for e in graph['edges'] if e['source'] == uid and e['type'] == 'SUPPORTED_BY'}
                require(actual == set(c['read_spans']), 'claim trace divergence')
            else:
                require(node['state'] == ('PLANNED' if node['type'] == 'PlannedArtifact' else 'PROPOSED'), 'planned work promoted')
                require(node.get('sources') and all(nodes[s]['type'] == 'Source' for s in node['sources']), 'proposal provenance')
    contracts = graph['predicate_contracts']
    triples, edge_ids = set(), set()
    for e in graph['edges']:
        require(e['uid'] not in edge_ids, 'duplicate edge UID')
        edge_ids.add(e['uid'])
        triple = (e['source'], e['type'], e['target'])
        require(triple not in triples, 'duplicate triple')
        triples.add(triple)
        require(e['source'] in nodes and e['target'] in nodes, 'missing endpoint')
        require(e['type'] in contracts, 'unknown predicate')
        c = contracts[e['type']]
        require(nodes[e['source']]['type'] in c['domain'] and nodes[e['target']]['type'] in c['range'], 'domain/range')
        require(e['authority'] == 'SECONDARY_AI' and e['state'] == 'PROPOSED_RELATION', 'edge attribution')
        require(e['sources'] and all(nodes[s]['type'] == 'Source' for s in e['sources']), 'edge provenance')
    for predicate, c in contracts.items():
        require(c['direction'] == 'source_to_target' and c['meaning'], 'predicate semantics')
        for uid, n in nodes.items():
            for end, type_key, prefix in [('source', 'domain', 'out'), ('target', 'range', 'in')]:
                if n['type'] not in c[type_key]:
                    continue
                count = sum(e[end] == uid and e['type'] == predicate for e in graph['edges'])
                require(count >= c[prefix+'_min'] and (c[prefix+'_max'] is None or count <= c[prefix+'_max']), 'cardinality')
        if c['acyclic']:
            active, done = set(), set()
            def visit(uid):
                require(uid not in active, 'dependency cycle')
                if uid in done:
                    return
                active.add(uid)
                for e in graph['edges']:
                    if e['type'] == predicate and e['source'] == uid:
                        visit(e['target'])
                active.remove(uid)
                done.add(uid)
            for uid in nodes:
                visit(uid)
    answers = {}
    for q in graph['competency_questions']:
        if 'select_type' in q:
            actual = [uid for uid, n in nodes.items() if n['type'] == q['select_type'] and all(n.get(k) == v for k, v in q['filter'].items())]
        else:
            end, opposite = ('source', 'target') if 'start' in q else ('target', 'source')
            anchor = q.get('start', q.get('end'))
            actual = [e[opposite] for e in graph['edges'] if e[end] == anchor and e['type'] == q['predicate']]
        require(sorted(actual) == sorted(q['expected']), 'CQ answers: '+q['id'])
        answers[q['id']] = sorted(actual)
    # Every published source anchor must resolve to an inspected span.
    text = (ROOT/'docs/KUBERNETES_SOURCE_ANALYSIS.md').read_text()
    for path, start, end in re.findall(r'/blob/'+PIN+r'/([^\s)]+?)#L(\d+)-L(\d+)', text):
        require(any(s['path'] == path and s['start_line'] == int(start) and s['end_line'] == int(end) for s in spans.values()), 'unrecorded code anchor')
    return answers


if __name__ == '__main__':
    graph = json.loads((ROOT/'graph/post-client-server-knowledge.json').read_text())
    evidence = json.loads((RECORD/'evidence.json').read_text())
    acquisition = json.loads((RECORD/'acquisition.json').read_text())
    answers = validate(graph, evidence, acquisition)
    rejected = []
    for probe in ['dangling_edge', 'altered_span', 'invented_execution', 'authority_promotion']:
        g, e = copy.deepcopy(graph), copy.deepcopy(evidence)
        if probe == 'dangling_edge': g['edges'][0]['target'] = 'absent'
        if probe == 'altered_span': e['read_spans'][0]['sha256'] = '0'*64
        if probe == 'invented_execution': e['upstream_tests'] = 'PASS'
        if probe == 'authority_promotion': next(n for n in g['nodes'] if n['type'] == 'Knowledge')['authority'] = 'USER_PRIMARY'
        try:
            validate(g, e, acquisition)
        except ValueError:
            rejected.append(probe)
        else:
            raise ValueError('negative probe accepted: '+probe)
    print(json.dumps({'status':'PASS','scope':'EVIDENCE_AND_GRAPH_INTEGRITY_ONLY',
                      'competency_answers':answers,'rejected_negative_probes':rejected,
                      'upstream_tests':'NOT_RUN','cluster_execution':'NOT_RUN'}, ensure_ascii=False, indent=2))
