# OMC 연구 지도

이 표는 source archive의 주제·관계를 조회하기 위한 `SECONDARY_AI` 지도다. 관계의 evidence는 고정 원문이며, `PRELIMINARY`·OPEN·설계 제안은 배포 또는 재현 완료가 아니다.

## 원문 inventory

- 상위: `SOURCES.md`, `PROM_16_FAMILY_VERIFICATION_REPORT.md`, `KUBERNETES_BORG_ABSORPTION_2026-07-15.md`
- 333: `333/SOURCES.md`, `333/PROM_16_REPORT.md`
- feasibility: `OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/{A,B,C,D,INDEX,PROM_16_REPORT,SOURCES}.md`
- engineboy: FSM, binding, measurement, caching, report, semantic hypergraph, SOURCES
- 보조: `ORRR/SOURCES.md`

### 정확한 archive links (20)

- [333 report](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/333/PROM_16_REPORT.md) · [333 sources](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/333/SOURCES.md) · [Kubernetes/Borg](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/KUBERNETES_BORG_ABSORPTION_2026-07-15.md) · [family report](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/PROM_16_FAMILY_VERIFICATION_REPORT.md) · [root sources](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/SOURCES.md) · [ORRR](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/ORRR/SOURCES.md)
- [A substrate](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/A_p2p_substrate.md) · [B token](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/B_token_primitives.md) · [C cold start](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/C_cold_start_sustainability.md) · [D cases](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/D_real_world_cases.md) · [feasibility index](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/INDEX.md) · [feasibility report](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/PROM_16_REPORT.md) · [feasibility sources](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/SOURCES.md)
- engineboy: [FSM](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/EMERGENCE_ENGINE_FSM_DESIGN_PRELIMINARY_2026-07-13.md), [binding](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/ENGINEBOY_333_BINDING_DESIGN_PRELIMINARY_2026-07-12.md), [measurement](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/MEASUREMENT_PLAYBOOK_2026-07-12.md), [traffic](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/PROM_16_CACHING_TRAFFIC_HIERARCHY_2026-07-13.md), [report](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/PROM_16_REPORT.md), [hypergraph](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/PROM_16_SEMANTIC_HYPERGRAPH_NN_2026-07-12.md), [sources](../sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/engineboy/SOURCES.md).

## typed relationship table

| Subject | Predicate | Object | Evidence | Status |
|---|---|---|---|---|
| OMC | HAS_COMMANDER_CONTEXT | 333 | `333/SOURCES.md:1-18` | source-declared |
| 333 | PAIRED_WITH | ORRR paid axis | `333/SOURCES.md:1-18` | source-declared |
| 333 design | REJECTS_AS_CARGO_CULT | PoW/global total-order for owned-object+CRDT framing | `333/PROM_16_REPORT.md:1-12, 24-49` | report finding; not rerun |
| 333 design | PRIORITIZES | content addressing + BFT-CRDT hardening | `333/PROM_16_REPORT.md:50-78` | proposed build order |
| Kubernetes | CONTRASTS_WITH | consensusless 333 framing via etcd/Raft | `KUBERNETES_BORG_ABSORPTION_2026-07-15.md:1-18` | archived analysis |
| Omega OCC | PARTIAL_MIRROR_OF | local conflict detection / scheduling framing | `333/SOURCES.md:35-52` | archived analysis |
| feasibility family | DECOMPOSES | substrate, token, cold-start, cases | `.../INDEX.md:1-36` | source inventory |
| engineboy | PROPOSES_MEASUREMENT_FOR | FSM/binding/traffic/hypergraph components | `engineboy/MEASUREMENT_PLAYBOOK_2026-07-12.md:1-12` | preliminary |
| OMD | IS_NOT_ALIAS_OF | OMC | `KUBERNETES_BORG_ABSORPTION_2026-07-15.md:11-24` | interpretation boundary |

## 2026-10-10 자원 기여와 공동 지능 이용

[OMC와 MHC의 목적 정리](RESOURCE_CREDIT_AND_SHARED_INTELLIGENCE.md)는 사용자가 설명한
지속적인 자원 제공 → 크레딧 획득 → 거대한 HSWM·CHU의 답변 이용을 연결한다.
사용자 원문은 `records/2026-10-10/resource-credit-shared-intelligence/`에 별도로 보존한다.
기존 구조와 목적의 분석은 WHAT_IS로, 구현을 발전시킬 질문은 후속 HOW_TO 연구의 입력으로 다룬다.
과거 source archive의 바이트나 당시 주장·판본을 이번 정리로 바꾸지 않는다.

## Known limits

The archive records reports and prior claims. It does not contain a current deployment receipt for a browser mesh, a rerun benchmark, or an authorization to allocate shared CPU/RAM.
