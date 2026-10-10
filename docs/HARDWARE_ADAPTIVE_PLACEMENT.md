# 하드웨어 상태에 적응하는 OMC 데이터 배치

사용자는 2026-10-10에 **HSWM의 추상 구조와 연결성을 유지하면서, 현재 하드웨어·CLI·메모리 상태를 읽고 AI와 도구로 데이터 배치를 최적화하는 것**을 OMC 기능 중 하나로 지정했다. [직접 발화](../records/2026-10-10/hardware-adaptive-placement/user-verbatim.txt)는 USER_PRIMARY다. 아래 구성·알고리즘·구현 범위는 SECONDARY_AI다. 이 기능으로 OMC의 철학적 의미나 전체 역할을 한정하지 않는다.

## 논리 구조와 물리 배치를 나누기

논리 구조 `G`에는 자원 고유 ID, 타입, 내용 revision, 출처, 의미, 링크 ID와 이름 있는 참여 역할이 있다. 물리 배치 `P(t)`에는 선택된 representation, workspace alias, 상대 경로와 저장 장치가 있다. OMC는 관측한 하드웨어 상황 `H(t)`와 소유 정책을 바탕으로 `P(t)`를 바꾼다. 수용 조건은 선택한 자원의 locator를 제외한 **전체 `G`가 동일**하다는 것이다. 선택하지 않은 자원의 locator도 바뀌면 거부한다.

```mermaid
flowchart LR
    A[AI: 이동 후보·목적 제안] --> P[계획: 시각·용량·RAM·데이터 분류 검사]
    H[CLI·디스크·RAM·가시 cgroup 관측] --> P
    P --> T[소유 CLI로 20TB 배치·선택적 4TB 복사]
    T --> V[원문·목적지 SHA-256 검증]
    V --> B[USL bind-graph]
    B --> C[ID·의미·역할·출처 불변 검사]
    C --> S[단일 writer가 배치 상태를 원자적으로 교체]
    S --> H
```

이 순환은 호출형 CLI로 구현했다. 상주 감시기나 무제한 자동 실행을 설치하지 않았다. AI는 후보를 골라 구조화된 요청을 내며, 이 버전에는 별도 학습 모델·비용 최적해 solver가 없다. 결정적 검사기가 실현 가능한 제한 배치를 선택한다. 데이터 바이트, RAM, CPU와 GPU 자원을 하나의 용량으로 합산하지 않는다.

## 저장소와 기존 도구의 책임

| 구성 | 책임 |
| --- | --- |
| OMC `scripts/placement.py` | 관측·계획·중복 방지·내용 검증·상태 비교·실행 기록 |
| THE GREAT FLOW `scripts/shared_storage.py` | 기존 source 검증을 거쳐 20TB에 새 객체를 복사하고, 선택 시 그 객체를 4TB 목적지로 복사 |
| USL `bind-graph`, `adapt check` | 기존 ID·의미·역할·metadata를 유지한 locator 재결속과 구조 검사 |
| 원래 데이터·서비스 소유자 | 큰 디렉터리의 쓰기 중지·복사·기존 경로 전환·원본 공간 회수·서비스 재시작 |

활성 DB·WAL·인증 정보·잠금·실시간 저널은 자동 배치 후보가 아니다. 원문이 확정된 `closed_artifact`, `research_snapshot`, `memory_snapshot`만 소유 registry에 등록한다. 분류는 소유자의 선언이며 파일 확장자로 내용의 안전성을 증명하지 않는다. 초기 adapter는 dev-01의 이미 등록된 NFS source와 별도 로컬 상태 디렉터리에 한정한다.

20TB는 주 복사본, 4TB는 선택적 추가 복사본이다. 두 장치는 각각 용량을 계산하지만 같은 제공 호스트의 장애 영역을 공유한다. SSD에는 원자적 상태·예약 기록을 남긴다. 이 CLI는 원본을 보존하며 `space_reclaim_bytes: 0`을 반환한다. 실제 SSD 회수량은 큰 자료를 처리하는 기존 소유 전송기의 결과와 파일시스템·thinpool 재관측으로 별도로 확인한다.

실제 4TB client mount는 `soft` NFS다. 이 경로로 쓰지 않고, 등록된 data-01 SSH 전송기를 통해 제공 서버의 로컬 ext4에 기록하고 읽어서 검증한다. 쓰기 전 제공 서버의 filesystem UUID를 확인한다. 새로운 OMC 복사 namespace는 기존 NFS의 익명 UID/GID 매핑과 소유 SSH 계정에 맞춰 별도로 만들었으며 기존 export·공용 마운트·다른 디렉터리 권한은 바꾸지 않았다. 클라이언트의 NFS 음성 캐시 때문에 방금 원격 게시된 파일이 바로 보이지 않을 수 있어, 4TB readback도 제공 서버에서 수행한다.

## CLI 사용

호스트 등록 파일과 상태는 무시되는 `.local/` 아래에 둔다. 실제 root·내부 장비 주소·개인 등록은 공개 그래프에 넣지 않는다. 호스트 등록에는 명시한 자원 UID·representation ID·허용 source workspace·상대 경로·SHA-256·크기·데이터 분류, 기존 두 저장 장치의 source, 소유 CLI 소스 핀이 있다. AI 요청에는 자원 목록·추가 복사 여부·목적만 들어간다. 요청에서 root·실행 명령·내용 핀을 바꾸면 거부한다.

```sh
python3 scripts/placement_graph.py check
python3 scripts/placement_graph.py query
python3 scripts/placement.py --help
python3 scripts/placement.py --host .local/placement/host.json init --graph .local/placement/input.usl.json
python3 scripts/placement.py --host .local/placement/host.json --out .local/placement/observation.json observe
python3 scripts/placement.py --host .local/placement/host.json --out .local/placement/plan.json plan --observation .local/placement/observation.json --request .local/placement/request.json
python3 scripts/placement.py --host .local/placement/host.json apply --plan .local/placement/plan.json --operation placement-20261010-001
python3 scripts/placement.py --host .local/placement/host.json status
```

`--out`은 subcommand 앞에 둔다. `init`은 새 소유 상태에 한 번만 수행한다. 원본 graph는 기존 자원을 가진 `usl-resource-graph/v1`이어야 한다. AI가 임의의 새 semantic graph로 현재 상태를 바꾸는 명령은 없다. 복사 합계가 100MiB를 넘으면 실제 `proxmox-scratch`의 bulk lease·예산·부팅·감독 프로세스·현재 작업 그룹을 확인한다. 환경 변수만 설정해서는 통과할 수 없으며, 실행기 거부를 직접 재실행으로 우회하지 않는다.

요청 예시:

```json
{"schema":"omc-placement-request/1","resources":["omc:artifact:placement-user-request-20261010"],"backup":true,"reason":"확정 원문을 20TB와 4TB에 보존"}
```

관측 TTL은 최대 300초다. 실행 전에 관측을 다시 수집하고 부팅 ID·호스트 설정·기존 상태 digest·배치 후보를 대조한다. 단일 파일은 64MiB, 한 계획은 최대 16개 자원·복사 합계 256MiB다. 전송기는 1MiB 청크를 쓰고 CLI 호출별 제한은 120초다. 디스크에는 장치별 최소 100GiB, SSD에는 최소 8GiB 여유를 요구한다. 메모리는 OS에서 보이는 가용량과 보이는 cgroup 조상 한도의 최소 여유를 검사한다. namespace 밖 제약은 UNKNOWN이며 이 검사를 물리 호스트 전체의 RAM 할당 승인으로 바꾸지 않는다.

## 중단·복구와 불변성

작업 키와 계획 digest를 intent에 먼저 기록한다. 동시에 실행된 같은 소유 상태의 writer는 로컬 파일 잠금으로 거부한다. 기존 복사본은 내용이 일치할 때만 재사용하고 덮어쓰지 않는다. 소스·목적지 내용 변경, 계획 이후 다른 상태 갱신, 잘못된 mount, 의미 변경은 실패한다.

`recover --plan <같은 계획> --operation <같은 키>`는 영속 상태를 대조한다. 일부 복사만 끝났다면 같은 원본 핀과 목적지 바이트를 재검사한다. 상태 교체 뒤 결과 기록 직전에 중단됐다면 준비된 결과와 상태 digest를 대조해 결과 기록만 완성한다. 새 키로 중복 실행을 숨기거나 예약·기존 기록을 지우지 않는다. 원본 삭제가 없으므로 미완료 복사본이 있어도 원문은 유지된다.

실행 코드가 바뀌면 과거 계획의 실행은 거부한다. 검토한 복구 수정에 한해 `recover --reviewed-implementation sha256:<현재 placement.py 바이트 해시>`로 같은 키를 이어갈 수 있다. 원래 intent·계획·원문 핀·상태 비교는 유지하고 이전/현재 구현 digest를 별도 복구 기록에 남긴다. 이 옵션은 상태 충돌·철회·원문 변경을 우회하지 않는다.

파일 복사·USL 상태 교체·다른 서비스의 읽기는 하나의 전역 트랜잭션이 아니다. 같은 OS 계정의 적대적인 변경, 전원 장애 시 NFS 내구성, 다른 소유 writer, 모든 HSWM runtime의 실시간 상태 보존은 별도 조건이다. 검사한 입력 graph의 의미 보존과 HSWM runtime 실행은 구분한다. 현재 CLI는 HSWM runtime을 실행하거나 shared KG에 쓰지 않는다.

## 표준 그래프 엔지니어링

[그래프](../graph/placement.json), [타입·관계 계약](../graph/placement-contract.json), [USL 투영](../graph/placement.usl.json)에 사용자 근거·기능·불변 조건·단계·기존 실행기·수용 검사를 별도 노드로 연결했다. UID 중복, 관계 domain/range·기수, 원문 핀, 세 질문의 정확한 답을 검사한다. 조회 질문은 무엇을 보존하는지, 누가 복사를 수행하는지, 사용자 근거가 무엇인지다.

이것은 소유 범위의 typed property graph와 실제 USL 계약을 따르는 구현이다. RDF·OWL·SHACL 인증이나 전체 분산 시스템에 대한 형식 증명을 주장하지 않는다. 테스트 정의, 테스트 실행 결과, 실장치의 복사 결과, 소유 전송기가 보고한 공간 회수는 별도 근거로 남긴다. [실행 기록](../records/2026-10-10/hardware-adaptive-placement/README.md).
