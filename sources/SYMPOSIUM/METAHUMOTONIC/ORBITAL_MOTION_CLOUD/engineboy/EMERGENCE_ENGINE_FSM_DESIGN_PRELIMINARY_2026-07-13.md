# engineboy 창발 엔진 — FSM 설계 (PRELIMINARY, 2026-07-13)

> traffic → weight **창발기**. PROM 16 B축(traffic-가중) + C축(계층)의 실행체.
> 씨앗: 사용자 "창발 엔진 설계부터, fsm 부터 제대로" (2026-07-13).
> status: PRELIMINARY / VerdictPending. source=claude(설계) ← user direction.
> KG: `engineboy-emergence-engine-fsm-design-2026-07-13`, 상위 `engineboy-caching-traffic-weighted-hierarchy-2026-07-13`.

---

## 0. 핵심 결정: FSM은 1개가 아니라 직교 3개

가중치·계층은 element(node/hyperedge) 하나의 여러 독립 측면이다. 이걸 한 flat FSM에 욱여넣으면 6×3×2=36 상태 폭발. 대신 **직교하는 3 sub-FSM의 곱**으로 모델링 — engineboy 자신의 3직교축(롱기누스 code↔KG / 오캄 현재↔과거 / 유레카 구체↔추상)과 동형.

| sub-FSM | 축 | 무엇이 창발 | 무기 |
|---|---|---|---|
| **① Activity FSM** | 활동/가중 (시간축) | 계층(hierarchy) | 오캄(archival)·하데스(materialize) |
| **② Validity FSM** | 신선도 (correctness) | — (정합성 보존) | 나생문(stale 감지) |
| **③ Visibility FSM** | 상계/하계 (ACL) | — (경계 보존) | 롱기누스(bind)·SpaceGirl(lock) |

**창발이 사는 곳 = ①**: 엣지(Hebbian 공동접근)와 계층(가중치 순위 승격)이 *설계되지 않고 Σtraffic에서 arise*. 이게 창발.

---

## 1. Element 상태 (persistent)

```
Element e ∈ {SemanticNode, Hyperedge}:
  w        : float      # traffic 가중치 (Hawkes intensity)
  t_last   : timestamp  # 마지막 갱신 시각 (lazy decay용)
  n        : int        # support = distinct-access 수 (cold-start 판정)
  s_act    : {NASCENT, WARM, HOT, COOLING, COLD, DORMANT}
  s_val    : {FRESH, STALE, REVALIDATING}
  s_vis    : {PRIVATE, PUBLISHED}
  tier     : s_act에서 derive (HOT→L1 / WARM→L2 / COLD→L3·disk / DORMANT→archive)
  embed    : vector(768)  # HNSW 좌표 (RESOLVE용)
```

---

## 2. 가중치 동역학 (Activity FSM을 *구동*하는 수식)

**Hawkes / 지수감쇠 커널** — "traffic→weight"를 frequency·recency·burst를 한 식으로:

```
access(e) at time t:
    w ← w · exp(−λ·(t − t_last)) + κ_actor      # lazy decay + impulse
    t_last ← t ;  n ← n + 1 (distinct actor/session만)
```

- **O(1)·history-free**: 접근 시점에만 감쇠 계산 → 주기적 tick 불필요 = "materialize, don't recompute"(A1)의 실체.
- **평형**: 접근율 r 정상 → w* ≈ κ·r/λ. 즉 **weight ∝ 접근율**. 인기↑, 끊기면 지수감쇠 → B3 stale-immortality 자동 방어.
- **Hebbian 엣지**: 한 쿼리/세션서 e_a, e_b 공동접근 → Δw_ab = 같은 impulse. 엣지가 traffic에서 *창발*.
- **κ_actor**: human vs AI 접근 가중치 (design knob, 기본 동일 시작 후 측정).

## 2-1. 승격 점수 = 창발의 constraint layer (anti-Matthew, UCB)

순수 w로 승격하면 rich-get-richer(B3). 승격은 w가 아니라 **UCB 점수**로:

```
score(e) = w(e) + c · sqrt( ln(Σ_j n_j) / n(e) )
```

- cold-start(n 작음) → bonus 큼 → 억제 탈출.
- 과인기(n 큼) → bonus ≈ 0 → 순수 w.
- **B3 완화가 bolt-on이 아니라 transition guard에 내장.** bandit 이론 grounded.

---

## 3. ① Activity FSM (창발 코어)

```
        access(unknown)
             │ 유레카: CREATE node / Hebbian edge 후보
             ▼
        ┌─────────┐  n≥n_est ∧ w≥θ_warm   ┌──────┐  score≥θ_hot ∧ L1여유  ┌─────┐
        │ NASCENT │──────────────────────▶│ WARM │──────────────────────▶│ HOT │
        └─────────┘  HNSW insert(L2)      └──────┘  롱기누스 bind, L1     └─────┘
             │                              ▲  │                          │ │
   age>T_grace ∧ n<n_est                    │  │ w<θ_warm−h               │ │ w<θ_hot−h (hysteresis)
             │ (cold-start 실패)            │  ▼                          │ ▼
             │                        w≥θ_warm  ┌──────┐  w≥θ_hot(re-burst) ┌─────────┐
             │        재접근 burst  ┌──────────│ COLD │◀──────────────────│ COOLING │
             │                      │          └──────┘  w<θ_cool·T_cool   └─────────┘
             ▼                      ▼             │
        ┌─────────┐   access    ┌──────┐  w<ε·T_dormant
        │ DORMANT │◀────────────┤ ...  │─────────────────▶ 오캄 archive (active/log 분리)
        └─────────┘   revive    └──────┘
```

**전이표 (guard):**

| From | Guard | To | Action(무기) |
|---|---|---|---|
| ∅ | access(unknown), no HNSW match<τ_sim | NASCENT | **유레카** CREATE + embed |
| NASCENT | n≥n_est ∧ w≥θ_warm | WARM | HNSW L2 insert |
| NASCENT | age>T_grace ∧ n<n_est | DORMANT | **오캄** soft-archive (revivable) |
| WARM | score≥θ_hot ∧ L1 top-K 여유 | HOT | L1 승격 + **롱기누스** bind |
| WARM | w<θ_warm−h | COLD | demote |
| HOT | w<θ_hot−h | COOLING | demotion 후보 mark |
| COOLING | w≥θ_hot | HOT | re-promote (hysteresis=flap 방지) |
| COOLING | w<θ_cool 지속 T_cool | COLD | L3/disk demote |
| COLD | 재접근 burst w≥θ_warm | WARM | **재-창발** |
| COLD | w<ε 지속 T_dormant | DORMANT | **오캄** archive (삭제 금지) |
| DORMANT | access | NASCENT/WARM | revive |

**불변식**: hard-delete terminal 없음. DORMANT=archived-but-revivable = Eilu va-Eilu / 오캄 삭제금지 계율. hysteresis(h)로 HOT⇄COLD flapping(=stampede·thrash) 차단.

---

## 4. ② Validity FSM (직교, 신선도 — A3 coherence)

```
FRESH ──source_changed──▶ STALE ──revalidate_start──▶ REVALIDATING ──revalidated──▶ FRESH
```

- serving 정책: HOT∧FRESH → fast path. HOT∧STALE → **SWR**(serve-stale-while-revalidate) 또는 block (policy knob). REVALIDATING → last-good 서빙.
- Activity와 독립 전이 → 상태폭발 없음. HOT이어도 STALE 가능.

## 5. ③ Visibility FSM (직교, ACL — D3 공격 차단)

```
PRIVATE ──publish_request + ACL_gate(pass)──▶ PUBLISHED
```

- **불변식(load-bearing)**: shared/공유 캐시 tier 배정은 `s_vis=PUBLISHED` 필수. PRIVATE는 per-actor/per-tenant 파티션에만, 공유 HNSW 진입 금지.
- 이 한 줄이 D3 3중 공격(embedding inversion / semantic collision / timing)을 **FSM 레벨에서 구조적으로 차단** — private 임베딩이 애초에 공유 캐시에 없음.

---

## 6. 이벤트 파이프라인 (3 FSM을 구동하는 transducer)

```
INGEST   event_id dedup(멱등, A3) + ts + actor{human|ai} + ACL ctx
  ▼
RESOLVE  HNSW nearest(embed): match<τ_sim → 기존 / else 유레카 CREATE(NASCENT)
         + 공동접근 집합 식별(Hebbian 후보)
  ▼
WEIGHT   lazy-decay+impulse(Hawkes) on node; Hebbian on co-access edges
  ▼
SCORE    UCB 승격 점수
  ▼
GUARD    ① Activity 전이 평가 → emit. tier 변경은 ③ Visibility로 gate
  ▼
COMMIT   증분 materialize(IVM, A1) → KG/cache. element당 원자적(CAS/lock)
```

- 동시성: element당 single-writer(lock) 또는 actor-partition. Hawkes impulse는 가법 → 병합 가능.
- **하데스**=COMMIT(추상 weight→구체 캐시/KG materialize). **나생문**=주기적 constraint audit(Matthew/stale/false-hit).

---

## 7. 커맨더 매핑 (장식 아님 — 각 action이 한 커맨더의 동사)

| FSM action | 커맨더 | 동사 |
|---|---|---|
| RESOLVE-CREATE (신규 노드/이름) | 유레카 | 발견·창조 (bottom-up) |
| Hebbian 엣지 + KG bind | 롱기누스 | 연결 |
| DORMANT archive (active/log 분리) | 오캄 | 정리 (삭제 X) |
| COMMIT materialize | 하데스 | 실현 (추상→구체) |
| constraint audit (Matthew/stale) | 나생문 | 검증 |
| PUBLISH gate / private lock | 롱기누스 / SpaceGirl | bind / 잠금 |

---

## 8. Falsifier (효능 주장 前 통과 필수 — 7커맨더 효능 게이트)

> 효능 측정선(project_efficacy_measurement_line): 설계는 UNMEASURABLE 기본. "작동한다" 주장 전 3-falsifier 통과.

- **F1 멱등**: 같은 이벤트 스트림 2회 재생 → 최종 weight 동일 (dedup 실측).
- **F2 감쇠 정확**: 정상율 r → w → κr/λ 수렴 (해석해 대조).
- **F3 anti-Matthew**: 합성 rich-get-richer 스트림서 UCB 승격이 순수-w가 억제할 cold-start ≥X% 승격. 실패 시 constraint layer=theater.
- **F4 ACL**: 적대적 publish 시도에도 PRIVATE element이 공유 tier에 절대 미출현.

---

## 9. 열린 결정 (VerdictPending)

- **OD-1 가중 formalism**: Hawkes 지수감쇠(권장, O(1)·평형해석) vs LFU-counter vs sliding-window.
- **OD-2 substrate**: bhgman_tool legion 신규 엔진(`legion run emergence`, Neo4j gds+vector 위, 권장) vs standalone.
- **OD-3 scope phase1**: ① Activity FSM만 먼저(권장) vs ①②③ 동시. (②③는 설계는 지금 완결, 구현은 phase2.)
- **OD-4 κ_actor**: human=AI 동일 시작(권장) vs 비대칭.
- **OD-5 embedding**: engineboy 실행갭 = embedding populate. RESOLVE가 embedding 전제 → populate가 phase0 선행조건.
