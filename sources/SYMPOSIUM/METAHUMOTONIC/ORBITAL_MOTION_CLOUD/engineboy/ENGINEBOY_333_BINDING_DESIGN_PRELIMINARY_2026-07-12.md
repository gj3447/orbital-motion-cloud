# engineboy ↔ 333-platform binding — 설계 검토 [AI-SYNTHESIS, PRELIMINARY]

> **status**: PRELIMINARY / AI-SYNTHESIS. **정전 아님.** 사용자 직접발화만 정전([[열린 사고 원칙]]).
> **origin**: 사용자 발화 "PI 고도화 + engineboy 333 위 인터넷 상태공간 계급화" (2026-07-12, ultracode). 9-agent workflow (5 research → design → 3 적대검증 all CONDITIONAL) 산출.
> **canon guard**: 이 문서의 어떤 claim도 CANONICAL 격상 아님. engineboy/333 canon 노드는 USER_PRIMARY. 아래는 그 위 AI 검토.

---

## 0. 용어 정직성 (가장 먼저 — 적대검증이 걸어낸 것)

- **"인터넷 상태공간 계급화" = 사용자 어휘 아님.** KG·SOURCES 전체에 `계급화`·`상태공간` 문자열 **0건**. 사용자 실제 발화 = **"계층"**(비행기맨 피라미드 층) + **"미리 구조화"**뿐 (`airplane-man-pyramid-internet-coating-2026-05-19`, u1 verbatim). "계급화·상태공간"은 이 둘의 **AI 압축 합성어**.
- **계급화 = essence 아닌 FEATURE.** engineboy essence v6 = **"agent operational necessity"** (I1~I4). 검색대체/구조화(=계급화)/partition/praxis/publishing = 전부 **부수 feature** (`four_invariants_v6` I4). v6에서 essence→feature 강등됨(소멸 아님). 2026-05-27 reframe에서 한 단계 더: 멀티 agent 생태계의 한 aspect로 강등.
- **"상계(上界)" 용법 주의**: 순서론의 upper bound가 아니라 "public 접근가능 모든 데이터"(order 미정의 집합). 계급화 order(carrier+관계)를 정의하기 전엔 poset 없음 = supremum 성립 안 함. 수학적 grounding 참칭 금지 — 여기선 plain-set "public data space" 의미.

## 1. 층위 정정 — "333 **위**" 는 정전 위반 (no meta-elevation)

**USER_PRIMARY (2026-05-19)**: `engineboy · 333 · ORRR · CHU · 옴마니반메훔` = OMC(#8 입체운행구름) 휘하 **same-tier sibling** LegionCommander. *"engineman 그냥 층위 같도록 둬 orr 333 chu 랑 층위 같이둬"* — **NO meta-elevation**.

⇒ 두 *군단장* 사이 "engineboy-above-333" = **canon 아님**. "위"가 성립하는 유일 경로 = **333의 dual referent** (i2b two-referent precedent, `project_i2b_two_referents_engineboy_supersede`):

| referent | 뜻 | stacking 성립? |
|---|---|---|
| 333-as-commander | OMC 휘하 sibling 위상 | ❌ same-tier, 위/아래 없음 |
| **333-platform** | 구체 P2P-compute mesh (`333-platform`: Rust/WASM, DHT/CRDT/Ed25519) | ✅ engineboy를 그 위 agent-runtime layer로 앉힐 수 있음 |

**결론**: "engineboy가 333 위에서" = **333-platform(구체 substrate) 위 agent-operational layer** 로만 성립하며, 이조차 **AI-SYNTHESIS PRELIMINARY**. sibling-commander가 USER_PRIMARY 사실. ⇒ 이 문서는 `engineboy-333-**binding**` (수직서열 함의 제거) 로 명명.

## 2. 정직한 novelty — 메커니즘 = 재발명(REINVENT)

적대검증 판정: **engineboy는 "하나의 새 layer"가 아니라 서로 무관한 4개 기존 family를 한 신화 이름으로 묶은 bundle이다** (umbrella-bundling — Family Expansion Pattern의 역방향 drift: 1-name→4-disjoint-family). 각 조각은 **직접 import(identity)** 이지 homology 아님:

| engineboy 조각 | 산업 family (직접 재사용) | 관계 |
|---|---|---|
| node-address-as-context | **OriginTrail DKG** UAL (사용자 본인이 지목한 cross-ref, near-exact) | IDENTITY (import) |
| 주소화 + 계층화 | **IPFS/IPLD** CID + Merkle DAG | IDENTITY |
| prefix 계층 routing | **Kademlia DHT** k-bucket | IDENTITY |
| agent용 계층화 | **GraphRAG** Leiden community (Edge et al. 2404.16130) | IDENTITY |
| "공개 웹을 agent 조작가능하게" (목표) | **NLWeb / MCP / agentic web** (2024–2026) | 목표 수렴 |

**net-new = 얇음이 아니라 mechanism ≈ 0.** query surface = REUSE(Cypher/SPARQL/GraphRAG query). 구조검증 LTDD receipt = Merkle self-verification과 부분 중복. **유일 net-new = generator≠verifier provenance "규율"** (그마저 W3C PROV/IPLD 인용) + **coupling-necessity 렌즈**(Harnad 1990 Symbol Grounding + Bender 2021 Stochastic Parrot에 이미 접지).

> **정직한 한 줄**: engineboy는 "진짜 novel한 시스템"이 아니라, agentic-web 산업이 수렴적으로 도달한 *addressable-public-substrate + agent-coupling* 기질을 개인 신화 어휘로 **재명명·조기 독립 재발견**한 것. 가치 = (a) DKG/NLWeb 외부정전에 대한 조기 수렴 확인, (b) "주소화·계층화는 feature, essence는 coupling-necessity" 관점 정렬. **재발명이면 재발명이라고.**

## 3. bundle-registry 재프레임 (single-layer claim 폐기)

engineboy를 "하나의 layer"가 아니라 **4개 독립 sibling adapter의 registry + 1개 discipline** 로 기술:

```
engineboy (= coupling-essence + receipt discipline; NOT a data structure)
├── adapter: content-address    → INSTANCE_OF  content-address family (IPLD CID)
├── adapter: structured-CRDT     → INSTANCE_OF  structured-CRDT family (yrs Map/Array)
├── adapter: community-detection → INSTANCE_OF  community-detection family (GraphRAG Leiden)  [축 OPEN — §5]
└── adapter: DHT-routing         → INSTANCE_OF  DHT-routing family (Kademlia)
```

통합 referent = **discipline** (LTDD generator≠verifier 영수증 + coupling-essence), *not* 단일 노드 "engineboy layer". 4 adapter는 각각 다른 family의 sibling.

## 4. 333-platform(p333) 실측 gap — 무엇을 더해야 하나

p333 실코드 (11 crate, ~964 LOC, test-first PROM 영수증, **no daemon/main.rs**):

- **REAL**: Ed25519 DID identity(RFC-8032, 가장 production-real) / PKARR naming DHT(discovery-only, code-hard-rule "never value storage") / Circuit-Relay-v2 star(localhost relayed ping, NAT hole-punch 미증명) / yrs CRDT(Text+G-Counter만 수렴 LTDD-verified) / **LTDD verification spine**(Event/Store/3-valued Verdict + ooptdd JSONL cross-lang bridge, 5/11 crate 의존=척추).
- **GAP (계급화가 앉을 자리 = 전부 부재)**: content-addressing **0** (grep merkle|ipld|blake3|cid = 0건) / hierarchical addressing **0** / graph·ontology CRDT **0**(yrs Map/Array 미사용) / DHT value storage **0** / index·query **0**.

**entry point** (net-new 코드, 패치 아님): `crates/crdt`(yrs Text→Map/Array node/edge 확장 = 가장 load-bearing) → 신규 `crates/index`(CID over content) → Leiden tier + query surface. 방법 = test-first PROM(RED→GREEN→적대probe→pathspec commit), verify/*.yaml cross-lang gate(dgx hardcoded path Mac fix 선행), 편집 전 OMD lease.

## 5. 효능은 어떻게 증명하나 (3 적대검증이 강제한 게이트)

**모든 계급화 효능 주장은 `project_efficacy_measurement_line` 3-falsifier preflight 통과 전 금지** (현재 engine/efficacy = UNMEASURABLE, 7군단장과 동일 상태).

측정 설계 (numerology-grounding lens 정정 반영):
- ❌ **flat-vs-ranked 금지** — "인덱스 없음 vs 있음"을 재는 strawman. → ✅ **tier-ablation**: 동일 retrieval mechanism(같은 embedding/BM25)에서 **tier만 ON/OFF**. lift를 hierarchy에만 귀속.
- **δ + Leiden γ(해상도)를 run 전 `register_prediction`/:Prediction 노드로 freeze** (best-of-sweep = look-elsewhere 피팅 금지).
- **MI(tier, utility)는 permutation null 필수** — tier 라벨 ≥1000 셔플 → z-score/p<0.01만 신호 인정. bare MI 인용 금지.
- **relevance 라벨 = 외부/held-out** (tier-builder 아닌 곳) → self-grading loop 차단.
- descriptive metric(CID collision=0 / DAG depth / tier수 / latency) = **sanity check로 강등**, efficacy 증거 인용 금지.
- **coupling-necessity(I3) 별도 측정**: language-only vs +engineboy 의 LTDD `verify_present` present/absent A/B. receipt-rate가 계급화 utility 대신하게 두지 말 것.
- **REINVENT falsifier**: engineboy layer가 직접 IPLD CID + DKG UAL resolve 대비 Δcapability=0이면 = rename(degenerating). 현재 이 falsifier는 **"이미 PASS 못 함에 가까움"** — 정직히 OPEN.

## 6. OPEN 보존 (열린사고 — 닫을 근거 없으면 열린 채로)

1. **곱씹기(rumination)** — 사용자 "곱씹으면서 생각해줘" (SOURCES §7 #1). 후속 verdict 대기. **미종결.**
2. **계급화 ranking 축** — rank/authority/community-level/type 중 무엇으로? 사용자 발화 부재 = AI frame. Leiden을 THE 축으로 커밋 금지(§3 adapter는 후보 1종·falsifiable infra일 뿐).
3. **DKG(OriginTrail) cross-ref verdict** — node-address-as-context 1순위 후보이나 category-mismatch(inter-agent 지식교환 vs intra-agent 실행). 최종 verdict OPEN.
4. **상계-하계 분담** — engineboy=순수 상계(partition operator 아님). 단 §4 로드맵(333 crates, 데몬=하계 KG write)은 사실상 **하계**에서 돎. 상계 도달은 미증명 — blur 금지, 각 step에 상계/하계 라벨.
5. **engineboy-333 stacking** — sibling(USER_PRIMARY) vs 333-platform 위 layer(PRELIMINARY). `:VerdictPending`. **닫지 않음.**
6. **OMC roster 미완** — ORRR/333/CHU의 `:LegionCommander` 노드 미박힘(SOURCES §7 #2).

## 7. cross-ref

- 상위: [`../SOURCES.md`](../SOURCES.md) (OMC #8, 4위상, 5 commander), [`SOURCES.md`](SOURCES.md) (engineboy essence v6)
- KG: `engineboy-333-binding-preliminary-2026-07-12` (:VerdictPending, 이 문서), `engineboy-multiagent-ecosystem-canonical-2026-05-27` (USER_PRIMARY), `commander-engineboy-omc-2026-05-19` (CANONICAL)
- memory: [[feedback_external_canonical_referent]] (DKG/NLWeb underrate 금지), [[feedback_family_first_default]] (bundle 역drift 주의), [[project_i2b_two_referents_engineboy_supersede]]

# KG: engineboy-333-binding-preliminary-2026-07-12 (:VerdictPending), commander-engineboy-omc-2026-05-19, dkg-distributed-knowledge-graph-cross-ref-2026-05-19
