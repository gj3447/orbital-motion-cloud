# OMC 원문을 읽고 재현 후보를 다루는 법

## 하드웨어 상태에 적응하는 데이터 배치

[배치 CLI와 그래프](HARDWARE_ADAPTIVE_PLACEMENT.md)는 현재 디스크·메모리 관측을 기반으로 확정 파일을 20TB와 선택적 4TB 복사본에 배치한다. 자원 ID·HSWM 추상 구조·의미 연결을 유지한 위치 변경을 검증한다. 실행 상태와 원본 공간 회수는 구분한다.

## MHC 컴퓨팅 안정화 HOW_TO

사용자 요청에 따라 인류역사흐름의강물 허브에 **HOW_TO_mhc-compute-stability** 독립 Git 연구 저장소를 만들었다.
[연구 진입 문서](/mnt/development/METAHUMOTONIC_SHARED/research/mhc-compute-stability/HOW_TO_mhc-compute-stability/README.md)와
[연구 본문](/mnt/development/METAHUMOTONIC_SHARED/research/mhc-compute-stability/HOW_TO_mhc-compute-stability/docs/HOW_TO.md)에서 이어간다.

기준 연산 단위, 기여 검증, 보상·발행·예약 회계, 미래 공급 대비 이용 의무, 강물의 사건 기록과 정책 재생,
공급 부족 대응을 연구한다. 사용자가 명명한 비행기맨에게 코인으로 지식을 구하는 순환을 출발점으로 삼는다.
현재는 HOW_TO 연구 설계이며 실험 결과는 아직 없다. [생성과 연결 기록](../records/2026-10-10/mhc-compute-stability/README.md).

## 1. 원문 무결성부터 확인

1. `python3 cli.py check`로 모듈 identity 선언을 확인한다. 이 명령은 source archive나 외부 시스템을 실행하지 않는다.
2. `APOSTLE_CONTENT.json`의 `source_revision`, `sha256`, `bytes`를 읽고, 필요한 파일만 `git -C <SYMPOSIUM> show ceaf2ccf1db10f621570badf9a88a394ca5c45a6:<source_path>`로 비교한다. 동일 바이트 확인은 원문 보존 확인일 뿐 그 원문의 현재 진실·배포 상태 증명이 아니다.
3. 주장에는 이 저장소의 archive path와 줄 범위를 붙인다. AI의 요약·설계안은 새 파일로 분리하고 `SECONDARY_AI`로 표시한다.

## 2. 질문별 읽기 순서

| 질문 | 시작 문서 | 이어 읽을 문서 | 멈춰야 할 지점 |
|---|---|---|---|
| 333에 global blockchain이 필요한가 | `333/PROM_16_REPORT.md` | `333/SOURCES.md`, OM_MANI feasibility | issuance·transferability·validator 구성이 미결이면 결론을 실행 명령으로 바꾸지 않는다. |
| Piper/Borg/Kubernetes 비유는 무엇인가 | `KUBERNETES_BORG_ABSORPTION_2026-07-15.md` | `333/SOURCES.md` | OMD/Piper와 OMC/Borg 축을 합치지 않는다. |
| browser P2P의 실제 gap은 무엇인가 | `A_p2p_substrate.md`, `C_cold_start_sustainability.md` | 333 보고서의 open questions | TURN/NAT, relay 비용, durability는 미검증 항목으로 남긴다. |
| engineboy의 측정 계획은 무엇인가 | `engineboy/MEASUREMENT_PLAYBOOK_2026-07-12.md` | FSM·binding·traffic·report | preliminary metric 계획을 통과한 benchmark로 기록하지 않는다. |

## 3. 재현은 별도 실험으로

원문이 언급한 333·Kubernetes·외부 논문을 재현하려면 먼저 대상 revision, 운영체제, 네트워크, 명령, 입력, 출력, 실패 조건을 새 실험 기록에 적는다. 그 기록은 archived source 아래에 덮어쓰지 않는다. 특히 문서에 기록된 과거 테스트 수나 clone 위치를 현재 성공으로 재사용하지 않는다.

권장 최소 산출물은 (a) 실행 전 가설, (b) 정확한 revision과 checksum, (c) command/output, (d) 예상과 실제의 차이, (e) 실패·미실행 이유다. 결과가 나오기 전에는 `PROM_16`의 cargo-cult/gap-filler 표를 설계 참고로만 사용한다.

## 4. AI가 제안하는 다음 질문

- 333의 credit가 genesis pre-mint인지 runtime issuance인지, 그리고 transferable asset인지 local credit인지 어떤 사용자 결정이 있는가?
- browser peer에서 signed causal DAG와 tombstone GC frontier를 어떤 failure model로 측정할 것인가?
- Omega OCC의 충돌 감지와 BFT quorum certificate를 같은 실험에서 비교하려면 어떤 workload와 durability fault injection이 필요한가?
- OMD의 shared-source-of-truth 제약과 OMC의 compute substrate 제약은 어느 API/ownership boundary에서 만나야 하는가?
