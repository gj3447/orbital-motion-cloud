# engineboy 측정층 실행 플레이북 — LakatoTree progressive로 올리는 법

> **목표**: `LakatosTree_Engineboy_SemanticHypergraphNN_20260712` 를 notebook/PENDING → progressive(또는 정직하게 degenerating). 사전등록 예측 `q-ab-vs-baseline`(baseline 0.5, novel=precision_lift_over_vectorRAG, δ=0.05, credence 0.35)을 measured A/B로 채점.
> **cycle**: PROM16 `prom16-engineboy-measurement-howto` (wf_47086ba3-fe7, 16-cell, 라이브 airo KG 직접 실측).
> **정직**: bhgman A/B 선례=uplift 0. **partial이 정직한 baseline 기대치.** 예측이 틀릴 수 있게 두는 게 이 실험의 요점 — 사후 threshold 하향 금지.

---

## ★ Substrate 실태 (설계를 강제하는 3 사실, 라이브 실측)

airo KG = Neo4j **5.26.24 Community** (`bolt://10.147.17.7:55200`), 308,046 노드 / ~1.37M 엣지.

1. **GDS 미설치** — `gds.pageRank`/`graph.project` 없음. → PPR은 in-DB 불가, **python igraph/scipy로** (= HippoRAG/HippoRAG2 실제 구현 방식, 우회 아닌 canon-정합). GDS 설치(공용 jetson restart)·100.64.0.3 미러(engineboy 데이터 없음, dim768) 둘 다 기각.
2. **embedding 24% + 오염** — 74,386노드가 dims 혼합(1024 voyage-3 / 768 일부는 **가짜 placeholder-hash** / 4096 qwen3 / 3072 gemini), 모델명 KG 미기록. **engineboy 타깃(LakatosNode 888 / PrismExperiment 913 / LakatosTree 50)은 embedding 0.** → legacy 재사용 불가(cross-model cosine 무의미), **단일 신규 모델로 eval corpus 재임베딩**.
3. **VECTOR index 없음** (native 지원은 kernel 코어, GDS 불요) → 전용 라벨에 신규 생성.

→ substrate가 실험을 막진 않음. 단 값싼 지름길(legacy 재사용)은 다 막고 **정직하지만 비싼 경로**(신규 단일모델 embed + python PPR)를 강제.

---

## 8-Step 실행 (ordered, critical path)

### Step 1 — eval corpus 확정 + 단일 모델 고정 `@design`
- 대상 = engineboy 리트리벌 타깃 `:LakatosNode`(888)+`:PrismExperiment`(913)+`:LakatosTree`(50) ≈ **1,851** (전부 embedding 없음) + precision@k 유의미할 비교 corpus.
- 모델 = **BAAI/bge-m3 (1024d, 다국어)** 고정 (KG에 한국어 다수). voyage-3=유료 API라 dgx 재현 불가 → 금지. **legacy 'embedding' property 재사용 금지, 신규 property `eval_embedding`**.
- `MATCH (n:LakatosNode|:PrismExperiment) RETURN elementId(n), coalesce(n.name,'')+'\n'+coalesce(n.description,'')`

### Step 2 — 임베딩 계산 `@dgx` (NOT Mac, NOT 100.64.0.3)
```bash
# dgx GB10:
vllm serve BAAI/bge-m3 --task embed   # then POST /v1/embeddings (input=name+description)
# fallback (CPU, 느림):
python -c "from sentence_transformers import SentenceTransformer; \
  m=SentenceTransformer('BAAI/bge-m3'); v=m.encode(texts,batch_size=64,normalize_embeddings=True)"
```
→ 단일모델·정규화·dim=1024, frozen source text에서 재현가능.

### Step 3 — write-back + native VECTOR INDEX `@airo` (GDS-free)
```cypher
// 배치 write (외부 계산 벡터, batch 100-500):
UNWIND $rows AS r MATCH (n) WHERE elementId(n)=r.eid
CALL db.create.setNodeVectorProperty(n,'eval_embedding',r.vec) SET n:RetrievalNode;
// 인덱스 (GDS 불요, kernel 코어):
CREATE VECTOR INDEX engineboy_emb IF NOT EXISTS FOR (n:RetrievalNode) ON (n.eval_embedding)
OPTIONS { indexConfig: { `vector.dimensions`:1024, `vector.similarity_function`:'cosine' } };
SHOW VECTOR INDEXES;  // state=ONLINE & 100% populated 확인 후 쿼리
```

### Step 4 — System A = vector-kNN baseline (full-strength) `@airo`
```cypher
CALL db.index.vector.queryNodes('engineboy_emb', $k, $queryVec) YIELD node, score RETURN node, score;
```
쿼리벡터도 **동일 bge-m3**. baseline은 전체 `:RetrievalNode` 커버(**flat/crippled baseline 금지 = tier-ablation anti-pattern**). 사전등록 baseline=0.5 앵커.

### Step 5 — System B = PPR 확산 (python igraph) `@Python` (NOT GDS)
```
엣지 1회 export: MATCH (a)-[r]->(b) RETURN id(a),id(b),coalesce(r.weight,1.0)  → igraph 빌드(캐시)
per query: seeds = System A top-N, reset weights = dense cosine (+ HippoRAG node-specificity s_i=1/|P_i|)
           igraph.personalized_pagerank(reset_vertices=seeds, weights=..., implementation='prpack')
```
**tier-ON vs tier-OFF**로 "TIER 구조가 인과인가 vs 그냥 그래프인가" 격리.

### Step 6 — held-out gold freeze + 3-arm A/B `@Python`
- **gold 라벨을 리트리벌 *전에* 파일로 freeze** (self-grading 금지). PRIMARY = MuSiQue/2Wiki/HotpotQA dev subset(gold=is_supporting). SECONDARY = airo 2-3 hop path 샘플.
- lift = `engineboy_p@k − vectorRAG_p@k` (동일 held-out set).
- ⚠️ **eval 쿼리는 2+hop/provenance 축으로 사전선별** — single-hop이면 Tier0가 이미 이겨 lift→0 (rigged 아니게).

### Step 7 — 통계 null 게이트 `@Python`
```
observed_lift = mean(precision_B) − mean(precision_A)
paired permutation (sign-flip, B=10,000) → p ; paired bootstrap 95% CI
MI permutation null: MI(tier_membership; is_gold) shuffle B× → p_MI
PASS iff lift≥0.05 AND p<0.01 (Goodhart/수비학 방어)
```

### Step 8 — judge 배선 `@Mac lakatotree MCP` (NO re-register)
> `spec-root`는 이미 PREDICTED (baseline 0.5 / noise 0.02 / δ 0.05 / credence 0.35 / closes q-ab-vs-baseline). **register_prediction 재호출 금지(409).**
```
(a) record_derivation(output=fixture.jsonl, output_sha=..., inputs_csv='raw:sha', kind='source')  // 계보
(b) run_cycle(dry_run=true)  // 판정 미리보기 (hard prerequisite, optional 아님)
(c) submit_result(tag='spec-root', value=<measured p@k>, script=<eval script>, script_sha=...,
      novel_measured=<lift>, novel_script=<eval script 경로>, result_path=result.json)
```
→ judge가 script-계산 숫자로 progressive/partial/degenerating 자동판정. **모든 파일은 `/Users/lagyeongjun/CD/SYMPOSIUM/PI` (=LAKATOS_RAW_ROOT) 아래** freeze (live Neo4j는 sha 불가 → reproducible 게이트).

---

## Blockers (실행 시점 먼저 확인)

- **dgx/딜타워 vLLM reachability** — Mac 임베딩 불가. 최근 "vLLM unreachable" 기록 있음. 둘 다 죽으면 CPU sentence-transformers fallback(느리지만 됨). **실행 전 FIRST 확인.**
- **legacy 모델 미식별** → 값싼 재사용 경로 BLOCKED (신규 재임베딩 강제).
- **신뢰 held-out 라벨** — self-generated path gold=순환(Goodhart). 깨끗한 외부앵커(MuSiQue is_supporting)는 corpus ingest 필요. **진짜 cost center = GPU 아니라 이 라벨링.**
- **LAKATOS_RAW_ROOT** — live Neo4j sha 불가 → fixture+result+script를 PI/ 아래 freeze 필수(아니면 reproducible=None, floor 영수증 없음).
- **spec-root single-shot** — 잘못된 value submit → 409 재제출 불가, 새 child node 강제. **dry_run 미리보기 필수.**

## Cost

compute는 싸다. **v1은 234k 백필 불요 — engineboy 타깃 ~1,851 + 비교 corpus 몇 k만.** bge-m3 dgx encode = 초 단위, +fetch/write ~15-45분. index build 1-3분. edge export+igraph 초~수십초(캐시). PPR/query <1s. null(B=10k) 초. **측정 compute ≈ 1-2시간.** 진짜 병목 = **held-out 라벨 하네스 + PI/ 결정론 eval script + 벤치 ingest ≈ 1-2일.**

## Honest Risks (partial이 정직한 기대치)

bhgman A/B 선례 uplift=0. **credence 0.35에 사전등록된 대로 lift<0.05일 실질 확률 존재** → judge가 partial/equivalent, value≤0.52면 degenerating/rejected. **이건 공학 실패가 아니라 옳은 과학적 결과** — 예측이 틀릴 수 있게 두는 게 정직 A/B의 요점. degenerating 경로: (a) 저분산 임베딩(연구노드 문체 유사)→cosine 붕괴→kNN floor→lift≈0, (b) 76% 미임베딩 이웃을 PPR만 도달→capability_delta로 읽힐지 artifact일지 gold 위치 의존→held-out 공정 scope 필수, (c) single-hop 쿼리면 Tier0 이겨 lift→0→2+hop 사전선별. **지금 committing: partial 기대. 사후 threshold 하향 금지(immutable prereg). judge가 뭐라 하든 기록.**

# KG: LakatosTree_Engineboy_SemanticHypergraphNN_20260712, lesson-prom16-engineboy-measurement-howto-2026-07-12, engineboy-weighted-hypergraph-internet-kg-2026-07-12
