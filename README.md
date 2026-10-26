# Orbital Motion Cloud

Copyright (c) 2026 **MetaHumotonic Open Source Foundation Initiative contributors**. [MetaHumotonic License 1.2](LICENSE)를 적용하는 소스 공개형 프로젝트다. 본체와 외부 원문의 적용 범위는 [LICENSE-NOTICE.md](LICENSE-NOTICE.md)를 따른다. [USL 기반 리밸런싱 기준](docs/OMC_OPERATING_MODEL.md#usl-rebalancing)은 의미·주소 연결 보존과 실제 자원 실행을 연결한다.

[LFM 아키텍처](docs/LFM_ARCHITECTURE.md)는 HOH의 경험·피드백·학습과 AI 생산·기여 정산·생활 지원을 연결하는 설계다. 기존 owner별 구현 경로, 데이터·그래프 계약, 단계별 수용 기준을 포함하며 구현·운영 완료와 구분한다.

**우리의 권한은 Dimension Walker, 회사의 권한은 METAHUMO다.** [사용자 원문](records/2026-10-26/omc-authority-operating-model/README.md#user-source)을 보존하고 [OMC 운영 헌법](docs/OMC_CONSTITUTION.md)과 [기술 운영 기준](docs/OMC_OPERATING_MODEL.md)에 적용했다. 회사의 기존 실행·관측 경로를 재사용하면서 목적·원천·결과를 연결하며, 이 문서 적용과 실제 상시 서비스 배포를 구분한다.

Position 8 apostle module. This repository preserves the source-attested identity and English label. The user's 2026-10-10 assignment adds hardware-adaptive data placement as one OMC function; the local implementation is a bounded CLI, with the original identity and source archive preserved.

**입운구 / OMC / 입체운행구름 / Orbital Motion Cloud** resolve to this module. Identity and source pins are in `APOSTLE_MODULE.json`. The research hub owner is [인역강 / THE GREAT FLOW](https://github.com/gj3447/the-great-flow); its `graph/apostles.json` records the aliases and roster selection. Historical Dashboard source pins retain their original owner URLs.

```sh
python3 cli.py identity
python3 cli.py show
python3 cli.py check
```

Start with [WHAT_IS](docs/WHAT_IS.md) for the conceptual map, then [RESEARCH_MAP](docs/RESEARCH_MAP.md) for source-to-claim relationships and current limits. [HOW_TO](docs/HOW_TO.md) gives a reproducible reading and evidence procedure.

[입체운행구름 아키텍쳐](docs/ORBITAL_MOTION_CLOUD_ARCHITECTURE.md) explains the hardware-native direction: AI composes software variants, data placement and execution around each machine's actual capabilities, while preserving meaning and linking resource contribution to shared intelligence.

[Hardware-adaptive placement](docs/HARDWARE_ADAPTIVE_PLACEMENT.md) observes storage and memory, checks an AI-selected batch, uses the existing owner transfer CLI, and verifies that USL resource IDs, meanings, roles and provenance survive location changes. Run `python3 scripts/placement_graph.py check` and `python3 scripts/placement.py --help`. Private host registrations stay under ignored `.local/`; the CLI preserves source files.

The [hardware and software fit plan](docs/HARDWARE_SOFTWARE_FIT_PLAN.md) extends that direction toward hardware-specific native program variants, execution settings and data placement under CHU OS. The [verbatim user statement](records/2026-10-10/hardware-software-fit/user-verbatim.txt) is separate from the [proposed graph and runtime contracts](graph/hardware-software-fit.proposal.json). This is a HOW_TO design, with phased acceptance criteria; it does not claim a deployed autonomous runtime. Validate the design with `python3 records/2026-10-10/hardware-software-fit/validate.py`.

[DGX runtime monitoring](docs/DGX_MONITORING.md) implements the bounded observation layer: host memory/CPU/storage, NVIDIA GPU activity, active and stopped model containers, and registered vLLM queues, KV occupancy and token counters. Use `omc-dgx`, `omc-dgx watch`, or `omc-dgx status --json` from the configured gateway. The native DGX collector keeps up to 12 hours of observations with systemd resource limits; it does not change models or perform automatic placement.

The [post-client-server knowledge plan](docs/POST_CLIENT_SERVER_KNOWLEDGE_PLAN.md) turns that direction into twelve knowledge areas, their dependencies, concrete contracts and a first bounded experiment. The [Kubernetes source analysis](docs/KUBERNETES_SOURCE_ANALYSIS.md) follows API updates, observation, controllers, scheduling and node execution at an official pinned commit. [Source records](records/2026-10-10/post-client-server-kubernetes/README.md) distinguish verbatim user input, acquired source bytes, static analysis and proposed OMC design. The [knowledge graph](graph/post-client-server-knowledge.json) is owner-local; validate it with `python3 records/2026-10-10/post-client-server-kubernetes/validate.py`.

The first follow-up study, **K01**, separates [workload semantics, retries and effects](docs/research/K01_WORKLOAD_SEMANTICS.md), then implements a [bounded pure-task contract](docs/research/K01_WORKLOAD_CONTRACT.md). Two local variants pass 20,575 candidate checks across 4,115 inputs; five deliberately incorrect variants are rejected. [Evidence and reproduction](records/2026-10-11/k01-workload-contract/README.md) distinguish actual local computation from a retry state model and unexecuted distributed work. K02 identity/version/location is the next research question; the twelve-area plan remains open.

The [2026-10-10 OMC and MHC purpose note](docs/RESOURCE_CREDIT_AND_SHARED_INTELLIGENCE.md)
records the user's direction: continuously contribute computing resources, earn credits,
and use the larger HSWM·CHU intelligence through a P2P economy and mutual agreement.
The [verbatim request](records/2026-10-10/resource-credit-shared-intelligence/user-verbatim.txt)
is preserved separately from the explanatory design note and the older source archive.


The [current HSWM graph / CHU_OS boundary](docs/HSWM_GRAPH_CHU_OS_BOUNDARY.md) governs the next work: engineer the HSWM semantic and cognitive graph using its existing canonical schema and standards tooling. In the [latest 2026-10-12 scope correction](records/2026-10-12/chu-computable-scope/README.md), CHU means Computable Hyper Universe: under the user's view that everything consists of hypergraphs, everything computable is CHU. Cognition is not a requirement. CHU_OS is a computer-based operating-system implementation within that scope; OMC adapts physical placement. The [owner concept ontology](../CHU/philosophy/graph/README.md) now includes this computable scope, cognition as a non-requirement, and the attributed hypergraph viewpoint (CHU commit `7d21bc0`). Run `./chu concept query scope` in CHU to retrieve the claims and original source. The [2026-10-12 graph record](records/2026-10-12/chu-concept-graph/README.md) remains historical evidence for its pinned revision. The owner records a separate CHU_OS initial handoff; consumer runtime transitions remain open. See the [dated separation record](../CHU/docs/CHU_CHU_OS_REPOSITORY_SPLIT.md). The earlier CHU storage adapter and implementation-evidence graph do not establish an HSWM graph implementation.

The historical [HOH chat flywheel plan](docs/HOH_CHAT_FLYWHEEL_PLAN.md) connects the user's near-term flywheel priority and long-term device participation direction. It specifies a CHU/HSWM-based conversation path, OMC execution, independently assessed outcomes and revision consumption in the next turn, with eight planned implementation stages. The [source review](docs/HOH_CHAT_FLYWHEEL_SOURCE_REVIEW.md) and [typed plan graph](graph/hoh-chat-flywheel.json) preserve observed source structure, user input and AI design separately. Run `python3 records/2026-10-11/hoh-chat-flywheel/validate.py`; this validates the plan, not a deployed cognitive loop.

The [F0 implementation record](records/2026-10-11/hoh-chat-f0/README.md) now links the bounded HOH host implementation to that plan: durable turns and outcomes, atomic confirmation/cancellation, restart recovery, and authenticated history/assessment APIs. Type checking, build and 110 tests passed locally; CHU admission, HSWM execution and live deployment remain subsequent work.

The [F1 implementation record](records/2026-10-11/hoh-chat-f1/README.md) adds request-time context capture and an authenticated CHU OS storage/exchange projection. The actual pinned CHU reference model verifies bytes, ordered roles and two immutable snapshots; 91 tests, type checking and build passed on a frozen source snapshot. HSWM semantic graph construction and its standards validation remain open; the next priority is that HSWM graph work. Production CHU admission and HSWM execution are separate remaining tasks.

## Content index

Start with [philosophical and technical-philosophical OMC](docs/OMC_LOGICAL_FOUNDATIONS.md)
for the argument connecting existence, persistence, shared intelligence and the
meaning, learning, resource and agreement loops. The [source review](docs/OMC_FOUNDATION_SOURCE_REVIEW.md)
separates inherited statements from the new reasoning; the [argument graph](graph/omc-foundations.json)
keeps inferential dependencies separate from conditional feedback cycles.

The [OMC perspectives and MIND sources](docs/OMC_PERSPECTIVES_AND_MIND.md) preserve
the user's distinction between technical OMC, actual philosophical OMC, and OMC
as seen by Dimension Walker. Five complete MIND texts, including the airplane-man
CLOUD CONNECT scene, are preserved with their provenance in the
[2026-10-10 source record](records/2026-10-10/mind-omc-perspectives/README.md).

The [token-efficiency flywheel](docs/FLYWHEEL.md) starts with a testable premise:
the same base LLM and total token budget should yield more useful answers through HSWM·CHU.
See the [generated cycle diagram](docs/FLYWHEEL_GRAPH.md) and [typed graph](graph/flywheel.json).
Run `python3 scripts/flywheel.py check` for provenance and graph validation, or
`python3 scripts/flywheel.py query` for the premise, accounting rules and evaluation status.
Performance and economic effects remain hypotheses awaiting experiments.

`APOSTLE_CONTENT.json` lists the original SYMPOSIUM archive's files, byte digests, and source revision. That archive begins at `sources/SYMPOSIUM/METAHUMOTONIC/ORBITAL_MOTION_CLOUD/`; it is `SOURCE_DOCUMENT`. The MIND snapshots have their own [source manifest](records/2026-10-10/mind-omc-perspectives/sources.json). This README and `docs/` are `SECONDARY_AI` guides. “OMC” is the canonical abbreviation for Orbital Motion Cloud; “OMD” is a separate shared-source-of-truth / coordination reference, not an alias for this apostle.
