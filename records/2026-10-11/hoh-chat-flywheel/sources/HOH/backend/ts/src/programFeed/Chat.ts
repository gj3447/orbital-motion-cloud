import { randomUUID } from "node:crypto"
import { applyContentAction, CONTENT_ACTION_REVISION, contentActionInput, parseContentCommand, type ContentActionRequest } from "./ContentActions.js"
import { ProgramFeedError, type ActorSession } from "./Domain.js"
import { PlannerError, type ContentPlanner } from "./Planner.js"
import type { ProgramFeedStore } from "./Store.js"

export type ChatRequest = { contentId: string; message: string; viewRevision: number; requestId: string; expectedStateRevision?: number | undefined }
type Proposal = { principalId: string; expiresAt: number; request: ContentActionRequest; title: string }

/** Authenticated host orchestration. Model text never supplies the actor or confirmation. */
export const createContentChat = (store: ProgramFeedStore, planner?: ContentPlanner, clock = Date.now) => {
  const proposals = new Map<string, Proposal>(), active = new Map<string, { superseded: boolean }>()
  const retire = (principalId: string) => {
    for (const [id, value] of proposals) if (value.principalId === principalId) proposals.delete(id)
  }
  const sweep = () => { for (const [id, value] of proposals) if (value.expiresAt <= clock()) proposals.delete(id) }
  const get = (actor: ActorSession, id: string) => {
    sweep(); const value = proposals.get(id)
    if (!value || value.principalId !== actor.principalId) throw new ProgramFeedError("NOT_FOUND", "proposal unavailable")
    return value
  }
  return {
    close() { proposals.clear(); for (const turn of active.values()) turn.superseded = true; planner?.close() },
    status: () => planner?.status() ?? { status: "NOT_READY", mode: "DECLARED_COMMANDS_ONLY", reason: "모델 연결이 설정되지 않았습니다. 콘텐츠 명령은 사용할 수 있습니다." },
    async submit(actor: ActorSession, input: ChatRequest) {
      const view = await store.readContent(actor, input)
      const command = parseContentCommand(input.message, view.content, view.manifest.kind)
      if (command) {
        if (view.actionContract.actions.find(action => action.id === command.actionId)?.effect === "write" && input.expectedStateRevision === undefined)
          throw new ProgramFeedError("INVALID_INPUT", "state revision required")
        retire(actor.principalId)
        const previous = active.get(actor.principalId); if (previous) previous.superseded = true
        // The store checks durable replay before CAS; a lost response must be recoverable.
        return store.invokeContent(actor, { contentId: input.contentId, requestId: input.requestId, viewRevision: input.viewRevision,
          contractRevision: CONTENT_ACTION_REVISION, expectedStateRevision: input.expectedStateRevision ?? view.stateRevision, ...command })
      }
      if (input.expectedStateRevision !== undefined && input.expectedStateRevision !== view.stateRevision)
        throw new ProgramFeedError("STATE_CONFLICT", "stale content state")
      if (!planner) throw new PlannerError("UNAVAILABLE")
      if (active.has(actor.principalId) || active.size >= 4) throw new PlannerError("BUSY")
      retire(actor.principalId)
      const turn = { superseded: false }; active.set(actor.principalId, turn)
      try {
        const plan = await planner.plan(input.message, view)
        // Navigation or a human edit during inference invalidates both answers and actions.
        const current = await store.readContent(actor, input)
        if (turn.superseded) throw new ProgramFeedError("CONFLICT", "chat turn superseded")
        if (current.stateRevision !== view.stateRevision) throw new ProgramFeedError("STATE_CONFLICT", "state changed while planning")
        if (plan.kind === "answer") return { answer: plan.answer, execution: "NONE", contentId: input.contentId, viewRevision: view.viewRevision }
        const action = view.actionContract.actions.find(value => value.id === plan.actionId)
        if (!action) throw new ProgramFeedError("INVALID_INPUT", "undeclared model action")
        const normalized = contentActionInput(action.id, plan.input)
        const preview = applyContentAction(view.content, view.manifest, view.appState, action.id, normalized)
        const request: ContentActionRequest = { contentId: input.contentId, actionId: action.id, input: normalized,
          contractRevision: CONTENT_ACTION_REVISION, expectedStateRevision: view.stateRevision, viewRevision: view.viewRevision, requestId: input.requestId }
        if (action.effect === "read") return store.invokeContent(actor, request)
        sweep()
        // One current proposal per principal; repeated model requests cannot fill the map for one user.
        retire(actor.principalId)
        if (proposals.size >= 128) throw new PlannerError("BUSY")
        const id = randomUUID(), expiresAt = clock() + 120_000
        proposals.set(id, { principalId: actor.principalId, request, expiresAt, title: action.title })
        return { answer: `적용할 내용: ${preview.answer}\n이 변경을 적용할까요?`, execution: "AWAITING_CONFIRMATION",
          contentId: input.contentId, viewRevision: view.viewRevision,
          proposal: { id, actionId: action.id, input: normalized, expiresAt: new Date(expiresAt).toISOString() } }
      } finally { active.delete(actor.principalId) }
    },
    async confirm(actor: ActorSession, id: string) {
      const proposal = get(actor, id)
      // Store authenticates expiry, checks CAS and durably replays the bound request ID.
      return store.invokeContent(actor, proposal.request)
    },
    async cancel(actor: ActorSession, id: string) {
      const proposal = get(actor, id)
      await store.profile(actor)
      proposals.delete(id)
      return { cancelled: true, contentId: proposal.request.contentId }
    }
  }
}
export type ContentChat = ReturnType<typeof createContentChat>
