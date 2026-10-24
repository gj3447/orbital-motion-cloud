# HOH 브라우저 기여 실행

HOH 공개 배포와 이용자의 실제 자원 기여 요청에 따라 추가한 `SECONDARY_AI` 구현이다.
HOH가 동의·계정·CSRF와 이용 화면을 소유하고 OMC가 작업 배정과 결과 검증을 소유한다.
이 기능은 HSWM 실행 허가, 일반 GPU 작업 배정, 금전 크레딧을 만들지 않는다.

```sh
python3 scripts/browser_contribution.py --help
python3 -m unittest discover -s tests -p test_browser_contribution.py
```

`--owner`는 live `resource-dispatch`/`resource-observe`의 실제 WorkingDirectory여야 한다.
그 소유자의 `Broker` 기본 연결에 브라우저 참여·감사 테이블을 추가한다. 별도 자원 DB나
fleet controller를 만들지 않고 기존 프로세스 예약에 개입하지 않는다.
`--config`의 `tokenFile`, `corpusFile`, `enabled`는 비공개 운영 설정이다. 토큰 파일은
mode 600이며 공개 작업 데이터만 corpus에 넣는다. 명시적 `PUBLIC_SHIPPABLE` 선언과
고정 필드·크기 검사를 통과해야 한다. 이 선언만으로 비공개 자료를 공개할 권한이 생기지 않는다.

현재 입력은 HOH가 공개 배포하도록 요청받은 서브컬처 글 52개, UTF-8 135,494 bytes다.
작업자는 문서 해시와 문자·바이트·줄 수를 계산한다. owner는 원본에서 계산한 결과와
비교한 뒤에만 `ACCEPTED`를 저장한다. 결과의 재전송은 중복 집계하지 않는다.
서로 다른 principal 두 개가 같은 판본을 검증하면 그 판본은 더 배정하지 않는다.
principal 구별이 물리적으로 독립된 기기의 증명은 아니다.

작업당 입력 64 KiB, 작업자 1개, 5초 종료, 다음 작업까지 최소 10초, 임대 45초다.
브라우저 보고 시간은 참고 관측이며 크레딧이 아니다. 원격 기기가 실제로 멈췄는지 알 수 없는
만료는 `UNKNOWN`, 브라우저의 종료 통보는 `BROWSER_REPORTED`로 구분한다. 작업이 없으면
대기한다. 사전 계산한 예상 결과와 비교하는 이 초기 감사 경로의 비용 절감은 평가하지 않았다.

서버는 loopback HTTP만 받고 HOH VM100까지 기존 SSH 인증의 Unix socket 포워딩을 사용한다.
토큰·socket·개인 원장은 Git에 넣지 않는다. `enabled=false`로 새 작업/결과 수락을 거부해도
취소·상태는 유지한다. 방문자에게 임의 코드, 파일 경로, URL을 실행 입력으로 받지 않는다.
실제 방송 영상·개인 채팅·카메라 프레임은 corpus가 아니다.

2026-10-24 단위 6개와 실제 HOH 브라우저 12개가 통과했다. 공개 앱 배포는 HOH의 운영
receipt로 별도 판단한다. 영상 중계·변환·아바타 렌더링을 이 감사 기능의 성과로 계산하지 않는다.
