# OMC knowledge plan and Kubernetes source study — 2026-10-10

- [User statement](user-verbatim.txt): exact UTF-8 text, USER_PRIMARY.
- [Knowledge/build plan](../../../docs/POST_CLIENT_SERVER_KNOWLEDGE_PLAN.md): HOW_TO, SECONDARY_AI / PROPOSED.
- [Kubernetes analysis](../../../docs/KUBERNETES_SOURCE_ANALYSIS.md): WHAT_IS, SECONDARY_AI / STATIC_CODE_ANALYSIS.
- [Acquisition](acquisition.json): official source pin, file bytes, SHA-256 and Git blob IDs. Reuses the existing 2026-10-07 master snapshot; three files independently fetched again at the same pin. The entire archive digest was rechecked, not all archive contents revalidated.
- [Code evidence](evidence.json): 15 bounded claims and 30 read spans. Acquisition of a full file does not mean its entire contents were read.
- [Upstream files](upstream): 27 files, 1,306,761 bytes, with original source headers and [Apache 2.0 license](upstream/LICENSE). This is a selected source corpus, not a standalone build tree.
- [Knowledge graph](../../../graph/post-client-server-knowledge.json): proposed dependencies, artifacts, invariants and source-backed code claims. Existing OMC identity is referenced, not re-ratified. This local property graph does not claim RDF/SHACL compliance or shared KG publication.
- [Validation](validation.json): source/digest/claim/graph integrity, five exact-answer queries and four negative probes. Not a Kubernetes or OMC runtime test result.
- [Owner research receipt](research-workflow.json): both existing research modules accepted their respective contribution; workflow state COMPLETE is record completion, not a runtime result.
- [Private hub publication](publication.json): checked additive research changes published and remote commit verified, preserving the concurrent avatar research history.

Run the read-only checks from the OMC checkout:

```sh
python3 records/2026-10-10/post-client-server-kubernetes/validate.py
python3 cli.py check
```

Kubernetes was not built or run; its tests were read but not executed. Borg, Omega and Ray were consulted at the author/conference abstract and bibliographic level; full-paper reproduction remains future work. OMC's proposed performance advantage is unmeasured.

Authored changes pass the Git whitespace check. The byte-preserved upstream README retains its original trailing spaces on lines 82, 90 and 98; those source bytes were not normalized.

Research placement reuses the existing `kubernetes` WHAT_IS and `infrastructure-orchestration` HOW_TO owners. The owner workflow receipt is recorded separately after application so immutable research input does not depend on its later publication receipt.
