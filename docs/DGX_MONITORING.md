# DGX의 OMC 운영 관측

2026-10-12 사용자의 DGX 자원·모델 CLI 모니터링 요청을 구현한 운영 adapter다.
기존 [OMC 하드웨어 적응 설계](HARDWARE_SOFTWARE_FIT_PLAN.md)의 `H(t)` 관측 계층에
해당한다. 원문은 비공개 THE GREAT FLOW의 `work/2026-10-12-dgx-monitoring/`에 보존한다.
아래 구성과 기본값은 AI의 구현 선택이며 새 정전이나 자동 최적화 정책이 아니다.

## CLI

dev-01에 설치한 `omc-dgx`는 기존 `dgx` SSH 별칭으로 관측 CLI만 호출한다.

```sh
omc-dgx                         # 저장된 최신 관측과 경과 시간
omc-dgx watch                   # 30초마다 표시, 기본 1시간, Ctrl+C 종료
omc-dgx once                    # 지금 한 번 읽기 전용 수집; 기록하지 않음
omc-dgx status --json           # AI·다른 CLI가 읽는 구조화된 관측
omc-dgx history --limit 10      # 최근 10개 기록
omc-dgx history --limit 10 --json
```

DGX 안에서는 `~/.local/bin/omc-monitor`로 같은 명령을 쓴다. `collect`만 SQLite에
관측을 저장하며 user systemd timer가 담당한다. `status/history/watch`는 DB를 읽고,
`once`는 새 관측을 출력한다. 모델 생성 요청, 임의 명령 실행, 패키지 설치, 캐시 스캔,
모델 교체·재시작은 수행하지 않는다. `watch`는 최소 30초 간격, 최대 2시간이다.

## 무엇을 보는가

- `/proc`: MemAvailable·총 메모리·swap·0.2초 구간 CPU·메모리 PSI, 부팅 ID.
- 루트 파일시스템: 실제 가용 공간. 100GiB 미만은 표시용 주의 기준이다.
- `nvidia-smi`: GPU UUID·활용률·온도·전력. GB10의 전용 VRAM `N/A`는 미관측으로 남긴다.
- Docker: 최대 32개 컨테이너 중 `--model` 또는 `serve MODEL` 설정을 가진 항목의
  모델·revision·실행/중지 상태·ID·시작 시각·메모리/CPU/PID 제한·보이는 cgroup memory.current.
- 등록된 vLLM loopback API: `/health`, `/v1/models`, `/metrics`의 요청 실행/대기 수,
  KV 점유율, prompt/output 토큰 누계, 종료 요청 누계, 관측 구간의 output tok/s.

모델 API의 별칭은 같은 `root`별로 묶는다. 이전 이름의 호환 별칭을 별도 적재 모델로
세지 않는다. 중지된 모델 컨테이너는 inventory로 표시하며 READY 서버로 취급하지 않는다.
Docker 밖 프로세스나 다운로드된 전체 모델 목록까지 발견했다고 주장하지 않는다.

GB10은 공유 메모리를 쓰므로 host·GPU·컨테이너 메모리를 합산하지 않는다.
특히 GPU 드라이버 할당과 host 전체 사용량을 `memory.current` 하나로 설명하지 않는다.
가용량은 host MemAvailable, 컨테이너 값은 해당 cgroup의 관측 범위다. 컨테이너 limit의
`?`는 명시적 한도 없음 또는 미관측이며 실효 무제한이라는 뜻이 아니다.

토큰 누계와 종료 요청 수는 서버가 시작한 이후의 값이다. `finished_requests`에는
abort/error 등의 종료 이유도 포함될 수 있어 성공한 대화 수로 해석하지 않는다.
tok/s는 두 관측 사이의 평균 처리량이며 토큰 생성 벤치마크가 아니다. 서버/모델/부팅 변경,
누계 감소, 90초 초과 간격에서는 rate를 미관측으로 만든다. 첫 관측도 rate는 `?`다.

관측 TTL은 90초다. 수집 실패는 PARTIAL, 오래된 값과 미래 시각은 STALE_OR_FUTURE,
등록 변경은 REGISTRATION_CHANGED로 표시한다. API 장애를 0 요청으로 바꾸지 않는다.
`status`는 정상이고 최신일 때 0, 부분/오래된 관측은 2, 조회 자체 실패는 1을 반환한다.

## 실행과 저장 한도

native Python 표준 라이브러리로 실행한다. 추가 컨테이너·exporter·웹 서버는 없다.
user systemd `omc-monitor.timer`는 작업 종료 후 30초마다 수집한다. 한 작업은 45초,
메모리 128MiB, swap 0, CPU 25%, PID 32로 제한한다. DGX 사용자의 기존 linger 설정을
확인하므로 SSH 접속이 끝나도 timer가 작동한다.

DB는 `~/.local/state/omc-monitor/observations.sqlite3`다. 파일 잠금으로 collector를
하나로 제한하고 SQLite transaction으로 최신 관측을 보존한다. 최대 12시간·1,440개,
관측당 16KiB, DB 최대 8,192페이지(기본 페이지 4KiB에서 32MiB)다. 실패 시 과거 값을
새 시각으로 덮지 않으며 신선도 표시가 오래된 수집을 드러낸다. 원문·응답·키·환경 변수는
수집하지 않는다. 프로세스 stderr는 systemd journal, 정상 관측은 SQLite에만 저장한다.

```sh
systemctl --user status omc-monitor.timer
systemctl --user show omc-monitor.service -p Result -p ExecMainStatus -p MemoryMax -p CPUQuotaPerSecUSec -p TasksMax
journalctl --user -u omc-monitor.service -n 30 --no-pager
systemctl --user disable --now omc-monitor.timer  # 새 수집 중단
systemctl --user stop omc-monitor.service        # 진행 중 수집 종료
```

위 systemd 명령은 DGX에서 실행한다. 중단 시 DB·모델 서버는 남는다. 새 버전 배포는
검증된 release와 wrapper를 명시적으로 전환하며 기존 관측을 삭제하지 않는다.

## 배포와 검사

`deploy/install_dgx_monitor.py --help`의 최초 설치기는 THE GREAT FLOW의 기존 fleet
전송기를 사용한다. 코드·등록·unit 묶음의 SHA-256으로 release를 나누고, 충돌하는 기존
설정은 덮어쓰지 않는다. 실제 `once`가 정상인 것을 확인한 뒤 timer를 켠다. 설치 결과의
실제 호스트 경로·측정값은 지정한 비공개 receipt에 남긴다.

```sh
python3 -B -m unittest discover -s tests -p test_monitor.py -v
python3 cli.py check
```

검사는 별칭 중복, metric 이름 혼동, N/A·NaN, 중지 상태, 비밀 설정 제외, 오래된 관측,
재시작과 누계 초기화, 이력 상한과 실패 시 기존 값 보존, API 장애를 다룬다.
수집 성공·역사 기록·자원 제한의 실제 배포 검증은 별도 receipt다.

OMC의 논리 자원 의미는 유지한다. `host:dgx`, 등록된 서비스 UID, 실제 container ID,
model root·revision, GPU UUID, 부팅 ID·관측 시각·설정 digest를 함께 기록해
**논리 대상 → 물리 배치 → 현재 관측**을 연결한다. 이 관측을 읽는 AI는 이후 별도
계약에서 배치나 설정을 제안할 수 있다. 이번 adapter가 자동 모델 이동, HSWM 의미
그래프 쓰기, CHU OS admission 또는 자원 예약까지 구현한 것은 아니다.
