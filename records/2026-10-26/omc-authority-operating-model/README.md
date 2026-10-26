# OMC 헌법·기술 운영 기준과 DW/METAHUMO 권한 구분

2026-10-26 · 작성 Codex · 사용자 원문과 회사 원천을 OMC 작업 규칙에 연결하는 기록.
독자와 소비자는 다음 OMC 작업 에이전트, 헌법·운영 기준의 개정자다. 원문은 이 기록 한 곳에 보존하며 별도 메모나 공유 KG에 복제하지 않는다.

<a id="user-source"></a>
## 사용자 원문 — USER_PRIMARY

이 대화에서 아래 순서로 직접 받은 두 메시지다. 날짜는 수집일이며 정확한 발화 시각은 제공되지 않았다.

> 해당 내용 가져와줘봐봐 ㅇㅇ 그 omc 헌법과 기술적으로 어케 운영해야할지에 대해서 ㅇㅇ.

> 내가 회사 작업을 더많이하다보니까 이런듯 그 우리는 디멘션워커 권한이고 회사는 metahumo 권한이라는걸 잊지말아줘 ㅇㅇ;

두 번째 메시지는 앞선 요청에 더해진 권한 구분이다. 회사 작업에 더 많은 시간을 썼다는 설명도 사용자 본인의 설명으로 보존한다. 비교 관측으로 원인을 입증했다는 뜻은 아니다.

## 이번 적용 — SECONDARY_AI

- [OMC 운영 헌법](../../../docs/OMC_CONSTITUTION.md): DW/회사 METAHUMO 구분을 제1조에 배치. 목적·원천·의미 보존·실행·공존·참여·지속 운영·개정 기준.
- [기술 운영 기준](../../../docs/OMC_OPERATING_MODEL.md): 권한별 책임, 기존 실행기 재사용, memory.high와 예약 구분, 읽기 CLI, 장애 판독, 단계별 수용 기준.
- `AGENTS.md`와 README에서 다음 작업이 헌법과 운영 기준으로 들어가게 한다. 문서 연결은 상시 서비스 배포나 HSWM W 학습 완료가 아니다.
- 이전의 [삼단 구조 지시](../../2026-10-16/dimension-walker-metahumo-operator/README.md)는 순서의 근거로 유지한다. 이번 발화가 새로 밝힌 우리/회사 권한을 추가하고, 오퍼레이터의 세부 권한은 추론해 확정하지 않는다.
- 공유 KG `sym:Character:디멘션워커`는 UID 충돌 없이 조회됐지만 기존 창작 설명의 권위는 `UNSPECIFIED`였다. 그 설명으로 이번 직접 지시를 대체하지 않고, 이 작업에서 공유 KG를 쓰지 않는다.

<a id="company-sources"></a>
## 가져온 회사 근거 — SOURCE_DOCUMENT

원천은 AILAB_DASHBOARD와 METAHUMO_MANUFACTURE의 각 소유 문서·정책이다. 문서 안의 사용자 인용도 여기서는 회사 문서의 보고로 보존한다.
기록한 Git 판본의 blob과 당시 원격 작업 파일이 같은지 확인하고, 수신 bytes의 SHA-256도 대조했다.
개인 OMC의 운영 원칙으로 적용한 선택·역할 배분은 AI 해석이다. 회사의 위임·계정·수치·호스트 정책을 우리 환경의 전역 권한으로 가져오지 않는다.

원문 사본은 Git에 중복 커밋하지 않고 ignored `.local/company-omc-source-20261026/<SHA-256>`에 가져왔다. 아래 표가 작은 출처 lock이며 새 checkout에서는 사본이 없을 수 있다.
누락은 `NOT_HYDRATED`, hash 불일치는 원문 검증 실패다. 복원할 때는 원 소유 checkout에서 아래 commit의 해당 파일을 `git show COMMIT:PATH`로 읽고,
부분 발췌는 명시한 원문 줄 전체(줄바꿈 포함)를 취한 뒤 크기·hash를 대조한다. 최신 main으로 몰래 교체하지 않는다.
외부 저장소 접근과 회사 자료 재공개는 기존 소유 범위를 따른다.

| 원천 | Git 판본 | 선택 범위 | bytes | SHA-256 |
|---|---|---|---:|---|
| [AILAB_DASHBOARD/docs/REBALANCE.md](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/docs/REBALANCE.md) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 28225 | `d2f57f6b962c31042c487675831242706beaa68fee527579f55b6bc3af804795` |
| [AILAB_DASHBOARD/docs/RESOURCE_COORDINATION.md](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/docs/RESOURCE_COORDINATION.md) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 17443 | `1ca0adf5674d5533f3ffd1f0926bf4cac833c01d7f2637b7100b25dce99d87af` |
| [AILAB_DASHBOARD/docs/COMPUTE.md](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/docs/COMPUTE.md) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 21212 | `52e2008e7b4b08aa2e06c5f2f3a344e6f2bd0f457abbd60720a0cf2efdb47a04` |
| [AILAB_DASHBOARD/docs/LOCAL_CI_POLICY.md](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/docs/LOCAL_CI_POLICY.md) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 5160 | `3843894efc2f658db9e56210415040237d6d75dfab3fcdadfb421f57d234ad74` |
| [AILAB_DASHBOARD/graph/rebalance.json](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/graph/rebalance.json) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 5307 | `644d202f39300b87f6e0add04d584fff50525e14fe73ada48de9ca3e87020efa` |
| [AILAB_DASHBOARD/graph/compute.json](https://github.com/airobotics-ailab/AILAB_DASHBOARD/blob/d45e09d08b2f3613813746c6d2fde9498bb8f90a/graph/compute.json) | `d45e09d08b2f3613813746c6d2fde9498bb8f90a` | 전체 파일 | 3732 | `c5b09adef01ccc68a0d7819e7c25e9a7b8191469d481f5d14c3735877b1c331e` |
| [METAHUMO_MANUFACTURE/docs/MINI_APPS.md](https://github.com/airobotics-ailab/METAHUMO_MANUFACTURE/blob/5a39c8232d3fb74c75e2412d631f83bb7a6d0a08/docs/MINI_APPS.md) | `5a39c8232d3fb74c75e2412d631f83bb7a6d0a08` | L1056–L1084 | 5564 | `5c2eb16953059f20cbd7be28e0f6e2f1756ab23967f9b0b03edae622a07fb1c4` |

MM `MINI_APPS.md` 전체 blob의 SHA-256은 `d8436380a3b8925af2c6a083083fd9f2d6f86df3615e19058c5ecc265c0a1081`이다. 표의 MM hash는 입운구 절만의 bytes다.

## 확인된 공백과 적용 판단

2026-10-26 읽기 조회에서 회사의 리밸런서·수집기와 10개 노드의 최근 관측, 현재값·이력 API를 확인했다. 우리 ops는 제한 수명 종료 후 응답하지 않았고 별도 DGX 관측은 정상이었다.
회사 자동 배정은 꺼져 있고 등록 작업은 고정 2종이었다. 이는 당시 운영 연결의 관측이며 회사 전체 기술·철학의 우월성이나 영구 가동을 증명하지 않는다.
우리 fleet의 exit 3은 임계 경보, 회사 CI의 exit 1은 특정 commit의 기존 검사 실패 보고였으므로 `failed`라는 표시만으로 수집기·실행기 고장이라 결론내리지 않는다.

회사 문서에는 과거 DTD `max_jobs: 0` 설명과 후속 함대 실행 연결이 함께 남아 있다. 고정한 `graph/compute.json` 및 당시 CLI는 DTD `max_jobs: 1`과 CPU/CUDA 템플릿을 보여줬다.
원문을 수정하지 않고 시간·문서와 현 정책을 구분한다. 다음 실행은 실제 현 정책과 admission을 다시 읽어야 한다.

같은 호스트를 개인/회사 두 번 세거나 같은 cgroup에 개인 조정기를 추가하는 방식은 택하지 않았다. 회사 소유 runtime을 재사용하고 DW의 목적·원천·결과 연결을 보강하는 방향을 운영 기준으로 작성했다.
서비스 재시작·회사 코드 변경·새 작업 dispatch·정산·공유 KG 쓰기는 이번 문서 적용에 포함하지 않았다.

## 연구 배치와 다음 사용

기존 `infrastructure-orchestration` 주제의 ACTIVE WHAT_IS/HOW_TO 쌍을 조회했다. 저장소 검색의 `orbital_motion_cloud`와 `입체운행구름` 결과는 0건이었으나,
현재 OMC manifest와 명시적 사용자 대상이 구현 소유자를 확인해 준다. 이름 검색 누락을 레포 부재로 해석하지 않는다.
이번 질문은 기존 OMC와 회사 실행 기반을 어떻게 운영으로 연결할지이므로 HOW_TO로 누적한다. 같은 질문의 후속 설계여서 새 연구 주제·실행기·독립 소스 홈을 만들지 않는다.
사용자 권한 발화 자체를 AI 연구 결론으로 분류하지 않는다. 원문은 위 절, HOW_TO에는 AI의 적용 설계만 귀속한다.

후속 작업은 기술 운영 기준 7절의 DW 관측 지속성부터 현재 owner 조건을 확인하고 진행한다. 연구 등록·구조 검사와 서비스 운영 수용은 서로 다른 완료 기준이다.
