# HOH 채팅 플라이휠 F1 — CHU 상태 표현과 참조 모델 연결

2026-10-11 · SECONDARY_AI. [계속 진행 요청 원문](user-request.txt)은 USER_PRIMARY로
별도 보존한다. 기존 `omc:chat-flywheel:work:F1`의 구현 관측이며 정전 변경이 아니다.

HOH의 실제 대화 저장소에 요청 당시 화면·콘텐츠·상태 문맥을 함께 저장하고,
인증된 `GET /api/program-feed/v1/chat/chu`로 CHU v0.1 호환 묶음을 읽도록 구현했다.
메시지 원문, 당시 문맥, 관측, 실제 결과, 사용자 평가, 대화/부모 관계를 보존한다.

고정 대화·turn 핸들과 변경되는 record/snapshot CID를 구분한다. 동일 바이트가
여러 역할에 나타나도 역할별 occurrence와 순서를 유지한다. CHU에 이미 등록된
`group`/`member`만 쓰며 HOH 역할을 새로운 native 관계로 몰래 등록하지 않는다.
문맥이 없는 옛 F0 기록은 계속 읽을 수 있지만, 과거 문맥을 만들어 내서 내보내지 않는다.

CHU 소유 저장소의 `scripts/chu_model.py`를 고정 커밋에서 직접 불러오는 검증을
추가했다. TypeScript가 실제 생성한 제한된 fixture를 `create → link`로 넣고,
바이트·역할·스냅숏 CID·이전 판본·요청 재실행 결과를 다시 조회한다.
틀린 역할/타입, 끊긴 endpoint, 요청 충돌 등의 거부와 상태 불변도 확인한다.

고정 소스 사본에서 91개 테스트·타입 검사·빌드가 통과했다. CHU 참조 모델의
반례 7개와 구현 근거 그래프의 질의 5개·반례 6개도 검증했다. 구현 근거 그래프는
31개 노드·40개 관계이며, 그 안의 코드 경로는 HOH 저장소 기준이다.

- [구현 설명](implementation-note.md): API, 역할·식별자 계약, 저장·복구 한계.
- [구현 근거 그래프](implementation-graph.json): 소스·테스트·관측·남은 경계의 형식 관계.
- [전체 검증 기록](verification.json): 타입 검사·테스트·빌드와 소스 바이트 해시.
- [CHU 실제 참조 모델 검증](native-verification.json): 두 판본 재조회와 반례 결과.
- [진행 기록](progress.json): HOH 소유 커밋, 사본 해시, 검증 범위.

완료 범위는 **호스트 표현·변환과 실제 CHU 참조 모델 호환성**이다. CHU 영구 커널과
운영 인증/admission 경계는 아직 미완성이므로 운영 연결 완료로 표시하지 않는다.
내보낸 묶음은 `NOT_SUBMITTED / NOT_READY`, 별도 로컬 검증은
`REFERENCE_MODEL_ACCEPTED`로 구별한다. HSWM 실행·학습·성능 향상·실서비스 배포는
수행하지 않았다. 후속 F2는 이 근거를 받는 선택/추론 계약부터 연결해야 한다.

원래 OMC 계획 그래프는 원문에 결속된 설계 판본으로 유지한다. 이 기록은 소유 코드와
검증 결과를 추가로 연결하며 공유 KG나 기존 정전의 권위를 승격하지 않는다.
