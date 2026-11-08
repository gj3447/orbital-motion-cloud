#!/usr/bin/env node
/** Owner-local plan queries, source hydration and RDF/SHACL checks. Never executes work items. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFile,lstat,mkdir,writeFile} from 'node:fs/promises';
import {dirname,resolve,join,relative,isAbsolute} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {parseArgs} from 'node:util';

export const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
export const V='https://gj3447.github.io/orbital_motion_cloud/memory-plan/v1/';
export const NS='urn:omc:memory-plan:';
export const GRAPH='graph/memory-recovery-plan.jsonld';
export const SHAPES='graph/memory-recovery-plan.shacl.ttl';
export const sha=data=>createHash('sha256').update(data).digest('hex');
export const CONTEXT={
 '@version':1.1,'@vocab':V,mp:V,prov:'http://www.w3.org/ns/prov#',rdfs:'http://www.w3.org/2000/01/rdf-schema#',xsd:'http://www.w3.org/2001/XMLSchema#',
 id:'@id',type:'@type',label:'rdfs:label',
 assignedTo:{'@type':'@id'},storedBy:{'@type':'@id'},maintainedBy:{'@type':'@id'},collaborator:{'@type':'@id'},
 dependsOn:{'@type':'@id'},acceptance:{'@type':'@id'},rollback:{'@type':'@id'},requiresGate:{'@type':'@id'},addresses:{'@type':'@id'},targets:{'@type':'@id'},evidence:{'@type':'@id'},
 workItem:{'@type':'@id'},source:{'@type':'@id'},dependent:{'@type':'@id'},prerequisite:{'@type':'@id'},relatedResource:{'@type':'@id'},completionEvidence:{'@type':'@id'},
 license:{'@type':'@id'},
 inStream:{'@type':'@id'},milestone:{'@type':'@id'},forStream:{'@type':'@id'},requiredWorks:{'@type':'@id'},parentWork:{'@type':'@id'},afterStep:{'@type':'@id'},expectsOutput:{'@type':'@id'},requiresOutput:{'@type':'@id'},expectedProducer:{'@type':'@id'},resumeAt:{'@type':'@id'},dependentStep:{'@type':'@id'},prerequisiteStep:{'@type':'@id'},
 derivedFrom:{'@id':'prov:wasDerivedFrom','@type':'@id'},attributedTo:{'@id':'prov:wasAttributedTo','@type':'@id'},primarySource:{'@id':'prov:hadPrimarySource','@type':'@id'},
 observedAt:{'@type':'xsd:dateTime'},recordedAt:{'@type':'xsd:dateTime'},bytes:{'@type':'xsd:integer'},ordinal:{'@type':'xsd:integer'},workRevision:{'@type':'xsd:integer'}
};
const TYPES=new Set(['Plan','SourceArtifact','Owner','WorkItem','AcceptanceCriterion','RollbackPlan','Gate','Dependency','EvidenceUse','RuntimePath','Problem','CompetencyQuestion','Agent','Resource','Workstream','Milestone','WorkStep','OutputContract','StepDependency']);
const REF_TYPES={assignedTo:['Owner'],storedBy:['Owner'],maintainedBy:['Owner'],collaborator:['Owner'],dependsOn:['WorkItem'],acceptance:['AcceptanceCriterion'],rollback:['RollbackPlan'],requiresGate:['Gate'],addresses:['Problem'],targets:['RuntimePath'],evidence:['SourceArtifact'],workItem:['WorkItem'],source:['SourceArtifact'],dependent:['WorkItem'],prerequisite:['WorkItem'],relatedResource:['Resource'],completionEvidence:['SourceArtifact'],derivedFrom:['SourceArtifact'],attributedTo:['Agent']};
REF_TYPES.license=['SourceArtifact'];
Object.assign(REF_TYPES,{inStream:['Workstream'],milestone:['Milestone'],forStream:['Workstream'],requiredWorks:['WorkItem'],parentWork:['WorkItem'],afterStep:['WorkStep'],expectsOutput:['OutputContract'],requiresOutput:['OutputContract'],expectedProducer:['WorkStep'],resumeAt:['WorkStep'],dependentStep:['WorkStep'],prerequisiteStep:['WorkStep']});
const COMMON=['id','type','label','authority','labelAuthority','status','attributedTo','recordedAt','derivedFrom'];
const FIELDS={
 Plan:['scope','executionStatus','version','relatedResource','description','previousGraphCommit'],
 SourceArtifact:['artifactKind','sourceStatus','path','bytes','sha256','storedBy','acquisitionMode','url','version','locator','upstreamCommit','project','publisher','sourceYear','doi','quote','ownerWorkId','ownerArtifactKind','ownerCommit','ownerPublicationState','observedAt','primarySource','license'],
 Owner:['ownerKey','repository'],WorkItem:['priority','ordinal','workRevision','executionClass','inputContract','outputContract','budget','assignedTo','collaborator','dependsOn','acceptance','rollback','requiresGate','addresses','targets','evidence','completionEvidence','inStream'],
 AcceptanceCriterion:['successCondition','negativeCases','verificationMethod','metric'],RollbackPlan:['procedure','preserve','precondition'],Gate:['gateKind','condition'],
 Dependency:['dependent','prerequisite','relationshipStatus','rationale'],EvidenceUse:['workItem','source','relationshipStatus','rationale','locator'],
 RuntimePath:['maintainedBy','path','baselineSha256','baselineRevision'],Problem:['detail','evidence'],CompetencyQuestion:['sparql','expectedIds'],Agent:['role'],Resource:['externalGraph','externalUid'],
 Workstream:['ordinal','objective','entryCondition','exitCondition','stopWhen','selectionMode','milestone','rationale'],
 Milestone:['forStream','requiredWorks','coverageMode','successCondition','evidenceRequired'],
 WorkStep:['parentWork','ordinal','stepRevision','stepKind','runtimeEffect','assignedTo','targets','afterStep','expectsOutput','requiresOutput','inputContract','doneWhen','checks','stopWhen','onFailure','resumeAt','budget','requiresGate','completionEvidence'],
 OutputContract:['expectedProducer','assignedTo','format','requiredFields','consumerIntent','verificationRule'],
 StepDependency:['dependentStep','prerequisiteStep','relationshipStatus','rationale']
};
const PUBLIC_HOSTS=new Set(['raw.githubusercontent.com','www.cs.cmu.edu','tangchq74.github.io','john.e-wilkes.com','static.usenix.org','www.usenix.org','docs.kernel.org','kubernetes.io','kueue.sigs.k8s.io','slurm.schedmd.com']);
export const kind=n=>Array.isArray(n.type)?n.type[0]:n.type;
const list=v=>v===undefined?[]:Array.isArray(v)?v:[v];
const relativePath=p=>typeof p==='string'&&p.length>0&&p.length<=512&&!isAbsolute(p)&&!p.split(/[\\/]/).includes('..')&&!p.includes('\\');
function url(value){const u=new URL(value);assert(u.protocol==='https:'&&!u.username&&!u.password&&PUBLIC_HOSTS.has(u.hostname),'Unapproved public source URL');return u;}
export function validateModel(m){
 assert.deepEqual(Object.keys(m).sort(),['@context','@graph'],'Unknown graph envelope field');
 assert.deepEqual(m['@context'],CONTEXT,'Only the inline owner context is accepted');
 assert(Array.isArray(m['@graph'])&&m['@graph'].length>0&&m['@graph'].length<=400,'Graph node bound');
 const nodes=new Map();
 for(const n of m['@graph']){
  assert(typeof n.id==='string'&&/^(urn:omc:|omc:knowledge:|research:work:)/.test(n.id)&&!nodes.has(n.id),'Duplicate or invalid node ID');
  assert(TYPES.has(kind(n)),'Unknown node type');assert(typeof n.label==='string'&&n.label.trim(),'Missing label');
  assert(Object.keys(n).every(k=>COMMON.includes(k)||FIELDS[kind(n)].includes(k)),'Unknown node property');
  assert(list(n.type).every(t=>TYPES.has(t)||['prov:Entity','prov:SoftwareAgent','prov:Person'].includes(t)),'Unknown secondary type');
  assert(['SECONDARY_AI','SOURCE_DOCUMENT','USER_PRIMARY'].includes(n.authority),'Unknown authority');nodes.set(n.id,n);
 }
 assert([...nodes.values()].filter(n=>kind(n)==='Plan').length===1,'Exactly one plan');
 const plan=[...nodes.values()].find(n=>kind(n)==='Plan');assert(plan.executionStatus==='NOT_STARTED'&&plan.scope==='OWNER_LOCAL_PLAN','Plan is not runtime authority');
 for(const n of nodes.values()){
  for(const [p,types] of Object.entries(REF_TYPES)){
   const refs=list(n[p]);assert(new Set(refs).size===refs.length,'Duplicate relation');
   for(const id of refs)assert(nodes.has(id)&&types.includes(kind(nodes.get(id))),`Dangling or mistyped ${p}: ${n.id}`);
  }
  if(kind(n)!=='SourceArtifact')assert(n.authority==='SECONDARY_AI','Planning interpretation cannot become user canon');
  if(kind(n)==='SourceArtifact'){
   assert(['PAPER','CODE','DOCUMENT','LICENSE','RESEARCH','USER_MESSAGE','OBSERVATION','EXECUTION_RECORD'].includes(n.artifactKind),'Unknown source kind');
   assert(n.sourceStatus==='PINNED_BYTES'&&/^[a-f0-9]{64}$/.test(n.sha256)&&Number.isSafeInteger(n.bytes)&&n.bytes>0&&n.bytes<=16*1024*1024,'Invalid byte pin');
   assert(relativePath(n.path)&&n.storedBy,'Invalid source path/owner');
   assert(['PUBLIC_HTTPS','OWNER_LOCAL'].includes(n.acquisitionMode),'Invalid acquisition mode');
   if(n.acquisitionMode==='PUBLIC_HTTPS'){url(n.url);assert(n.storedBy===NS+'owner:omc'&&n.path.startsWith('.local/'),'Public bytes stay in ignored owner hydration');}
   if(n.artifactKind==='CODE')assert(/^[a-f0-9]{40}$/.test(n.upstreamCommit)&&n.url.includes('/'+n.upstreamCommit+'/'),'Code needs an immutable commit URL');
   if(n.artifactKind==='USER_MESSAGE')assert(n.authority==='USER_PRIMARY'&&typeof n.quote==='string','User quote provenance');
   else assert(n.authority===(['RESEARCH','OBSERVATION','EXECUTION_RECORD'].includes(n.artifactKind)?'SECONDARY_AI':'SOURCE_DOCUMENT'),'Source content authority mismatch');
  }
  if(kind(n)==='Owner')assert(['OMC','ORCA_SETTING','HOH','THE_GREAT_FLOW'].includes(n.ownerKey),'Unknown owner');
  if(kind(n)==='RuntimePath')assert(relativePath(n.path)&&/^[a-f0-9]{64}$/.test(n.baselineSha256),'Runtime baseline pin required');
  if(kind(n)==='Gate')assert(n.status==='UNVERIFIED'&&typeof n.condition==='string'&&n.condition.trim(),'Plan cannot grant execution permission');
  if(kind(n)==='AcceptanceCriterion'){
   for(const k of ['successCondition','verificationMethod','metric'])assert(typeof n[k]==='string'&&n[k].trim(),'Missing acceptance '+k);
   assert(Array.isArray(n.negativeCases)&&n.negativeCases.length>0&&n.negativeCases.every(x=>typeof x==='string'&&x.trim())&&n.status==='NOT_EVALUATED','Acceptance must retain counterexamples and unmeasured status');
  }
  if(kind(n)==='RollbackPlan')for(const k of ['procedure','preserve','precondition'])assert(typeof n[k]==='string'&&n[k].trim(),'Missing rollback '+k);
  if(kind(n)==='WorkItem'){
   assert(['PLANNED','CONDITIONAL','VERIFIED'].includes(n.status)&&['P0','P1','CONDITIONAL'].includes(n.priority),'Work status/priority');
   assert(['READ_ONLY','LOCAL_TEST','SHADOW','LIVE_CHANGE','RESEARCH'].includes(n.executionClass),'Execution class');
   assert(Number.isSafeInteger(n.workRevision)&&n.workRevision>0&&n.assignedTo,'Work revision/owner');
   for(const p of ['inputContract','outputContract','budget'])assert(typeof n[p]==='string'&&n[p].trim(),`Missing ${p}`);
   for(const p of ['acceptance','rollback','evidence','targets','addresses'])assert(list(n[p]).length>0,`Missing work ${p}`);
   for(const path of list(n.targets))assert(nodes.get(path).maintainedBy===n.assignedTo,'Target writer differs from work owner');
   if(n.executionClass==='LIVE_CHANGE')assert(list(n.requiresGate).some(id=>nodes.get(id).gateKind==='AUTHORIZATION'),'Live work needs an explicit owner gate');
   if(n.status==='CONDITIONAL')assert(n.priority==='CONDITIONAL'&&list(n.requiresGate).length,'Conditional scope must retain prerequisites');
   if(n.status==='VERIFIED')assert(list(n.completionEvidence).length>0&&list(n.completionEvidence).every(id=>nodes.get(id).artifactKind==='EXECUTION_RECORD'),'Completion needs execution evidence, not research completion');
  }
  if(['Dependency','EvidenceUse','StepDependency'].includes(kind(n)))assert(n.relationshipStatus==='PROPOSED'&&typeof n.rationale==='string'&&n.rationale,'Qualified relationship meaning/status required');
  if(kind(n)==='CompetencyQuestion')assert(typeof n.sparql==='string'&&/^SELECT\b/i.test(n.sparql)&&! /\b(SERVICE|LOAD|INSERT|DELETE|CREATE|CLEAR|DROP|MOVE|COPY|ADD)\b/i.test(n.sparql)&&Array.isArray(n.expectedIds),'Bounded SELECT question contract');
 }
 const flat=new Set(),qualified=new Set(),support=new Set(),uses=new Set();
 for(const n of nodes.values()){
  if(kind(n)==='WorkItem'){for(const x of list(n.dependsOn))flat.add(n.id+'\n'+x);for(const x of list(n.evidence))support.add(n.id+'\n'+x);}
  if(kind(n)==='Dependency'){const key=n.dependent+'\n'+n.prerequisite;assert(!qualified.has(key),'Duplicate dependency claim');qualified.add(key);}
  if(kind(n)==='EvidenceUse'){const key=n.workItem+'\n'+n.source;assert(!uses.has(key),'Duplicate evidence claim');uses.add(key);}
 }
 assert.deepEqual([...flat].sort(),[...qualified].sort(),'Dependency projection lost meaning');assert.deepEqual([...support].sort(),[...uses].sort(),'Evidence projection lost provenance');
 const active=new Set(),done=new Set();
 function visit(id){assert(!active.has(id),'Dependency cycle');if(done.has(id))return;active.add(id);for(const p of list(nodes.get(id).dependsOn))visit(p);active.delete(id);done.add(id);}
 for(const n of nodes.values())if(kind(n)==='WorkItem')visit(n.id);
 validateBreakdown(nodes);
 return nodes;
}
function validateBreakdown(nodes){
 const all=[...nodes.values()],works=all.filter(n=>kind(n)==='WorkItem'),streams=all.filter(n=>kind(n)==='Workstream'),steps=all.filter(n=>kind(n)==='WorkStep');
 assert(streams.length>0&&steps.length>0,'A large-work plan requires streams and local steps');
 const text=(n,k)=>assert(typeof n[k]==='string'&&n[k].trim(),`Missing ${kind(n)} ${k}`);
 const texts=(n,k)=>assert(Array.isArray(n[k])&&n[k].length&&n[k].every(x=>typeof x==='string'&&x.trim()),`Missing ${kind(n)} ${k}`);
 const same=(a,b,message)=>assert.deepEqual([...a].sort(),[...b].sort(),message);
 const byWork=new Map(works.map(w=>[w.id,steps.filter(s=>s.parentWork===w.id)]));
 for(const stream of streams){
  for(const p of ['objective','entryCondition','exitCondition','rationale'])text(stream,p);texts(stream,'stopWhen');
  assert(['CORE','OPTIONAL'].includes(stream.selectionMode)&&stream.status==='PLANNED','Workstream scope');
  const members=works.filter(w=>w.inStream===stream.id);assert(members.length,'Empty workstream');
  const milestone=nodes.get(stream.milestone);assert(milestone?.forStream===stream.id,'Milestone stream binding');
  same(milestone.requiredWorks,members.map(w=>w.id),'Milestone coverage differs from stream');
  assert(milestone.status==='NOT_EVALUATED'&&milestone.coverageMode===(stream.selectionMode==='CORE'?'ALL_MEMBERS':'SELECTED_BRANCHES'),'Milestone is not an implementation result');
  text(milestone,'successCondition');texts(milestone,'evidenceRequired');
 }
 assert(all.filter(n=>kind(n)==='Milestone').length===streams.length,'One milestone per workstream');
 for(const w of works){
  assert(w.inStream&&byWork.get(w.id).length>=2,'Every parent has a stream and a bounded breakdown');
  const children=byWork.get(w.id);assert(children.length<=8&&new Set(children.map(s=>s.ordinal)).size===children.length,'Step count/order bound');
  if(w.status==='VERIFIED')assert(children.every(s=>s.status==='VERIFIED'),'Parent verification cannot skip unfinished children');
 }
 const allowed={READ_ONLY:['INSPECT','DEFINE','TEST'],LOCAL_TEST:['INSPECT','DEFINE','IMPLEMENT','TEST','OBSERVE','DECIDE'],SHADOW:['INSPECT','DEFINE','OBSERVE','TEST','DECIDE'],LIVE_CHANGE:['INSPECT','DEFINE','TEST','ACTUATE','DEPLOY','OBSERVE','DECIDE'],RESEARCH:['INSPECT','DEFINE','TEST','ACTUATE','OBSERVE','DECIDE']};
 const active=new Set(),done=new Set();
 function visit(id){assert(!active.has(id),'Step dependency cycle');if(done.has(id))return;active.add(id);for(const p of list(nodes.get(id).afterStep))visit(p);active.delete(id);done.add(id);}
 for(const s of steps)visit(s.id);
 const exits=w=>byWork.get(w).filter(s=>!byWork.get(w).some(other=>list(other.afterStep).includes(s.id)));
 const ancestors=id=>{const seen=new Set();function walk(x){for(const p of list(nodes.get(x).afterStep)){if(seen.has(p))continue;seen.add(p);walk(p);}}walk(id);return seen;};
 const flat=new Set(),qualified=new Set(),outputs=new Set();
 for(const s of steps){
  const w=nodes.get(s.parentWork);assert(w&&s.assignedTo===w.assignedTo,'Step writer must match its parent');
  assert(Number.isSafeInteger(s.ordinal)&&s.ordinal>0&&Number.isSafeInteger(s.stepRevision)&&s.stepRevision>0,'Step order/revision');
  assert(['PLANNED','VERIFIED'].includes(s.status)&&allowed[w.executionClass].includes(s.stepKind),'Step kind/status exceeds parent scope');
  assert(['NONE','OWNER_SCOPED'].includes(s.runtimeEffect),'Step runtime effect');
  const live=['ACTUATE','DEPLOY'].includes(s.stepKind);assert(live===(s.runtimeEffect==='OWNER_SCOPED'),'Step effect classification differs');
  const gates=[...list(w.requiresGate),...list(s.requiresGate)].map(id=>nodes.get(id).gateKind);
  if(live)for(const g of ['AUTHORIZATION','IDENTITY','RESOURCE','EVIDENCE'])assert(gates.includes(g),'Live step missing inherited owner gate: '+g);
  for(const p of ['inputContract','doneWhen','onFailure','budget'])text(s,p);texts(s,'checks');texts(s,'stopWhen');
  assert(list(s.targets).length&&list(s.targets).every(x=>list(w.targets).includes(x)),'Step targets exceed parent boundary');
  assert(nodes.get(s.resumeAt)?.parentWork===w.id,'Resume point must stay in the local owner unit');
  const output=nodes.get(s.expectsOutput);assert(output?.expectedProducer===s.id&&output.assignedTo===s.assignedTo,'Output producer/owner mismatch');
  assert(!outputs.has(output.id)&&output.status==='EXPECTED','Output contract is not a materialized result');outputs.add(output.id);
  for(const p of ['format','consumerIntent','verificationRule'])text(output,p);texts(output,'requiredFields');
  if(s.status==='VERIFIED')assert(list(s.completionEvidence).length&&list(s.completionEvidence).every(id=>nodes.get(id).artifactKind==='EXECUTION_RECORD'),'Verified step needs execution evidence');
  const internal=list(s.afterStep).filter(id=>nodes.get(id).parentWork===w.id),external=list(s.afterStep).filter(id=>nodes.get(id).parentWork!==w.id);
  if(internal.length)assert(external.length===0,'Cross-owner handoff belongs at the parent entry');
  else same(external,list(w.dependsOn).flatMap(id=>exits(id).map(s=>s.id)),'Step bypasses or invents a parent prerequisite');
  const upstream=ancestors(s.id),required=list(s.requiresOutput);
  for(const id of required)assert(upstream.has(nodes.get(id).expectedProducer),'Input output is not produced by a prerequisite');
  for(const id of list(s.afterStep)){flat.add(s.id+'\n'+id);assert(required.includes(nodes.get(id).expectsOutput),'Missing input handoff from predecessor');}
 }
 assert(all.filter(n=>kind(n)==='OutputContract').length===outputs.size,'Unbound output contract');
 for(const d of all.filter(n=>kind(n)==='StepDependency')){const key=d.dependentStep+'\n'+d.prerequisiteStep;assert(!qualified.has(key),'Duplicate step dependency');qualified.add(key);}
 same(flat,qualified,'Step dependency projection lost its rationale');
}
export async function loadModel(root=ROOT){const bytes=await readFile(join(root,GRAPH));assert(bytes.length<=1024*1024,'Graph byte bound');const m=JSON.parse(bytes);validateModel(m);return m;}
export async function loadRdf(){
 const base=process.env.OMC_RDF_RUNTIME||resolve(ROOT,'../HSWM/src/hswm/effect-runtime/package.json');const req=createRequire(base);
 const n3=req('n3'),jsonld=req('jsonld'),{QueryEngine}=req('@comunica/query-sparql-rdfjs');const {default:SHACLValidator}=await import(pathToFileURL(req.resolve('rdf-validate-shacl')));
 return {...n3,jsonld,QueryEngine,SHACLValidator};
}
export async function dataset(m,rdf){
 rdf ||= await loadRdf();
 validateModel(m);const nq=await rdf.jsonld.toRDF(m,{format:'application/n-quads',documentLoader:async()=>{throw Error('Remote JSON-LD contexts are disabled');}});
 return {rdf,store:new rdf.Store(new rdf.Parser({format:'N-Quads'}).parse(nq)),nq};
}
export async function shacl(compiled,root=ROOT){
 const {rdf,store}=compiled,shapeBytes=await readFile(join(root,SHAPES),'utf8');assert(shapeBytes.length<=128*1024,'Shape bound');
 const shapes=new rdf.Store(new rdf.Parser().parse(shapeBytes));
 const report=await new rdf.SHACLValidator(shapes,{importGraph:async()=>{throw Error('Shape imports disabled');}}).validate(store);
 return {conforms:report.conforms,results:report.results.map(r=>({focus:r.focusNode?.value,path:r.path?.value,message:r.message.map(x=>x.value)}))};
}
function ownerRoots(root){return new Map([[NS+'owner:omc',root],[NS+'owner:orca',resolve(root,'../ORCA_SETTING')],[NS+'owner:hoh',resolve(root,'../HOH')],[NS+'owner:research',resolve(root,'../THE_GREAT_FLOW')]]);}
async function checkedPath(base,path,missing=false){
 assert(relativePath(path),'Path traversal');const target=resolve(base,path);assert(!relative(base,target).startsWith('..'),'Source leaves approved root');
 let cursor=base;for(const segment of path.split('/')){cursor=join(cursor,segment);try{assert(!(await lstat(cursor)).isSymbolicLink(),'Source symlink');}catch(e){if(e.code==='ENOENT'&&missing)return target;throw e;}}
 return target;
}
export async function verifySources(m,root=ROOT){
 const nodes=validateModel(m),roots=ownerRoots(root),sources=[...nodes.values()].filter(n=>kind(n)==='SourceArtifact');let total=0;const checks=[];let ledger;
 for(const n of sources){
  const base=roots.get(n.storedBy);assert(base,'Unmapped source owner');let path;
  try{path=await checkedPath(base,n.path);}catch(e){if(e.code==='ENOENT')throw Error('NOT_HYDRATED: '+n.id);throw e;}
  const info=await lstat(path);assert(info.isFile()&&info.size===n.bytes,'Source size differs: '+n.id);total+=info.size;assert(total<=64*1024*1024,'Source corpus bound');
  const raw=await readFile(path);assert(raw.length===n.bytes&&sha(raw)===n.sha256,'Source digest differs: '+n.id);
  if(n.artifactKind==='PAPER')assert(raw.subarray(0,5).toString()==='%PDF-','PDF response required');
  if(n.artifactKind==='USER_MESSAGE')assert(raw.toString().trimEnd()===n.quote,'User quote differs');
  if(n.artifactKind==='RESEARCH'){
   if(!ledger){const data=await readFile(join(roots.get(NS+'owner:research'),'graph/research-workflow.json'));assert(data.length<=16*1024*1024,'Owner ledger bound');ledger=JSON.parse(data);}
   const runs=ledger.runs.filter(r=>r.id===n.ownerWorkId);assert(runs.length===1&&runs[0].state==='COMPLETE','Research publication incomplete');
   const a=runs[0].artifacts.filter(a=>a.kind===n.ownerArtifactKind);assert(a.length===1&&a[0].commit===n.ownerCommit&&a[0].source_sha256===n.sha256&&a[0].source_path===n.path&&a[0].authority==='SECONDARY_AI','Research publication pin mismatch');
  }
  checks.push({id:n.id,sha256:n.sha256,bytes:n.bytes,state:'MATCH'});
 }
 for(const w of nodes.values())if(kind(w)==='WorkItem'&&w.status==='VERIFIED'){
  const criteria=new Set(list(w.acceptance));for(const id of list(w.completionEvidence)){
   const n=nodes.get(id),record=JSON.parse(await readFile(await checkedPath(roots.get(n.storedBy),n.path),'utf8'));
   assert(record.schema==='omc-memory-plan-completion/1'&&record.workItem===w.id&&record.workRevision===w.workRevision&&record.status==='PASS','Completion binding mismatch');
   for(const x of record.passedCriteria||[])criteria.delete(x);
  }assert(criteria.size===0,'Completion criteria are not all evidenced');
 }
 for(const s of nodes.values())if(kind(s)==='WorkStep'&&s.status==='VERIFIED'){
  const parent=nodes.get(s.parentWork),passed=new Set();let output=false;
  for(const id of list(s.completionEvidence)){
   const n=nodes.get(id),record=JSON.parse(await readFile(await checkedPath(roots.get(n.storedBy),n.path),'utf8'));
   assert(n.storedBy===s.assignedTo&&record.schema==='omc-memory-step-completion/1'&&record.step===s.id&&record.stepRevision===s.stepRevision&&record.parentRevision===parent.workRevision&&record.status==='PASS','Step completion binding mismatch');
   for(const x of record.passedChecks||[])passed.add(x);
   if(record.outputContract===s.expectsOutput&&/^[a-f0-9]{64}$/.test(record.outputSha256||''))output=true;
  }
  assert(output&&s.checks.every(x=>passed.has(x)),'Step completion lacks output or checks');
 }
 return {state:'MATCH',files:checks.length,bytes:total,checks};
}
export async function targetDrift(m,root=ROOT){const roots=ownerRoots(root),rows=[];for(const n of m['@graph'].filter(n=>kind(n)==='RuntimePath')){try{const p=await checkedPath(roots.get(n.maintainedBy),n.path);rows.push({id:n.id,state:sha(await readFile(p))===n.baselineSha256?'MATCH':'DRIFT'});}catch{rows.push({id:n.id,state:'UNAVAILABLE'});}}return rows;}
export async function query(m,id,compiled){
 const q=m['@graph'].find(n=>kind(n)==='CompetencyQuestion'&&(n.id===id||n.id.endsWith(':'+id)));assert(q,'Unknown competency question');
 const c=compiled||await dataset(m),engine=new c.rdf.QueryEngine(),stream=await engine.queryBindings(`PREFIX mp: <${V}> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ${q.sparql}`,{sources:[c.store],fetch:async()=>{throw Error('Query network disabled');}});
 const rows=[],timer=setTimeout(()=>stream.destroy(Error('Query deadline exceeded')),5000);
 try{for await(const binding of stream){assert(rows.length<512,'Query result bound');const row={};for(const [key,value] of binding)row[key.value]=value.value;rows.push(row);}}finally{clearTimeout(timer);stream.destroy();}
 return {question:q.id,text:q.label,rows};
}
export function sequence(m){const nodes=validateModel(m),pending=new Map([...nodes].filter(([,n])=>kind(n)==='WorkItem')),done=new Set(),phases=[];
 while(pending.size){const ready=[...pending.values()].filter(n=>list(n.dependsOn).every(x=>done.has(x))).sort((a,b)=>a.ordinal-b.ordinal);assert(ready.length,'Dependency cycle');phases.push(ready.map(n=>({id:n.id,label:n.label,owner:n.assignedTo,priority:n.priority,status:n.status,gates:list(n.requiresGate)})));for(const n of ready){pending.delete(n.id);done.add(n.id);}}
 return phases;
}
export function roadmap(m){
 const nodes=validateModel(m),all=[...nodes.values()];
 return {streams:all.filter(n=>kind(n)==='Workstream').sort((a,b)=>a.ordinal-b.ordinal).map(s=>({stream:s,milestone:nodes.get(s.milestone),work:all.filter(w=>kind(w)==='WorkItem'&&w.inStream===s.id).sort((a,b)=>a.ordinal-b.ordinal).map(w=>({id:w.id,label:w.label,owner:w.assignedTo,dependsOn:w.dependsOn,status:w.status,steps:all.filter(x=>kind(x)==='WorkStep'&&x.parentWork===w.id).sort((a,b)=>a.ordinal-b.ordinal)}))})),executionAuthorized:false};
}
export function packet(m,id){
 const nodes=validateModel(m),all=[...nodes.values()],step=all.find(n=>kind(n)==='WorkStep'&&(n.id===id||n.id.endsWith(':'+id)));assert(step,'Unknown step');
 const parent=nodes.get(step.parentWork);
 return {step,parent,stream:nodes.get(parent.inStream),prerequisites:list(step.afterStep).map(x=>nodes.get(x)),inputOutputs:list(step.requiresOutput).map(x=>nodes.get(x)),expectedOutput:nodes.get(step.expectsOutput),targetBaselines:step.targets.map(x=>nodes.get(x)),evidence:all.filter(n=>kind(n)==='EvidenceUse'&&n.workItem===parent.id),sourcePins:list(parent.evidence).map(x=>nodes.get(x)),criteria:list(parent.acceptance).map(x=>nodes.get(x)),rollback:list(parent.rollback).map(x=>nodes.get(x)),gates:[...new Set([...list(parent.requiresGate),...list(step.requiresGate)])].map(x=>nodes.get(x)),readiness:'DEPENDENCIES_ONLY; fresh inputs, owner policy and gates must be checked at execution',executionAuthorized:false};
}
export function view(m,level='work'){
 assert(['work','step'].includes(level),'Unknown view level');validateModel(m);
 const step=level==='step',all=m['@graph'],nodes=all.filter(n=>kind(n)===(step?'WorkStep':'WorkItem'));
 const edges=all.filter(n=>kind(n)===(step?'StepDependency':'Dependency'));
 return {schema:'memory-plan-view/1',authority:'SECONDARY_AI',scope:'DISPLAY_PROJECTION_NOT_CANONICAL',sourceGraphSha256:sha(JSON.stringify(m)),edgeDirection:'dependent_to_prerequisite',nodes:nodes.map(n=>({uid:n.id,type:kind(n),label:(step?n.id.split(':').at(-1):n.id.split(':').at(-1).toUpperCase())+' '+n.label,record:n})),edges:edges.map(n=>({uid:n.id,type:step?'afterStep':'dependsOn',source:n[step?'dependentStep':'dependent'],target:n[step?'prerequisiteStep':'prerequisite'],status:n.relationshipStatus,record:n}))};
}
export async function hydrate(m,root=ROOT){
 const nodes=validateModel(m),roots=ownerRoots(root);let total=0;const results=[];
 for(const n of nodes.values())if(kind(n)==='SourceArtifact'&&n.acquisitionMode==='PUBLIC_HTTPS'){
  total+=n.bytes;assert(total<=64*1024*1024,'Hydration budget');const path=await checkedPath(roots.get(n.storedBy),n.path,true);
  try{const raw=await readFile(path);assert(raw.length===n.bytes&&sha(raw)===n.sha256,'Existing source changed; never overwrite');results.push({id:n.id,state:'MATCH'});continue;}catch(e){if(e.code!=='ENOENT')throw e;}
  let current=url(n.url),response;
  for(let redirects=0;redirects<4;redirects++){response=await fetch(current,{redirect:'manual',signal:AbortSignal.timeout(25000)});if(response.status>=300&&response.status<400){current=url(new URL(response.headers.get('location'),current).href);await response.body?.cancel();continue;}break;}
  assert(response?.ok&&response.body,'Source HTTP failure');const chunks=[];let size=0;
  for await(const chunk of response.body){size+=chunk.length;assert(size<=n.bytes&&size<=16*1024*1024,'Source exceeds pin');chunks.push(chunk);}
  const bytes=Buffer.concat(chunks);assert(bytes.length===n.bytes&&sha(bytes)===n.sha256,'Source changed; review a new version');await mkdir(dirname(path),{recursive:true});await checkedPath(roots.get(n.storedBy),n.path,true);await writeFile(path,bytes,{flag:'wx'});results.push({id:n.id,state:'RESTORED'});
 }
 return {files:results,executionAuthorized:false};
}
export async function check(m,root=ROOT){
 const compiled=await dataset(m),shapes=await shacl(compiled,root);assert(shapes.conforms,JSON.stringify(shapes));const sources=await verifySources(m,root),questions=[];
 for(const q of m['@graph'].filter(n=>kind(n)==='CompetencyQuestion')){const result=await query(m,q.id,compiled);assert.deepEqual([...new Set(result.rows.map(r=>r.id))].sort(),[...q.expectedIds].sort(),'Wrong competency answer: '+q.id);questions.push(result);}
 return {status:'PASS',nodes:m['@graph'].length,triples:compiled.store.size,shacl:shapes,sourceBytes:sources.state,sourceFiles:sources.files,sourceTotalBytes:sources.bytes,questions,targetDrift:await targetDrift(m,root),scope:'LOCAL_PLAN_RDF_SHACL_AND_SOURCE_BYTES; NOT_RUNTIME_OR_EFFECT_VALIDATION',executionAuthorized:false,liveKgPublished:false};
}
const help='node scripts/memory_plan.mjs check|next|next-steps|sequence|roadmap|packet STEP_ID|sources|why WORK_ID|query QUESTION_ID|hydrate|export --format turtle|nquads|mermaid|work-view|step-view [--out PATH]\nOffline except explicit hydrate. Queries never execute plan work. RDFJS libraries use OMC_RDF_RUNTIME or the existing sibling HSWM package dependencies; no HSWM runtime is invoked.';
async function main(){const {values,positionals}=parseArgs({allowPositionals:true,options:{help:{type:'boolean'},format:{type:'string',default:'turtle'},out:{type:'string'}}});if(values.help||!positionals.length){console.log(help);return;}
 const [command,arg]=positionals,m=await loadModel();let result;
 if(command==='check')result=await check(m);
 else if(command==='query')result=await query(m,arg);
 else if(command==='next'||command==='next-steps'){result=await query(m,command);result={...result,executionAuthorized:false,readiness:'DEPENDENCIES_ONLY; owner gates and fresh runtime checks remain'};}
 else if(command==='sequence')result={phases:sequence(m),executionAuthorized:false};
 else if(command==='roadmap')result=roadmap(m);
 else if(command==='packet')result=packet(m,arg);
 else if(command==='sources')result={sources:m['@graph'].filter(n=>kind(n)==='SourceArtifact'),readback:await verifySources(m)};
 else if(command==='why'){const nodes=validateModel(m),w=[...nodes.values()].find(n=>kind(n)==='WorkItem'&&(n.id===arg||n.id.endsWith(':'+arg)));assert(w,'Unknown work');result={work:w,prerequisites:list(w.dependsOn).map(id=>nodes.get(id)),evidence:m['@graph'].filter(n=>kind(n)==='EvidenceUse'&&n.workItem===w.id),criteria:list(w.acceptance).map(id=>nodes.get(id)),rollback:list(w.rollback).map(id=>nodes.get(id)),gates:list(w.requiresGate).map(id=>nodes.get(id)),executionAuthorized:false};}
 else if(command==='hydrate')result=await hydrate(m);
 else if(command==='export'){
  let output;if(values.format==='mermaid'){const nodes=validateModel(m);output='flowchart TD\n';for(const n of nodes.values())if(kind(n)==='WorkItem'){const id=n.id.split(':').at(-1);output+=`  ${id}["${n.label.replace(/["<>]/g,'')}"]\n`;for(const p of list(n.dependsOn))output+=`  ${p.split(':').at(-1)} --> ${id}\n`;}}
  else if(['work-view','step-view'].includes(values.format))output=JSON.stringify(view(m,values.format.split('-')[0]),null,2)+'\n';
  else{assert(['turtle','nquads'].includes(values.format),'Unsupported export');const c=await dataset(m);output=values.format==='nquads'?c.nq:await new Promise((res,rej)=>{const writer=new c.rdf.Writer({prefixes:{mp:V,prov:CONTEXT.prov}});writer.addQuads([...c.store]);writer.end((err,text)=>err?rej(err):res(text));});}
  if(values.out){const out=resolve(values.out);assert(out.startsWith(resolve(ROOT,'.local')+'/'),'Generated exports belong under .local');await mkdir(dirname(out),{recursive:true});await writeFile(out,output);result={path:relative(ROOT,out),bytes:Buffer.byteLength(output)};}else{process.stdout.write(output);return;}
 }else throw Error('Unknown action');console.log(JSON.stringify(result,null,2));}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(e=>{console.error(e.message);process.exitCode=1;});
