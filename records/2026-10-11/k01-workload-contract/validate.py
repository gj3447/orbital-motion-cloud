"""Validate K01 source pins, observed scope and owner-local graph contracts."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
RECORD=Path(__file__).resolve().parent
NS='omc:k01:'

def require(ok,message):
    if not ok: raise ValueError(message)

def read(path):
    p=ROOT/path
    require(p.resolve().is_relative_to(ROOT) and not p.is_symlink(),'source scope')
    return p.read_bytes()

def validate(g):
    require(g['schema']=='omc-k01-research-graph/1' and g['authority']=='SECONDARY_AI','schema/authority')
    require(g['scope']=='OWNER_LOCAL_RESEARCH' and not g['runtime_deployed'] and not g['shared_kg_written'],'effects')
    nodes={n['uid']:n for n in g['nodes']}
    require(len(nodes)==len(g['nodes']),'duplicate nodes')
    for uid,n in nodes.items():
        require(n['type'] in {'Source','Study','KnowledgeReference','Artifact','Finding'},'node type')
        require(n['authority']==('USER_PRIMARY' if uid==NS+'source:user' else 'SECONDARY_AI'),'authority promotion')
        if 'path' in n: require(hashlib.sha256(read(n['path'])).hexdigest()==n['sha256'],'source digest')
        if n['type']=='KnowledgeReference':
            raw=read(n['source_graph'])
            require(hashlib.sha256(raw).hexdigest()==n['source_graph_sha256'],'historical graph pin')
            require(any(x['uid']==uid for x in json.loads(raw)['nodes']),'reference UID')
    require(nodes[NS+'finding:retry']['state']=='SIMULATED_ONLY','simulated result promoted')
    require(nodes[NS+'finding:native-contract']['state']=='PROPOSED','native proposal promoted')
    require(nodes[NS+'study:20261011']['state']=='LOCAL_FIRST_SLICE_COMPLETE','study scope')
    triples=set(); ids=set()
    for e in g['edges']:
        require(e['uid'] not in ids,'duplicate edge UID'); ids.add(e['uid'])
        triple=(e['source'],e['type'],e['target'])
        require(triple not in triples,'duplicate edge'); triples.add(triple)
        require(e['source'] in nodes and e['target'] in nodes,'missing endpoint')
        require(e['type'] in g['predicate_contracts'],'unknown predicate')
        c=g['predicate_contracts'][e['type']]
        require(nodes[e['source']]['type']==c['domain'] and nodes[e['target']]['type']==c['range'],'domain/range')
        require(e['authority']=='SECONDARY_AI' and nodes[e['source_ref']]['type']=='Source','edge source/authority')
    for name,c in g['predicate_contracts'].items():
        require(c['direction']=='source_to_target' and c['meaning'],'predicate meaning')
        for uid,n in nodes.items():
            for endpoint,key,prefix in [('source','domain','out'),('target','range','in')]:
                if n['type']!=c[key]: continue
                count=sum(e[endpoint]==uid and e['type']==name for e in g['edges'])
                require(count>=c[prefix+'_min'] and (c[prefix+'_max'] is None or count<=c[prefix+'_max']),'cardinality')
    answers={}
    for q in g['competency_questions']:
        a=sorted(e['target'] for e in g['edges'] if e['source']==q['start'] and e['type']==q['predicate'])
        require(a==sorted(q['expected']),'CQ '+q['id']); answers[q['id']]=a
    result=json.loads((RECORD/'experiment.json').read_text())
    require(result['outcome']=='PASS' and result['input_cases']==4115 and result['verified_candidates']==20575 and result['permutation_checks']==209,'observed results')
    require(len(result['mutants'])==5 and all(x['rejected'] for x in result['mutants']),'mutants')
    require(result['heterogeneous_hardware']==result['performance_comparison']=='NOT_RUN','execution scope')
    require(result['retry_model']['kind']=='SIMULATED_STATE_TRACE','retry model scope')
    for filename,digest in result['source_sha256'].items():
        require(hashlib.sha256(read('research/k01_workload_contract/'+filename)).hexdigest()==digest,'experiment code drift')
    tests=json.loads((RECORD/'unit-tests.json').read_text())
    require(tests['tests_run']==14 and tests['failures']==tests['errors']==tests['exit_code']==0,'test observation')
    for filename,digest in tests['source_sha256'].items():
        require(hashlib.sha256(read('research/k01_workload_contract/'+filename)).hexdigest()==digest,'test code drift')
    return answers

if __name__=='__main__':
    g=json.loads((ROOT/'graph/k01-workload-contract.json').read_text())
    answers=validate(g); rejected=[]
    for probe in ['missing_endpoint','promoted_simulation']:
        bad=copy.deepcopy(g)
        if probe=='missing_endpoint': bad['edges'][0]['target']='absent'
        else: next(n for n in bad['nodes'] if n['uid']==NS+'finding:retry')['state']='OBSERVED_DISTRIBUTED'
        try: validate(bad)
        except ValueError: rejected.append(probe)
        else: raise ValueError('negative probe escaped: '+probe)
    print(json.dumps({'status':'PASS','scope':'RECORD_AND_GRAPH_INTEGRITY','competency_answers':answers,'negative_probes_rejected':rejected},ensure_ascii=False,indent=2))
