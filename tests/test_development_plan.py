import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import development_plan as p

class DevelopmentPlanTests(unittest.TestCase):
 def setUp(self):
  self.model=p.load()
 def node(self, suffix):
  return next(n for n in self.model["@graph"] if n["id"]==p.NS+suffix)
 def test_real_plan_has_exact_answers_and_is_not_execution(self):
  result=p.check(self.model)
  self.assertEqual(result["status"],"PASS")
  self.assertEqual(result["shacl"]["targets"],{"work":8,"definition":13,"existing":3,"role":5})
  self.assertEqual(result["roles"],{"roles":5,"externalWorks":29,"externalPaths":20})
  self.assertEqual(result["questions"],8)
  self.assertEqual(result["delegatedWork"],12)
  self.assertEqual(result["execution"],"NOT_STARTED")
  self.assertFalse(result["runtimeEffects"])
  self.assertEqual([x["id"] for x in p.questions(self.model,"unrealized")[0]["answers"]],[p.NS+"def:dw-view",p.NS+"def:philosophy"])
 def test_duplicate_identity_and_reversed_relation_rejected(self):
  self.model["@graph"].append(copy.deepcopy(self.node("d01")))
  with self.assertRaisesRegex(ValueError,"identity"):p.model_check(self.model)
  self.model=p.load();self.node("d04")["realizes"]=[p.NS+"d02"]
  with self.assertRaisesRegex(ValueError,"reversed"):p.model_check(self.model)
 def test_dependency_cycle_and_missing_handoff_rejected(self):
  self.node("d02")["dependsOn"]=[p.NS+"d05"];self.node("d02")["requiresOutput"]=[p.NS+"output:d05"]
  with self.assertRaisesRegex(ValueError,"cycle"):p.model_check(self.model)
  self.model=p.load();self.node("d05")["requiresOutput"].pop()
  with self.assertRaisesRegex(ValueError,"handoff"):p.model_check(self.model)
 def test_completion_and_authority_cannot_be_promoted(self):
  for suffix,field,value,error in [("d02","status","VERIFIED","Unproven"),("d02","authority","USER_PRIMARY","Authority"),
    ("def:rebalancing","authority","USER_PRIMARY","Authority"),("source:physical-mhc","authority","USER_PRIMARY","Authority"),
    ("source:what-is","authority","USER_PRIMARY","Authority")]:
   with self.subTest(node=suffix,field=field):
    self.model=p.load();self.node(suffix)[field]=value
    with self.assertRaisesRegex(ValueError,error):p.model_check(self.model)
 def test_definition_coverage_is_enforced_both_ways(self):
  # An in-scope definition cannot silently lose its only work.
  self.node("d06")["realizes"]=[p.NS+"def:rebalancing"]
  with self.assertRaisesRegex(ValueError,"Definition coverage.*tool-growth"):p.model_check(self.model)
  # A perspective the user left undefined cannot be claimed by a work.
  self.model=p.load();self.node("d08")["realizes"].append(p.NS+"def:dw-view")
  with self.assertRaisesRegex(ValueError,"outside development scope"):p.model_check(self.model)
 def test_delegation_must_match_class_and_existing_plan(self):
  del self.node("d03")["delegatesTo"]
  with self.assertRaisesRegex(ValueError,"Delegation mismatch"):p.model_check(self.model)
  self.model=p.load();self.node("existing:mobility-feedback")["externalIds"]=["urn:omc:workload-mobility:w99"]
  with self.assertRaisesRegex(ValueError,"Delegated work missing"):p.verify_delegations(self.model)
  # An output contract of the other plan is not a work item.
  self.model=p.load();self.node("existing:mobility-feedback")["externalIds"]=["urn:omc:workload-mobility:output:w09"]
  with self.assertRaisesRegex(ValueError,"Delegated work missing"):p.verify_delegations(self.model)
 def test_changed_user_source_and_missing_target_rejected(self):
  source=self.node("source:agent-cloud")
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for n in self.model["@graph"]:
    for path in ([n["path"]] if "path" in n else [])+n.get("targetPaths",[]):
     target=root/"repo"/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p.ROOT/path,target)
   self.assertEqual(p.verify_sources(self.model,root/"repo")["pinned"],13)
   (root/"repo"/source["path"]).write_text("입운구는 다른 것이다\n")
   with self.assertRaisesRegex(ValueError,"Source bytes changed"):p.verify_sources(self.model,root/"repo")
   shutil.copyfile(p.ROOT/source["path"],root/"repo"/source["path"]);(root/"repo/scripts/rebalance.py").unlink()
   with self.assertRaisesRegex(ValueError,"Target missing"):p.verify_sources(self.model,root/"repo")
  self.model=p.load();self.node("source:agent-cloud")["sourceStatus"]="LIVE_PATH";del self.node("source:agent-cloud")["sha256"]
  with self.assertRaisesRegex(ValueError,"immutable"):p.model_check(self.model)
 def test_wrong_question_answer_and_write_query_rejected(self):
  self.node("question:next")["expectedIds"]=[p.NS+"d01"]
  with self.assertRaisesRegex(ValueError,"Wrong competency answer"):p.questions(self.model,"next")
  self.model=p.load();self.node("question:next")["sparql"]="DELETE WHERE { ?s ?p ?o }"
  with self.assertRaisesRegex(ValueError,"Read-only"):p.model_check(self.model)
 def test_shacl_selects_targets_and_rejects_a_known_violation(self):
  from rdflib import Graph
  # Bypass model_check so the violation reaches the shapes themselves.
  self.node("d05")["executionClass"]="AUTOMATIC";del self.node("def:rebalancing")["derivedFrom"]
  result=p.shape_check(Graph().parse(data=json.dumps(self.model),format="json-ld"))
  self.assertFalse(result["conforms"])
  self.assertIn("executionClass",result["report"]);self.assertIn("wasDerivedFrom",result["report"])
  with self.assertRaisesRegex(ValueError,"target coverage"):p.shape_check(Graph())

 def role_tree(self, tmp, mutate=lambda graphs: None):
  """A root holding the referenced plan graphs and an empty file for every owned path."""
  root=Path(tmp)/"repo";nodes=p.model_check(self.model)
  roles={n["owner"]:n for n in nodes.values() if n["type"]=="RoleBoundary"}
  owner_of={path:r for r in roles.values() for path in r.get("ownsPaths",[])}
  graphs={n["graphPath"]:json.loads((p.ROOT/n["graphPath"]).read_text()) for n in nodes.values() if n["type"]=="ExistingWork"}
  mutate(graphs)
  for graph,data in graphs.items():
   target=root/graph;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(data))
   for row in data["@graph"]:
    if row.get("id") in owner_of:
     f=root/owner_of[row["id"]]["checkout"]/row["path"];f.parent.mkdir(parents=True,exist_ok=True);f.touch()
  for r in roles.values():(root/r["checkout"]).mkdir(parents=True,exist_ok=True)
  return root
 def test_hoh_and_omc_roles_cannot_edit_each_others_paths(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(p.verify_roles(self.model,self.role_tree(tmp))["externalWorks"],29)
  def hoh_places_work(graphs):
   # HOH taking over placement (an OMC execution path) is the case the user ruled out.
   row=next(r for r in graphs["graph/workload-mobility-plan.jsonld"]["@graph"] if r.get("id")=="urn:omc:workload-mobility:w05")
   row["assignedTo"]="urn:omc:memory-plan:owner:hoh"
  def omc_edits_hoh_release(graphs):
   row=next(r for r in graphs["graph/workload-mobility-plan.jsonld"]["@graph"] if r.get("id")=="urn:omc:workload-mobility:w09")
   row["targets"].append("urn:omc:workload-mobility:path:release")
  def unowned_path(graphs):
   graphs["graph/workload-mobility-plan.jsonld"]["@graph"].append({"id":"urn:omc:workload-mobility:path:new","type":"RuntimePath","label":"x","path":"x.py"})
  for mutate,error in [(hoh_places_work,"Role boundary.*w05.*HOH.*path:launch.*입운구"),(omc_edits_hoh_release,"Role boundary.*w09.*path:release"),(unowned_path,"Path without a role")]:
   with self.subTest(case=mutate.__name__),tempfile.TemporaryDirectory() as tmp:
    with self.assertRaisesRegex(ValueError,error):p.verify_roles(self.model,self.role_tree(tmp,mutate))
 def test_own_work_targets_stay_inside_the_owner_checkout(self):
  # MHC settlement receives OMC's run record through D02's output, not by editing OMC.
  self.node("d04")["targetPaths"].append("scripts/resource_selection.py")
  with self.assertRaisesRegex(ValueError,"Role boundary.*d04.*resource_selection"):p.model_check(self.model)
  self.model=p.load();self.node("d02")["targetPaths"].append("../HOH/backend/ts/scripts/verify-feedback.mjs")
  with self.assertRaisesRegex(ValueError,"Role boundary.*d02"):p.model_check(self.model)
 def test_role_definitions_are_exclusive_and_user_decided(self):
  for change,error in [(lambda: self.node("role:hoh")["ownsPaths"].append("urn:omc:workload-mobility:path:launch"),"more than one role"),
    (lambda: self.node("role:omc").update(derivedFrom=[p.NS+"source:operating-model"]),"user's decision"),
    (lambda: self.node("role:hoh")["excludes"].append("HOH 합격 기준"),"Role responsibilities"),
    (lambda: self.node("role:mhc").update(checkout="../HOH"),"Role checkout")]:
   with self.subTest(error=error):
    self.model=p.load();change()
    with self.assertRaisesRegex(ValueError,error):p.model_check(self.model)

if __name__=="__main__":
 unittest.main()
