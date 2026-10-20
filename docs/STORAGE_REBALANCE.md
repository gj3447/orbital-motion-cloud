# OMC 저장소 압력과 실제 회수 경계

`scripts/storage_rebalance.py`는 data-01의 containerd 저장소를 읽고, 같은 제공 서버의
별도 20TB 로컬 ext4로 옮기는 **운영 검토안**을 만든다. 실행·삭제·서비스 정지는 하지 않는다.
기존 파일 [placement](HARDWARE_ADAPTIVE_PLACEMENT.md)는 원본을 보존하므로 회수량이 0이고,
등록 archive의 실제 이전은 ORCA_SETTING의 `storage-tier adaptive`가 담당한다.
운영 containerd는 archive adapter로 처리할 수 없다.

계획의 독자는 다음 유지보수 결정을 내리는 storage owner와 사용자다. 실제 장비 주소·
컨테이너 ID·개인 등록은 ignored `.local/storage-rebalance/`에만 남긴다. 새 공유 KG 기록이나
HSWM 실행 권한을 만들지 않는다. 이번 변경은 운영 진단이며 새 연구 결과가 아니다.

## 재현

```sh
python3 scripts/storage_rebalance.py --help
umask 077
mkdir -p .local/storage-rebalance
python3 scripts/storage_rebalance.py --collect \
  --host .local/storage-rebalance/host.json \
  --placement-state .local/placement/state/state.json \
  --runtime-state .local/rebalance-owner-loop/state-canonical.json \
  > .local/storage-rebalance/plan.json
python3 -m unittest discover -s tests -p 'test_storage_rebalance.py' -v
```

`--collect`는 기존 SSH transport로 정해진 mount·용량·Docker ID/상태·containerd namespace만
읽는다. 컨테이너 환경 변수·자격 증명을 수집하지 않는다. 일반 `--observation FILE`은 동일한
owner 입력의 검사를 재현하며 새 현장 관측이 아니다. 300초 넘은 관측은 거절한다.
기존 계획과 비교할 때는 새 출력 파일에 `--verify-before <이전 plan.json>`을 사용한다.
동일 파일로 입력과 출력을 리다이렉션하지 않는다.

`--host`는 운영자가 선택한 private `omc-storage-owner-host/1` 입력이다. `host_uid`,
`ssh_target`, `pool_uuid`, `bulk_uuid`, `source_path`, `source_device`, `target_path`,
`target_mount`, `target_device`를 담는다. 그래프나 모델 출력에서 접속 권한을 유도하지 않는다.
현재 매핑은 ignored 경로에만 있고 코드·테스트에는 실제 내부 주소·장치 UUID를 넣지 않는다.

계획은 원래 소비 경로를 유지하는 로컬 bind mount를 제안한다. provider 자신의 OS 디스크를
자신이 제공하는 NFS로 이전하는 순환 의존성, 동일 장치, 다른 UUID, 기존 목적지,
100GiB reserve 침범, 다른 containerd namespace를 거절한다. 98% emergency는 그대로다.
정지 승인이 있어도 복사·복원·guard·실행기 조건 없이 실행 가능한 계획으로 승격하지 않는다.

`--maintenance-policy FILE`은 기존 사용자 결정을 다시 묻지 않고 계획에 결속한다.
private JSON은 `schema: omc-storage-maintenance-policy/1`, `registration_digest`(선택한
host JSON의 canonical SHA-256), `decision: AUTHORIZED_WITHOUT_SERVICE_INTERRUPTION`,
`source_ref`(결정 원문 참조)만 받는다. 다른 host 등록이나 추가 권한 필드는 거절한다.
실행 서비스가 있으면 `HOLD_SERVICE_CONTINUITY`를 내며, Docker live-restore 설정도
containerd root의 무중단 이전이나 검증된 failover를 증명하지 않는다. 이 기록은 실행 권한,
복구 검증, 저장소 admission을 대체하지 않는다.

pool 계산 목표는 storage owner 기본 정책의 **80% 미만**이다. **85%는 평가 시작점**이므로
그 아래가 됐다고 회수 필요량을 0으로 만들지 않는다. 실제 압력 해제는 owner의 root 여유
검사도 필요하며 이 계획은 pool 조건만 추정한다. 원격 쓰기·공유 블록의 효과는 미측정이다.

## USL과 HSWM 보존

선택한 기존 placement state와 runtime state **전체 JSON**의 digest를 비교한다.
USL resource/link/meaning UID·locator·참여 역할과 순서·metadata·revision, HSWM read-set 및
미래 추가 필드도 비교에 포함된다. 두 state가 서로 다른 USL graph를 담으면 거절한다.
이 검사는 선택한 owner export의 보존이며 canonical HSWM 저장소나 전체 KG의 현장 검사와
다르다. native USL `adapt --format resource-graph --operation check`로 graph 구조도 검사한다.

containerd 이동은 애플리케이션 경로와 이미지·컨테이너 ID를 유지해야 한다. 따라서 이 계획은
USL locator 변경도 요구하지 않는다. 실제 전환 뒤에는 원래 소비 경로, 이미지 전체 집합,
기존 컨테이너 ID·mount·서비스 건강, owner state와 source hash를 다시 검사해야 한다.
검사기의 PASS를 실제 이전 완료나 전체 의미 보존의 증명으로 표현하지 않는다.

## 승인 대상과 이전 순서

실제 대상·예상 용량·실행 중 서비스 목록과 unit 초안은 private plan과
`.local/storage-rebalance/maintenance.md`를 따른다. 이 문서 자체는 정지 승인이 아니다.

1. 최신 pool·목적지 UUID·독립 복구 공간·이미지/컨테이너 집합을 재확인한다. 원격 쓰기의
   증가량·프로세스 수명도 관리 runner가 관측하도록 owner 실행기를 연결한다. 거절을 우회하지 않는다.
2. 영향을 받는 서비스의 유지보수 중단 범위를 확정한다. 관측된 실행 컨테이너만 정상 종료하고
   Docker socket·Docker·containerd writer를 정지한다. 다른 writer·overlay mount가 남으면 중단한다.
   NFS 서버와 VM200 부팅 디스크는 이동하거나 정지하지 않는다.
3. 중지된 원본을 별도 디스크의 복구 사본과 20TB 목적지에 복사한다. numeric UID/GID, ACL,
   xattr, 내부 hardlink, sparse 파일과 내용 hash를 검증한다. 이 동작은 root 권한을 가진
   소유 실행기의 서버 로컬 ext4 경로에서 수행하며 NFS squash를 통해 metadata를 복원하지 않는다.
4. 복구 사본의 전체 readback과 목적지 검증 뒤 원래 경로를 새 ext4 자료에 bind한다.
   Docker와 containerd에 mount 의존성을 설치하여 미마운트 시 SSD로 쓰는 fallback을 막는다.
   일반 `data-root` 변경만으로 containerd 위치가 바뀐다고 가정하지 않는다.
5. 원래 실행하던 컨테이너만 시작한다. 전체 이미지 ID·컨테이너 ID·volume/bind 경로와
   기존 health/readiness를 대조하고 원래 포트의 기능을 검증한다. USL/HSWM 선택 state도 비교한다.
6. 검증을 마친 원본 SSD 사본만 회수하고 root TRIM 전후의 실제 thin-pool 사용률을 측정한다.
   `du` 크기, Docker의 reclaimable 표시, TRIM 보고 bytes를 실제 회수량으로 더하지 않는다.

새 저장소에 쓰기가 발생한 뒤에는 오래된 SSD 사본으로 단순 전환하지 않는다. 서비스를 다시
정상 종료하고 새 저장소의 변경분을 보존·대조한 후 역방향 복구해야 한다. 시작 전 실패라면
원래 디렉터리와 mount 의존성을 원복한다. 복구 과정 자체가 실패하면 미완료 상태를 남긴다.

Docker의 공식 문서는 containerd image store에서 이미지·snapshot과 Docker volume/config의
저장소가 나뉘며 `data-root`로 전자를 변경하지 못한다고 설명한다.
[Docker 저장 디렉터리](https://docs.docker.com/engine/daemon/#daemon-data-directory),
[containerd 운영 문서](https://github.com/containerd/containerd/blob/main/docs/ops.md).
bind mount 선택은 경로를 보존하려는 이 환경의 운영 설계이며 upstream의 무중단 이전 보장이 아니다.

## 2026-10-18 HSWM 연결 유지 조건 반영

사용자는 작업 진행을 승인하면서 HSWM 연결 유지를 요구했다. 전체 containerd 이전은
canonical Neo4j를 포함한 15개 실행 서비스의 정지가 필요하므로 현재 조건에서는 보류한다.
기존 승인을 재요청하지 않으며, 유지보수 결정과 최신 관측은 ignored
`.local/storage-rebalance/maintenance-policy.json`, `plan-continuity.json`에 보존한다.

13:30 UTC 관측은 pool 84.55%, 후보 21.07GB다. 그사이 다른 저장소 작업이 회수한 양을
본 작업의 성과로 합산하지 않는다. 80% 미만까지 약 17.75GB가 더 필요하다.
13:38 UTC 재관측은 84.57%, 필요량 약 17.83GB이며, 등록된 56개 자료는 모두 이미 bulk에 있다.
HSWM 정본 read-set 3개는 `VERIFIED_READ_ONLY`, KG 조회와 연구 fabric doctor는 통과했다.
HOH 운영 응답은 chat `READY`, native HSWM `CONNECTED_EXPERIMENTAL`이다.
이는 연결 상태 관측이며 새 모델 실행·학습이나 추천 품질 검증이 아니다.
서비스 정지·이전·추가 회수는 하지 않았다. 아래 수치는 승인 전 당시 관측이다.

## 2026-10-18 앞선 준비 결과

실제 검사에서 containerd 약 34.06GB, 실행 컨테이너 15개/전체 18개를 확인했다.
pool 97.49%에서 모든 후보 블록이 반환된다는 가정이면 약 88.76%이며 85%까지는
추가 약 14.66GB가 필요하다. 공유 블록·동시 쓰기 때문에 실제 결과는 다를 수 있다.
후속 read-only 관측은 pool 96.92%였으며 같은 후보의 예상치는 약 88.19%, 추가 필요량은
약 12.44GB다. 이 사이 다른 저장소 작업도 진행 중이었으므로 감소를 본 작업의 회수로 계산하지 않는다.
8개 반례 검사와 native USL 구조 검사가 통과했다. 선택한 USL graph는 자원 두 개이며
그중 파일 자원 하나의 원문 449 bytes/SHA-256도 일치했다. 전체 KG의 모든 자원을 검사한 것은 아니다.
**이번 준비 작업의 추가 회수는 0이며 서비스 정지·이전은 미실행이다.**
당시 다음 결정은 private 유지보수안의 서비스 중단 허용 여부였으며, 후속 결정은 위에 기록했다.

## 내부 장비 관측과 Dell scratch guard

2026-10-18에 Dell 루트 디스크가 `/var/tmp/kjra-scratch`(421G)로 가득 차 Orca main이 `ENOSPC`로
응답을 멈췄다(10-11 사건과 같은 원인). 사용자 요청에 따라 1단계로 관측과 자동 정리만 설치했다.
자료 이전·서비스 재시작은 하지 않으며 실행 중 세션을 건드리지 않는다.

- **관측:** `scripts/fleet_memory.py`가 dev-01 사용자 timer(15분)로 등록 장비의 로컬 filesystem,
  RAM, swap, LVM thin pool과 guard 상태를 읽기 전용 sh probe로 읽는다. 85% 이상 warning,
  95% 이상 critical(종료 코드 3), RAM 여유 10% 미만 warning이다. 장비 목록은 private
  `~/.config/omc/fleet-hosts.json`(원본 `.local/fleet-memory/hosts.json`), 최신 결과는
  `~/.local/state/omc/fleet-memory.json`이다.
- **정리:** `deploy/omc-scratch-guard`가 Dell kjra 사용자 timer(10분)로 scratch filesystem 사용률을
  본다. `HIGH_PCT`(85) 미만이면 아무것도 하지 않는다. 그 이상이면 scratch 최상위 항목
  (`claude-<uid>/` 아래는 한 단계 더 깊은 항목) 중 `IDLE_MIN`(3일) 안에 수정된 파일이 없고,
  읽을 수 있는 프로세스가 fd/cwd로 잡고 있지 않으며, 이름이 `PROTECT_REGEX`(`env`)와 맞지 않는
  것만 지운다. 정리 후에도 `CRIT_PCT`(95) 이상이면 종료 코드 3으로 실패한다.
  읽을 수 없는 하위 디렉터리가 있는 항목은 유휴를 증명할 수 없으므로 보존한다(10-19 19:16부터
  이 경우 `find` 실패로 guard가 매번 중단됐다). 목록 비교는 `LC_ALL=C`로 하고 삭제 직전 보존 목록과
  다시 정확히 대조한다(10-20 첫 수정본은 ko_KR 정렬로 `comm` 경고를 냈다).
  scratch 밖, `/srv/sim`, DGX의 k8s 볼륨·모델 캐시는 관측만 한다.
- **작업 메모리 상자:** `deploy/omc-job-memory-cap`이 Dell kjra 사용자 서비스로 15초마다 Orca 터미널
  daemon scope 안을 본다. claude/codex 아래 shell·wrapper 다음의 첫 프로세스를 작업 root로 보고,
  그 트리의 anon RSS 합이 `TRIGGER_GIB`(8)에 이르면 트리 전체를 새 `omc-jobcap-<pid>-<start>.scope`
  (`MemoryMax` 40G, swap 0, `OOMPolicy=continue`)로 옮긴다. 넘치면 그 상자 안에서만 OOM이 난다.
  나중에 fork된 자식은 같은 상자에 붙인다. 신호를 보내지 않으며 agent·shell·언어서버·Isaac·Orca와
  이미 다른 scope(`systemd-run --user --scope`)에 있는 작업은 옮기지 않는다. 40G를 넘게 쓸 작업은
  직접 scope를 만들어 실행한다. `MemoryHigh`는 기본 해제다. swap이 없을 때 Dell 실측에서 작업을 죽이지도
  끝내지도 않고 기어가게 만들었다. 2026-10-19 사건(agent 작업 34G로 RAM·swap 소진)의 예방 조치다.

```sh
python3 -m unittest tests.test_scratch_guard tests.test_fleet_memory -v
install -m 755 scripts/fleet_memory.py ~/.local/bin/omc-fleet-memory
cp deploy/omc-fleet-memory.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now omc-fleet-memory.timer
omc-fleet-memory show --state ~/.local/state/omc/fleet-memory.json

scp deploy/omc-scratch-guard delltower:.local/bin/
scp deploy/omc-scratch-guard.{service,timer} delltower:.config/systemd/user/
ssh delltower 'systemctl --user daemon-reload && systemctl --user enable --now omc-scratch-guard.timer'

python3 -m unittest tests.test_job_memory_cap -v
ssh delltower 'DRY_RUN=1 ONCE=1 python3 -' < deploy/omc-job-memory-cap   # 옮길 대상만 출력
scp deploy/omc-job-memory-cap delltower:.local/bin/
scp deploy/omc-job-memory-cap.service delltower:.config/systemd/user/
ssh delltower 'systemctl --user daemon-reload && systemctl --user enable --now omc-job-memory-cap.service'
```
