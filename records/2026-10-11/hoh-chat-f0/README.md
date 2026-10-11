# HOH 채팅 플라이휠 F0 구현 관측

2026-10-11 · SECONDARY_AI. [진행 요청 원문](user-request.txt)과 구현 해석·관측을 구분한다.

기존 `omc:chat-flywheel:work:F0`의 제한된 HOH 호스트 구현을 private HOH 커밋
`8f7af5acc52310fc9e9667f1d5391638a04eebac`에 반영하고 main 원격과 대조했다.
요청·대화/부모 관계·상태 관측·답변·실행 결과·확인/취소·사용자 평가를 영속 저장한다.
콘텐츠 효과와 완료 기록은 같은 상태 트랜잭션에서 확정하며, 재시작 후 미완료 요청은
UNKNOWN으로 복원한다. 동일 요청은 자동 재실행하지 않는다.

- [구현 설명의 고정 사본](implementation-note.md): API, 범위, 저장 한도와 복구 계약.
- [구현 그래프의 고정 사본](implementation-graph.json): 실제 owner 코드·테스트·근거·다음 선행관계. 경로는 HOH 저장소 기준이다.
- [검증 기록 사본](verification.json): 타입 검사·빌드·110개 테스트, 실행 당시 소스 해시.
- [진행 기록](progress.json): owner 커밋, 사본 해시와 원격 확인.

HOH 저장소의 `backend/engineering/chat-turn-f0/check.py`가 소스 해시와 질의 4개,
반례 3개를 검증한다. 29개 노드·26개 관계는 로컬 구현 근거이며 공유 KG 정전 변경이 아니다.
기존 OMC 계획 그래프는 원문에 결속된 설계 판본으로 보존했다.

F1 CHU admission, F2 HSWM 실행·학습, OMC 계산 배치와 실제 배포는 수행하지 않았다.
F0는 계정별 256개 turn의 제한 구현이며 브라우저 이력 UI·보관량 관리도 후속 작업이다.
