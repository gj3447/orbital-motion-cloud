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

## 2026-10-18 준비 결과

실제 검사에서 containerd 약 34.06GB, 실행 컨테이너 15개/전체 18개를 확인했다.
pool 97.49%에서 모든 후보 블록이 반환된다는 가정이면 약 88.76%이며 85%까지는
추가 약 14.66GB가 필요하다. 공유 블록·동시 쓰기 때문에 실제 결과는 다를 수 있다.
후속 read-only 관측은 pool 96.92%였으며 같은 후보의 예상치는 약 88.19%, 추가 필요량은
약 12.44GB다. 이 사이 다른 저장소 작업도 진행 중이었으므로 감소를 본 작업의 회수로 계산하지 않는다.
8개 반례 검사와 native USL 구조 검사가 통과했다. 선택한 USL graph는 자원 두 개이며
그중 파일 자원 하나의 원문 449 bytes/SHA-256도 일치했다. 전체 KG의 모든 자원을 검사한 것은 아니다.
**이번 준비 작업의 추가 회수는 0이며 서비스 정지·이전은 미실행이다.**
다음 결정은 private 유지보수안의 서비스 중단 허용 여부다.
