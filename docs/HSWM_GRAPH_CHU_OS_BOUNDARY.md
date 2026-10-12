# HOH 플라이휠의 구축 대상 정정 — HSWM 그래프와 CHU_OS

2026-10-11 작성 / 2026-10-12 명명 정정 · SECONDARY_AI · 현재 작업 안내.

**최신 구분:** CHU는 인지능력체 자체를 가리키는 개념, CHU_OS는 컴퓨터 기반 운영체제 구현이다.
이 문서의 이전 `CHU는 OS` 표기를 바로잡는다. 우주 자체도 월드모델 CHU라는 사용자 관점은
[최신 원문](../records/2026-10-12/chu-chu-os-separation/user-verbatim.txt)으로 보존한다.
[소유 저장소의 설명](../../CHU/canon/CHU_AND_CHU_OS.md)과
[저장소 분리안](../../CHU/docs/CHU_CHU_OS_REPOSITORY_SPLIT.md)을 참조한다.
아래 2026-10-11 원문·검증 기록은 당시의 기록이다.
[사용자 원문](../records/2026-10-11/hswm-graph-chu-os-correction/user-verbatim.txt)과
[근거·진행 범위 정정](../records/2026-10-11/hswm-graph-chu-os-correction/correction.json)을 분리한다.
이 문서는 기존 설계·실험 기록의 해석과 다음 작업 대상을 바로잡는다. 새 연구 결과나
HSWM 런타임 그래프의 구현 완료를 주장하지 않는다.

**표준 그래프 엔지니어링의 중심 대상은 HSWM의 지속적 의미·인지 그래프다. CHU_OS는 그 컴퓨터 기반 구현을 담당한다.**

| 구성 | 이번 작업에서의 책임 |
|---|---|
| HSWM | 원자·관계·Semantic Weight·역할·문맥·예외·프로그램·경험·판본으로 이루어진 지속적 AI 상태와 그 선택·전이·학습 |
| CHU | 인지능력체 자체를 부르는 상위 개념 |
| CHU_OS | 컴퓨터 기반 구현으로, 구조·프로그램의 저장·접근·실행·자원을 다루는 운영체제 역할 |
| OMC | HSWM 의미·연결성을 보존하면서 실제 하드웨어에 맞게 데이터·프로그램·작업을 배치하는 역할 |
| HOH | 사람·기기의 접점, 대화·콘텐츠 상호작용과 실행 결과·명시적 평가의 출처 |

역할 구분은 현재 구현 경계다. CHU_OS를 단순 파일 저장소로 축소하거나 OS의 인지 동작을
HSWM과 분리된 고정 엔진으로 못박지 않는다. 기존 사용자 원문에는 CHU_OS의 동작 방식이
HSWM으로 이루어지면 그 전체를 AI로 본다는 조건부 관점도 있다.

## 지난 작업의 정확한 범위

F0는 HOH 호스트의 대화·결과 저장이고, F1에서 구현한 `ChatChu.ts`와 `/chat/chu`는
**CHU_OS의 내용 주소·관계 표현에 맞추는 저장/교환 어댑터**다. 그 참조 모델의 통과는
해당 OS 표현의 호환성 근거로 유지한다.

F1의 31개 노드·40개 관계는 코드·테스트·관측을 연결한 **구현 근거 그래프**다.
HSWM의 실제 의미·인지 상태 그래프가 구축됐다는 근거로 계산하지 않는다.
91개 테스트에도 HSWM canonical atom 수용, HSWM용 SHACL·SPARQL 검증 또는 실제
선택·전이·학습 완료를 부여하지 않는다. 당시 결과·고정 사본·소스 해시는 그대로 보존한다.

## HSWM에서 재사용할 실제 계약

기존 HSWM의 `canonical-atom-v2-schema.ts`와 `canonical-atom-v2-rdf-projection.ts`를
기준으로 작업한다. 아래는 이미 있는 계약의 재사용 기준이며 새 wire schema 선언이 아니다.

- 원자 판본은 `schemaVersion`, `lineageId`, `atomUid`, `revisionId`를 구별한다.
  승인된 각 원자 판본의 `responsibilityOwner`는 해당 schema가 책임을 정한다.
- `references`의 `referenceType`, `role`, `target`과 참여 순서를 보존한다. 관계 원자와
  incidence 표현을 써서 동일 대상의 여러 역할, 문맥과 예외를 유지한다.
- 기존 RDF view의 `hasTypedReference`, `sourceAtom`, `targetAtom`, `referenceType`,
  `role`, `ordinal`을 재사용한다. 문장 직렬화 순서를 관계 참여 순서로 사용하지 않는다.
- 원문 payload·provenance·content descriptor와 schema/state revision을 결속한다.
  metadata view에서 원문 의미나 예외 내용까지 자동 복원된다고 가정하지 않는다.
- HSWM이 채택한 RDF 1.1·SHACL·SPARQL·PROV-O 경로를 사용한다. 실제 shape/query
  결과를 확인한 범위만 표준 그래프 검증 결과로 보고한다.
- RDF projection의 `writeBack: FORBIDDEN`을 지킨다. 조회용 그래프를 canonical 상태
  쓰기 경로로 바꾸지 않고, 상태 변경은 기존 HSWM 소유 schema·수용·revision 경로를 따른다.

Semantic Weight, 선택 점수, 평가 효용과 권한을 같은 숫자나 필드로 합치지 않는다.
LLM은 이 그래프의 필요한 국소 입력으로 전이를 수행하는 내부 연산자라는 방향을 유지한다.
폐기된 H/W/A/F/Π 고정 분해를 재도입하지 않는다.

## 다음 작업과 완료 기준 정정

기존 F2를 이어갈 때 **HOH 대화의 의미를 HSWM 원자·관계·역할에 대응시키는 그래프 구성과
검증을 먼저 한다.** CHU_OS용 번들 확장을 다음 중심 과제로 삼지 않는다.
HSWM schema/shape/query 설계와 제한된 자료 검증을 CHU 운영 커널 완성 뒤로 미루지 않는다.

완료 판정에는 다음의 서로 다른 근거가 필요하다.

1. 선택한 HOH 요청·문맥·결과·평가가 정확한 HSWM 원자 판본과 출처로 대응되는가.
2. 참여 역할·순서·문맥·예외·책임 owner·revision을 실제 HSWM 검사기와 표준 view에서
   재조회할 수 있는가. 누락·역할 교환·오래된 판본 등의 반례를 거절하는가.
3. 어떤 HSWM 그래프 판본과 read-set이 **실제** 국소 입력·선택·전이에 소비됐는가.
   요청 수락 당시의 HOH 관측과 나중에 모델이 소비한 입력을 구별하는가.
4. 결과와 독립 평가가 다음 의미·관계 revision 및 다음 선택에 연결되는가.
   학습 효용은 별도 대조 실험으로 판정하는가.

1–2는 HSWM 그래프 구축·검증, 3–4는 그 그래프의 동작·학습 연결이다. CHU_OS 저장·실행과
OMC 물리 배치는 이 의미·판본·역할 계약을 보존하도록 결합한다. 이번 정정은 문서와 작업
대상 정리까지이며 위 HSWM 구현·검증·실행을 수행한 것으로 표시하지 않는다.

기존 [설계 문서](HOH_CHAT_FLYWHEEL_PLAN.md)와 [F1 고정 기록](../records/2026-10-11/hoh-chat-f1/README.md)은
과거 판본으로 유지한다. 이후 재개 시 이 정정을 함께 읽는다. 최신 사용자 정정이 현재 작업
대상의 기준이며, 이를 공유 KG에 이미 게시·비준했다고 주장하지 않는다.
