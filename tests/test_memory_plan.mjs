import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,rm,unlink,symlink} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {ROOT,NS,V,loadModel,kind,validateModel,dataset,shacl,query,sequence,verifySources,hydrate,check,sha,roadmap,packet,view} from '../scripts/memory_plan.mjs';
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
test('source fixture verifies every identity and research publication binding',()=>fixture(async({m,root})=>{const r=await verifySources(m,root);assert.equal(r.files,32);}));
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

test('workstream organization and step packets retain evidence and owner handoff',()=>{
 const r=roadmap(model);assert.equal(r.streams.length,6);assert.equal(r.streams.flatMap(s=>s.work).length,15);assert.equal(r.streams.flatMap(s=>s.work.flatMap(w=>w.steps)).length,45);
 const p=packet(model,'w06-s01');assert.deepEqual(p.prerequisites.map(s=>s.id),[NS+'step:w03-s03',NS+'step:w05-s03']);assert.equal(p.inputOutputs.length,2);assert(p.sourcePins.length>0&&p.criteria.length>0&&p.rollback.length>0);assert.equal(p.executionAuthorized,false);
 const canary=packet(model,'w08-s02');assert.equal(canary.step.runtimeEffect,'OWNER_SCOPED');assert.deepEqual([...new Set(canary.gates.map(g=>g.gateKind))].sort(),['AUTHORIZATION','EVIDENCE','IDENTITY','RESOURCE']);
});
test('views preserve canonical edge direction, identity and rationale',()=>{
 const v=view(model,'step');assert.equal(v.nodes.length,45);assert.equal(v.edgeDirection,'dependent_to_prerequisite');
 const e=v.edges.find(e=>e.source===NS+'step:w03-s01');assert.equal(e.target,NS+'step:w01-s03');assert.equal(e.record.dependentStep,e.source);assert(e.record.rationale);assert.equal(v.scope,'DISPLAY_PROJECTION_NOT_CANONICAL');
 assert.equal(view(model).nodes.length,15);assert.throws(()=>view(model,'runtime'),/Unknown view/);
});
invalid('step writer cannot exceed parent owner',m=>node(m,'step:w03-s02').assignedTo=NS+'owner:omc',/writer must match/);
invalid('step cannot target unrelated owner files',m=>node(m,'step:w03-s02').targets=[NS+'path:ops'],/targets exceed/);
invalid('read-only parent cannot hide actuation',m=>{Object.assign(node(m,'step:w01-s01'),{stepKind:'ACTUATE',runtimeEffect:'OWNER_SCOPED'});},/exceeds parent scope/);
invalid('live effect cannot be relabeled harmless',m=>node(m,'step:w08-s02').runtimeEffect='NONE',/effect classification/);
invalid('live step must retain all owner gates',m=>{node(m,'w08').requiresGate=[];node(m,'step:w08-s02').requiresGate=[];},/explicit owner gate/);
invalid('research actuator cannot omit inherited resource checks',m=>{node(m,'w14').requiresGate=[NS+'gate:authorization',NS+'gate:damon'];node(m,'step:w14-s02').requiresGate=[];},/missing inherited owner gate/);
invalid('parent prerequisite cannot be bypassed by a child',m=>node(m,'step:w06-s01').afterStep=[NS+'step:w03-s03'],/bypasses or invents/);
invalid('workstream grouping cannot invent cross-parent dependencies',m=>node(m,'step:w02-s01').afterStep=[NS+'step:w01-s03'],/bypasses or invents/);
invalid('immediate handoff must consume predecessor output',m=>node(m,'step:w03-s03').requiresOutput=[],/Missing input handoff/);
invalid('step cannot consume output from its future',m=>node(m,'step:w03-s01').requiresOutput.push(NS+'output:w03-s03'),/not produced by a prerequisite/);
invalid('declared output retains producer identity',m=>node(m,'output:w03-s02').expectedProducer=NS+'step:w03-s03',/producer\/owner mismatch/);
invalid('expected output cannot pretend to be a measured artifact',m=>node(m,'output:w03-s02').status='VERIFIED',/not a materialized result/);
invalid('milestone cannot omit a difficult member',m=>node(m,'milestone:s02').requiredWorks=[NS+'w03'],/coverage differs/);
invalid('step dependency cycles are rejected separately',m=>node(m,'step:w03-s02').afterStep=[NS+'step:w03-s03'],/Step dependency cycle/);
invalid('qualified step edges must match the dependency projection',m=>m['@graph'].splice(m['@graph'].findIndex(n=>kind(n)==='StepDependency'),1),/projection lost/);
invalid('failure resume stays in the same owner work unit',m=>node(m,'step:w03-s02').resumeAt=NS+'step:w04-s01',/Resume point/);
invalid('parent cannot claim verified while children remain planned',m=>{const source=m['@graph'].find(n=>n.artifactKind==='OBSERVATION');source.artifactKind='EXECUTION_RECORD';node(m,'w03').status='VERIFIED';node(m,'w03').completionEvidence=[source.id];},/cannot skip unfinished children/);
test('failure recovery cycles are valid without dependency cycles',()=>{
 const m=copy();node(m,'step:w03-s01').resumeAt=NS+'step:w03-s02';node(m,'step:w03-s02').resumeAt=NS+'step:w03-s01';assert.doesNotThrow(()=>validateModel(m));
});
test('conditional steps stay out of ready answers even after removing their dependencies',async()=>{
 const m=copy(),w=node(m,'w13'),s=node(m,'step:w13-s01');w.dependsOn=[];s.afterStep=[];s.requiresOutput=[];
 m['@graph']=m['@graph'].filter(n=>!(kind(n)==='Dependency'&&n.dependent===w.id)&&!(kind(n)==='StepDependency'&&n.dependentStep===s.id));
 const result=await query(m,'next-steps');assert(!result.rows.some(r=>r.id.startsWith(NS+'step:w13-')));
});
test('independent SHACL rejects a step without a declared output',async()=>{
 const {DataFactory:{namedNode}}=compiled.rdf,store=new compiled.rdf.Store([...compiled.store]);store.removeQuads(store.getQuads(namedNode(NS+'step:w03-s02'),namedNode(V+'expectsOutput'),null,null));assert.equal((await shacl({...compiled,store})).conforms,false);
});
test('independent SHACL rejects actuation disguised as no runtime effect',async()=>{
 const {DataFactory:{namedNode,literal,quad}}=compiled.rdf,store=new compiled.rdf.Store([...compiled.store]);const s=namedNode(NS+'step:w08-s02'),p=namedNode(V+'runtimeEffect');store.removeQuads(store.getQuads(s,p,null,null));store.addQuad(quad(s,p,literal('NONE')));assert.equal((await shacl({...compiled,store})).conforms,false);
});
test('step completion evidence must match current revision, checks and output',()=>fixture(async({m,root,owners})=>{
 const s=node(m,'step:w03-s01'),source=m['@graph'].find(n=>n.artifactKind==='OBSERVATION');source.artifactKind='EXECUTION_RECORD';source.storedBy=s.assignedTo;source.path='completion.json';s.status='VERIFIED';s.completionEvidence=[source.id];
 const record={schema:'omc-memory-step-completion/1',step:s.id,stepRevision:s.stepRevision,parentRevision:node(m,'w03').workRevision,status:'PASS',passedChecks:s.checks,outputContract:s.expectsOutput,outputSha256:'a'.repeat(64)};
 const write=async()=>{const raw=Buffer.from(JSON.stringify(record));source.sha256=sha(raw);source.bytes=raw.length;await mkdir(owners[s.assignedTo],{recursive:true});await writeFile(join(owners[s.assignedTo],source.path),raw);};
 await write();await verifySources(m,root);record.stepRevision++;await write();await assert.rejects(verifySources(m,root),/Step completion binding mismatch/);
 record.stepRevision--;record.passedChecks=[];await write();await assert.rejects(verifySources(m,root),/lacks output or checks/);
}));
