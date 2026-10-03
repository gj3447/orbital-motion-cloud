# PROM 16 — 333 개발을 위한 블록체인/암호화폐 기초: 무엇이 필요하고 무엇이 cargo-cult인가

> **cycle_id**: `prom16-blockchain-333-2026-07-12` · **N**: 16 (4 axis × 4 sub) · **workflow**: `wf_188c113d-f31` (16 research + synthesis, 1.1M tok, 0 err)
> **KG**: `lesson-prom16-blockchain-foundations-for-333-2026-07-12` (resolved), 16 `ResearchFinding`, `consensus-prom16-333-no-blockchain-2026-07-12`, 2 `:VerdictPending`
> **need_verdict 분포**: **13 CARGO-CULT / 3 GAP-FILLER / 0 blockchain-NEEDED** (16/16 HIGH 만장)

---

## ★ 한 줄 판정

> **333은 full 블록체인(global ledger / PoW / on-chain total-order consensus)이 필요 없다.** 333의 실제 아키텍처(browser-P2P + yrs CRDT local-first + owned-object single-writer Lane A)는 Bitcoin이 존재하는 이유 — "TTP 없는 익명·불신 다수 writer가 공유 fungible 원장의 double-spend를 total-order로 막는 문제" — 를 **설계상 회피**하도록 지어졌다. "코인이니까 블록체인이니까 PoW"는 근거가 아니라 전형적 **cargo-cult**. Bitcoin 도구함에서 이식가치 있는 단 하나는 blockchain이 아니라 **Merkle content-addressing**이며, 그 계보조차 Nakamoto가 아니라 IPFS/IPLD·BFT-CRDT다.

**형식적 근거 3정리**: (1) **Wüst-Gervais 결정트리** — writer가 DID로 known이거나 상태가 mergeable하면 blockchain 불필요. (2) **CALM 정리** — monotonic 연산(CRDT semilattice)은 coordination-free 수렴, consensus 불필요. (3) **Guerraoui "consensus number of a cryptocurrency"**(PODC 2019, arXiv 1906.05574) — 소유자당 1인 asset transfer의 consensus number = **1**, 즉 reliable/consistent broadcast만으로 double-spend 방지, total-order 불요.

---

## 0. 사전 지식 (333 실측 접지)

333 = OMC #8 휘하 same-tier sibling. "P2P 브라우저 free 분산컴퓨팅". ORRR(paid)↔333(free) dual. 333 Coin=compute/storage/relay 지불 utility.
**p333 실코드**(11 crate, ~964 LOC, no daemon): 있음=Ed25519 DID / PKARR naming DHT(pointer-only) / Circuit-Relay-v2 / yrs CRDT(Text+G-Counter) / credit-bucket metering(conservation invariant) / **Lane A = Sui-Lutris/FastPay owned-object fast-path**. 없음(gap)=content-address(cid=0) / value-storage / total-order consensus / graph CRDT.

---

## 1. Consensus (합의 — HIGH)

**C1 [16/16 만장]** — 333은 full 블록체인 불필요. browser-P2P + CRDT local-first + owned-object가 Bitcoin의 존재 이유를 소거.
**C2 [HIGH]** — double-spend 방지는 owned-object single-writer(FastPay/Sui-Lutris = **Lane A, 이미 채택**)로 total-order 없이 해결 = consensus-number=1 정리의 정본 구현. **333의 선택은 이미 옳다.**
**C3 [HIGH]** — Bitcoin에서 이식가치 있는 유일 조각 = **content-addressing(Merkle-DAG/CID)**. 이 하나가 content-address=0 gap을 메우는 *동시에* CRDT를 Byzantine-safe(BFT-CRDT)하게 만드는 바로 그 primitive.
**C4 [HIGH]** — 'DHT는 location pointer만, never value storage' hard-rule은 결함 아닌 **옳은 설계**(IPNS/PKARR 정본 일치). DHT value storage로 확장 = 퇴보(republish convoy).
**C5 [HIGH]** — permissionless 브라우저 피어에선 plain yrs가 악성 피어에 diverge/위조 가능 → **Kleppmann BFT-CRDT(BEC)** 하드닝 필요. 이는 블록체인 아닌 **CRDT 강화**, PoW 불요.
**C6 [HIGH]** — cold-start/relay 자금은 crypto 문제 아닌 **경제 문제**, PoW로 안 풀림. credit-metering + ORRR paid→333 free cross-subsidy(WebRTC Swarms 모델)가 정답.
**C7 [HIGH]** — 토큰: mining 금지, **fixed max supply를 genesis pre-mint**로 두어 런타임 발행(=유일한 global invariant)을 제거하면 모든 이동이 owned-object가 되어 **consensus 필요가 0으로 붕괴**. Sybil은 credit-conservation + 역할-본드 staking + free-tier earn-first 설계로.

---

## 2. 판정표 — 무엇을 넣고 무엇을 버릴 것인가

### ❌ CARGO-CULT (넣지 마 — 블록체인 반사신경)
- **PoW mining** — 브라우저 hashpower=0, DID로 신원 이미 존재, 'free'와 3중 모순. 물리적 infeasible.
- **difficulty adjustment** — 순수 PoW artifact, PoW 없으면 존재이유 0.
- **Nakamoto longest-chain / global total-order ledger** — owned-object엔 total-order 불필요(Guerraoui), CRDT는 monotonic 수렴(CALM). 넣으면 1/3 fault 한계+지연+병목만 추가.
- **probabilistic finality / reorg** — **REGRESSION**. owned-object broadcast는 결정적 finality(reorg 없음).
- **51% attack 프레임** — 잘못된 위협모델. 333 위협면 = hashpower 아닌 metering/relay 경제적 Sybil + cold-start.
- **block/tx 배칭 · UTXO** — CRDT delta를 블록으로 상각할 이유 없음. credit-bucket이 이미 account-balance 보존.
- **DHT value storage(full Kademlia store)** — **REGRESSION**. pointer-only가 옳음.
- **SPV blockchain light-client · PoS global consensus · proof-of-useful-work mining** — 검증할 체인 자체가 없음.

### ✅ GAP-FILLER / NEEDED (실제 필요)
- **Ed25519 / DID** (이미 있음) — PoW 대체 load-bearing primitive. 서명 provenance = 모든 것의 바닥.
- **content-addressing / Merkle-DAG (CID·IPLD)** — **최우선 gap-filler**. content-address=0이 headline gap. 이 **1 primitive가 4가지 동시 해결**: content-addr + BFT tamper-evidence + inclusion-proof + tombstone GC frontier.
- **BFT-CRDT** (Kleppmann 2022) — yrs op를 Ed25519 서명 + hash-linked causal DAG로 승격(있는 DID 재사용). 악성 피어 credit 위조·equivocation 차단.
- **owned-object consistent broadcast** (Lane A, 이미 있음) — 유지·형식화. total-order 추가 금지.
- **verifiable-compute / referee** — paid=NEEDED(referee+redundant re-execution 먼저), free=OPTIONAL. zkVM=ORRR 미래.

---

## 3. Divergence (충돌)

- **고정 max supply 유지?** — 정전(fixed cap, pre-mint하면 consensus까지 소거) **vs** C4: 하드캡=deflationary hoarding으로 결제성 훼손 가능(Akash식 elastic).
- **333 Coin 본성** — transferable fungible(→owned-object broadcast + 숨은 quorum) **vs** non-transferable local credit(→G-Counter로 충분, consensus 완전 OPTIONAL).
- **total-order를 'gap'으로 볼 것인가** — task inventory는 total-order=0을 gap 표기 **vs** owned-object/CRDT엔 애초에 gap 아닌 옳은 설계(표기 재검토).
- **consensusless = authority-less?** — 대부분 'consensus 불필요' 강조 **vs** D4: FastPay/Sui-Lutris도 quorum cert 발급 **permissioned validator(super-peer) 집합** 전제 = 진짜 중앙화·Sybil 지점.

---

## 4. Open Questions (열린 채로)

1. 333 Coin = genesis pre-mint vs runtime issuance? — **'ANY consensus 필요 여부'를 가르는 결정적 변수** (`vp-prom16-333-coin-premint-vs-runtime-issuance`).
2. 333 Coin = transferable fungible vs non-transferable local credit? (`vp-prom16-333-coin-transferable-vs-local-credit`).
3. quorum cert 발급 validator/super-peer 집합은 누구·어떻게 신뢰·재구성? = consensusless의 숨은 authority.
4. cold-start signaling/TURN relay 비용 mechanism-design 미해결 (`333_GAP_ColdStart`).
5. open-membership에서 tombstone GC causal-stability 판정 (`333_GAP_CRDTStateExplosion`).
6. WebRTC NAT hole-punch 미증명 — symmetric NAT에서 TURN 없이 브라우저 연결 성립하는가(crypto 직교, 'free decentralized'의 load-bearing 인프라 가정).

---

## 5. 권장 빌드 순서

1. **content-addressing** — 최소 `sha256(payload + predecessor_hashes)` op-id부터(풀 IPLD codec 나중). content-address=0 gap + BFT가 요구하는 자기검증 hash-DAG 동시 확보. **최우선.**
2. **BFT-CRDT 하드닝** — yrs op → Ed25519 서명 + hash-linked causal DAG(있는 DID 재사용). credit=G-Counter 위조 표적 우선 보호.
3. **Lane A owned-object broadcast 형식화** — Coin/credit 정산 정본. total-order 추가 금지. consensus-number=1 근거를 SOURCES에 명시.
4. **토큰 발행 결정** — 333 Coin genesis pre-mint 고정공급 확정(런타임 minting 제거 → 발행-consensus 소멸). transferable/credit 분기 명시.
5. **cold-start 경제 배선** — credit-bucket ↔ relay/TURN/signaling 인센티브(WebRTC Swarms). ORRR paid → 333 free cross-subsidy. block reward 아님.
6. **tombstone GC** — content-addressed hash-DAG의 stable causal frontier를 snapshot+prune 경계로(2번 DAG 재활용).
7. **AntiCheat** — referee + redundant re-execution 먼저. verifiable-compute/zkVM은 ORRR paid 미래.
8. **ORRR paid micropayment** — 단방향/streaming payment channel(Lightning/L402). 풀 HTLC 라우팅은 over-eng 확인 후.
9. **DEFER** — shared-object permissioned BFT lane(HotStuff/Bullshark/Sui-Lutris shared): 진짜 contended multi-writer 등장 시만. **PoW/PoS/global ledger는 로드맵 어디에도 넣지 마라.**

---

## 부록 — 주요 1차 출처

- Bitcoin whitepaper (Nakamoto) — bitcoin.org/bitcoin.pdf
- The Consensus Number of a Cryptocurrency (Guerraoui et al., PODC 2019) — arXiv 1906.05574
- Sui Lutris (broadcast + consensus hybrid, owned vs shared object) / FastPay (consistent broadcast, consensus 제거)
- Kleppmann 2022 — Making CRDTs Byzantine Fault Tolerant (PaPoC); local-first software
- CALM theorem (Hellerstein-Alvaro); Wüst-Gervais "Do you need a Blockchain?"
- IPFS/IPLD content-addressing (CID, Merkle-DAG); Bitswap
- Golem GLM / Akash AKT (분산 compute marketplace); Lightning BOLT / L402 (payment channel)
- WebRTC Swarms 2025 (incentivized relay bootstrap); Automerge 3.0 (CRDT memory 10x)

# KG: lesson-prom16-blockchain-foundations-for-333-2026-07-12, consensus-prom16-333-no-blockchain-2026-07-12, commander-333-omc-2026-05-19, 333_GAP_ColdStart, 333_GAP_CRDTStateExplosion
