# 토큰당 지능 전제와 플라이휠 기록

`premise-verbatim.txt`는 직전 사용자의 전제 설명, `request-verbatim.txt`는 이번 구축 요청이다.
UTF-8 원문 뒤 최종 줄바꿈 하나를 붙였으며 `sources.json`의 해시는 파일 전체 바이트에 대한 값이다.
메시지의 정확한 발생 시각은 제공되지 않았으므로 비워 두고 수집일만 기록했다.

설계 소유자는 `gj3447/orbital-motion-cloud`다. 원문은 USER_PRIMARY, 문서와 그래프의
정식화·인과 연결·측정 방식은 SECONDARY_AI다. 성능 실험은 PLANNED이며 결과는 없다.

- [핵심 설명](../../../docs/FLYWHEEL.md)
- [그래프 그림](../../../docs/FLYWHEEL_GRAPH.md)
- [정본 그래프](../../../graph/flywheel.json) · [관계 계약](../../../graph/flywheel-contract.json)
- [이전 기여 목적](../resource-credit-shared-intelligence/README.md)

검사: `python3 scripts/flywheel.py check`, `python3 -m unittest discover -s tests -v`,
`python3 cli.py check`. 조회: `python3 scripts/flywheel.py query`.
출처 해시·UID·관계·기수·가설 권위·순환·다섯 질의를 검사하며 성능이나 경제 효과를 판정하지 않는다.
설계 전제가 바뀌면 새 발화를 별도 원문으로 남기고 그래프·계약·생성 그림을 함께 갱신한다.

기존 `infrastructure-orchestration` 주제의 HOW_TO 후속 기록으로 연결한다.
배치 근거: OMC는 명시된 연구 소유자이며, 이전 WHAT_IS의 기여 목적을 이어 받아
답변 효율 가설과 발전·실험 방향을 구체화한다. 코인 일반 연구나 별도 HSWM 구현으로 소유를 옮기지 않는다.
공유 KG 쓰기 및 모델·자원 실행은 이 기록에 포함되지 않는다.
