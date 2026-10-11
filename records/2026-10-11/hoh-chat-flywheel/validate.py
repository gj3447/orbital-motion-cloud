"""Validate a proposed flywheel graph, source bytes, roles, queries and failure cases."""
from pathlib import Path
from collections import Counter
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
PREFIX='omc:chat-flywheel:'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def answers(g):
    out=[]
    for q in g['competency_questions']:
        cur={q['start']}
        for p in q['via']:cur={e['target'] for e in g['edges'] if e['source'] in cur and e['type']==p}
        out.append(dict(id=q['id'],subjects=sorted(cur)))
    return out

def check(g,c,verify_bytes=True):
    require(g['schema']==c['graph_schema'] and g['scope']=='OWNER_LOCAL_DESIGN_GRAPH','schema/scope')
    require(g['runtime_status']=='NOT_IMPLEMENTED_BY_THIS_PLAN','false runtime status')
    index={n['uid']:n for n in g['nodes']};require(len(index)==len(g['nodes']),'duplicate node')
    counts=Counter();incs=Counter();eids=set();triples=set();source_checks=[]
    for n in g['nodes']:
        require(n['type'] in c['node_types'],'unknown node type')
        require(all(k in n for k in c['common_required']) and n['label'],'required properties')
        if n['type']=='Source':
            require(n['status']=='PINNED','source status')
            require(n['authority'] in {'USER_PRIMARY','SECONDARY_AI','SOURCE_CODE','MIXED_ATTRIBUTED_SOURCE'},'source authority')
            path=Path(n['path']);require(not path.is_absolute() and '..' not in path.parts,'unsafe source path')
            if verify_bytes:
                p=ROOT/path;require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT),'source unavailable')
                require(digest(p)==n['sha256'],'source digest mismatch: '+n['uid']);source_checks.append(n['uid'])
        else:
            require(n['authority']=='SECONDARY_AI' and n['status']=='PROPOSED','AI authority or plan promoted')
        for ref in n.get('source_refs',[]):require(index.get(ref,{}).get('type')=='Source','source reference')
        if n['type'] in {'Component','Contract','WorkItem','Evaluation','Stage','RelationTemplate'}:require(bool(n.get('source_refs')),'missing source refs')
        if n['type']=='WorkItem':require(n['execution_status']=='PLANNED' and n['horizon'] in {'NEAR','LATER'},'work falsely complete')
        if n['type']=='Evaluation':require(n['execution_status']=='NOT_RUN' and n['result'] is None and n['evidence_needed'],'evaluation falsely executed')
        if n['type']=='Contract':require(n['schema_status']=='PROPOSED_NOT_NATIVE_ADMITTED' and n['required_fields'],'false native admission')
        if n['type']=='SourceObservation':require(n['scope']=='STATIC_SOURCE_ONLY','static observation promoted')
    for e in g['edges']:
        require(e['uid'] not in eids and e['uid'] not in index,'duplicate edge');eids.add(e['uid'])
        a,b,p=e['source'],e['target'],e['type'];require(a in index and b in index,'missing endpoint')
        require(p in c['predicates'],'unknown predicate');spec=c['predicates'][p]
        require(index[a]['type'] in spec['domain'] and index[b]['type'] in spec['range'],'domain/range')
        require(e['authority']=='SECONDARY_AI' and e['status']=='PROPOSED','edge authority or completion')
        occurrence=(p,a,b,e.get('role'),e.get('index'));require(occurrence not in triples,'duplicate relation');triples.add(occurrence)
        counts[a,p]+=1;incs[b,p]+=1
        if p=='MAY_ENABLE':require(bool(e['condition']) and index.get(e['evaluation_uid'],{}).get('type')=='Evaluation','unqualified loop edge')
        if p=='DERIVED_FROM' and verify_bytes:
            snippet=index[a].get('verbatim_excerpt',index[a].get('excerpt'))
            require(snippet and snippet in (ROOT/index[b]['path']).read_text(),'attributed excerpt absent')
    for p,spec in c['predicates'].items():
        for uid,n in index.items():
            for side,k,cs in [('out','domain',counts),('in','range',incs)]:
                if n['type'] not in spec[k]:continue
                count=cs[uid,p];hi=spec[side+'_max']
                require(count>=spec[side+'_min'] and (hi is None or count<=hi),'cardinality '+uid+' '+p)
    def visit(u,visiting,done,p):
        require(u not in visiting,'dependency cycle')
        if u in done:return
        visiting.add(u)
        for e in g['edges']:
            if e['type']==p and e['source']==u:visit(e['target'],visiting,done,p)
        visiting.remove(u);done.add(u)
    for p in c['acyclic_predicates']:
        done=set()
        for u in index:visit(u,set(),done,p)
    for cycle in g['cycles']:
        path=cycle['stages'];require(len(path)>=3 and path[0]==path[-1],'unclosed flywheel')
        for a,b in zip(path,path[1:]):require(any(e['source']==a and e['target']==b and e['type']=='MAY_ENABLE' for e in g['edges']),'missing flywheel step')
    for n in g['nodes']:
        if n['type']=='RelationTemplate':
            require(n['template_only'] is True,'fake executed turn')
            parts=sorted([e for e in g['edges'] if e['source']==n['uid'] and e['type']=='PARTICIPANT'],key=lambda e:e['index'])
            require([e['index'] for e in parts]==list(range(9)),'participant order')
            require([e['role'] for e in parts]==c['participant_roles'],'participant roles')
            require([e['target'] for e in parts]==[PREFIX+'contract:'+k for k in c['participant_targets']],'participant binding')
            require(len({e['occurrence_id'] for e in parts})==9,'participant occurrence')
    require(len({q['id'] for q in g['competency_questions']})==len(g['competency_questions']),'duplicate CQ')
    ans=answers(g)
    for q,a in zip(g['competency_questions'],ans):require(a['subjects']==sorted(q['expected']),'CQ identity mismatch: '+q['id'])
    return dict(nodes=len(index),edges=len(g['edges']),sources=source_checks,answers=ans,cycles=[x['id'] for x in g['cycles']])

def main():
    gp=ROOT/'graph/hoh-chat-flywheel.json';cp=ROOT/'graph/hoh-chat-flywheel-contract.json';g=json.loads(gp.read_text());c=json.loads(cp.read_text());result=check(g,c)
    tests=[]
    def reject(label,f,bytes=False):
        bad=copy.deepcopy(g);f(bad)
        try:check(bad,c,verify_bytes=bytes)
        except ValueError as e:tests.append(dict(case=label,status='REJECTED',reason=str(e)))
        else:raise ValueError('undetected invalid graph: '+label)
    reject('duplicate UID',lambda x:x['nodes'].append(copy.deepcopy(x['nodes'][0])))
    reject('dangling endpoint',lambda x:x['edges'][0].update(target='missing'))
    reject('AI interpretation promoted',lambda x:next(n for n in x['nodes'] if n['type']=='Requirement').update(authority='USER_PRIMARY'))
    reject('unrun work complete',lambda x:next(n for n in x['nodes'] if n['type']=='WorkItem').update(execution_status='COMPLETE'))
    reject('unrun evaluation result',lambda x:next(n for n in x['nodes'] if n['type']=='Evaluation').update(result={'success':True}))
    reject('fake native admission',lambda x:next(n for n in x['nodes'] if n['type']=='Contract').update(schema_status='ADMITTED'))
    reject('dependency cycle',lambda x:x['edges'].append(dict(uid='bad-cycle',source=PREFIX+'work:F0',target=PREFIX+'work:F4',type='REQUIRES',authority='SECONDARY_AI',status='PROPOSED')))
    reject('missing feedback closure',lambda x:x['edges'].remove(next(e for e in x['edges'] if e['type']=='MAY_ENABLE' and e['target']==PREFIX+'stage:turn')))
    reject('n-ary role destroyed',lambda x:next(e for e in x['edges'] if e['type']=='PARTICIPANT').update(role='member'))
    reject('participant order collision',lambda x:next(e for e in x['edges'] if e['type']=='PARTICIPANT').update(index=8))
    reject('wrong placement owner',lambda x:next(e for e in x['edges'] if e['source']==PREFIX+'contract:intent' and e['type']=='RESPONSIBLE_OWNER').update(target='sym:KG_CREATIVE:hoh'))
    reject('source byte mismatch',lambda x:x['nodes'][0].update(sha256='0'*64),bytes=True)
    print(json.dumps(dict(schema='omc-chat-flywheel-validation/1',status='PASS',recorded_at=datetime.now(timezone.utc).isoformat(),graph_sha256=digest(gp),contract_sha256=digest(cp),validator_sha256=digest(Path(__file__)),checked=result,negative_controls=tests,scope='Source/plan/graph integrity only. No actual cognitive execution, model efficacy or economics measured.'),ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except (KeyError,ValueError,OSError,TypeError,StopIteration) as e:
        print(json.dumps(dict(status='FAIL',reason=str(e)),ensure_ascii=False));sys.exit(1)
