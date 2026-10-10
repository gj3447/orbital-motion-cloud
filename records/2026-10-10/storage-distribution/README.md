# SSD · 20TB · 4TB 저장 분배 확인

후속: [OMC 배치 구현·실행 기록](../hardware-adaptive-placement/README.md)에 12개 자료의 소유 전송기 완료 관측과 OMC의 20TB·4TB 소규모 실장치 검증을 추가했다. 아래 최초 조사·실패 관측은 당시 상태로 보존한다.

2026-10-10 UTC. 사용자 요청은 [원문](user-verbatim.txt), 실측은 [관측 기록](observation.json), 아래 판단은 Codex의 SECONDARY_AI 운영 해석이다. 기존 [20TB 이전 설계](/home/lagyeongjun/CD/THE_GREAT_FLOW/data/research-organization/dev01-20tb-migration-plan.md)를 재사용한다. 새 연구 주제·사도 역할·KG 정체성을 만들지 않는다.

## 확인한 저장 장치

| 위치 | 실측 및 역할 |
| --- | --- |
| dev-01 SSD `/` | 조사 시작 시 약 8.5 GiB 여유, 96% 사용. 실행 중인 DB, WAL, 예약 원장, 잠금, 인증·세션 상태를 우선 유지한다. |
| 20TB `/mnt/development` | 약 17.5 TiB 여유. 큰 입력·모델·닫힌 실험 결과·보관 파일의 주 저장 위치로 사용한다. |
| 4TB `/mnt/bulk` | 약 1.22 TiB 여유, 64% 사용. 이미 쓰는 데이터가 있으므로 빈 디스크로 취급하지 않는다. 중요 원문·Git 이력·일관된 DB 백업의 추가 복사본을 위한 후보다. |

20TB와 4TB는 data-01에서 서로 다른 ext4 UUID로 확인했다. 다만 같은 제공 호스트를 사용하므로 호스트·전원·네트워크 장애까지 독립된 백업은 아니다. 4TB 전체를 새 가용 용량으로 더하지 않는다. 이번 확인에서는 4TB에 파일을 쓰거나 기존 서비스를 옮기지 않았다.

SQLite WAL은 네트워크 파일시스템에서 동작하지 않는다는 [SQLite 공식 설명](https://www.sqlite.org/wal.html)에 따라, 현재 사용 중인 DB 파일을 NFS 디렉터리로 단순 이동하지 않는다. 20TB로 보내는 DB 자료는 해당 DB의 지원 방식으로 만든 일관된 백업이어야 한다.

## USL 연결이 유지되는 조건

1. 기존 resource UID, representation ID, 관계 UID, 참여 역할, 의미, 출처·revision·콘텐츠 해시는 유지한다. 물리 경로 변경을 새 정체성으로 취급하지 않는다.
2. 전체 workspace 이동은 호스트의 workspace root 매핑을 바꾼다. 일부 데이터만 이동한다면 그 데이터의 선택된 representation이 새 저장 workspace를 가리키도록 소유자 바인딩을 갱신한다. 절대 경로는 호스트 설정에 둔다.
3. **기존 경로의 심볼릭 링크만으로 USL 호환을 보장할 수 없다.** 설치된 USL은 `realpath`가 등록된 workspace 밖으로 나가면 거부한다. 기존 파일 경로의 호환과 USL 바인딩의 허용 범위를 각각 확인해야 한다. 범위 검사를 완화하지 않는다.
4. 복사 후 파일별 바이트·SHA-256·필요 메타데이터를 확인하고, 단일 쓰기 주체를 보장한 상태에서 경로를 전환한다. `rsync -a`만으로 모든 ACL·xattr·hardlink 보존을 가정하지 않는다. [rsync 공식 매뉴얼](https://download.samba.org/pub/rsync/rsync.1.html).
5. 구조 검증과 실제 파일 읽기를 분리한다. USL `check/context` 통과는 파일 전체 무결성, 마이그레이션 완료, 서비스 정상 작동의 증거가 아니다.
6. 원본 정리 후 게스트 파일시스템 여유와 PVE thinpool 사용률을 각각 확인한다. 파일 복사·이름 변경만으로 SSD의 실제 블록이 회수되지는 않는다.

근거: [설치된 USL 바인딩 계약](/home/lagyeongjun/CD/USL/docs/RESOURCE_BINDINGS.md), [경계 검사 구현](/home/lagyeongjun/CD/USL/src/resource-bindings.ts:159), [공유 그래프 엔지니어링 계약](/home/lagyeongjun/CD/ORCA_SETTING/skills/kg-ontology/references/graph-engineering.md).

## 이번 확인의 범위와 진행 중 작업

별도 세션이 이미 [저장 공간 복구 작업](/home/lagyeongjun/CD/THE_GREAT_FLOW/work/2026-10-10-storage-recovery/)을 시작한 것을 확인했다. 후속 확인에서 첫 실행 `e3b41250d57149a8a9aaf5aecfaca29d`가 15:04:39 UTC에 exit 1로 종료됐다. 개별 이전 기록은 `COPYING`에 남아 있었으며, 원본 디렉터리는 그대로였다. 복사 로그의 전송량은 약 9.1 GB이나 전체 검증·경로 전환·공간 회수 완료 근거는 아니다. 상위 실행의 오류 원인은 이 세션에서 확정하지 않았다.

이 세션은 같은 원본을 중복 이동하거나 해당 실행을 중단하지 않았다. 관측 시점의 기록은 `observation.json`에 있으며 다른 세션의 후속 복구 결과를 대신하지 않는다.

기존 fleet USL 투영의 구조와 `host:dev-01` → `storage:expansion20tb` 탐색을 확인했다. 원본 그래프와 검사·탐색 영수증의 digest를 보존했다. 이는 기존 선언의 구조 확인이며, 앞으로 이동할 모든 파일의 USL 바인딩 검증을 뜻하지 않는다. 이 세션은 전역 KG, fleet 선언, 바인딩, 서비스 설정을 바꾸지 않았다.

MHC HOW_TO 저장소는 이미 [20TB 연구 저장 공간](/mnt/development/METAHUMOTONIC_SHARED/research/mhc-compute-stability/HOW_TO_mhc-compute-stability/README.md)에 있다. 기존 [복구 기록](../mhc-compute-stability/recovery.json)의 허브 최종 갱신·검사는 아직 남아 있다. 현재 디스크 대응의 소유 작업과 중복 실행하지 않았다.
