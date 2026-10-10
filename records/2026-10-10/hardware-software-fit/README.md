# OMC 하드웨어와 소프트웨어 결합 설계 기록

`user-verbatim.txt`는 이번 사용자 메시지 전체를 UTF-8로 보존한다. 맞춤법·띄어쓰기·“신일 합일”·쿠버네티스 비유를 수정하지 않았으며 뒤에 줄바꿈을 추가하지 않았다. `chu-os-user-verbatim.txt`는 앞선 CHU OS 자동 분배 발화를 별도 보존한다. 두 원문은 USER_PRIMARY다.

[계획](../../../docs/HARDWARE_SOFTWARE_FIT_PLAN.md)과 [그래프](../../../graph/hardware-software-fit.proposal.json)는 SECONDARY_AI / PROPOSED다. `sources.json`은 로컬 원문 바이트 SHA-256, 기존 자료 revision, 외부 문서 접근 시점을 구분한다. 외부 웹 문서의 불변 사본을 확보했다고 주장하지 않는다.

```sh
python3 records/2026-10-10/hardware-software-fit/validate.py
python3 cli.py check
```

`validation.json`은 설계 그래프의 타입·방향·기수·출처·단계 DAG와 여섯 질의의 정확한 답을 확인한 기록이다. 누락 끝점, AI 해석의 사용자 정전 승격, 미실행 단계의 완료 표기, 잘못된 질의 답을 넣은 네 반례도 거부했다. 런타임 성능·장비 간 실행·자동 최적화를 검증한 기록은 아니다.

기존 연구 주제 `infrastructure-orchestration`을 재사용한다. OMC의 데이터 배치를 하드웨어별 프로그램·실행 설정까지 확장하는 HOW_TO이므로 별도 주제나 역할 정본을 만들지 않는다. KG 조회에서는 OMC의 기존 subject ID만 재사용했고 CHU OS의 정본 ID는 확인하지 못했다. 허브 boot의 연구 context는 registry 크기 한도로 PARTIAL이어서 기존 주제 CLI·소유 registry·OMC 소스의 읽기 전용 조회로 보완했다.

THE GREAT FLOW 연결 결과는 `research-receipt.json`에 별도로 기록한다. 워크플로 COMPLETE는 연구 보존과 그래프 갱신의 완료이며, 제안한 자동 실행기의 완성을 뜻하지 않는다.
