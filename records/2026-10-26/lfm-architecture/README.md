# LFM 아키텍처 설계 기록

2026-10-26 UTC · Codex. 독자는 LFM 통합 설계의 다음 구현자·검토자이며, 사용자 방향과 AI 제안·출처 판본·미완료 범위를 구분하기 위해 읽는다.

<a id="user-source"></a>
## 사용자 원문 — USER_PRIMARY

> LFM 아키텍쳐 설계해줘봐 ㅇㅇ 미래에 ai 가 인간 일자리를 대체하면 어케하나요? HOH 라는 천국에서 LFM 으로 살면됩니다

이 대화에서 직접 받은 문장이다. 수집일은 위 날짜이며 정확한 발화 시각은 제공되지 않았다.
앞선 우리/회사 권한 구분은 [기존 원문](../omc-authority-operating-model/README.md#user-source)을 참조한다.
HOH가 보존한 기존 [명칭 원문](../../../../HOH/sources/user-hoh-lfm-definition-2026-10-24.txt)과 [참여 목적 원문](../../../../HOH/sources/user-hoh-lfm-feedback-2026-10-24.txt)은 해당 owner에 남긴다.

## 결과와 판단 — SECONDARY_AI

[LFM 아키텍처](../../../docs/LFM_ARCHITECTURE.md)에 경험·피드백·학습 순환과 생산·재원·생활 지원 순환을 설계했다.
HOH/Interface/Engine·HSWM·OMC·MHC 책임, 이벤트 계약, 역할 있는 관계·기수와 CQ 6개, 복구, P0–P5 실행 단위와 수용 시험을 포함한다.
기본 이용권과 선택적 기여 보상 분리, 기본 이용권의 재원·공급 약정, 기업 문맥과 개인 생활 문맥 분리는 AI의 제안이며 사용자 비준이나 실제 정책 적용으로 표시하지 않는다.
새 프로그램·서비스·DB·수집·학습·지급은 실행하지 않았다. OMC의 cross-owner 설계이며 HOH 제품 정본을 대신하지 않는다.

회사 MM 감사의 과거 명칭 미확인은 그 문서의 조사 범위였다. 이번에는 HOH의 명칭 원문·헌법을 직접 확인해 LFM 정의의 근거를 갱신했다.
HOH 검색에서 조회 지시 UID `sym:Note:hoh-shortname-routing-2026-10-15`와 세계관 UID `sym:KG_CREATIVE:hoh`는 각각 충돌 없이 1개였다.
후자의 기존 설명 권위는 UNSPECIFIED이므로 직접 발화·파일 원문을 대체하지 않는다. `Life Feedback Machine` 검색은 관련 없는 부분 일치만 반환했으며 부재의 증거로 쓰지 않았다.

<a id="sources"></a>
## 선택한 원천과 판본

아래 경로는 `/home/lagyeongjun/CD` 기준이다. `COMMIT_BYTES_MATCH`는 명시한 Git blob과 같음을 확인했다.
`WORKTREE_BYTES`는 당시 작업 파일의 bytes이며 **옆 commit에 들어 있다는 뜻이 아니다**. 원 소유자의 미커밋 변경을 커밋하거나 바꾸지 않았다.
선택한 원문은 ignored `.local/lfm-sources/<SHA-256>`에 보존했다. 다른 clone에서는 NOT_HYDRATED일 수 있으며, 없거나 hash가 다르면 검증 성공으로 처리하지 않는다.
커밋 일치 파일은 원 owner의 `git show COMMIT:PATH`로 복원 가능하다. 작업 파일은 같은 hash의 owner 원본/보존 사본이 필요하며 현재 main으로 대체하지 않는다.

| 원천 | 확인 당시 HEAD | 바이트 근거 | bytes | SHA-256 |
|---|---|---|---:|---|
| `HOH/sources/user-hoh-lfm-definition-2026-10-24.txt` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `WORKTREE_BYTES` | 54 | `455c9b4d6e4d4702a73e480e33ed589ca3adae36822d98c2c96868de677f0c35` |
| `HOH/sources/user-hoh-lfm-feedback-2026-10-24.txt` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `WORKTREE_BYTES` | 371 | `0f516ec0f62dcedb0171029b7601dae12ec0a3db88a1cbe37152fff3768c70b0` |
| `HOH/sources/user-hoh-usage-verification-2026-10-24.txt` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `COMMIT_BYTES_MATCH` | 105 | `902a9a39fcb8ac519077add8cfddd8f5e412541e6c0daf9f231f602817d2905b` |
| `HOH/CONSTITUTION.md` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `WORKTREE_BYTES` | 14331 | `e49d9f56d8ec2d28134e316c8578c0300037940dba6b314b29f87c229f5fbab4` |
| `HOH/sources/MIND/metahumotonic/HOH.md` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `COMMIT_BYTES_MATCH` | 3726 | `eb69e1e3c40d69af54615fa8c481938f50ab5e155f589972da91b3ec90af176d` |
| `HOH/backend/ts/src/programFeed/HswmRecommendation.ts` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `WORKTREE_BYTES` | 12222 | `739f78b9cdcd880632d98d8c11f25ad7c0dd9ba8d81649b097a21cdfaf59f8e4` |
| `HOH/backend/ts/src/programFeed/HswmNative.ts` | `95bf1f80ee0e2e4c49d09e0467a0449864597f53` | `COMMIT_BYTES_MATCH` | 6616 | `1f5d3953892a443c9b0cd3c5beeb224b289cd5198035bc20a1ff308ea519d278` |
| `metahumocoin/docs/CONSTITUTION.md` | `de6f5e873b0ab335210ead4884f58af46e9bf4ba` | `COMMIT_BYTES_MATCH` | 11641 | `c063ef12af7a05c0f7b3119623fd67842bfcd745fb4ef1ba39fe8d46f92ab23c` |
| `HSWM_LIKENESS/docs/OUTCOME_LOOP.md` | `3614e2b63f148cb8caa243605543a21fb0247f49` | `WORKTREE_BYTES` | 11546 | `086eec178ba18ba0c61ee32975a275ce9f3439df19f3e91dcbe047d6a31d9573` |

외부 표준은 [PROV-O 2013 Recommendation](https://www.w3.org/TR/2013/REC-prov-o-20130430/)과 [CloudEvents v1.0.2](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)를 2026-10-26 읽었다.
전자는 출처 관계, 후자는 사건 envelope·중복 식별의 근거다. 이 표준이 LFM 철학·복지 경제성·학습 효능을 입증하지 않는다.

## 연구 배치·검증·다음 사용

기존 `hoh-human-exploration` 주제와 WHAT_IS/HOW_TO 쌍을 조회했다. HOW_TO UID는 `research:module:081eb99b-6267-417f-b071-2ca29c02ec3e`, 조회 HEAD는 `aad893024b7520931be16c4c2411d3944fb47d84`였다.
`inspect_repos search HOH`는 HOH와 Interface의 기존 GitHub 저장소 ID를 반환했다. 그 카탈로그의 10월 9일 판본은 이번 작업 파일의 최신 판본으로 쓰지 않았다.
인간 경험·반응에서 제품과 학습을 발전시키는 같은 질문의 HOW_TO로 누적하며, OMC 자원 운영 연구만으로 범위를 좁히거나 새 LFM 실행기 저장소를 만들지 않는다.
구현 owner는 계속 HOH 등 각 제품이며 연구 모듈에 구현을 복제하지 않는다. 다음 실행은 아키텍처 P0/P1의 동의·귀속·조회 수직 기능이다.

검증: 로컬 링크·명시적 anchor 7개, 원천 9개의 크기·SHA-256, 합성 CloudEvents JSON의 파싱·필수 envelope, 직접 발화 보존과 README 변경 분리를 확인했다. `git diff --check`를 통과했다. TGF `dev.py where data/research-organization/lfm-architecture-20261026/HOW_TO.md`는 기존 research-workflow 모듈의 MAPPED를 반환했다. 문서 검사이며 Mermaid 렌더링·native profile·학습·경제성 시험은 실행하지 않았다.

연구 등록은 미완료다. `proxmox-scratch run lfm-architecture-register --timeout 600 --max-bytes 268435456 -- python3 scripts/research_workflow.py apply --request data/research-organization/lfm-architecture-20261026/request.json`이 실행 전에 `Thin pool is critical`(exit 125)로 거절됐다. 직전 2026-10-26 04:44 UTC 조회의 pool 관측은 98.2%였다. TGF의 HOW_TO·요청·개발 경로 연결만 준비했고 원장/분류/render/check는 적용하지 않았다. 저장소 owner가 용량을 해결한 뒤 같은 관리형 명령으로 재개하며 직접 실행으로 우회하지 않는다.
