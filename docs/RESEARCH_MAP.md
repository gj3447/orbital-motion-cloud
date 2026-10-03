# OMC 연구 지도

이 표는 source archive의 주제·관계를 조회하기 위한 `SECONDARY_AI` 지도다. 관계의 evidence는 고정 원문이며, `PRELIMINARY`·OPEN·설계 제안은 배포 또는 재현 완료가 아니다.

## 원문 inventory

- 상위: `SOURCES.md`, `PROM_16_FAMILY_VERIFICATION_REPORT.md`, `KUBERNETES_BORG_ABSORPTION_2026-07-15.md`
- 333: `333/SOURCES.md`, `333/PROM_16_REPORT.md`
- feasibility: `OM_MANI_PADME_HUM/PROM_16_TECH_FEASIBILITY_2026-05-20/{A,B,C,D,INDEX,PROM_16_REPORT,SOURCES}.md`
- engineboy: FSM, binding, measurement, caching, report, semantic hypergraph, SOURCES
- 보조: `ORRR/SOURCES.md`

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

## Known limits

The archive records reports and prior claims. It does not contain a current deployment receipt for a browser mesh, a rerun benchmark, or an authorization to allocate shared CPU/RAM.
