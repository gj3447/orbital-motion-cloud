# 입운구 메모리 복구 계획 그래프

2026-11-10 · v2.1.0 · 작성·설계 귀속 SECONDARY_AI. [최초 요청](../records/2026-11-07/memory-plan/user-request.txt)과 [큰 작업 분해 요청](../records/2026-11-08/memory-plan-breakdown/user-request.txt)을 별도 출처로 보존한다.
독자는 사용자와 OMC/ORCA_SETTING/HOH 담당자다. 그래프를 읽는 실제 소비자는 `scripts/memory_plan.mjs`, 회귀 검사, OMC 전체 그래프 inventory다.

**7개 작업군 → 19개 담당 작업 → 57개 세부 단계 → 57개 산출물 계약으로 연결했다.** 각 단계는 담당·선행·입력·출력·검사·중단·재개 지점을 가진다. 구현·운영 작업은 아직 실행하지 않았다.

## 2026-11-10 브라우저 메모리 관리 인수인계

사용자 요청(`USER_PRIMARY`, HOH 작업 대화 발췌):

> 그 해당 내용 입운구에 밀어넣어줘봐 ㅇㅇ
> 일단 codex 는 그 거의다 아마 그 개발 사용중인거일꺼야

사용자는 메모리 최적화를 OMC에 반영하고, 현재 Chrome 창이 모두 필요한지 먼저 판단하도록 요청했다.
아래는 기존 W01·W02·W04·W05·W11에 연결하는 `SECONDARY_AI` 운영 보완안이다.
**문서·실제 JSON-LD/SHACL 계획에 반영했으며, 자동 정리 기능의 구현·배포·절감 효과는 미검증이다.**
기존 15개 작업의 UID·상태·의존성·출처 pin을 보존하고 S07에 W16–W19와 12개 단계를 추가했다.

### 현재 관측과 필요한 상주 범위

2026-11-10 08:58 UTC에 네 자동화 계정의 CDP 창 식별자와 탭 목록을 읽었다.
창은 계정별 한 개, 총 **4개**였으며 탭은 각각 **6·3·9·1개, 총 19개**였다.
같은 시각 소유 CLI의 전체 GUI 관측은 앞의 두 계정에서 `GENERATING`, 나머지에서 `IDLE`을 반환했다.
관측 직후 별도 runtime 조회에는 일부 계정의 `WAITING_USER`가 남아 있었다.
이 값들은 변하는 시점 관측이며, IDLE·활성 슬롯 0·오래된 탭만으로 완료나 정리 가능성을 확정하지 않는다.
과거 대화 목록과 열린 탭, 브라우저 창과 renderer/worker 프로세스 수도 구별한다.

네 계정을 유지하는 프로필 격리에는 이유가 있지만, 모든 과거 대화를 계속 열린 탭으로 둘 필요는 없다.
초기 운영안은 **사용 중인 계정별 대기 탭 0~1개와 진행 중 요청 탭**을 유지하고,
회수·승인·사용자 입력 대기, 수동 탭과 복구 대상은 별도 보호하는 것이다.
현재 소유 계약의 계정당 생성 1개는 생성 동시성 조건이지 탭 전체를 임의로 1개로 줄이라는 뜻이 아니다.
로그인 프로필을 디스크에 보존하는 것과 모든 계정 브라우저를 상시 실행하는 것도 별개다.
계정의 필요 시 기동은 기존 relay의 준비·배정·복구 계약을 검증한 뒤 검토한다.

### 대상별 정책과 실행 소유자

| 대상 | 판단과 처리 | 담당 경계 |
| --- | --- | --- |
| Codex 및 현재 개발 세션 | 이번 정리의 보호 대상. 나이·낮은 CPU 사용률로 종료·정지·메모리 한도 축소하지 않는다. | ORCA_SETTING의 기존 세션/작업 소유 경계 유지 |
| 완료된 자동화 탭 | 정확한 요청과 탭이 연결되고 결과 회수·전달이 끝났으며 초안·생성·승인·복구 대기가 없을 때 소유 API로 닫는다. | `chatgpt-api`의 `cleanupModel` → `finishOwned` 재사용 |
| 보관할 유휴 탭 | 저장된 상태로 복원 가능한 탭에 한해 Memory Saver/Discard를 검토한다. 단순 freeze는 메모리 반환과 같은 결과로 세지 않는다. | 브라우저 소유자가 복원 계약과 실제 Chromium 지원 확인 |
| 종료된 테스트 브라우저 | 작업 종료 receipt와 PID 생성 시각·cgroup 신원으로 자기 자원임을 확인한다. 테스트의 `finally`에서 자기 page/context와 전용 browser를 닫는다. | 테스트 실행기; 공유 계정 브라우저 전체 종료 금지 |
| 파일·커널 캐시 | 프로세스의 익명 메모리와 구분하고, 허용된 대상에서 제한된 회수 뒤 실제 효과·재읽기 비용을 확인한다. | OMC의 기존 단일 controller와 native owner |
| 필요한 활성 작업 | 회수할 탭이 없으면 새 작업의 동시성과 배치를 조절한다. 기존 메모리 보호량을 조용히 낮추지 않는다. | OMC 배치 판단 + ORCA_SETTING admission |

OMC는 관측·후보 선정·예산·효과 검증을 맡고, 탭 완료 판정과 실제 종료는 브라우저 소유자가 맡는다.
기존 `chatgpt-api/scripts/chatgpt_web_relay/src/{relay,browser,provider}.ts`에는 완료·결과 회수·초안 확인 뒤
자기 탭을 닫는 경로가 있다. 새 정리기를 만들기 전에 이 경로의 누락·실패·남은 요청 상태를 대조한다.
현재 설치 판본과 source의 동일성, 열린 19개 탭 각각의 정리 적격성은 아직 확인하지 않았다.
OMC가 PID 이름만 보고 Chrome을 죽이거나 계정의 pause/승인을 해제하지 않는다.

### 다음 구현과 수용 순서

1. **W01·W02 — 읽기 전용 분류.** 계정·탭·요청·실행 owner를 연결하고 진행/회수 대기/정리 가능/미확인을 나눈다.
   로그에는 대화 본문·초안 내용·인증값을 넣지 않는다. 미확인 대상은 보호한다.
2. **W02·W05 — 완료 자원 반환.** 기존 소유 잠금 안에서 요청과 현재 탭·초안을 다시 확인한 뒤 한 대상만 처리한다.
   새 요청·사용자 조작·대상 교체와 경쟁하면 보류한다. 응답 유실은 같은 요청으로 조회하고 중복 종료하지 않는다.
3. **W04·W05 — 캐시 회수 복구.** 현재 `STOPPED_GUARD`의 정확한 사건·후속 검사·누적 예산을 보존한다.
   일시적인 I/O 압박, 권한 만료, 무효과, 미확정 실행을 구분해 소유 복구 계약으로 판단한다. 상태 삭제나 서비스 재시작만으로 잠금을 풀지 않는다.
4. **W11 — 실제 효과 비교.** 최초 소유 탭 1개를 대상으로 정리 전후와 지연 관측을 비교한다.
   측정값은 브라우저 cgroup의 anon/file/current, 프로세스 PSS, PSI·refault·swap·OOM 변화, 새 요청/복원 성공,
   HOH 동일 검증 작업의 입장·완료 시간이다. 공유 메모리를 중복 합산하거나 요청 회수량을 절감량으로 기록하지 않는다.
5. 검증된 결과를 기존 controller와 요청 상태에 반영한다. **Codex 종료 0, 진행 중 요청 손실 0, 결과 회수 누락 0**이 수용 조건이다.
   성능 악화·불확실 결과가 있으면 확대하지 않고 해당 대상과 시도에서 멈춘다.

### 기술 근거와 적용 한계

- [Chromium 다중 프로세스 구조](https://www.chromium.org/developers/design-documents/multi-process-architecture/): 프로세스 수를 창·작업 수 또는 낭비량으로 해석하지 않는다.
- [Playwright Browser](https://playwright.dev/docs/api/class-browser#browser-new-context): 직접 만든 context를 명시적으로 닫고, 전용 browser 종료 전에 결과 파일을 마무리한다. 공유 기본 context의 소유와 수명은 별도다.
- [Chrome Memory Saver](https://support.google.com/chrome/answer/12929150?hl=en)와 [Page Lifecycle](https://developer.chrome.com/docs/web-platform/page-lifecycle-api): discard는 재로드를 수반한다. 입력 중 폼·재생·다운로드 등 보호 조건과 복원 가능성을 확인한다. Google Chrome의 안내를 설치된 자동화 Chromium의 동작 증거로 대신하지 않는다.
- [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), [PSI](https://docs.kernel.org/accounting/psi.html), [PSS](https://www.kernel.org/doc/html/latest/filesystems/proc.html): 익명 메모리·파일·커널 캐시와 공유분을 분리하고 회수 후 지연·재접근 비용을 함께 측정한다. `slab_reclaimable`은 즉시 전량 회수 가능하다는 보장이 아니다.
- [drop_caches](https://kernel.org/doc/html/latest/admin-guide/sysctl/vm.html#drop-caches)는 상시 최적화 루프로 쓰지 않는다. [DAMON_RECLAIM](https://docs.kernel.org/admin-guide/mm/damon/reclaim.html)은 기존 W14의 커널·소유 제어·비용 검증 뒤 조건부로 검토한다.

### 그래프에서 실행자가 읽는 브라우저 작업

| 작업 | 쓰기 소유자 | 선행 | 세 단계와 산출물 |
| --- | --- | --- | --- |
| W16 요청·탭 분류 | chatgpt-api | 없음 | 목록화 → 분류 계약 → 보호 반례. 본문 없는 신원·상태·보호 사유 |
| W17 완료 반환·보관 정책 | chatgpt-api | W16 | 기존 경로 대조 → 로컬 구현 → 경쟁·복원 검사. source/fixture 결과 |
| W18 OMC 연결 | OMC | W02·W17 | 중단·응답 계약 → 기존 controller 연결 → 부분 결과 검사. owner 반환과 예산/episode |
| W19 한 대상 운영 검증 | chatgpt-api, OMC/HOH 협업 | W17·W18 | 판본·복구점 확인 → 소유 전환·한 탭 처리 → 지연 비용·HOH 결과. 실제 실행 전 모두 미검증 |

`assignedTo`가 실제 파일 writer이며 `collaborator`는 협업 역할이다. W19-S02만 새 브라우저 작업의
`OWNER_SCOPED` 단계다. Codex 보호는 `COMPATIBILITY` 조건으로 두고 `IDENTITY`·실행 위임과 별도로 검사한다.
새 조건이 다른 필수 조건을 대신 충족하지 않도록 반례를 둔다. 작업 하나마다 입력·산출물·검사·중단·재개·rollback이 연결된다.

```sh
node scripts/memory_plan.mjs query browser-owners
node scripts/memory_plan.mjs query browser-protection
node scripts/memory_plan.mjs query browser-canary-prerequisites
node scripts/memory_plan.mjs query browser-source
node scripts/memory_plan.mjs query browser-live-steps
node scripts/memory_plan.mjs query browser-implemented
node scripts/memory_plan.mjs packet w19-s01
```

질의 결과는 정확한 owner/조건/원문 UID와 선행 W02·W16·W17·W18을 반환하고,
`browser-implemented`는 빈 목록이다. 문서의 현재 탭 수는 시점 관측이며 계획상의 정리 허가로 변환하지 않았다.
브라우저 소유 코드는 계속 개발 중이므로 `check.targetDrift`의 현재 차이를 숨기지 않는다.
실행자는 `packet.targetBaselines`와 실제 설치 판본을 다시 대조한다. 문서·구조 검증은 source drift를 해결하거나 실행을 승인하지 않는다.

## 정본과 표준 사용

- [정본 JSON-LD](../graph/memory-recovery-plan.jsonld): 431개 노드, RDF 변환 후 6,720개 triple. JSON-LD 1.1의 inline context를 쓴다.
- [SHACL Core와 어휘 계약](../graph/memory-recovery-plan.shacl.ttl): 타입·domain/range·기수·필수 필드·권위 경계를 검사한다. dependency DAG와 파일 바이트/owner 발행 pin은 별도 소유 CLI가 검사한다.
- PROV-O의 `wasDerivedFrom`, `wasAttributedTo`, `hadPrimarySource`로 AI 설계·사용자 원문·공개 자료를 구분한다. 구조 PASS가 실행·효과 PASS를 뜻하지 않는다.
- `Dependency`, `StepDependency`, `EvidenceUse`는 역할·이유·관계 상태를 보존하는 명시적 노드다. 편의용 `dependsOn`/`afterStep`/`evidence` 투영과 정확히 일치해야 한다. 작업과 세부 단계의 의존성만 각각 비순환이어야 하며 전체 의미 그래프를 DAG로 강제하지 않는다. 실패 재개 `resumeAt`의 자기 참조·순환은 허용한다.
- `omc:knowledge:resource:memory`와 인역강의 기존 `research:work:omc-memory-admission-20261107:WHAT_IS/HOW_TO`를 재사용한다. 이름이 비슷한 새 개체로 갈아끼우지 않는다.
- 기존 rebalance knowledge 계약은 작업 순서·수용·rollback 타입을 지원하지 않으므로, 그 계약의 의미를 바꾸지 않고 이 작업 전용 계획 모델을 추가했다. 원문·논문·기존 구현의 소유는 그대로다.

이것은 owner-local RDF/SHACL 모델이다. 공유 KG에 발행하거나 HSWM 실행·지속 store를 열지 않았다. OMC에서 이미 사용하는 RDFJS 의존성만 재사용하며 HSWM runtime 모듈을 호출하지 않는다.

## 실제 확보한 자료

기존 공개 자료 27개와 연구 원문 2개, read-only 감사 1개, 사용자 원문 2개를 보존했다. 브라우저 보완에는 Playwright 1.63.0 문서·Chrome lifecycle 문서 snapshot·이번 사용자 원문을 추가했다. 현재 공개 자료 29개(논문 6, 핵심 코드 7, 문서 10, 라이선스 6)와 로컬 원문 6개, 총 **35개 파일, 7,744,273 bytes**를 해시로 검증한다. 기존 논문 파일은 해시를 확인해 재사용했고, 원본은 `.local/rebalance-research/papers/`와 `.local/memory-plan/sources/`에 남는다. 대용량 원문을 Git에 복제하지 않는다.

논문은 TMO, Borg, Autopilot, DRF, Infiniswap, AIFM이다. 코드는 Senpai Python, oomd Senpai, damo, Kubernetes scheduler/kubelet eviction, Kueue scheduler, controller-runtime의 관련 파일이다. 이는 해당 저장소 전체 clone이나 빌드 완료를 뜻하지 않는다. 공개 commit, URL, 논문 연도/DOI, 읽은 절/함수, SHA-256과 바이트 수는 각각 SourceArtifact에 있다.

로컬 연구 원문은 허브 원장의 `COMPLETE`·역할·Git commit·source SHA까지 대조한다. 원문 출처 노드의 `PINNED_BYTES`, 연구 등록의 `COMPLETE`, 구현 작업의 `VERIFIED`는 서로 다른 상태다. `VERIFIED` 작업을 추가하려면 해당 work revision과 모든 수용 기준에 묶인 별도 실행 근거가 필요하다.

## 작업 순서

```mermaid
flowchart TD
  w01[W01 관측·입장 기준선] --> w03[W03 원자 RAM 예약]
  w01 --> w04[W04 회수 목표 계산]
  w02[W02 대상·중단 기준선] --> w04
  w02 --> w05[W05 복구 상태 전이]
  w04 --> w05
  w03 --> w06[W06 통합·적대적 재생]
  w05 --> w06
  w06 --> w07[W07 shadow 비교]
  w07 --> w08[W08 작은 canary]
  w08 --> w09[W09 ORCA native 전환]
  w09 --> w10[W10 OMC controller 전환]
  w10 --> w11[W11 HOH 작업 효과 비교]
  w11 --> w12[W12 판본별 peak 이력]
  w12 --> w13[W13 조건부 다른 worker 배치]
  w03 --> w13
  w11 --> w14[W14 조건부 DAMON 평가]
  w13 --> w15[W15 장기 원격 memory]
  w16[W16 브라우저 분류] --> w17[W17 소유 반환 구현]
  w02 --> w18[W18 OMC 연결]
  w17 --> w18
  w17 --> w19[W19 한 대상 운영 검증]
  w18 --> w19
```

| 작업 | 담당 | 선행 | 산출물·완료를 판단할 핵심 |
| --- | --- | --- | --- |
| W01 관측·입장 기준선 | ORCA_SETTING | 없음 | 원천 시각, scope, capacity, cache credit, 예약을 구분한 계약. stale/future 입력 거절 |
| W02 대상·중단 기준선 | OMC | 없음 | target 신원·만료·기존 intent·예산 보존. 관측만으로 재개하지 않음 |
| W03 원자 RAM 예약 | ORCA_SETTING | W01 | 동시 시작의 과다 예약 차단, 같은 attempt의 멱등 반환, 실제 charge와 이중 차감 방지 |
| W04 회수 목표 계산 | OMC | W01·W02 | cache credit 감소까지 반영한 회복 목표. 작은 잔여 부족·상한·PSI·보호량 반례 통과 |
| W05 복구 상태 전이 | OMC | W02·W04 | 일시 대기/권한 만료/효과 없음/실행 불확실을 구분하고 누적 예산 유지 |
| W06 통합·적대적 재생 | OMC, ORCA 협업 | W03·W05 | 구/신 producer-consumer·동시성·대상 종료·rollback 경계 확인 |
| W07 shadow 비교 | OMC | W06 | 같은 현재 입력의 기존/후보 판단 비교. kernel·lease·정책 쓰기 0 |
| W08 작은 canary | OMC | W07 | 정확히 허용된 대상과 유한 예산에서 native 결과·지연 refault·PSI 확인 |
| W09 native 예약 판본 전환 | ORCA_SETTING | W08 | 기존 작업·lease를 보존하며 새 실행이 의도한 owner 판본을 읽는지 확인 |
| W10 controller 판본 전환 | OMC | W09 | 한 actuator writer, 권한 만료와 서비스 수명의 분리, 상태·예산 연속성 |
| W11 HOH 작업 효과 비교 | HOH | W10 | 동일 소스·도구·workload의 입장 지연, 완료율, peak, PSI, P95, OOM 비교 |
| W12 peak 이력 | OMC | W11 | 판본·domain별 수요와 OOM으로 잘린 표본을 보존하는 보수적 다음 예산 |
| W13 다른 worker 배치 | OMC, 조건부 | W03·W12 | owner 예약·호환성·데이터 이동 비용을 충족하는 배치안 |
| W14 DAMON 평가 | OMC, 조건부 | W11 | 커널 capability·제어권·관측 overhead를 확인한 채택/보류 결정 |
| W15 원격 memory | OMC, 조건부 | W13 | RDMA/네트워크 또는 앱 API 변경과 장애 복구를 포함한 실험 가능성 |

원격 memory의 검토는 DAMON을 필수 선행으로 요구하지 않는다. v1.0.1의 15개 작업 UID·의존성·출처 pin을 보존하며 아래에 세부 단계를 붙였다. v2.0.0의 그래프를 포함하는 직전 commit `490c543`을 `previousGraphCommit`에 고정했다.

W01·W02와 W03·W04는 각각 서로 독립적인 선행 단위다. 이는 계획의 의존성 설명이며 agent를 자동 생성하거나 작업을 병렬 실행하는 명령이 아니다.

각 WorkItem은 입력·출력 계약, 담당 저장소, 실제 수정 대상의 기준 SHA, 근거 자료, 수용 기준과 반례, budget, rollback을 가진다. 운영 단계는 별도로 `AUTHORIZATION`, `IDENTITY`, `RESOURCE`, `EVIDENCE` gate를 요구하며 현재 모두 `UNVERIFIED`다. 조건부 단계의 kernel/worker/원격 memory 조건도 미확인으로 남긴다.

## 조회와 재현

OMC 루트에서 Node 24와 기존 RDFJS 도구 환경을 사용한다.

```sh
node scripts/memory_plan.mjs check
node scripts/memory_plan.mjs next
node scripts/memory_plan.mjs next-steps
node scripts/memory_plan.mjs sequence
node scripts/memory_plan.mjs roadmap
node scripts/memory_plan.mjs packet w03-s02
node scripts/memory_plan.mjs why w04
node scripts/memory_plan.mjs query rollout-prerequisites
node scripts/memory_plan.mjs query conditional
node scripts/memory_plan.mjs query papers
node scripts/memory_plan.mjs query implemented
node scripts/memory_plan.mjs sources
node --test tests/test_memory_plan.mjs
python3 -m unittest tests.test_graph_checks.SourceChecksTests
```

현재 `next`는 W01·W02·W16, `next-steps`는 W01-S01·W02-S01·W16-S01을 반환한다. 이는 선행 의존성이 없는 계획 단위라는 뜻이며 runtime 실행 허가가 아니다. `packet`은 선택 단계의 부모·출처·수용 기준·rollback·합쳐진 gate·입출력 계약을 함께 반환한다. `implemented`의 답은 빈 배열이다. gate 검증·실행 효과·새 상태 기록을 이 CLI가 대신 수행하지 않는다.

검사는 19개 competency question의 정확한 답과 source role을 비교한다. 기존 8개 질문(다음 작업, 회수 근거, ORCA 소유 작업, 배포 전 선행, 조건부 작업, rollback, 논문, 검증된 구현)에 작업군, 다음 세부 단계, 예약 구현 분해, 실제 효과를 요구하는 단계, 생산자→소비자 인수인계를 추가했다.

읽기 전용 query는 선언된 graph 구조·국소 SELECT만 사용한다. 원문 바이트와 owner 발행 pin의 현재 일치는 `check`/`sources`에서 확인한다. 현재 구현 파일이 baseline SHA와 달라지면 `targetDrift`에 표시한다. 이전 관측이 새 코드의 증거가 되지 않도록 실제 착수 때 owner가 다시 기준선을 잡아야 한다.

```sh
# 명시적인 이 명령만 공개 HTTPS를 사용해 누락 bytes를 복원한다.
node scripts/memory_plan.mjs hydrate
# 재생성 가능한 교환 파일은 .local에 둔다.
node scripts/memory_plan.mjs export --format turtle --out .local/memory-plan/plan.ttl
node scripts/memory_plan.mjs export --format nquads --out .local/memory-plan/plan.nq
node scripts/memory_plan.mjs export --format mermaid --out .local/memory-plan/plan.mmd
node scripts/memory_plan.mjs export --format work-view --out .local/memory-plan/breakdown-20261108/work.json
node scripts/memory_plan.mjs export --format step-view --out .local/memory-plan/breakdown-20261108/steps.json
node scripts/memory_plan.mjs export --format turtle --out .local/memory-plan/breakdown-20261108/plan.ttl
river-graph validate --input .local/memory-plan/breakdown-20261108/steps.json
river-graph render --input .local/memory-plan/breakdown-20261108/steps.json --format svg --layout dot --output .local/memory-plan/breakdown-20261108/steps-proposed.svg
river-graph shacl --input .local/memory-plan/breakdown-20261108/plan.ttl --shapes graph/memory-recovery-plan.shacl.ttl
```

`hydrate`는 이미 있는 변경된 파일을 덮어쓰거나 remote pin을 갱신하지 않는다. URL의 내용이 달라졌으면 실패하며 새 판본 검토가 필요하다. 없는 원문은 `NOT_HYDRATED`다. 문서의 공개 URL은 변할 수 있으므로 그 경우 보존된 bytes 또는 검토한 후속 판본이 필요하다.

RDF 도구는 기존 `../HSWM/src/hswm/effect-runtime/package.json`에서 제3자 라이브러리만 해석한다. 다른 설치는 `OMC_RDF_RUNTIME`에 해당 package.json을 지정한다. 확인한 버전은 n3 2.7.2, jsonld 9.0.0, rdf-validate-shacl 0.6.5, Comunica query-sparql-rdfjs 5.3.0이다. 기존 설치를 변경하지 않았고 native HSWM 실행·store·권한 경로를 사용하지 않았다.

## 검증과 남은 단계

v2.1.0의 **431개 노드/6,720개 triple**, 실제 RDF 왕복·SHACL Core, **35개 원문 해시**, **19개 SPARQL 질의**, **78개 검사**가 통과했다. 커밋할 정확한 검사기 판본도 별도로 실행했다. 브라우저 보호 제거·다른 owner 전환은 JS와 독립 RDF 변이/SHACL에서 거절했다. 최초 새 반례에서 보호 조건이 IDENTITY 검사를 대신 충족하는 분류 오류를 발견해 COMPATIBILITY로 분리했으며, 수정 후 78개가 통과했다.

v2.0.0의 65개 검사·별도 inventory/source 6개 및 `river-graph` pySHACL 통과는 이전 판본의 이력이다. 이번에는 그 별도 엔진 검사를 재실행하지 않았다. 공용 도구의 구조 PASS는 owner 의미 검증의 대체물이 아니다.

중복 ID, 끊긴 끝점, 잘못된 owner, 의존성 cycle, 누락 rollback/반례, 부모 선행 우회, 허구의 추가 선행, 미전달 산출물, 미래 출력 소비, read-only 아래 actuation 숨기기, 조건부 단계의 ready 승격, 미완료 자식을 둔 부모 완료, 권위 승격, byte 손상·누락·경로 탈출, 틀린 질의 답을 거절했다. 완료 evidence는 단계/부모 revision·검사 목록·출력 digest와 결속해야 한다.

이번 readback의 `targetDrift`에는 기존 credit·ops·feedback·ops-guide와 새 browser-relay 기준선, 총 5개 차이가 표시됐다. 원래 pin을 자동 갱신하지 않았으며, 실제 착수 때 현재 owner 변경분과 설치 판본을 다시 확인해야 한다. 계획 구조 검증과 실제 코드 판본의 실행 준비 상태를 구분한다.

이 결과는 계획 구조와 출처 연결의 검증이다. 메모리 복구·예약 구현, 운영 성능 개선, kernel reclaim, controller 재시작, 원격 작업 배정은 이번 구축에서 실행하지 않았다. 다음 소비자는 `next`와 `why`로 W01·W02·W16의 입력을 확인한 뒤 각 owner의 작업 범위에서 착수한다.

## 큰 작업의 인수인계 계약

| 작업군 | 범위 | 완료 관문 |
| --- | --- | --- |
| S01 관측과 대상 기준선 | W01–W02, 6단계 | 원천 freshness·domain·target expiry를 구분한 기준선 |
| S02 예약·회수·복구 핵심 | W03–W05, 9단계 | 원자 예약, 회수 오차, crash 후 예산 보존 검증 |
| S03 통합 검증과 제한 적용 | W06–W08, 9단계 | 교차 판본 replay → 무쓰기 shadow → 허용된 canary |
| S04 소유자별 전환과 HOH 효과 | W09–W11, 9단계 | ORCA → OMC 실제 판본 readback과 동일 HOH workload 비교 |
| S05 판본별 수요 예산 | W12, 3단계 | OOM 검열 표본·시간 분리 평가·희소 표본 fallback |
| S06 조건부 확장 연구 | W13–W15, 9단계 | 선택 분기별 worker·kernel·network 조건과 채택/보류 이유 |
| S07 브라우저 수명과 반환 | W16–W19, 12단계 | Codex 보호, 소유 cleanup, OMC 연결, 한 대상 canary와 지연 효과 |

작업군은 읽기 위한 묶음이며 새 순서 제약이 아니다. 각 부모의 첫 단계는 기존 `dependsOn`의 마지막 단계 출력을 받으며 내부 단계는 자기 부모 안에서 이어진다. 세부 단계의 쓰기 소유자와 대상 경로는 부모 범위를 넘지 못한다. `OutputContract`는 앞으로 만들 산출물의 필드·검사 규칙이며, 이미 확보한 `SourceArtifact`와 구분한다.

조건부 연구 3개는 선행 완료만으로 ready에 포함되지 않는다. W08/W09/W10/W14/W15/W19의 S02는 실제 owner 효과가 있는 단계이며 권한·신원·자원·검증 gate를 상속한다. 나머지 단계의 로컬 문서·코드·시험 출력은 운영 actuator 효과로 분류하지 않는다. 출력은 모두 EXPECTED, 완료 관문은 모두 NOT_EVALUATED다.

실행자는 `packet <단계>`를 읽고 fresh 관측·현재 owner 정책으로 시간/표본/RAM 예산을 구체화한다. 단계마다 정해진 입력 계약·산출물·검증 묶음까지만 진행하며, 실패 기록을 남긴 뒤 해당 `resumeAt`에서 입력을 다시 확인한다. 의존성상 함께 가능한 작업을 자동 agent 생성이나 고정 동시 슬롯 수로 바꾸지 않는다.

v2.0.0의 이전 15개 작업 시각화는 [.local의 전체 작업 SVG](../.local/memory-plan/breakdown-20261108/work-proposed.svg)와 [45단계 SVG](../.local/memory-plan/breakdown-20261108/steps-proposed.svg)로 생성했다. SVG 화살표는 정본과 같이 **후행 → 선행**을 가리킨다. 위 Mermaid는 진행 순서를 읽기 쉽게 반대로 그린 표시다. JSON view는 원래 노드·관계 UID·이유를 보존한 표시용 투영이며 정본이나 실행 입력이 아니다. 생성 그림은 Git에 보관하지 않는다.

## 기존 45개 세부 단계

| 단계 | 작업 | 예상 산출물 | 완료 조건 |
| --- | --- | --- | --- |
| W01-S01 | 원천 관측과 입장 경로 목록화 | 관측 경로 목록 | 각 판단 값의 원천·단위·시각·domain이 연결된다. |
| W01-S02 | 판본 있는 freshness·headroom 계약 | 입장 관측 계약 | raw 여유·credit·예약·유효 여유를 중복 계산 없이 구분한다. |
| W01-S03 | 시간·scope 경계 fixture 고정 | 관측 회귀 결과 | stale/future/다른 domain/누락 값이 명시적 거절로 귀결된다. |
| W02-S01 | 대상 신원·만료·intent 목록화 | 대상 신원 목록 | 실행 중·만료·사라진 대상을 읽기만 하여 구분한다. |
| W02-S02 | 중단 사유와 누적 예산 계약 | 복구 가능성 기준선 | 일시 대기·권한 만료·효과 없음·실행 불확실을 별도 사유로 둔다. |
| W02-S03 | 무쓰기 신원·만료 반례 재생 | 대상 검증 결과 | 만료·교체·불확실 사례를 차단하고 외부 상태 쓰기가 0이다. |
| W03-S01 | RAM 예약 lease와 이행 계약 | 예약 lease 계약 | 신규·기존 lease 호환과 예약/실제 charge 전환을 정의한다. |
| W03-S02 | 원자 reserve·release 구현 | 예약 구현 판본 | 같은 domain의 검사와 예약이 하나의 원자 경계에 들어간다. |
| W03-S03 | 경쟁·재시작·멱등 반환 검증 | 예약 검증 묶음 | 예약 총량 상한·중복 release·만료·재시작 보존이 모두 통과한다. |
| W04-S01 | credit를 반영한 회수 수학 고정 | 회수 목표 모델 | credit 구간과 high 경계를 포함한 회수 후 여유를 계산한다. |
| W04-S02 | 유한 회복 목표 planner 구현 | 회수 planner 판본 | 미소 부족분을 보존하면서 보호량·요청/회차/총량 상한을 지킨다. |
| W04-S03 | 부분 회수·EAGAIN·refault 경계 검증 | 회수 계산 검증 묶음 | 요청량과 관측 회수량을 구분하고 악화·무진전·불확실에 정지한다. |
| W05-S01 | 복구 episode 전이표 확정 | 복구 상태 전이 계약 | 복구 가능 대기와 terminal·uncertain 상태를 구분한다. |
| W05-S02 | episode·예산 지속 저장 구현 | 복구 상태 구현 판본 | 상태·시도 ID·누적 비용을 내구성 경계로 보존한다. |
| W05-S03 | crash·만료·중복 coordinator 검증 | 복구 연속성 결과 | 불확실 실행을 자동 retry하지 않고 single writer와 예산 단조성을 지킨다. |
| W06-S01 | producer-consumer 호환 행렬 고정 | 교차 판본 시험 행렬 | 구/신 native와 controller 조합별 허용·거절을 명시한다. |
| W06-S02 | 적대적 통합 trace 재생 | 통합 trace 결과 | 동시 예약·target 종료·stale·부분 회수·rollback trace를 통과한다. |
| W06-S03 | 판본별 호환 근거 묶음 확정 | 통합 인수인계 묶음 | 실제 통과와 미측정을 분리한 고정 digest 묶음을 만든다. |
| W07-S01 | shadow 입력·판정 기준 사전 등록 | shadow 비교 계획 | 같은 관측에서 기존/후보 판단을 비교할 수 있다. |
| W07-S02 | 유한 shadow 표본 관측 | shadow 관측 표본 | kernel·lease·정책 쓰기 없이 등록된 표본 범위만 수집한다. |
| W07-S03 | 판단 차이와 canary 가능성 평가 | shadow 채택 판단 | 차이의 원인과 미측정을 설명하고 후보/보류를 결정한다. |
| W08-S01 | canary 범위·예산·복구점 확인 | canary 실행 명세 | fresh identity·유효 위임·자원·복구 근거가 모두 같은 대상에 묶인다. |
| W08-S02 | 허용된 작은 canary 실행 | canary 원시 실행 기록 | 허용된 단일 범위와 누적 상한 안에서 실제 결과를 남긴다. |
| W08-S03 | 지연 refault·PSI·상태 readback | canary 효과 판단 | 즉시 여유와 지연 비용을 함께 보고 채택/되돌림을 결정한다. |
| W09-S01 | native 릴리스와 lease 보존 준비 | ORCA 전환 명세 | 동작 중 lease를 보존할 호환·백업·되돌림 절차가 고정된다. |
| W09-S02 | ORCA owner 절차로 native 전환 | ORCA 전환 기록 | owner 절차로 정확한 artifact를 반영하고 기존 세션을 보존한다. |
| W09-S03 | 새 실행 판본·lease readback | ORCA 전환 검증 | 새 작업의 실제 판본과 기존 예약 연속성이 확인된다. |
| W10-S01 | controller 단일 writer·checkpoint 준비 | OMC 전환 명세 | writer 중복 방지와 episode·예산 보존 경계가 확인된다. |
| W10-S02 | OMC owner 절차로 controller 전환 | OMC 전환 기록 | 정확한 controller 판본 하나가 기존 상태를 이어받는다. |
| W10-S03 | 판본·만료·예산 연속성 readback | OMC 전환 검증 | single writer·만료 준수·예산 단조성을 실제 상태로 확인한다. |
| W11-S01 | HOH 동일 workload 비교 설계 | HOH 비교 명세 | 같은 소스·기기 조건·작업 정의의 전후 비교가 가능하다. |
| W11-S02 | HOH browser·build 제한 비교 | HOH 측정 결과 | 작업별 입장 지연·완료·peak·PSI·P95·OOM을 유한 실행으로 기록한다. |
| W11-S03 | 메모리 효과·회귀 판정 | HOH 효과 보고 | 표본 크기·미측정·변동을 보존해 유지/되돌림을 결정한다. |
| W12-S01 | peak·검열 표본 계약 | 수요 표본 계약 | OOM·취소·입장 거절을 서로 다른 표본 상태로 보존한다. |
| W12-S02 | 판본별 보수적 수요 추정 | 예산 추정 구현 | 판본/domain을 분리하고 희소 표본에는 현재 owner fallback을 쓴다. |
| W12-S03 | 시간 분리·검열·이상 표본 평가 | 예산 추정 검증 | 미래 누출 없이 부족 추정과 과다 예약 tradeoff를 평가한다. |
| W13-S01 | 등록 worker·데이터 이동 조건 확인 | 배치 가능 조건 목록 | 등록 owner·호환성·데이터 이동권을 확인한다. |
| W13-S02 | 다자원·전송비용 배치안 작성 | 배치 후보 계약 | DRF 관점의 병목과 이동 비용을 명시한 후보를 만든다. |
| W13-S03 | 배치 shadow로 채택·보류 판단 | 배치 분기 판단 | 원격 실행 없이 후보 타당성과 남은 owner 조건을 결정한다. |
| W14-S01 | DAMON 커널·제어권 조건 확인 | DAMON 조건 목록 | 지원 기능과 기존 controller 충돌 여부를 읽어서 확인한다. |
| W14-S02 | 허용된 격리 DAMON 관측 평가 | DAMON 비용 관측 | 정확한 격리 범위에서 비용과 cleanup을 유한 측정한다. |
| W14-S03 | DAMON 채택·보류와 철거 판정 | DAMON 분기 판단 | 이득·비용·미지원 조건을 설명하고 보류 또는 다음 실험을 제안한다. |
| W15-S01 | 원격 memory 실패·API 가정 정의 | 원격 memory 가정 계약 | RDMA 방식과 앱 API 방식의 적용 조건을 구분한다. |
| W15-S02 | 허용된 격리 prototype 계측 | 원격 memory 실험 결과 | 유한한 격리 prototype에서 장애·비용·정리 결과를 기록한다. |
| W15-S03 | 장애 복구·성능·도입비 판정 | 원격 memory 분기 판단 | 성능과 통합/운영 비용을 근거로 후속 구현 또는 보류를 결정한다. |
