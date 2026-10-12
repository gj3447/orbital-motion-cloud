# CHU / CHU_OS 개념 그래프 연결

2026-10-12 · SECONDARY_AI. [구축 요청](user-request.txt)과
[계속 진행 요청](user-continue.txt)은 USER_PRIMARY 원문으로 따로 보존한다.

정본은 CHU의 [개념·주장 그래프](../../../../CHU/philosophy/graph/README.md)다.
OMC는 [검증된 소유 판본과 바이트](verification.json)를 참조한다. 실제 질의 답은
[answers.json](answers.json)에 보존했다. 이는 소유 그래프의 검증 관측이며 새 공유 KG 정전이 아니다.

그래프에서 조회하는 내용은 다음과 같다.

- C01: 인지능력체 CHU와 컴퓨터 기반 운영체제 구현 CHU_OS의 구분.
- C02: 철학을 먼저 정리하고 별도 CHU_OS 저장소를 둔다는 사용자 지시.
- C03: 우주 자체도 월드모델 CHU라는 사용자 관점, 월드모델 문맥과 원문 출처.
- 소유자의 이관 기록: CHU는 개념·철학·원문·Lean 정본, CHU_OS는 새 OS 구현 정본.
  초기 별도 저장소 이관과 소비자 전환 미수행을 서로 다른 상태로 기록한다.

RDF 데이터·로컬 온톨로지·SHACL shape·SPARQL 질의가 실제 파일로 존재하며,
기존 저장소 그래프 목록과 `./chu`에 연결했다. CHU 루트에서 조회한다.

```bash
./chu concept query distinction
./chu concept query viewpoint
./chu concept query separation
./chu concept query sources
./chu check --only concept-claims --only repo-graph --json
```

원문·출처와 정규화된 AI 주장을 분리한다. 이관 상태는 CHU의 고정 판본
`806258fe9a7974cf9bb237d6578d2c61094eabe0`에 기록된 관측이며 현재 서비스를
매번 실시간 점검한 결과가 아니다. 이전 OMC의 “레포 분리안만 작성” 기록은 그때의 상태로
남긴다. 소유 저장소에 그 이후 기록된 초기 이관을 이번 그래프가 반영한다.

이번 구축은 **개념·관점·소유·진행 상태를 출처와 함께 다루는 그래프**까지다.
HOH의 CHU_OS 런타임 전환, HSWM 인지 상태 그래프 실행, 공유 KG 발행은 수행하지 않았다.
