# HSWM content profile — proposed mapping

이 프로파일은 HOH 콘텐츠를 HSWM이 읽을 수 있는 출처·역할·상태·행동 근거로
연결하는 설계다. HSWM 실행·학습·원격 접근을 활성화하지 않는다.
현재 참조 구현 상태는 `NOT_CONNECTED`이며, HSWM 연결 실행은 `NOT_READY`다.

HSWM의 현행 원문은 LLM을 계산 자원으로 사용하는 지속적 하이퍼그래프 인지체라는
목표와, 실제로 검증된 구현·효능을 구분한다. 기존 KG의 고정 `H/W/A/F/Π` 설명은
최신 로컬 정전과 일치하지 않아 이번 계약의 고정 데이터 구조로 채택하지 않았다.
조회한 파일·리비전·바이트 해시와 권위 구분은 [조사 출처](research/semantic-content-references.json)에 있다.

| HOH 근거 | HSWM 호스트로 넘길 수 있는 참조 | 보존할 것 |
| --- | --- | --- |
| 콘텐츠 descriptor | 자원·schema-relative 의미 참조 | 안정 ID, descriptor revision, 원문 출처 |
| 관찰 상태 | 특정 시점·revision의 관찰 | 권한에 따라 정제된 값, 관측 시각, 증거 |
| 선언된 action | 실행 후보·도구 계약 참조 | 입력/출력 schema, effect, 허용 조건 |
| 실행 receipt | outcome의 원천 근거 | 요청·행위자·전후 상태·결과, 실행 여부 |
| 의미 관계 | 선택된 n항 관계의 projection | 관계 ID, predicate, 참여자별 role, 출처·상태 |

HOH는 임의의 유사도나 모델 확신을 HSWM의 W로 승격하지 않는다. 학습·가중치 갱신은
해당 HSWM 소유자의 정의, 실행·결과 계약과 평가 절차에 속한다. 단순 RDF 노드 집합을
HSWM 인지 객체 자체라고 부르지 않는다.

최소 호스트 확장 문서는 `profileId`, `resourceId`, `representationId`,
`schemaRevision`, `sourceRevision`, `sourceDigest`, `authorityClass`,
`observedAt`, `executionStatus`와 역할이 보존된 관계를 포함하도록 설계한다.
이는 아직 동작하는 HSWM 어댑터의 wire schema가 아니다. 실제 호스트의 정전·스키마와
대조한 뒤 버전을 고정해야 한다. USL 자원 ID와 표현을 재사용하고 절대 로컬 경로는
공개 descriptor에 넣지 않는다.

연결 실행 전에는 선택 자원의 USL 매핑, 지정 수신자, 소유자 승인, 최소 접근 범위·
만료·철회 수단, 승인된 경로의 읽기 전용 도달성 확인이 모두 필요하다.
이번 작업은 로컬 계약·구현·검증으로 한정되며 해당 연결 절차를 수행하지 않았다.

## 추천 연구 데이터의 로컬 구현 — 2026-10-09

[추천 연구 그래프](../research/recommendation-landscape/graph/graph.jsonld)는
기존에 보관한 9개 자료의 주장을 출처·한계·적용 제안·평가 계획으로 구별한다.
각 적용 관계는 근거, 제안, 평가의 참여자 역할과 순서, 적용 맥락과 예외를 보존한다.
[SHACL 계약](../research/recommendation-landscape/graph/shapes.ttl)과
[SPARQL 질문](../research/recommendation-landscape/graph/questions.json)이 그 의미를 검사한다.
외부 웹 원문의 바이트 스냅샷은 없으며, 로컬 검토·사용자 원문·주석의 해시와
웹 자료의 버전·읽은 범위를 구별한다. 기존 WHAT_IS/HOW_TO 원문은 변경하지 않는다.

[로컬 데이터 번들](../research/recommendation-landscape/graph/content-bundle.json)은
이 RDF 표현과 입력 해시를 HSWM의 기존 canonical content descriptor에 대응시킨다.
[검증 코드](../research/recommendation-landscape/graph/native-content.mjs)는 기존 공개
HSWM API의 메모리 계층에서 정확한 바이트 저장·읽기, 반복 저장, 반환값 변조 격리,
잘못된 해시·길이 거절 및 승인 없는 canonical admission 거절을 확인한다.
바이트 저장소는 media type을 해석하지 않으므로 전체 descriptor 비교도 별도로 한다.
이는 **유한 연구 데이터의 로컬 호환성 검사**이며 일반 CHU 인터프리터, 지속적 CHU 저장소,
실제 HSWM 인지 실행, 학습된 W 또는 콘텐츠 실행 어댑터의 완성을 뜻하지 않는다.
사용 스키마도 `UNJUDGED`인 독립 검사 스키마로, 운영 인스턴스가 승인한 스키마가 아니다.

새 검증 결과는 [동반 검증 기록](../research/recommendation-landscape/graph/validation.json)에
별도로 기록한다. 기존 문헌 검토의 검증 기록이나 THE_GREAT_FLOW 보관 완료 상태를
새 실험의 성공 근거로 재사용하지 않는다. 이번 추가는 이미 보관된 연구의 공학적 표현과
호환성 검사이며 새 추천 효능 연구 결과가 아니다.

재검증은 RDFLib/pySHACL이 설치된 Python으로 아래 명령을 실행한다.
`--render`는 고정 입력에서 그래프와 로컬 번들을 의도적으로 다시 만드는 경우에만 추가한다.

```sh
proxmox-scratch run hoh-recommendation-graph --timeout 180 --max-bytes 134217728 -- \
  python research/recommendation-landscape/graph/verify.py --hswm-root /path/to/HSWM
```

[연결 인계안](../research/recommendation-landscape/graph/handoff.json)에 최소 전달 필드와
제외할 정보, 첫 읽기 전용 연결의 목적, 아직 정해지지 않은 수신자·전송 경로·범위·만료·철회
정보를 모았다. 로컬 번들 전체를 이 전달 범위로 자동 간주하지 않는다. 실제 연결 후에도
선택 이전 기록, 독립적인 호스트 결과, 버전 있는 정책 갱신, 다음 선택의 변화와 롤백을
평가해야 한다. 현재 운영 연결 상태는 계속 `NOT_CONNECTED`다.
