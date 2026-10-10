# OMC 하드웨어 적응형 데이터 배치 구현 기록

[사용자 원문](user-verbatim.txt)은 OMC 기능 중 하나를 직접 지정한다. [기능·구현 문서](../../../docs/HARDWARE_ADAPTIVE_PLACEMENT.md)와 [소유 그래프](../../../graph/placement.json)는 AI의 구현 해석이다.

원래 데이터·서비스 소유자가 진행하는 대용량 이전과 OMC의 제한된 CLI 인수를 구분한다. 기존 HSWM 추상 구조를 변경하거나 shared KG에 역할을 자동 게시하지 않는다.

- [실장치 인수와 테스트](acceptance.json): 449바이트 확정 원문을 실제 20TB와 4TB에 보존하고 선택한 USL locator를 갱신했다. 의미 digest는 전후 동일하며, 첫 작업 재조회에서 generation 1을 유지했다. 후속 실장치 검증 작업은 기존 두 복사본을 해시로 재확인하고 generation 2를 기록했다. 전체 로컬 테스트 40개를 관리형 실행기에서 통과했다.
- [기능 그래프 USL 검사](usl-check.json): 원래 OMC persona UID와 소유 범위의 기능·불변 조건·단계·검사 노드를 연결한다. 구조 검사와 실장치 인수를 별도로 기록한다.
- [사용자 역할 반영](role-update.json): OMC의 기능 중 하나로 모듈·허브 역할 선언을 갱신하고 직접 발화의 해시를 연결했다. 사도 자리·정체성·기존 관계는 유지한다.
- [소유 전송기 관측](owner-migration-observation.json): 별도 소유 작업이 12개 디렉터리, 28,495,249,001바이트를 검증·이전했다고 기록했다. 이 세션이 해당 대용량 복사를 실행했다는 뜻은 아니다.
- [소유 허브 연구 기록](research-receipt.json): 기존 `infrastructure-orchestration` 주제를 재사용한 HOW_TO 기록과 관리형 최종 갱신이 `COMPLETE`로 끝났다. MHC 안정화 연구의 중단된 갱신도 같은 배치에서 복구했다.

실제 경로·등록·상태·상세 전송 영수증은 무시되는 `.local/placement/`에 있다. 새 4TB OMC namespace에만 소유 계정과 기존 NFS 익명 매핑에 맞는 권한을 설정했다. 기존 공유 export·마운트·서비스·다른 데이터의 권한은 변경하지 않았다.

[완료·게시 기록](publication.json): OMC 테스트 40개, 허브 관련 테스트 25개와 생성물 검사를 통과했다. 이번 변경만 포함한 허브 커밋 `943b71a`를 기존 private origin의 main에서 확인했다. OMC 자체 구현은 로컬 Git에 저장했으며 public 원격 push는 수행하지 않았다.
