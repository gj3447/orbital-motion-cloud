# 333 — OMC #8 휘하 군단장 (P2P browser base, free)

> **canonical name**: 333 — OMC apostle #8 휘하 *free* 인프라 위상.
>
> **tier**: OMC-legion-commander (sibling with ORRR / CHU / 옴마니반메훔 / engineboy). 사용자 verdict 2026-05-19 same-tier. NO meta-elevation.
>
> **paired_with (dual axis)**: `commander-orrr-omc-2026-05-19` (paid ↔ free 측 인프라 dual).
>
> **KG canonical node**: `commander-333-omc-2026-05-19` (:PRELIMINARY:LegionCommander). user_verdict = PRIMARY.

## 정의

333 = OMC 휘하 *free / decentralized* 인프라 위상. P2P 브라우저 기반 측 substrate. ORRR (paid) ↔ 333 (free) 측 dual axis.

상위 framing (4 위상 2026-04-28 spec) 측 cross-ref:
- 4 위상 표 측 **분산 컴퓨팅 인프라** (AGENT_CLOUD/) 측 free 분기
- 4 동치 측 인프라 axis 측면 측 free split

## 역할

- agent 들이 *무료* P2P resource 측 접근하는 substrate
- ORRR 와 dual — paid (centralized marketplace) ↔ free (decentralized P2P)
- 검열 저항성 + 비용 측면 측 ORRR 와 differential

## OPEN

1. **333 측 외부 referent** — webRTC / libp2p / IPFS / SOLID / Beaker browser / FreeNet 등 측 mapping OPEN
2. **명명 측 의미** — 사용자 발화 측 "333" 측 P2P browser 측 specific reference 측 verdict 대기 (3-3-3 측 어떤 layered structure 측 표지일 가능성?)
3. **CANONICAL 격상** — P4 propagation 5-check 통과 시 candidate

## 2026-07-12 PROM 재판정 — 블록체인 기초 (지식 선행)

> [`PROM_16_REPORT.md`](PROM_16_REPORT.md) — 16-cell WebSearch. **판정: 333은 full 블록체인 불필요** (13 CARGO-CULT / 3 GAP-FILLER / 0 blockchain-NEEDED, 16/16 HIGH).

- **OPEN #1 (외부 referent) 상당 응답**: 333의 정본 referent = **Bitcoin 아님** → **Sui-Lutris/FastPay**(owned-object broadcast, consensus-number=1) + **IPFS/IPLD**(content-addressing) + **Kleppmann BFT-CRDT**. Nakamoto PoW/global ledger는 owned-object+CRDT local-first 아키텍처엔 cargo-cult.
- **최우선 gap-filler**: content-addressing(Merkle-DAG/CID) — 1 primitive가 content-addr gap + BFT tamper-evidence + inclusion-proof + tombstone GC frontier 동시 해결.
- **토큰**: mining 금지, genesis pre-mint 고정공급(런타임 발행 제거 → consensus 필요 0으로 붕괴).
- **USER 결정 대기 2건** (consensus 필요여부 gate): Coin=pre-mint vs runtime issuance / transferable fungible vs local credit.
- KG: `lesson-prom16-blockchain-foundations-for-333-2026-07-12`, `consensus-prom16-333-no-blockchain-2026-07-12`

## 2026-07-15 Kubernetes/Borg/Omega 흡수 — 333의 다리는 k8s가 아니라 Omega

> [`../KUBERNETES_BORG_ABSORPTION_2026-07-15.md`](../KUBERNETES_BORG_ABSORPTION_2026-07-15.md) (사용자 "구글 파이퍼/보그" 비유 흡수) + [`FINDINGS/omc-open-problems-2026-07-15/`](../../../FINDINGS/omc-open-problems-2026-07-15/) (4트랙 후속). clone: `dgx:/mnt/ext4/nas/symposium-git/kubernetes` (`153eedf9b8`).

- **OPEN #1(외부 referent) 추가 응답**: **Kubernetes ≈ ORRR, NOT 333.** k8s 컨트롤플레인 = etcd/Raft 강한 합의(CP) = 333 consensusless와 정반대 → k8s는 333에게 **대조 canon**(합의 병목 수용 시 etcd가 스케일 천장).
- **다리 = Omega OCC** (Schwarzkopf et al. 2013): 모놀리식 합의 없이 *공유상태 + 낙관적 동시성 + 충돌감지*로 스케줄링 = 333 consensusless의 **산업 원형**. 이미 인용한 Sui-Lutris(블록체인 측)와 **같은 정리의 다른 결정화**. 333 ↔ Omega = PARTIAL_MIRROR.
- **333 = 3층 합성**: Omega OCC(동시성) + Sui-Lutris owned-object(합의 국소화) + BFT quorum-cert n≥3f+1(비잔틴 방어). k8s/Omega는 아래 2층까지만 crash-fault로 검증.
  - **비잔틴 3층은 2026-07-14 구현 완료** (Ed25519 + QC quorum=n−f + Committee + type-state `Verified` rail + 실 TCP + Plumtree + node binary + ooptdd 4/4). `gj3447/333` tip `fb08f13`, **cargo 89 passed / 0 failed** 실측 2026-07-15.
  - **그러나 P0 잔존 = 영속성**: [FSM 감사](../../../FINDINGS/audit-333-fsm-vs-borg-k8s-2026-07-15/) 실측 **durable 0/26 FSM**. `Authority.locked`가 in-memory → 재시작이 lock 소거 → **정직 노드 crash-restart 1회 = 비잔틴 예산 1 소모**. certificate uniqueness가 f개 초과 재시작에서 붕괴. (PRELIMINARY, 나생문 미실시)
- "블록체인 기초" 라벨 → **"Omega OCC + 합의 국소화" 라벨로 정밀화 권장** (lakatos concept-stretching).
- 잔존 프론티어: browser substrate(WebRTC/WASM — 정체성 갭, 비호환 3군데뿐) / 동적 멤버십(K-T DISC 2020 경로 열림, 현재 부재) / DV-2 복구(CONDITIONAL) / mint CN-k formal.

## Cross-ref

- 상위 OMC: `../SOURCES.md` §2026-05-19 5 Commander Roster
- 짝패 (paid ↔ free): `../ORRR/SOURCES.md`
- 4 위상 측 같은 framing: `../AGENT_CLOUD/`

# KG: commander-333-omc-2026-05-19 (:PRELIMINARY:LegionCommander)
# KG: apostle-legion-commanders-pattern-2026-05-15 (:StructuralPattern:CanonicalPattern)
