# WHAT_IS — HOH 채팅·OMC·HSWM 연결의 현재 근거

2026-10-11 · SECONDARY_AI / STATIC_SOURCE_REVIEW. [출처 핀](../records/2026-10-11/hoh-chat-flywheel/sources.json)의 Git commit과 로컬 바이트를 대조했다. 라이브 서비스·모델·자원·사용자 효과를 재측정한 기록은 아니다.

| 관측한 범위 | 근거 파일 | 확인한 구조 | 남은 연결 |
|---|---|---|---|
| HOH 채팅 host | `HOH/backend/ts/src/programFeed/Chat.ts` | 접근 가능한 view를 읽고 exact command와 planner를 분기. 상태 재검사·제안 확인·취소. answer는 execution NONE | persistent cognitive turn, CHU 상태 판본·선택 trace·outcome·다음 학습의 경계 |
| 현재 모델 port | `HOH/backend/ts/src/programFeed/Planner.ts` | message와 현재 OpenView를 받는 plan. HTTP 모델·도구 계약, 제한 시간·출력, 설정·준비 상태 분리 | 대화/인지 상태, 다중 관계 문맥, 예산/실행 trace/결과를 잇는 계약 |
| HOH 표현 부품 | `HOH/backend/ts/src/programFeed/Substrate.ts` | 정확한 바이트의 content ID, 순서 있는 group/member, 정렬된 state identity | native CHU admission과 인지 실행은 별도 |
| HOH→HSWM 설계 | `HOH/docs/HSWM_CONTENT_PROFILE.md` | 콘텐츠·상태·동작·receipt·n항 역할을 대응시키는 제안; 로컬 번들 호환성 기록 | 문서 상태는 NOT_CONNECTED/NOT_READY; HOH 실제 인지·W 학습 완료의 증거 없음 |
| HSWM 선택→학습 | `HSWM/docs/operations/HSWM_CORE_SELECTION_LEARNING_BRIDGE_2026-10-10.md` | 기존 부품과 B1–B7 연결 결손, L1 정책과 L2 관계 의미 수정 구분 | 선택 기록→독립 outcome→owner 적용→다음 선택의 통합 adapter |
| OMC 플라이휠 | `OMC/docs/FLYWHEEL.md`, `graph/flywheel.json` | 동일 모델·총토큰 A/B/C, 경험/자원/경제의 조건부 순환과 미검증 가설 | HOH 채팅의 구체적 producer/consumer·실행 단위와 단계별 인계 |
| OMC 물리 실현 | `OMC/docs/HARDWARE_SOFTWARE_FIT_PLAN.md` | 의미·연결 유지와 variant·설정·데이터 위치의 적응 | 범용 채팅 계산 실행 adapter; 기존 데이터 이동만으로 대체 불가 |

각 파일의 선언·코드 경로를 확인한 범위다. `NOT_CONNECTED`라는 설계 문구를 모든 호스트의 현재 연결 상태에 대한 probe 결과로 해석하지 않는다. 저장소에 native 실행기가 존재하는 것과 HOH에서 그것을 실제 호출·학습하는 것은 다르다.

HSWM의 사용자 원문은 지속적 living harness·world model·token 연산·continuous learning을 목표로 한다. CHU 존재/HSWM 구조 문서는 사용자 직접 발화와 AI 역할 해석을 분리한다. 혼합 문서의 제목이나 AI 요약 전체를 USER_PRIMARY로 표시하지 않았다. 원자별 schema-relative 책임 owner 원칙을 보존하며 폐기된 고정 H/W/A/F/Π를 새 설계에 쓰지 않는다.

이번 새 사용자 발화는 장기 기기 참여와 지금의 플라이휠 우선순위, HOH 채팅 자체의 OMC·CHU·HSWM 기반을 요구한다. [후속 HOW_TO](HOH_CHAT_FLYWHEEL_PLAN.md)는 이를 구현 경계·평가·선행 순서로 풀어 쓴 AI 설계다. 기존 연구 `infrastructure-orchestration`을 중심으로 이어가며 HOH 추천 연구를 관련 소유 연구로 연결한다. 새 정체성이나 독립 연구 저장소를 이름만으로 만들지 않는다.
