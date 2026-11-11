"""Read-only development plan checks and queries. Never starts work or grants authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GRAPH = "graph/development-plan.jsonld"
SHAPES = "graph/development-plan.shacl.ttl"
NS = "urn:omc:development-plan:"
VOCAB = "https://gj3447.github.io/orbital_motion_cloud/development-plan/v1/"
MP = "https://gj3447.github.io/orbital_motion_cloud/memory-plan/v1/"
COMMON = {"id", "type", "label", "authority"}
FIELDS = {
 "prov:SoftwareAgent": set(),
 "Owner": {"repository"},
 "SourceArtifact": {"sourceKind","sourceStatus","path","sha256","bytes","locator","quote"},
 "DefinitionElement": {"elementKind","developmentScope","derivedFrom"},
 "ExistingWork": {"graphPath","externalPlan","externalIds","identityMerge"},
 "WorkItem": {"status","relationshipStatus","ordinal","assignedTo","dependsOn","realizes","delegatesTo","evidence","derivedFrom","attributedTo","executionClass","targetPaths","inputContract","expectsOutput","requiresOutput","acceptance","budget","onFailure","stopWhen","userDecision"},
 "OutputContract": {"status","expectedProducer","assignedTo","requiredFields"},
 "AcceptanceCriterion": {"status","successCondition","negativeCases"},
 "CompetencyQuestion": {"sparql","expectedIds"},
 "Plan": {"status","executionStatus","runtimeEffects","recordedAt","workItems","derivedFrom","attributedTo","scope","description"},
 "RoleBoundary": {"owner","checkout","responsibilities","excludes","ownsPaths","derivedFrom"},
}
REFS = {"assignedTo":"Owner","dependsOn":"WorkItem","realizes":"DefinitionElement","delegatesTo":"ExistingWork",
 "acceptance":"AcceptanceCriterion","evidence":"SourceArtifact","expectsOutput":"OutputContract","requiresOutput":"OutputContract",
 "expectedProducer":"WorkItem","workItems":"WorkItem","derivedFrom":"SourceArtifact","attributedTo":"prov:SoftwareAgent","owner":"Owner"}
# A source keeps the authority of what it is; a label or summary never raises it.
SOURCE_AUTHORITY = {"USER_MESSAGE":"USER_PRIMARY","ARCHIVE_DOCUMENT":"SOURCE_DOCUMENT","RECORD_WITH_USER_QUOTE":"SECONDARY_AI","OWNER_DOCUMENT":"SECONDARY_AI"}
CLASSES = {"DELEGATED_PLAN","OWNER_RUNTIME_CHANGE","MEASUREMENT","PROPOSAL"}
def require(ok, message):
 if not ok: raise ValueError(message)
def many(value):
 return value if isinstance(value,list) else [value]
def unique_object(pairs):
 result={}
 for k,v in pairs:
  require(k not in result, "Duplicate JSON key")
  result[k]=v
 return result
def load(path=ROOT/GRAPH):
 raw=Path(path).read_bytes();require(len(raw)<=1024*1024,"Plan size bound")
 return json.loads(raw,object_pairs_hook=unique_object)
def kinds(node):
 return set(many(node.get("type")))
def inside(path, checkout):
 """Whether an OMC-relative path lies in an owner checkout, by path arithmetic only."""
 path=os.path.normpath(path);checkout=os.path.normpath(checkout)
 if checkout==".":return not path.startswith("..")
 return path.startswith(checkout+os.sep)
def model_check(model):
 require(set(model)=={"@context","@graph"},"Graph envelope")
 context=model["@context"]
 require(context.get("@version")==1.1 and context.get("@vocab")==VOCAB and context.get("mp")==MP,"Inline owner context required")
 for k,v in context.items():
  require(not isinstance(v,list),"Context arrays unsupported")
  if isinstance(v,dict):require(set(v)<={"@id","@type"},"Remote/nested context forbidden")
 rows=model["@graph"];require(isinstance(rows,list) and 1<=len(rows)<=150,"Node bound")
 nodes={}
 for row in rows:
  require(isinstance(row,dict),"Node object")
  uid=row.get("id");kind=row.get("type")
  require(isinstance(uid,str) and uid.startswith("urn:omc:") and uid not in nodes,"Duplicate/invalid identity")
  require(kind in FIELDS and set(row)<=COMMON|FIELDS[kind],"Unknown node type/property")
  require(isinstance(row.get("label"),str) and row["label"].strip(),"Missing label")
  expected=SOURCE_AUTHORITY.get(row.get("sourceKind")) if kind=="SourceArtifact" else "SECONDARY_AI"
  require(row.get("authority")==expected,"Authority promotion")
  nodes[uid]=row
 for row in rows:
  for prop,target_type in REFS.items():
   if prop not in row:continue
   vals=many(row[prop]);require(len(vals)==len(set(vals)),"Duplicate relation")
   require(all(v in nodes and nodes[v]["type"]==target_type for v in vals),"Dangling or reversed "+prop)
 works=[n for n in rows if n["type"]=="WorkItem"]
 plans=[n for n in rows if n["type"]=="Plan"]
 require(len(plans)==1,"Exactly one plan")
 plan=plans[0]
 require(plan.get("executionStatus")=="NOT_STARTED" and plan.get("runtimeEffects") is False and plan.get("status")=="PROPOSED","Plan is not runtime evidence")
 require(works and set(plan["workItems"])=={w["id"] for w in works},"Plan coverage")
 require(len({w["ordinal"] for w in works})==len(works),"Duplicate work order")
 active=set();done=set()
 def visit(uid):
  require(uid not in active,"Dependency cycle")
  if uid in done:return
  active.add(uid)
  for dep in nodes[uid].get("dependsOn",[]):visit(dep)
  active.remove(uid);done.add(uid)
 realized=set()
 for w in works:
  require(w.get("status")=="PLANNED" and w.get("relationshipStatus")=="PROPOSED","Unproven completion")
  require(w.get("executionClass") in CLASSES,"Execution class")
  for p in ("inputContract","budget","onFailure","userDecision"):
   require(isinstance(w.get(p),str) and bool(w[p].strip()),"Missing work "+p)
  require(w.get("realizes") and w.get("evidence") and w.get("targetPaths") and w.get("stopWhen"),"Work definition/evidence/target")
  # Delegation and the class that says "do not redo this here" must agree.
  require((w["executionClass"]=="DELEGATED_PLAN")==bool(w.get("delegatesTo")),"Delegation mismatch")
  for e in w["realizes"]:
   require(nodes[e]["developmentScope"]=="IN_PLAN","Work realizes an element outside development scope")
   realized.add(e)
  out=nodes[w["expectsOutput"]]
  require(out.get("expectedProducer")==w["id"] and out.get("assignedTo")==w["assignedTo"],"Output producer mismatch")
  require(set(w["requiresOutput"])=={nodes[d]["expectsOutput"] for d in w["dependsOn"]},"Input handoff differs from dependencies")
  visit(w["id"])
 require(len([n for n in rows if n["type"]=="OutputContract"])==len(works),"Output coverage")
 require(len({w["acceptance"] for w in works})==len(works),"Acceptance reuse")
 # One role per owner. Its checkout is where its writer works; nothing else does.
 roles={n["owner"]:n for n in rows if n["type"]=="RoleBoundary"}
 owners={n["id"] for n in rows if n["type"]=="Owner"}
 require(len(roles)==len([n for n in rows if n["type"]=="RoleBoundary"]) and set(roles)==owners,"Role per owner")
 checkouts=[os.path.normpath(r.get("checkout","")) for r in roles.values()]
 require(len(set(checkouts))==len(checkouts) and all(c=="." or re.fullmatch(r"\.\./[A-Za-z0-9_.-]+",c) for c in checkouts),"Role checkout")
 owned=[p for r in roles.values() for p in r.get("ownsPaths",[])]
 require(len(owned)==len(set(owned)) and all(isinstance(p,str) and p.startswith("urn:omc:") for p in owned),"Path owned by more than one role")
 for r in roles.values():
  resp,excl=r.get("responsibilities"),r.get("excludes")
  require(isinstance(resp,list) and resp and isinstance(excl,list) and excl and not set(resp)&set(excl),"Role responsibilities")
  require(any(nodes[s]["authority"]=="USER_PRIMARY" for s in r.get("derivedFrom",[])),"Role boundary without the user's decision")
 for w in works:
  for path in w["targetPaths"]:
   require(inside(path,roles[w["assignedTo"]]["checkout"]),"Role boundary: "+w["id"]+" targets "+path+" outside its owner's checkout")
 used_sources=set()
 for n in rows:
  kind=n["type"]
  if kind=="DefinitionElement":
   # Every in-scope definition needs a work; out-of-scope ones stay visibly unassigned.
   require((n["developmentScope"]=="IN_PLAN")==(n["id"] in realized),"Definition coverage: "+n["id"])
   require(n.get("derivedFrom"),"Definition without source")
   used_sources.update(n["derivedFrom"])
  if kind in {"WorkItem","Plan","RoleBoundary"}:
   used_sources.update(n.get("evidence",[]));used_sources.update(n.get("derivedFrom",[]))
  if kind=="OutputContract":
   require(n.get("status")=="EXPECTED" and n.get("requiredFields") and len(n["requiredFields"])==len(set(n["requiredFields"])),"Output contract")
  if kind=="AcceptanceCriterion":
   require(n.get("status")=="NOT_EVALUATED" and n.get("negativeCases") and n.get("successCondition"),"Unmeasured acceptance")
  if kind=="ExistingWork":
   require(n.get("identityMerge") is False and n.get("externalIds") and isinstance(n.get("externalPlan"),str),"Existing work reference")
  if kind=="SourceArtifact":
   status=n.get("sourceStatus")
   require(status in {"PINNED_BYTES","LIVE_PATH","INLINE_QUOTE"},"Source status")
   if status=="INLINE_QUOTE":require(n.get("quote") and "path" not in n,"Inline quote")
   else:
    p=Path(n.get("path",""));require(p.parts and not p.is_absolute() and ".." not in p.parts,"Source path")
    require((status=="PINNED_BYTES")==("sha256" in n),"Only pinned sources carry a digest")
   # A user's words are pinned or quoted, never read from a document that can change.
   require(n["authority"]!="USER_PRIMARY" or status!="LIVE_PATH","User source must be immutable")
  if kind=="CompetencyQuestion":
   q=n.get("sparql","")
   require("SELECT" in q and not re.search(r"\b(SERVICE|FROM|LOAD|INSERT|DELETE|CREATE|CLEAR|DROP|MOVE|COPY|ADD)\b",q,re.I),"Read-only bounded SELECT required")
   require(isinstance(n.get("expectedIds"),list) and set(n["expectedIds"])<=nodes.keys(),"Question answers")
 require({n["id"] for n in rows if n["type"]=="SourceArtifact"}==used_sources,"Unused source")
 return nodes

def verify_sources(model, root=ROOT):
 """Compare pinned bytes and live paths with the working tree."""
 pinned=live=0
 for n in model_check(model).values():
  if n["type"]=="SourceArtifact" and n["sourceStatus"]!="INLINE_QUOTE":
   target=root/n["path"]
   if n["sourceStatus"]=="PINNED_BYTES":
    raw=target.read_bytes()
    require(len(raw)==n["bytes"] and hashlib.sha256(raw).hexdigest()==n["sha256"],"Source bytes changed: "+n["path"])
    pinned+=1
   else:
    require(target.is_file(),"Source missing: "+n["path"]);live+=1
  if n["type"]=="WorkItem":
   for path in n["targetPaths"]:
    require(not Path(path).is_absolute() and (root/path).is_file(),"Target missing: "+path)
 return {"pinned":pinned,"live":live}
def verify_delegations(model, root=ROOT):
 """A delegated work must still exist, as a work item of the named plan, in the plan it points at."""
 checked=0
 for n in model_check(model).values():
  if n["type"]!="ExistingWork":continue
  path=Path(n["graphPath"]);require(not path.is_absolute() and ".." not in path.parts,"Delegated graph path")
  other={row["id"]:row for row in json.loads((root/path).read_bytes())["@graph"] if isinstance(row,dict) and "id" in row}
  require("Plan" in kinds(other.get(n["externalPlan"],{})),"Delegated plan missing: "+n["externalPlan"])
  for uid in n["externalIds"]:
   require("WorkItem" in kinds(other.get(uid,{})),"Delegated work missing: "+uid)
   checked+=1
 return checked
def verify_roles(model, root=ROOT):
 """Every work in a referenced plan edits only paths of its own owner's role.

 Collaborators are consulted, not writers, so they never widen a work's paths.
 """
 nodes=model_check(model)
 roles={n["owner"]:n for n in nodes.values() if n["type"]=="RoleBoundary"}
 path_role={p:r for r in roles.values() for p in r.get("ownsPaths",[])}
 for r in roles.values():require((root/r["checkout"]).is_dir(),"Role checkout missing: "+r["checkout"])
 works=paths=0
 for graph in sorted({n["graphPath"] for n in nodes.values() if n["type"]=="ExistingWork"}):
  other=[row for row in json.loads((root/graph).read_bytes())["@graph"] if isinstance(row,dict) and "id" in row]
  for row in other:
   if "RuntimePath" not in kinds(row):continue
   role=path_role.get(row["id"]);require(role is not None,"Path without a role: "+row["id"])
   require((root/role["checkout"]/row["path"]).is_file(),"Owned path missing: "+row["id"]);paths+=1
  for row in other:
   if "WorkItem" not in kinds(row):continue
   owner=row.get("assignedTo");require(owner in roles,"Work without a role: "+row["id"])
   for target in row.get("targets",[]):
    require(target in path_role,"Path without a role: "+target)
    require(path_role[target]["owner"]==owner,"Role boundary: "+row["id"]+" ("+roles[owner]["label"]+") targets "+target+" ("+path_role[target]["label"]+")")
   works+=1
 return {"roles":len(roles),"externalWorks":works,"externalPaths":paths}
def dataset(model):
 from rdflib import Graph
 model_check(model)
 # No remote contexts, imports or SPARQL SERVICE are accepted by model_check.
 return Graph().parse(data=json.dumps(model),format="json-ld")
def shape_check(data, shapes=ROOT/SHAPES):
 from rdflib import Graph,URIRef,RDF
 from pyshacl import validate
 schema=Graph().parse(shapes,format="turtle")
 targets={name:len(set(data.subjects(RDF.type,URIRef(iri)))) for name,iri in (("work",MP+"WorkItem"),("definition",VOCAB+"DefinitionElement"),("existing",VOCAB+"ExistingWork"),("role",VOCAB+"RoleBoundary"))}
 require(all(targets.values()),"SHACL target coverage")
 conforms,_,report=validate(data,shacl_graph=schema,inference="none",advanced=False,do_owl_imports=False)
 return {"conforms":bool(conforms),"targets":targets,"triples":len(data),"report":str(report) if not conforms else None}
def questions(model, name=None):
 data=dataset(model);nodes=model_check(model);answers=[]
 for n in nodes.values():
  if n["type"]!="CompetencyQuestion" or name and n["id"]!=NS+"question:"+name:continue
  result=list(data.query(n["sparql"]));require(len(result)<=150,"Query result bound")
  ids=sorted({str(row.id) for row in result})
  require(ids==sorted(n["expectedIds"]),"Wrong competency answer: "+n["id"])
  answers.append({"id":n["id"],"question":n["label"],"answers":[{"id":i,"label":nodes[i]["label"]} for i in ids]})
 require(answers,"Unknown query")
 return answers
def check(model, root=ROOT):
 nodes=model_check(model);shapes=shape_check(dataset(model))
 require(shapes["conforms"],shapes["report"])
 return {"status":"PASS","scope":"LOCAL_PLAN_STRUCTURE_RDF_SHACL_EXACT_QUERY_ANSWERS_SOURCE_BYTES_DELEGATED_UIDS_AND_ROLE_PATHS","nodes":len(nodes),"shacl":shapes,
  "questions":len(questions(model)),"sources":verify_sources(model,root),"delegatedWork":verify_delegations(model,root),"roles":verify_roles(model,root),"execution":"NOT_STARTED","runtimeEffects":False}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("command",choices=["check","query","show","export"])
 parser.add_argument("name",nargs="?")
 parser.add_argument("--graph",type=Path,default=ROOT/GRAPH)
 args=parser.parse_args();model=load(args.graph)
 if args.command=="check":value=check(model)
 elif args.command=="query":value=questions(model,args.name)
 elif args.command=="show":
  nodes=model_check(model);require(NS+str(args.name) in nodes,"Unknown node");value=nodes[NS+args.name]
 else:
  print(dataset(model).serialize(format="turtle"));return 0
 print(json.dumps(value,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":
 try:
  # Reuse the installed owner-pinned graph environment; never installs packages.
  try: import rdflib,pyshacl
  except ImportError:
   python=Path(os.environ.get("OMC_GRAPH_PYTHON",ROOT.parent/"THE_GREAT_FLOW/.cache/graph-engineering/.venv/bin/python"))
   require(python.is_file() and python.absolute()!=Path(sys.executable).absolute(),"Set OMC_GRAPH_PYTHON to the existing pinned graph environment")
   os.execv(str(python),[str(python),str(Path(__file__).resolve()),*sys.argv[1:]])
  raise SystemExit(main())
 except (ValueError,OSError,KeyError,TypeError) as error:
  print(json.dumps({"status":"FAIL","error":str(error)},ensure_ascii=False),file=sys.stderr);raise SystemExit(1)
