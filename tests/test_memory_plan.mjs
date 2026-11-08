import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,rm,unlink,symlink} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {ROOT,NS,V,loadModel,kind,validateModel,dataset,shacl,query,sequence,verifySources,hydrate,check,sha} from '../scripts/memory_plan.mjs';
const model=await loadModel(),copy=()=>structuredClone(model),node=(m,id)=>m['@graph'].find(n=>n.id===NS+id);
const compiled=await dataset(model);

test('actual JSON-LD satisfies SHACL Core and roundtrips as RDF',async()=>{
 assert.equal((await shacl(compiled)).conforms,true);
 const text=await new Promise((res,rej)=>{const w=new compiled.rdf.Writer();w.addQuads([...compiled.store]);w.end((e,t)=>e?rej(e):res(t));});
 const round=new compiled.rdf.Store(new compiled.rdf.Parser().parse(text));
 assert.equal(round.size,compiled.store.size);for(const q of compiled.store)assert(round.has(q));
});
for(const question of model['@graph'].filter(n=>kind(n)==='CompetencyQuestion'))test('competency: '+question.label,async()=>{
 const result=await query(model,question.id,compiled);
 assert.deepEqual([...new Set(result.rows.map(r=>r.id))].sort(),question.expectedIds.slice().sort());
});
test('dependency phases preserve owner order and keep conditional research last',()=>{
 const phases=sequence(model);assert.deepEqual(phases[0].map(n=>n.id),[NS+'w01',NS+'w02']);
 const index=new Map(phases.flatMap((phase,i)=>phase.map(n=>[n.id,i])));
 for(const work of model['@graph'].filter(n=>kind(n)==='WorkItem'))for(const dep of work.dependsOn)assert(index.get(dep)<index.get(work.id));
 assert(index.get(NS+'w09')<index.get(NS+'w10'));assert(index.get(NS+'w11')<index.get(NS+'w12'));
});
const invalid=(name,mutate,pattern)=>test(name,()=>{const m=copy();mutate(m);assert.throws(()=>validateModel(m),pattern);});
invalid('duplicate identifiers are rejected before RDF merges them',m=>m['@graph'].push(structuredClone(node(m,'w01'))),/Duplicate/);
invalid('dangling dependency is rejected',m=>node(m,'w03').dependsOn.push(NS+'missing'),/Dangling/);
invalid('wrong owner type is rejected',m=>node(m,'w03').assignedTo=node(m,'w04').evidence[0],/mistyped/);
invalid('cross-owner target write is rejected',m=>node(m,'w03').targets=[NS+'path:ops'],/writer differs/);
invalid('missing rollback is rejected',m=>delete node(m,'w04').rollback,/Missing work rollback/);
invalid('missing falsifiers are rejected',m=>node(m,'accept:w04').negativeCases=[],/counterexamples/);
invalid('interpretation cannot become user canon',m=>node(m,'w04').authority='USER_PRIMARY',/user canon/);
invalid('researched source does not make implementation verified',m=>{node(m,'w04').status='VERIFIED';node(m,'w04').completionEvidence=['research:work:omc-memory-admission-20261107:HOW_TO'];},/execution evidence/);
invalid('planning graph cannot grant an owner gate',m=>node(m,'gate:authorization').status='VERIFIED',/execution permission/);
invalid('unqualified evidence projection is rejected',m=>m['@graph'].splice(m['@graph'].findIndex(n=>kind(n)==='EvidenceUse'),1),/lost provenance/);
invalid('qualified dependency cannot drift from its projection',m=>m['@graph'].find(n=>kind(n)==='Dependency').prerequisite=NS+'w02',/lost meaning/);
invalid('dependency cycles fail even with matching qualified edges',m=>{node(m,'w01').dependsOn=[NS+'w03'];const d=structuredClone(m['@graph'].find(n=>kind(n)==='Dependency'));Object.assign(d,{id:NS+'dependency:cycle',dependent:NS+'w01',prerequisite:NS+'w03'});m['@graph'].push(d);},/cycle/);
invalid('remote JSON-LD context cannot trigger fetching',m=>m['@context']='https://example.invalid/context',/inline owner context/);
invalid('unmodeled fields do not silently disappear in RDF',m=>node(m,'w01').runtimeApproved=true,/Unknown node property/);
invalid('public code must pin a commit rather than a branch',m=>m['@graph'].find(n=>n.artifactKind==='CODE').upstreamCommit='main',/immutable commit/);
invalid('source path traversal is rejected',m=>m['@graph'].find(n=>n.artifactKind==='PAPER').path='../escape',/source path/);
invalid('SPARQL remote SERVICE is not a local competency query',m=>node(m,'question:next').sparql='SELECT ?id WHERE { SERVICE <https://example.invalid> { ?id ?p ?o } }',/SELECT question/);
test('independent SHACL catches duplicate owners in the RDF dataset',async()=>{
 const {DataFactory:{quad,namedNode}}=compiled.rdf,store=new compiled.rdf.Store([...compiled.store]);
 store.addQuad(quad(namedNode(NS+'w03'),namedNode(V+'assignedTo'),namedNode(NS+'owner:omc')));
 const result=await shacl({...compiled,store});assert.equal(result.conforms,false);assert(result.results.some(r=>r.focus===NS+'w03'));
});
test('independent SHACL catches an absent rollback in RDF',async()=>{
 const {DataFactory:{namedNode}}=compiled.rdf,store=new compiled.rdf.Store([...compiled.store]);
 store.removeQuads(store.getQuads(namedNode(NS+'w04'),namedNode(V+'rollback'),null,null));assert.equal((await shacl({...compiled,store})).conforms,false);
});
async function fixture(fn){
 const base=await mkdtemp(join(tmpdir(),'omc-memory-plan-')),root=join(base,'OMC'),m=copy();
 const owners={[NS+'owner:omc']:root,[NS+'owner:research']:join(base,'THE_GREAT_FLOW'),[NS+'owner:orca']:join(base,'ORCA_SETTING'),[NS+'owner:hoh']:join(base,'HOH')};
 const artifacts=[];
 try{
  for(const n of m['@graph'].filter(n=>kind(n)==='SourceArtifact')){
   const raw=Buffer.from(n.artifactKind==='USER_MESSAGE'?n.quote+'\n':n.artifactKind==='PAPER'?'%PDF-fixture\n':'bounded fixture '+n.id);
   n.sha256=sha(raw);n.bytes=raw.length;const path=join(owners[n.storedBy],n.path);await mkdir(resolve(path,'..'),{recursive:true});await writeFile(path,raw);
   if(n.artifactKind==='RESEARCH')artifacts.push({kind:n.ownerArtifactKind,commit:n.ownerCommit,source_sha256:n.sha256,source_path:n.path,authority:'SECONDARY_AI'});
  }
  const ledger=join(owners[NS+'owner:research'],'graph/research-workflow.json');await mkdir(resolve(ledger,'..'),{recursive:true});await writeFile(ledger,JSON.stringify({runs:[{id:'omc-memory-admission-20261107',state:'COMPLETE',artifacts}]}));
  await fn({m,root,owners,ledger});
 }finally{await rm(base,{recursive:true,force:true});}
}
test('source fixture verifies every identity and research publication binding',()=>fixture(async({m,root})=>{const r=await verifySources(m,root);assert.equal(r.files,31);}));
test('corrupt bytes fail without repinning or overwriting',()=>fixture(async({m,root,owners})=>{
 const n=m['@graph'].find(n=>n.artifactKind==='CODE'),p=join(owners[n.storedBy],n.path),raw=await readFile(p);raw[0]^=1;await writeFile(p,raw);
 await assert.rejects(verifySources(m,root),/digest differs/);await assert.rejects(hydrate(m,root),/never overwrite/);assert.deepEqual(await readFile(p),raw);
}));
test('missing source is NOT_HYDRATED and check never downloads it',()=>fixture(async({m,root,owners})=>{
 const n=m['@graph'].find(n=>n.artifactKind==='PAPER');await unlink(join(owners[n.storedBy],n.path));await assert.rejects(verifySources(m,root),/NOT_HYDRATED/);
}));
test('linked source bytes cannot escape the declared owner',()=>fixture(async({m,root,owners})=>{
 const n=m['@graph'].find(n=>n.artifactKind==='CODE'),p=join(owners[n.storedBy],n.path),raw=await readFile(p);await writeFile(p+'.other',raw);await unlink(p);await symlink(p+'.other',p);await assert.rejects(verifySources(m,root),/symlink/);
}));
test('unfinished research workflow cannot masquerade as completed publication',()=>fixture(async({m,root,ledger})=>{
 const v=JSON.parse(await readFile(ledger));v.runs[0].state='ARTIFACTS_COMMITTED';await writeFile(ledger,JSON.stringify(v));await assert.rejects(verifySources(m,root),/publication incomplete/);
}));
test('wrong golden answer fails although shape and node counts remain valid',async()=>{
 const m=copy();node(m,'question:next').expectedIds=[NS+'w03'];await assert.rejects(check(m),/Wrong competency answer/);
});

test('far-memory feasibility does not require the optional DAMON path',()=>{
 const nodes=validateModel(model),seen=new Set();
 const visit=id=>{for(const p of nodes.get(id).dependsOn||[]){if(seen.has(p))continue;seen.add(p);visit(p);}};
 visit(NS+'w15');assert(seen.has(NS+'w13'));assert(!seen.has(NS+'w14'));
});
