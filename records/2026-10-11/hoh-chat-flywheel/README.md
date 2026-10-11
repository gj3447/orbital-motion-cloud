# HOH 채팅 플라이휠 설계 기록

2026-10-11. `user-direction.txt`와 `user-request.txt`는 대화 원문에 마지막 LF를 붙인 UTF-8다. 정확한 발화 시각은 주어지지 않았고 기록일과 구분한다. 원문의 “좀비”는 그대로 보존했다. 참여 한도·중단·자동 작업이라는 운영 해석은 별도 AI 설계다.

- [HOW_TO 계획](../../../docs/HOH_CHAT_FLYWHEEL_PLAN.md): 첫 대화 순환, 경험·개선, 장기 자원·경제, 계약과 8개 구현 단계.
- [WHAT_IS 조사](../../../docs/HOH_CHAT_FLYWHEEL_SOURCE_REVIEW.md): 선택한 코드·문서의 정적 분석. 실제 서비스 상태 probe가 아니다.
- [그래프](../../../graph/hoh-chat-flywheel.json)와 [관계 계약](../../../graph/hoh-chat-flywheel-contract.json): 기존 UID, 방향·기수·역할·근거·계획 상태·질의.
- `sources.json`, `sources/`: 선택한 로컬 원본 12개를 Git commit 바이트와 대조한 사본 및 사용자 원문 2개. 혼합 정전 문서의 AI 재서술을 사용자 직접 발화로 바꾸지 않는다.
- `validation.json`: 68개 노드·105개 관계, 출처 파일 16개, 정확한 답을 검증하는 CQ 7개, 허용 순환 3개, 거절한 반례 12개. 수치는 구조 검사 범위이며 품질 점수가 아니다.

재검사: 저장소 루트에서 `python3 records/2026-10-11/hoh-chat-flywheel/validate.py`.
원래 플라이휠은 `python3 scripts/flywheel.py check`로 별도 검사한다.

이번에는 실행 가능한 인지 런타임, 실제 모델 실험, CHU admission, HSWM 학습, 기기 참여나 경제 정산을 수행하지 않았다. 다음 구현은 계획 F0의 HOH durable turn/outcome 경계다. 연구 보관 완료와 F0–F7의 구현 완료를 구분한다.

연구 보관 완료: [workflow 영수증](research-workflow.json)에 기존 infrastructure-orchestration WHAT_IS/HOW_TO 모듈의 커밋과 원문 바이트 검증을 기록했다. [연구 허브 반영 영수증](publication.json)에 렌더링·무결성 검사 및 private owner main의 원격 커밋 확인을 기록했다. 설계 커밋은 `8f3f4df2156db5763d4931f331c6c2f52c4a57af`, 연구 허브 반영은 `a6530adbe5df499db5186c8061e7053fbbdbeff6`다.
