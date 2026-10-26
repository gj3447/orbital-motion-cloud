# 입체운행구름 공개와 Foundation 라이선스

2026-10-26 UTC · Codex. 다음 공개 관리자가 요청·적용 범위·실제 원격 상태를 확인하는 기록이다.

<a id="user-source"></a>
## 사용자 원문 — USER_PRIMARY

> USL 기반으로도 리밸런싱 해야하는데 ㅇㅇ 인정하냐 ㅇㅇ? 그리고 입체운행구름이랑 그 비행기맨은 퍼블릭으로 바까줘봐 ㅇㅇ 그 metahumotonic foundation 젖작권으로 ㅇㅇ

이 대화에서 직접 받은 원문이다. USL 리밸런싱 방향과 두 본체 저장소의 공개·Foundation 저작권 표시 요청으로 적용한다.
구체적 USL 실행 경계·라이선스 적용 구분은 아래의 AI 운영 해석이다.

## 대상과 적용

- 입체운행구름: `gj3447/orbital-motion-cloud`, GitHub ID `1403344489`. 조회 당시 Private, 기본 브랜치 main.
- 비행기맨 본체: `gj3447/bhgman`, GitHub ID `1408294645`. 조회 당시 이미 Public이며 원격 LICENSE에 MHL 1.1과 Foundation contributors 표시가 있었다. 기존 허락을 유지한다. `bhgman_tool`은 별도 저장소이므로 대상에 포함하지 않는다.
- OMC에는 Foundation의 현행 MHL 1.2 전문, LICENSE-NOTICE와 README 저작권·조건 안내를 추가한다. 가져온 SYMPOSIUM 자료의 MIT 허가문을 보존한다.
- 소유 계정·저장소 이름·제3자 권리를 이전하지 않는다. Foundation 표시는 원 권리자의 권리를 지우지 않는다.
- USL의 의미/주소 연결 보존과 OMC의 실행 책임을 [운영 기준 9절](../../../docs/OMC_OPERATING_MODEL.md#usl-rebalancing)에 연결한다. 이번 작업은 실제 자원 이동이나 native USL rebalance 실행을 수행하지 않는다.

| 적용 파일 | 정확한 원천 | SHA-256 |
|---|---|---|
| `LICENSE` | `gj3447/metahumotonic-foundation@41f31697c8aae1e9b269cf8147f88d2e1de78494:LICENSE` | `dc4439a4bc7ea4cb913ba3a5a9ff679a1dc148a03f77a6deba82758c5a92b5a3` |
| `licenses/SYMPOSIUM-MIT.txt` | `gj3447/symposium@ceaf2ccf1db10f621570badf9a88a394ca5c45a6:LICENSE` | `86b56515043a9209622fab6a1cd0273cf73cf95585d89dcd1e551348f3c87c1e` |

두 원천은 해당 Git blob과 일치한다. 라이선스 고지 전달은 배포 소비자가 필요로 하는 원문이므로 전문을 보존한다.
새 라이선스나 Foundation 전체 규범을 제정한 것이 아니다.

## 공개 전 확인과 실행

현재 OMC HEAD와 원격 ref에서 도달 가능한 388개 blob, 4,656,005 bytes를 읽어 인식 가능한 개인키·GitHub/AWS/Slack/OpenAI 자격 증명 패턴을 검사했고 일치가 없었다.
검사한 HEAD의 추적 파일에는 `.env`·개인키·credentials 이름이 없었으며 GitHub Actions 실행 이력은 0건이었다.
이는 제한된 공개 전 점검이며 모든 종류의 비밀 부재를 증명하지 않는다. ignored `.local`의 원천 사본·운영 설정과 다른 작업자의 미커밋 변경은 게시하지 않는다.

공개 변경은 기존 `gh repo edit gj3447/orbital-motion-cloud --visibility public --accept-visibility-change-consequences`를 사용하고,
이후 GitHub API의 repository ID·visibility와 원격 main의 LICENSE 바이트를 다시 확인한다.
공개 명령의 실행·확인 결과는 다음 절에 기록한다.

## 완료 확인

2026-10-26 06:20:41 UTC: 라이선스·고지·USL 운영 기준을 `6e63f2d`로 커밋해 원격 main에 게시한 뒤 공개 변경 명령이 exit 0으로 끝났다.
GitHub 연결 도구에서 두 repository ID의 visibility가 모두 `public`임을 확인했고, 인증 헤더 없는 GitHub REST 조회도 각각 HTTP 200·`private: false`를 반환했다.
OMC 원격 LICENSE의 전체 텍스트는 로컬 원문과 일치하며 Git blob SHA는 `6a4d209452c371bb5e9eac73683a71869ea12af4`다.
비행기맨은 기존 Public·MHL 1.1·Foundation 표시를 확인한 것으로, 이번 작업에서 공개 설정이나 라이선스 판본을 변경하지 않았다.

검증은 두 라이선스의 고정 원천 bytes 일치, 새 고지·기록의 로컬 링크/anchor 5개, staged diff 검사와 원격 되읽기다.
README는 이번 삽입분만 커밋했고 다른 작업자의 미커밋 파일을 포함하지 않았다. 공유 KG·연구 원장·실제 리밸런싱 runtime은 변경하지 않았다.
