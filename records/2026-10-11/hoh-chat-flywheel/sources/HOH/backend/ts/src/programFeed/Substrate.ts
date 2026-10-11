import { createHash } from "node:crypto"

export type Cid = `urn:sha256:${string}`
type Json = null | boolean | string | Json[] | { [key: string]: Json }
const canonicalize = (value: Json): Json => {
  if (Array.isArray(value)) return value.map(canonicalize)
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonicalize(value[key]!)]))
  }
  return value
}
/** CHU edge/state JSON uses no numbers, sorts keys recursively, and preserves array order. */
export const chuJson = (value: Json): Uint8Array => Buffer.from(JSON.stringify(canonicalize(value)), "utf8")
/** Content objects hash their exact bytes, without JSON normalization. */
export const cid = (bytes: Uint8Array): Cid => `urn:sha256:${createHash("sha256").update(bytes).digest("hex")}`
export type Participant = { role: "group" | "member"; node: Cid }
export type ChuEdge = { schema: "chu-edge/v1"; type: "group"; participants: Participant[] }
export type ChuState = { schema: "chu-state/v1"; nodes: Cid[]; edges: Cid[] }
export type Source = { uid: string; bytes: Uint8Array; authority: string; revision: string; kind: string }
export type Substrate = { objects: Map<Cid, Uint8Array>; edge: ChuEdge; edgeCid: Cid; state: ChuState; snapshotCid: Cid }

export function materializeBundle(bundleUid: string, manifestBytes: Uint8Array, sources: Source[]): Substrate {
  if (!bundleUid || sources.length === 0 || sources.some(source => !source.uid || source.uid === bundleUid)
    || new Set(sources.map(source => source.uid)).size !== sources.length) {
    throw new Error("bundle requires uniquely identified sources")
  }
  const label = Buffer.from(`metahumotonic research bundle ${bundleUid}`)
  const objects = new Map<Cid, Uint8Array>()
  for (const raw of [label, manifestBytes, ...sources.map(source => source.bytes)]) objects.set(cid(raw), raw)
  const participants: Participant[] = [
    { role: "group", node: cid(label) }, { role: "member", node: cid(manifestBytes) },
    ...sources.map(source => ({ role: "member" as const, node: cid(source.bytes) }))
  ]
  const edge: ChuEdge = { schema: "chu-edge/v1", type: "group", participants }
  const edgeCid = cid(chuJson(edge))
  const state: ChuState = { schema: "chu-state/v1", nodes: [...objects.keys()].sort(), edges: [edgeCid] }
  return { objects, edge, edgeCid, state, snapshotCid: cid(chuJson(state)) }
}
