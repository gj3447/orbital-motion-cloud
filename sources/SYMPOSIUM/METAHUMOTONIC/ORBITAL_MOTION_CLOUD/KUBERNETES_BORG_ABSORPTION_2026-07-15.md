# Kubernetes / Borg / Omega 흡수 — 333·ORRR 오케스트레이션 substrate 접지

> **cycle**: `omc-kubernetes-borg-absorption-2026-07-15` (PRELIMINARY) · 외부 OSS 흡수 6-step (`reference_oss_industry_absorption_pattern`)
> **trigger**: 사용자 발화 2026-07-15 — *"333 이랑 orrr 은 약간 구글의 파이퍼 그 보그 같은거야 ㅇㅇ 쿠버네티스 엔진 git repo 받아서 연구를 해야해"*
> **clone**: `dgx:/mnt/ext4/nas/symposium-git/kubernetes` (406M, shallow depth=1, HEAD 30839 files). Mac 미보유 (`reference_git_clones_to_dgx_4tb_ssd`).
> **선행 접지**: SOURCES.md §"CHU 수직축 = Kubernetes Scheduler/Node/GC family 와 동형" (이미 2026-05-09 박힌 씨앗) + `THEORY/333_CONSENSUSLESS_FRONTIER/` (consensus number 프론티어).

---

## 0. 사용자 비유 해부 — Piper ≠ Borg, 두 축을 분리해야 함

사용자가 한 문장에 **두 개의 서로 다른 구글 인프라**를 묶었다. 흡수하려면 먼저 갈라야 한다 (layer 정렬 먼저 = 카테고리 오류 회피).

| 구글 인프라 | 본질 | SYMPOSIUM 대응 | 오픈소스 canon |
|---|---|---|---|
| **Piper** (+CitC) | *하나의* 거대 공유 소스-오브-트루스 트리. trunk-based, fine-grained ACL, 대규모 병렬 write 조정 (Potvin & Levenberg 2016, CACM) | **KG(정본) + monorepo mirror + OMD** (N agent가 *한* repo에 disjoint write-set lease로 병렬) | (직접 오픈소스 없음; OMD가 자체 결정화) |
| **Borg** | 클러스터 job 스케줄러. bin-packing, priority/preemption, quota (Verma et al. 2015, EuroSys) | **AGENT_CLOUD / 333 / ORRR** — agent가 compute에 배치되는 substrate | **Kubernetes** (Borg의 오픈소스 후예) |

→ **결론**: 사용자의 "파이퍼"는 *공유 상태/소스-오브-트루스* 축(= OMD·KG), "보그"는 *compute 오케스트레이션* 축(= 333·ORRR)이다. 본 흡수는 **보그 축 = Kubernetes**를 정본으로 받아 333·ORRR를 접지한다. Piper 축은 OMD 쪽 cross-ref만 남긴다 (§5).

**핵심 통찰 (사용자 비유의 정합)**: Piper와 Borg는 구글에서 *한 쌍*이다 — Piper가 "무엇을 실행할지의 단일 진리(코드)", Borg가 "그것을 어디서 돌릴지의 단일 진리(배치)". 333·ORRR도 같은 쌍 구조: OMD/KG가 *설계 진리*, 333/ORRR가 *실행 substrate*. 4위상 정전의 *데이터(CHU) ↔ 인프라(AGENT_CLOUD)* 동치의 산업 결정화.

---

## 1. Kubernetes 아키텍처 랜드마크 (실측, TPA TCW)

clone된 실제 트리에서 확인한 control-plane 골격 (`cmd/`, `pkg/scheduler`, `pkg/controller`):

```
control plane (cmd/):
  kube-apiserver          — 유일한 상태 관문. 모든 read/write가 여기로. etcd 앞단.
  kube-scheduler          — Pod → Node 배치 결정 (pkg/scheduler/schedule_one.go)
  kube-controller-manager — 수십 개 control loop 묶음 (pkg/controller/*)
  kubelet                 — per-node agent. 배치된 Pod을 실제로 실행 (node substrate)
  kube-proxy              — per-node 네트워크 규칙
  cloud-controller-manager — 클라우드 provider 연동 (LB, 볼륨, 노드)

상태 저장 (트리 밖):
  etcd — Raft 합의 (Ongaro & Ousterhout 2014). CP-in-CAP. 강한 일관성 단일 진리.
```

**세 개의 근본 메커니즘** (이게 흡수 대상):

1. **선언적 desired-state reconciliation (level-triggered control loop)**
   `pkg/controller/doc.go`: *"controllers (like the replication controller)"*. 각 컨트롤러 = 무한 루프: `desired state`(사용자가 선언) 를 읽고 `actual state`(관측) 와 비교, diff를 향해 세계를 민다. **edge-triggered(이벤트) 아님 — level-triggered(현재값)** = 이벤트를 놓쳐도 다음 관측에서 수렴. 자가치유(self-healing)의 원천.

2. **스케줄러 = filter → score → bind 파이프라인** (`pkg/scheduler/framework/`, `schedule_one.go:scheduleOnePod`)
   plugin framework: **Filter**(하드 제약 = 이 노드에 놓을 수 있나 predicates) → **Score**(소프트 랭킹 = 어느 노드가 더 나은가 priorities) → **Reserve/Bind**(확정). 확장점(extension point)마다 plugin 교체 가능.

3. **강한 일관성 단일 store (etcd/Raft)**
   모든 컨트롤러·스케줄러가 apiserver를 통해 *하나의* 일관된 상태를 read/write. 낙관적 동시성은 리소스 `resourceVersion`(MVCC)로 apiserver 레벨에서 처리하지만, **밑바닥 진리는 Raft 합의 = 리더 기반 전순서(total order)**.

기타 흡수 가치 높은 컨트롤러 (실측 `pkg/controller/`):
- `garbagecollector/` — ownerReferences + finalizers로 고아 객체 회수 → **오캄(Occam) 직접 대응**
- `resourcequota/` — 네임스페이스별 자원 상한 강제 → **ORRR 과금/미터링 대응**
- `podautoscaler/` — 부하 기반 replica 조정 → 탄력 substrate
- `nodelifecycle/`, `disruption/` — 노드 실패/축출 처리 → liveness

`staging/src/k8s.io/dynamic-resource-allocation/` + `pkg/scheduler/backend/api_dispatcher` (실측 import) = **DRA(Dynamic Resource Allocation)**: GPU 등 특수 자원을 claim/allocate하는 최신 서브시스템 → **ORRR paid-compute marketplace의 산업 원형** (자원 = claim 대상 = 가격표 붙일 수 있는 것).

---

## 2. 결정적 발견 — Kubernetes ≈ ORRR, NOT 333

333 SOURCES(2026-07-12 PROM)의 정본: **333 = free/decentralized/P2P, consensusless (owned-object, consensus number 1, no global ledger)**. 이건 Kubernetes와 *정반대*다.

| 축 | Kubernetes | 333 (free/P2P) | ORRR (paid marketplace) |
|---|---|---|---|
| 상태 진리 | etcd/Raft **강한 합의** (CP) | **합의 없음** (owned-object, CRDT local-first) | 중앙 marketplace 장부 (managed) |
| 신뢰 모델 | 단일 관리 도메인 (crash-fault, 비잔틴 아님) | 무신뢰 P2P (검열저항) | 과금 주체 신뢰 (미터링) |
| 스케일 한계 | etcd 합의 = 병목 (~5000 노드/클러스터, 넘으면 federation) | 병목 없음이 목표 | marketplace 처리량 |
| 배치 | 중앙 스케줄러 filter/score/bind | P2P 자원 발견 (gossip/DHT) | bid/ask 가격 매칭 |
| 회수 | GC 컨트롤러 (ownerRef) | tombstone + CRDT GC frontier | 결제 정산 |

→ **판정**: Kubernetes는 333의 *모델*이 아니라 ORRR의 *모델*이다. 그리고 333에게는 **대조 canon(cautionary canon)** 이다 — "합의 병목을 받아들이면 이렇게 된다(강한 일관성·자가치유는 얻지만 etcd가 스케일 천장이 된다)"를 보여주는 반례. 이는 `consensus-prom16-333-no-blockchain-2026-07-12`(333은 full 블록체인 불필요)와 정합: Kubernetes도 *부분* 합의(컨트롤플레인)만 쓰고 데이터플레인(kubelet이 실제 실행)은 합의 밖에 둔다. 합의의 *국소화*.

---

## 3. 다리 — Omega의 낙관적 동시성이 333_CONSENSUSLESS_FRONTIER의 산업 원형

여기가 이번 흡수의 최고 가치다. Borg→Omega→Kubernetes 진화(Burns, Grant, Oppenheimer, Brewer, Wilkes 2016, "Borg, Omega, and Kubernetes", ACM Queue)에서 **Omega**(Schwarzkopf et al. 2013, EuroSys)가 핵심:

- **Borg**: *monolithic* 중앙 스케줄러 — 모든 배치 결정이 한 곳을 통과 (전역 락 성격). 스케일·유연성 병목.
- **Omega**: *shared-state + optimistic concurrency control*. 여러 스케줄러가 셀 상태의 *공유 사본*을 각자 보고, 배치를 **낙관적으로 claim**, 커밋 시 **원자적 트랜잭션 + 충돌 감지**로 해소. 충돌하면 재시도. **전역 락 없음, 그러나 일관된 공유 상태(MVCC).**
- **Kubernetes**: apiserver `resourceVersion` = 같은 낙관적 동시성(OCC)을 REST 리소스마다 적용. compare-and-swap write.

→ **이게 정확히 `333_CONSENSUSLESS_FRONTIER`가 더듬는 지점이다**: 모놀리식 합의(Raft 전순서) 없이, *낙관적 동시성 + 충돌 감지*로 자원 이전/배치의 정합을 유지하는 중간 길. 333 SOURCES가 이미 인용한 **Sui-Lutris/FastPay**(owned-object broadcast, 단일소유 이전은 consensus number 1)는 *블록체인 측* 같은 아이디어이고, **Omega의 OCC-on-shared-state는 *클러스터 스케줄링 측* 같은 아이디어**다. 둘이 같은 정리의 두 결정화.

**흡수 명제 (PRELIMINARY)**:
> `omega-occ-is-333-consensusless-precedent-2026-07-15`: 333의 consensusless 자산이전/배치는 *비합의(no-order)*가 아니라 **낙관적 동시성 + 충돌 감지 + 재시도(OCC)**로 재정의되어야 한다. "합의 없음"의 정확한 공학 이름 = *pessimistic total-order(Raft)의 거부 + optimistic conflict-detection의 채택*. Omega는 이것이 프로덕션 스케일에서 동작함을 보인 산업 증거(2013~).

이는 333_CONSENSUSLESS_FRONTIER의 **DV-1/C9**(transfer333는 quorum·서명 없음 → Byzantine-transferable 미달, equivocation 테스트가 oracle)에 방향을 준다: Omega는 *crash-fault* 가정(단일 신뢰 도메인)이라 비잔틴 방어를 안 한다. 따라서 333이 **무신뢰 P2P**를 원하면 Omega의 OCC만으로 부족하고 **C3의 Byzantine quorum-certificate(n≥3f+1)** 계층이 OCC 위에 얹혀야 한다. 즉 333 = *Omega OCC (성능·동시성) + Sui-Lutris owned-object (합의 국소화) + BFT quorum-cert (비잔틴 방어)* 3층 합성. Kubernetes/Omega는 이 중 **아래 두 층까지만** 검증된 산업 canon을 제공하고, 최상위 비잔틴 층은 여전히 333의 프론티어(OPEN)로 남는다.

> **보정 (2026-07-15 실측, 원문 보존)**: 위 마지막 문장("비잔틴 층 = 프론티어 OPEN")은 작성 시점에 이미 stale이었다. **비잔틴 quorum-cert 층은 2026-07-14에 transfer333에 구현 완료** — Ed25519 authority(RFC8032) + Certificate/QC(quorum=n−f) + Committee + type-state `Verified` rail + 결정론 mesh + 실 TCP transport + Plumtree epidemic + 멀티프로세스 node binary + ooptdd conformance 4/4 GREEN (canonical repo `gj3447/333` = `CD/333`, tip `fb08f13`, cargo test **89 passed / 0 failed** 실측 2026-07-15). 3층 합성 프레임 자체는 유효하나 상태는 OPEN이 아니라 **IMPLEMENTED**. 잔존 프론티어(진짜 OPEN) = ① browser substrate (WebRTC/WASM — 333 정체성 "P2P browser base" vs 현 native TCP) ② 동적 멤버십(committee reconfiguration, membership333 orphaned) ③ DV-2 equivocation-lock 복구의 합의-free 가능성 ④ mint CN-k formal verification. 근거: memory `project_333_and_hnsw_hardening_blockers_2026_07_14` + 본 세션 실측.

---

## 4. TPA 5-drift audit (333·ORRR vs Kubernetes)

| drift 축 | 333 (free/P2P) | ORRR (paid marketplace) |
|---|---|---|
| **Missing** (k8s엔 있으나 우리 정전에 없음) | level-triggered reconciliation control loop; DRA claim/allocate 프로토콜 | resourcequota 미터링; scheduler score에 *가격* 차원; DRA = paid resource 원형 |
| **Orphan** (우리 정전엔 있으나 k8s와 무관) | 검열저항·무신뢰 P2P (k8s는 단일 신뢰 도메인 — 대응 없음) | (거의 없음 — ORRR ≈ k8s+과금) |
| **SigMismatch** (같은 개념 다른 형태) | 333 "consensusless" ↔ Omega "OCC on shared state" (같은 정리, 다른 어휘) | ORRR "marketplace 매칭" ↔ k8s "filter→score→bind" (score축에 price 추가) |
| **PatternDiv** (구조 발산) | 333 = 합의 병목 *제거* 지향 ↔ k8s = 합의 병목 *수용*(etcd) | ORRR = 다중 provider 시장 ↔ k8s = 단일 클러스터 (federation은 별도) |
| **LabelRot** (라벨 노후) | "블록체인 기초"(2026-07-12에 이미 CARGO-CULT 판정) — Omega OCC 라벨로 교체 권장 | "paid compute marketplace"는 유효 — DRA로 산업 grounding 강화 |

**Mirror 판정** (`family-relation-mirror-hypothesis`):
- 333 ↔ Kubernetes = **NOT_MIRROR** (책임 분할·합의 모델 정반대. k8s는 대조 canon).
- 333 ↔ **Omega OCC** = **PARTIAL_MIRROR** (낙관적 동시성 층에서 STRONG, 비잔틴 층에서 GAP).
- ORRR ↔ Kubernetes(+quota+DRA) = **STRONG_MIRROR_CANDIDATE** (managed·미터링·중앙 스케줄러 = ORRR 본질).

**Lakatos 판정**: **PROGRESSIVE** — 새 사실(Omega OCC가 consensusless의 산업 원형) 예측 + 정직한 한계(비잔틴 층은 k8s 밖) + Goodhart 안전장치(k8s는 crash-fault라 333의 무신뢰 목표를 *부분만* 충족). *lakatos_mechanism = concept-stretching*(333 "consensusless"를 "OCC + 합의 국소화 + BFT quorum" 3층으로 정밀화).

---

## 5. Piper 축 cross-ref (OMD와의 연결 — 별도 축, 참고만)

사용자 비유의 "파이퍼" 절반은 333/ORRR가 아니라 **OMD(Orbital Motion Droplet)** 로 간다:
- Piper/CitC = *한* 트리에 다수가 병렬 작업, 충돌을 사전 방지 (workspace 격리 + fine-grained lock).
- OMD = *한* git repo에 N agent 병렬, 충돌을 사전 방지 (git-worktree 격리 + server-authoritative disjoint write-set lease).
- **동형**: Piper의 "누가 어느 파일을 쓸 수 있나(ACL/lock)" = OMD의 `claim(agent, paths)` write-set lease. Piper의 CitC(Clients in the Cloud) = OMD worktree.
- 단 Piper는 *소스코드* 진리, OMD는 *병렬 dev 조정*. Kubernetes(Borg 축)는 *런타임 배치* 진리. 세 개가 4위상 정전의 데이터/인프라/런타임을 각각 결정화.

→ 별도 흡수 사이클 후보: `THEORY/재배맨/` 또는 OMD 문서에서 Piper 흡수 (본 리포트 범위 밖, OPEN).

---

## 6. 흡수 결정화 (PRELIMINARY — CANONICAL 격상은 사용자 verdict 게이트)

제안 KG 노드 (아직 미write — 사용자 verdict 후 결정화):
- `omega-occ-is-333-consensusless-precedent-2026-07-15` (:AbsorptionFinding:PRELIMINARY) — §3 핵심 명제
- `kubernetes-is-orrr-model-not-333-2026-07-15` (:AbsorptionFinding:PRELIMINARY) — §2 판정
- `k8s-reconciliation-loop-canonical-2026-07-15` (:DaemonPattern:PRELIMINARY) — level-triggered desired-state 루프 (Harness/Hades realize 축 cross)
- `:ABSORBED_FROM` edge: ORRR → Kubernetes {industry_strength: STRONG_MIRROR}, 333 → Omega {industry_strength: PARTIAL_MIRROR}, 333 → Kubernetes {industry_strength: CONTRAST_CANON}

SOURCES 갱신 (본 커밋): `333/SOURCES.md` OPEN #1·#2 + `ORRR/SOURCES.md` OPEN #2 에 Kubernetes/Borg/Omega 정본 referent 답 반영.

---

## 7. 1차 소스 (외부 정본)

| # | 소스 | 관련 |
|---|---|---|
| 1 | Verma, Pedrosa, Korupolu, Oppenheimer, Tune, Wilkes. *Large-scale cluster management at Google with Borg*. EuroSys 2015 | Borg = 원형 |
| 2 | Schwarzkopf, Konwinski, Abd-El-Malek, Wilkes. *Omega: flexible, scalable schedulers for large compute clusters*. EuroSys 2013 | **OCC on shared state = 333 다리** |
| 3 | Burns, Grant, Oppenheimer, Brewer, Wilkes. *Borg, Omega, and Kubernetes*. ACM Queue 14(1) 2016 | 진화 3단계 |
| 4 | Ongaro & Ousterhout. *In Search of an Understandable Consensus Algorithm (Raft)*. USENIX ATC 2014 | etcd 합의 = ORRR 강한 일관성 |
| 5 | Potvin & Levenberg. *Why Google Stores Billions of Lines of Code in a Single Repository*. CACM 59(7) 2016 | Piper = OMD cross-ref (§5) |
| 6 | `kubernetes/kubernetes` HEAD (dgx clone 2026-07-15) — `pkg/scheduler/schedule_one.go`, `pkg/controller/{garbagecollector,resourcequota,podautoscaler}`, `staging/.../dynamic-resource-allocation` | 실측 |

---

## Cross-ref
- 상위 OMC: `SOURCES.md`
- 짝패: `333/SOURCES.md`, `ORRR/SOURCES.md`
- consensus 프론티어: `THEORY/333_CONSENSUSLESS_FRONTIER/`
- Piper 축: OMD (`about()` MCP / OMD README)

# KG (제안, PRELIMINARY): omega-occ-is-333-consensusless-precedent-2026-07-15, kubernetes-is-orrr-model-not-333-2026-07-15, k8s-reconciliation-loop-canonical-2026-07-15
# KG (선행): commander-333-omc-2026-05-19, commander-orrr-omc-2026-05-19, consensus-prom16-333-no-blockchain-2026-07-12, formal-grounding-orbital-motion-cloud-2026-05-09
