# HOH chat → CHU v0.1 — bounded F1 adapter

2026-10-11 · SECONDARY_AI implementation. Owner: private HOH backend.
Work UID: `omc:chat-flywheel:work:F1`, from OMC design commit
`8f3f4df2156db5763d4931f331c6c2f52c4a57af`. This is an additive implementation
observation; it does not rewrite the source plan or user canon.

## Behavior and ownership

On request acceptance the host now persists the exact UTF-8 JSON representation
of the selected `OpenView`, before any chat action changes content. Its SHA-256,
content/state digests, manifest revision and view/state revisions are checked on
publication and reopen. The capture is limited to 256 KiB per turn. It includes
that profile's selected content, manifest, action contract, state, comments and
recommendation evidence, so it has the same private access boundary as the turn.
It does not contain a session token. It is historical evidence, not a capability.
This is the host's request-acceptance observation. The existing planner rereads
the view afterward; this bundle alone does not attest the exact later model
input. F2 must bind the actually consumed snapshot to its cognitive-turn trace.

`GET /api/program-feed/v1/chat/chu?requestId=…` prepares an immutable graph bundle
from the currently authenticated profile's saved turn. It checks current session
and content visibility and returns `Cache-Control: private, no-store`. No actor
ID is accepted from the caller. Optional `expectedRecordCid=urn:sha256:…` pins
readback to one record version; a changed outcome or assessment returns HTTP 409.
An unknown/other-profile request returns 404; missing authentication returns 401.

Legacy F0 records without captured context remain readable/replayable. Export
returns HTTP 503 `chat_chu_context_unavailable`; it never substitutes today's
content for the original context. New and old records may coexist. An older F0
binary rejects the added field: rollback must preserve the current store and use
a compatible captured snapshot, not strip new evidence to force startup.

## Identity and lossless graph projection

| Field | Identity and meaning |
|---|---|
| `scopeCid` | Digest of a versioned profile-scope descriptor; not an access credential or anonymization guarantee |
| `conversationCid` | Content-addressed descriptor of profile scope and conversation ID |
| `turnCid` | Stable logical handle for that conversation's request ID |
| `recordCid` | SHA-256 of the exact serialized saved turn at this observation |
| `snapshotCid` | CHU canonical state encoding over sorted node/edge CID sets |
| `viewRevision`, `stateRevision` | HOH host revisions retained in evidence; neither is a CHU snapshot CID |
| CHU request/base/result | Supplied to the native reference operation during verification; not inferred from the browser request ID |

All content objects contain exact bytes encoded in Base64, a lowercase
`urn:sha256` digest and a decimal byte-length string. JSON content is hashed as
emitted, without Unicode normalization or post-hash reserialization. The bundle
is a selected-turn projection, not a complete profile or historical CHU branch.

CHU v0.1 registers `group` and `requires-any`. This adapter reuses **only `group`**:
its first incidence has native role `group`; the rest have native role `member`.
No HOH-specific relation is silently added to CHU's registry.

The record node is the group for an ordered list of explicit
`hoh-chat-incidence/v1` occurrence nodes. Each occurrence contains its record CID,
zero-based decimal ordinal, semantic role and payload CID. A second native group
edge connects that occurrence to its payload, so traversal does not depend on an
unresolved CID buried in a JSON string. Every endpoint exists in the snapshot.
Equal payload bytes in different roles share a content node and retain separate
occurrences. Consumers inspect ordered incidences; CHU's set-valued `members`
convenience query alone cannot recover repetition or order.

The fixed role sequence is `conversation`, `turn`, `request`, `message`, `context`,
`observation`, `outcome`, `assessments`, then optional `parent`. `message` contains
the original raw UTF-8 input; `context` contains the captured view bytes. `outcome`
keeps the actual status, events and available response/proposal/failure. Pending,
failed, cancelled and unknown requests are not relabelled as successes.
`assessments` retains `USER_REPORTED` attribution. `parent` refers to a logical
handle only; this one-turn bundle does not claim to include the parent's record.

Stable handles survive changes to outcome or assessment; record and snapshot
CIDs change. Previously retrieved bundles remain immutable observations. This
GET endpoint serves the current saved version and does not add a historical
snapshot retrieval service. `assertChatChuReadback` compares a transport result
against a trusted retained host expectation; it is not a general import validator
or an authorization check.

## Actual native verification and remaining boundary

The consumer harness imports `scripts/chu_model.py` directly from the CHU owner
checkout pinned to `236d5395600f4d2e8dc2509d71e276940b31973f` and checks its source
bytes before execution. Its contracts are `spec/IDENTITY.md`, `DATA_MODEL.md`,
`OPERATIONS.md` and `PROJECTION.md` at that revision. No copied replacement model
or newly invented native admission API stands in for the owner implementation.

Controlled fixtures generated by the production TypeScript adapter go through
actual `Model.apply(create)` and `Model.apply(link)`. The harness compares native
snapshot CID, every node's bytes, every edge's ordered roles, two record versions,
retained old snapshots and idempotent request replay. Negative controls exercise
missing endpoints, invalid/native-unregistered roles/types, conflicting request
reuse, unknown base, deletion of referenced nodes and wrong content digests.
Failures must leave the model's state/event history unchanged.

This proves compatibility with the **in-memory executable specification**. The
owner's persistent kernel, capability/authentication boundary and production
admission transport remain unfinished. Every prepared bundle therefore reports
`admission: NOT_SUBMITTED`, `runtime: NOT_READY`. A local test may separately
report `REFERENCE_MODEL_ACCEPTED`. These are different observations. No real
user profile is sent to the reference harness, and no HSWM call is made.

F1's bounded projection/reference-model part is implemented; production admission
is still open. F2 can next define a consumer contract over this evidence, but any
HSWM-connected execution must satisfy its existing owner workspace/transport
requirements. State persistence, reference compatibility, learning and improved
outcomes are separate claims.

## Reproduce and inspect evidence

Use the existing managed bulk runner and pinned Node wrapper from `backend/`:

```sh
bash ts/scripts/with-node.sh npm --prefix ts run typecheck
HOH_CHU_FIXTURE_DIR="$STORAGE_ARTIFACT_DIR/fixtures" \
  bash ts/scripts/with-node.sh npm --prefix ts test -- program-feed --maxWorkers=1
bash ts/scripts/with-node.sh npm --prefix ts run build
```

Then, within the same managed artifact scope, use the pinned CHU Python 3.13.5
environment to run `engineering/chat-chu-f1/verify_native.py --chu-root SELECTED_CHU_CHECKOUT
--fixtures FIXTURE_DIRECTORY --output RESULT_JSON`. The script requires the
exact owner revision and existing dependency environment; it performs no install.
Caller-selected local roots stay outside committed evidence.

[Predictions](../engineering/chat-chu-f1/prediction.json),
[verification](../engineering/chat-chu-f1/verification.json), and
[typed implementation graph](../engineering/chat-chu-f1/graph.json) preserve the
source/test relationship. Run `python3 engineering/chat-chu-f1/check.py` from
`backend/` to verify source hashes, predicate contracts, exact competency answers
and negative controls. Use `--git-ref VERIFIED_COMMIT` to inspect that commit's
bytes when the shared working tree has subsequent changes. The final test run
used a frozen archive of the recorded base plus only this adapter's patch, with
the existing pinned dependency installation. It did not create another Git
worktree. Because the isolated archive links that installation, its compiler
uses `--preserveSymlinks` to avoid exporting absolute dependency paths. All
project strict checks remain enabled; build runs `tsc` with that flag followed
by the unchanged `copy-assets.mjs`. The normal canonical-checkout commands above
do not need this archive-specific flag. The unavailable LakatoTree tool has no
asserted verdict.
