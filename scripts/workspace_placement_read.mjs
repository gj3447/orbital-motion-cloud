#!/usr/bin/env node
import { createHash } from "node:crypto"
import { execFile } from "node:child_process"
import { lstat, readFile } from "node:fs/promises"
import { isAbsolute, parse, resolve, sep } from "node:path"
import { promisify } from "node:util"

const run = promisify(execFile)
const args = process.argv.slice(2)
const value = key => { const i = args.indexOf(key); if (i < 0 || i + 1 >= args.length) throw new Error(`missing ${key}`); return args[i + 1] }
const digest = bytes => `sha256:${createHash("sha256").update(bytes).digest("hex")}`
const runtimeFiles = ["package.json", "package-lock.json", "src/integrations/omc-workspace.ts", "src/contract-core.ts", "src/resource-bindings.ts", "src/json-data.ts", "src/locator.ts"]

/** Require every component, including a trusted source's ancestors, to be physical. */
const directPath = async (input, kind) => {
  const absolute = resolve(input), root = parse(absolute).root
  let cursor = root
  const rootInfo = await lstat(cursor)
  if (rootInfo.isSymbolicLink() || !rootInfo.isDirectory()) throw new Error("registered path has symbolic-link root")
  for (const part of absolute.slice(root.length).split(sep).filter(Boolean)) {
    cursor = resolve(cursor, part)
    const info = await lstat(cursor)
    if (info.isSymbolicLink()) throw new Error("registered path traverses symbolic link")
  }
  const info = await lstat(absolute)
  if ((kind === "file" && !info.isFile()) || (kind === "directory" && !info.isDirectory())) throw new Error("registered path has wrong type")
  return absolute
}

/** Pin direct runtime sources plus the dependency lock, with unambiguous byte framing. */
const runtimeDigest = async repository => {
  const root = await directPath(repository, "directory"), hash = createHash("sha256")
  for (const relative of runtimeFiles) {
    const file = await directPath(resolve(root, relative), "file"), bytes = await readFile(file)
    hash.update(relative); hash.update("\0"); hash.update(String(bytes.byteLength)); hash.update("\0"); hash.update(bytes)
  }
  return `sha256:${hash.digest("hex")}`
}

if (args.includes("--runtime-digest")) {
  console.log(await runtimeDigest(value("--usl-repository")))
  process.exit(0)
}

const configPath = value("--config")
await directPath(configPath, "file")
const config = JSON.parse(await readFile(configPath, "utf8"))
const read = config.read
if (!read || typeof read !== "object") throw new Error("registered read configuration missing")
for (const key of ["registration", "registrationDigest", "uslRepository", "uslRuntimeDigest", "adapterDigest", "nodeRuntime", "ownerResourceId"]) {
  if (typeof read[key] !== "string") throw new Error("invalid registered read configuration")
}
if (read.ownerResourceId !== config.resourceId) throw new Error("registered owner resource mismatch")
if (read.nodeRuntime !== process.version) throw new Error("Node runtime pin mismatch")
if (!isAbsolute(read.registration) || !isAbsolute(read.uslRepository)) throw new Error("registered paths must be absolute")
await directPath(read.registration, "file"); await directPath(read.uslRepository, "directory")
const registrationBytes = await readFile(read.registration)
if (digest(registrationBytes) !== read.registrationDigest) throw new Error("read registration pin mismatch")
const reg = JSON.parse(registrationBytes)
if (!reg || typeof reg !== "object" || Array.isArray(reg) || Object.keys(reg).sort().join(",") !== "allowedRoots,bindings,maxBytes,schema,selection" || reg.schema !== "omc-usl-workspace-read-registration/v1") throw new Error("invalid read registration")
if (!Array.isArray(reg.allowedRoots) || reg.allowedRoots.length === 0 || reg.allowedRoots.some(root => typeof root !== "string" || !isAbsolute(root))) throw new Error("invalid registered allowed roots")
if (!Number.isSafeInteger(reg.maxBytes) || reg.maxBytes < 1 || reg.maxBytes > 16 * 1024 * 1024) throw new Error("invalid registered byte budget")
if (!reg.selection || typeof reg.selection !== "object" || Array.isArray(reg.selection)) throw new Error("invalid registered selection")
const adapterPath = new URL(import.meta.url).pathname
await directPath(adapterPath, "file")
if (digest(await readFile(adapterPath)) !== read.adapterDigest) throw new Error("OMC read adapter source pin mismatch")
if (await runtimeDigest(read.uslRepository) !== read.uslRuntimeDigest) throw new Error("USL consumer runtime pin mismatch")
const modulePath = resolve(read.uslRepository, "src/integrations/omc-workspace.ts")
const py = resolve(new URL(".", import.meta.url).pathname, "workspace_placement.py")
const fetchCurrent = async signal => {
  if (signal.aborted) throw new Error("aborted")
  const { stdout } = await run("python3", [py, "--config", configPath, "resolve-for-read"], {
    timeout: 12_000, maxBuffer: 1024 * 1024, signal,
    env: { PATH: "/usr/bin:/bin", PYTHONDONTWRITEBYTECODE: "1" },
  })
  return JSON.parse(stdout)
}
const { createOmcWorkspaceConsumer } = await import(modulePath)
const consumer = createOmcWorkspaceConsumer({ fetchCurrent, ownerResourceId: read.ownerResourceId,
  bindings: reg.bindings, selection: reg.selection, allowedRoots: reg.allowedRoots, maxBytes: reg.maxBytes, timeoutMs: 15_000 })
const result = await consumer.read()
if (result.status === "PASS") console.log(JSON.stringify({ status: "PASS", resource: result.resource, representation: result.representation,
  contentDigest: result.contentDigest, contentBytes: result.contentBytes, checkpoint: result.checkpoint, consistency: result.consistency }))
else console.log(JSON.stringify(result))
