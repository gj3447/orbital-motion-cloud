#!/usr/bin/env node
import { createHash } from "node:crypto"
import { execFile } from "node:child_process"
import { lstat, readFile } from "node:fs/promises"
import { isAbsolute, resolve } from "node:path"
import { promisify } from "node:util"
const run = promisify(execFile)
const args = process.argv.slice(2)
const value = key => { const i=args.indexOf(key); if(i<0||i+1>=args.length) throw new Error("missing "+key); return args[i+1] }
const digest = b => "sha256:"+createHash("sha256").update(b).digest("hex")
const configPath=value("--config")
const config=JSON.parse(await readFile(configPath,"utf8"))
const read=config.read
if (!read || typeof read!=="object") throw new Error("registered read configuration missing")
for (const key of ["registration","registrationDigest","uslRepository","uslModuleDigest","ownerResourceId"]) if(typeof read[key]!=="string") throw new Error("invalid registered read configuration")
if (read.ownerResourceId!==config.resourceId) throw new Error("registered owner resource mismatch")
const directRegular=async path=>{ const info=await lstat(path); if(!info.isFile()||info.isSymbolicLink()) throw new Error("registered source is not a direct regular file") }
const directDirectory=async path=>{ const info=await lstat(path); if(!info.isDirectory()||info.isSymbolicLink()) throw new Error("registered source is not a direct directory") }
if(!isAbsolute(read.registration)||!isAbsolute(read.uslRepository)) throw new Error("registered paths must be absolute")
await directRegular(read.registration); await directDirectory(read.uslRepository)
const registrationBytes=await readFile(read.registration)
if(digest(registrationBytes)!==read.registrationDigest) throw new Error("read registration pin mismatch")
const reg=JSON.parse(registrationBytes)
if (!reg || typeof reg!=="object" || Array.isArray(reg) || Object.keys(reg).sort().join(",")!=="allowedRoots,bindings,maxBytes,schema,selection" || reg.schema!=="omc-usl-workspace-read-registration/v1") throw new Error("invalid read registration")
if (!Array.isArray(reg.allowedRoots)||reg.allowedRoots.length===0||reg.allowedRoots.some(root=>typeof root!=="string"||!isAbsolute(root))) throw new Error("invalid registered allowed roots")
if (!Number.isSafeInteger(reg.maxBytes)||reg.maxBytes<1||reg.maxBytes>16*1024*1024) throw new Error("invalid registered byte budget")
if (!reg.selection || typeof reg.selection!=="object" || Array.isArray(reg.selection)) throw new Error("invalid registered selection")
const modulePath=resolve(read.uslRepository,"src/integrations/omc-workspace.ts")
await directRegular(modulePath)
if(digest(await readFile(modulePath))!==read.uslModuleDigest) throw new Error("USL consumer source pin mismatch")
const py=resolve(new URL(".",import.meta.url).pathname,"workspace_placement.py")
const fetchCurrent=async signal=>{
 if(signal.aborted) throw new Error("aborted")
 const argv=[py,"--config",configPath,"resolve-for-read"]
 const {stdout}=await run("python3",argv,{timeout:15000,maxBuffer:1048576,env:{PATH:"/usr/bin:/bin",PYTHONDONTWRITEBYTECODE:"1"}})
 return JSON.parse(stdout)
}
const { createOmcWorkspaceConsumer }=await import(modulePath)
const consumer=createOmcWorkspaceConsumer({fetchCurrent,ownerResourceId:read.ownerResourceId,bindings:reg.bindings,selection:reg.selection,allowedRoots:reg.allowedRoots,maxBytes:reg.maxBytes,timeoutMs:15000})
const result=await consumer.read()
if(result.status==="PASS") console.log(JSON.stringify({status:"PASS",resource:result.resource,representation:result.representation,contentDigest:result.contentDigest,contentBytes:result.contentBytes,checkpoint:result.checkpoint,consistency:result.consistency}))
else console.log(JSON.stringify(result))
