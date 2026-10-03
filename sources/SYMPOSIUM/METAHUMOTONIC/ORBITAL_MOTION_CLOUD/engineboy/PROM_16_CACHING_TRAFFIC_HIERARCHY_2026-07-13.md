# PROM 16 — engineboy 캐싱·traffic-가중·계층 인덱스 (2026-07-13)

> cycle_id: `prom16-engineboy-caching-2026-07-13` · N=16 (4축 × 4렌즈) · haiku 16기 · 16/16 HIGH confidence
> 씨앗: 사용자 발화 2026-07-13 "engineboy 에서 중요한건 캐싱도 있다고봐 …" → KG `engineboy-caching-traffic-weighted-hierarchy-2026-07-13`
> KG: `lesson-engineboy-caching-research-prom16-2026-07-13` + 16 `rf-engineboy-caching-{A1..D4}-2026-07-13`

engineboy = **인터넷 공개데이터(상계)를 검색 traffic으로 가중치 매기고 HNSW식 계층으로 로컬 캐시(materialize)한 가중 시멘틱 하이퍼그래프**. 4축(A 캐싱 / B traffic-가중 / C 계층 인덱스 / D public·private 경계)으로 이론·산업 지식을 수집.

---

## 0. 한 줄 판정

engineboy가 겨눈 아키텍처는 **2026 현재 이미 존재하는 4개 산업 스택의 통합**이다. 발명이 아니라 계승 — 각 축마다 정본(foundations)·production 시스템·함정·2026 최전선이 명확히 자리잡혀 있고, engineboy의 신규성은 이 넷을 *한 몸(가중 시멘틱 하이퍼그래프)*으로 묶는 데 있다. **최근접 최전선 = GraphRAG + HippoRAG2 + RAPTOR + DiskANN**.

---

## 1. Consensus (축별 정본)

### C1 — engineboy = 4개 확립된 스택의 통합, 재발명 아님
- **A 캐싱**: Materialized View(IVM, DBSP/Enzyme 2025) + semantic caching(Dar VLDB1996) + learned index(Kraska 2018). "클라우드서 그대로 안 돌리고 복사"는 곧 **증분 뷰 유지(recompute 회피)**의 정확한 재기술.
- **B traffic-가중**: LFU(접근빈도) + PageRank(링크 정상반복) + **Hebbian**("fire together wire together"). 사용자 직관 "traffic으로 가중치 창발"의 정본 = Hebbian + click-graph learning-to-rank. **2026 발견: Hopfield 네트워크(Hebbian) = Transformer attention의 dual** (HeLa-Mem 2026).
- **C 계층**: **HNSW**(Malkov 2018)가 "계층으로 빠르게"의 산업 표준 (Weaviate/Milvus/Qdrant/pgvector 전부 채택, 95-99% recall @ 4-16ms p50).
- **D 경계**: public/private 캐시 경계는 **relevance가 아니라 query-user identity + IAM 실시간 검증**으로 그어야 함. Glean/MS Copilot/Slack/Google Vertex 전부 production 확증.

### C2 — traffic이 가중치를 만든다 (사용자 핵심 직관 = 정본)
검색·클릭 traffic → implicit feedback → 동적 가중치. 검색엔진(LambdaMART/BPR)과 2026 최전선(learned index + adaptive routing + RLHF)이 모두 이 루프. **정적 링크(PageRank)보다 동적 traffic(Hebbian/click-graph)이 사용자 의도에 더 가깝다.**

### C3 — 계층화 = 효율·속도의 실제 자료구조 (사용자 직관 = 정본)
"계층구조로써 동작하게 해서 빠르게"의 산업 정답 = HNSW 계층 + 메모리 L1/L2/L3 tiering + hot/warm/cold. 최전선은 여기에 **GraphRAG 커뮤니티 트리 + HippoRAG2 PageRank seed + RAPTOR 재귀요약 + DiskANN disk-cache**를 얹음.

### C4 — engineboy 최근접 최전선 = HippoRAG2 계열
가중 시멘틱 하이퍼그래프 + PageRank 가중 seed + 계층 캐시 = **HippoRAG2 + GraphRAG + DiskANN**이 그대로. engineboy vision(2026-07-12 USER_PREFIGURED)과 일치. Hopfield fast-weight 적응성이 차별점.

---

## 2. Divergence / Tension

- **D-1 (가중치 출처)**: traffic 동적 가중(Hebbian/click) ↔ 임베딩 정적 유사도. 둘의 합성 방식 미결. → **열린 질문 OQ-1**.
- **D-2 (prompt caching 상충)**: Anthropic prompt caching은 prefix-tree(결정적 바이트 순서) 요구 → engineboy의 *adaptive weight ordering*과 상충(A2). 결론: engineboy는 캐싱층 *안*이 아니라 *위(전략층)*에 위치.
- **D-3 (cache-first 낙관)**: engineboy "로컬 캐시" 설계는 메모리 footprint 낙관적(C3). HNSW는 >10B 스케일서 cost/memory 금지적, embedding drift·orphan-node 열화 노출.

---

## 3. Open Questions (닫지 않음)

- **OQ-1 (가중치 합성)**: traffic 가중치가 primary이고 임베딩은 bootstrap인가, 아니면 곱/가중합인가? KG `oq-engineboy-weight-source-traffic-vs-embedding-2026-07-13`.
- **OQ-2 (private → 상계 캐시 경계)**: 사용자가 던진 "private가 어디에 있고"가 여기. **D3가 경고**: private를 shared 임베딩 캐시로 당기면 3중 공격(inversion<1000쿼리 / semantic collision 86% / timing side-channel). **현 engineboy는 multi-tenant와 비호환** — 완화책 = per-tenant embedder(효율↓) 또는 privacy-preserving(latency↑). KG `oq-engineboy-private-into-sangye-cache-boundary-2026-07-13`.
- **OQ-3 (traffic 가중 병리)**: Matthew-effect / filter-bubble / cold-start / stale-immortality 6 실패모드 단일 완화책 없음(B3). engineboy는 multi-axis constraint layer 필요 — 오캄(occam)·나생문(naesengmoon) 결합 지점 후보.

---

## 4. 권장 후속 작업

| # | 작업 | 근거 셀 | 무기 |
|---|---|---|---|
| 1 | HNSW 계층 캐시 프로토타입 (KG gds+vector dim768 위) | C1/C2 | 하데스(실현) |
| 2 | traffic→weight 창발 엔진 설계 (Hebbian/click-graph, LFU-variant) | B1/B2/B4 | 유레카(창조) |
| 3 | Matthew-effect constraint layer (cold-start·diversity 정규화) | B3 | 나생문+오캄 |
| 4 | private/public 경계 = ACL-aware 캐시 정책 (D3 공격 3종 방어) | D1/D2/D3 | 롱기누스(바인딩)+SpaceGirl |
| 5 | HippoRAG2 계열 벤치마크 → engineboy vision과 gap 측정 | C4 | 프로메테우스+engineboy_measurement |

**핵심 병목(gap)**: 모든 축이 산업적으로 성숙 → engineboy 실행 갭은 (a) **embedding populate**(기존 vision 결론) + (b) **hypergraph N:N materialization spec**(2026 시스템은 다 DAG/tree 가정, engineboy의 하이퍼그래프는 신설 필요) 두 가지뿐.

---

## 부록 — 16셀 1줄 요약

| 셀 | 도메인 | 요약 |
|---|---|---|
| A1 | 캐싱/기초 | IVM+locality+semantic distance+learned index = 이론 기초 |
| A2 | 캐싱/시스템 | CDN<25ms, prompt caching 0.1x, vLLM<4%, Redis 73%절감 |
| A3 | 캐싱/함정 | invalidation·false-hit(0.91 경계)·stampede·coherence·Goodhart |
| A4 | 캐싱/최전선 | Agentic Plan Caching + Verified Semantic(31%) + TVCACHE |
| B1 | 가중/기초 | LFU+PageRank+Hebbian(=attention dual) |
| B2 | 가중/시스템 | Click Model→LTR(LambdaMART)+BPR, query clustering |
| B3 | 가중/함정 | Matthew-effect 자기강화, 6 실패모드, 단일완화책 없음 |
| B4 | 가중/최전선 | learned index(RL)+adaptive routing+RLHF 수렴 |
| C1 | 계층/기초 | HNSW+skip-list+ball-tree+small-world |
| C2 | 계층/시스템 | HNSW 95-99% recall @4-16ms, insert-order 민감 |
| C3 | 계층/함정 | 고차원·drift·동적업데이트서 recall loss/orphan |
| C4 | 계층/최전선 | GraphRAG+HippoRAG2+RAPTOR+DiskANN = engineboy 최근접 |
| D1 | 경계/기초 | ACL query-time enforcement, relevance≠authorization |
| D2 | 경계/시스템 | Glean/Copilot/Slack/Vertex 실시간 권한동기화 |
| D3 | 경계/함정 | inversion+collision+timing 3중 공격, multi-tenant 비호환 |
| D4 | 경계/최전선 | federated KG embedding + on-device(ExecuTorch) + DP/HE/TEE |
