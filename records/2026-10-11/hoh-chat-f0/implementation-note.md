# HOH durable chat turns — F0

2026-10-11 · SECONDARY_AI implementation note. Owner: private HOH backend.
This is the bounded host-side F0 implementation from OMC's
`omc:chat-flywheel:work:F0` in `graph/hoh-chat-flywheel.json` at OMC design commit
`8f3f4df2156db5763d4931f331c6c2f52c4a57af`. It does not admit a CHU, execute HSWM,
learn a policy, enroll a device, or deploy the live site.

## Behavior

Each accepted chat request binds the authenticated profile to an exact message,
content ID, view/state revisions, content/state digests, conversation ID and
parent request. Request IDs are unique within a profile across conversations and
existing mutation endpoints. `conversationId` defaults to `main`; an omitted
parent follows the latest recorded turn in that conversation. Explicit parents
must already exist in that profile and conversation.

The append-only status events belong to the existing private, content-addressed
profile store. Answers and read commands now write chat history; their content
state stays unchanged. Content writes and their successful chat receipts publish
in one atomic state-head update. Repeating the same request reads its saved
result, even after navigation or process restart. Changing that request's payload
is a conflict. A failed request keeps its failure; a deliberate new attempt needs
a new request ID. The ordinary unbound content-action endpoint retains its
existing contract and cannot take over an ID owned by chat.

Pending write proposals persist for their original two-minute confirmation window.
A newer accepted turn supersedes the profile's pending proposal or unfinished
turn. Confirmation and cancellation serialize in the same store: cancellation
before completion prevents the effect; cancellation after completion returns
`cancelled: false, status: SUCCEEDED`. It never undoes or conceals an executed
change. Expired proposals cannot execute. History retains the original deadline.

A running request can be cancelled by request ID. Durable cancellation is recorded
before signalling the provider's AbortController. A provider that ignores the
signal still cannot commit a late answer or action. Cancellation does not imply
that external compute incurred zero cost. HTTP provider calls retain their
existing timeout, response size and output-token limits; no automatic retry is
introduced. Model tests use controlled fixtures, not a real model or efficacy run.

On opening a store containing a `PENDING` request, it becomes `UNKNOWN` before the
store is exposed. Its ID never automatically re-executes. An uncertain filesystem
commit faults the existing store; reopening determines whether its durable head
contains the completed effect or an unfinished request. The existing single-writer
lock remains authoritative. After a crash, an operator must verify the old writer
is gone before resolving its lock; this change does not delete another process's
lock. The tests exercise persisted interruption and reopen, not a power-loss
certification or a claim of exactly-once external effects.

## API

All paths are under `/api/program-feed/v1`. Current session authentication is
required. Mutations additionally retain same-origin and CSRF validation; reads
return `Cache-Control: private, no-store` and do not accept a client actor ID.

| Endpoint | Purpose |
|---|---|
| `POST /chat` | Existing request plus optional `conversationId`, `parentRequestId` |
| `GET /chat/turn?requestId=…` | Exact owner-scoped request, observation, status events, result and assessments |
| `GET /chat/history?conversationId=…&limit=20` | Latest 1–50 turns of that profile/conversation, in stored order |
| `POST /chat/confirm` | Existing `proposalId`; saved result replay is preserved |
| `POST /chat/cancel` | Existing `proposalId`; truthful final cancellation status |
| `POST /chat/cancel-turn` | `requestId`; cancel a running or confirmation-pending turn |
| `POST /chat/assessment` | `requestId`, `assessmentId`, `HELPFUL` or `UNHELPFUL` rating |

Assessments are idempotent, explicit `USER_REPORTED` observations. They are
separate from the host execution receipt and are not an objective success score,
learning reward, or proof of improvement. A completed answer has execution
`NONE`; request completion does not mean a content mutation occurred.

## Retention, compatibility and limits

This implementation begins retaining exact chat messages and responses in the
profile store. It stores no session tokens in a turn. History is account/profile
scoped, not browser-session isolated: another authenticated session of the same
principal can read that principal's history. Different principals cannot.

A profile may retain at most 256 turns, with 4,000 input characters per request
and up to 16 assessments per completed turn. At capacity, new requests fail
before inference or execution. Old identities are not evicted and then rerun.
Automatic retention deletion, export/compaction, pagination beyond the most
recent 50 records and browser history UI are follow-up product work. Underlying
immutable objects remain retained by the existing store; this is a bounded
first implementation, not unbounded chat hosting.

Historical profiles without `chatTurns` load without changing their other fields.
The field is validated at every publication and reopen, including fingerprints,
parent scope, event order, terminal state and receipt/proposal binding. Older
binaries reject the new field. Rollback therefore requires preserving the new
store and restoring a separately captured compatible snapshot under the existing
operator procedure; do not delete turn history to make an old binary start.

## Verification and next boundary

[Predictions](../engineering/chat-turn-f0/prediction.json) were recorded before the
first regression run. [Implementation graph](../engineering/chat-turn-f0/graph.json)
and [verification](../engineering/chat-turn-f0/verification.json) identify the
actual source files, tests and bounded claim. The unavailable LakatoTree tool
surface was not bypassed, and no external automatic verdict is claimed.

Run from `backend/` using the managed runner and installed pinned Node:

```sh
bash ts/scripts/with-node.sh npm --prefix ts run typecheck
bash ts/scripts/with-node.sh npm --prefix ts test -- program-feed --maxWorkers=1
```

Tests inspect actual persisted objects and reopen the file-store adapter. They
cover durable answers/proposals, parent lineage, replay, cross-profile access,
stale state, cancel/confirm races, caller abort, storage failure, unfinished
recovery, corrupt records and bounded capacity. Production HTTP composition tests
exercise authenticated readback, schema rejection, Origin/CSRF and assessment.

F1 remains a separate owner-specific CHU admission/state adapter. F0 supplies
stable host evidence for it; serializing a chat record as JSON is not that
admission. Subsequent HSWM-connected execution still requires its owner transport
and workspace prerequisites. Deployment and live service verification are separate.
