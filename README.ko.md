# Azure Functions Scaffold

[![PyPI](https://img.shields.io/pypi/v/azure-functions-scaffold.svg)](https://pypi.org/project/azure-functions-scaffold/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/azure-functions-scaffold/)
[![CI](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml)
[![Release](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml)
[![Security Scans](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-scaffold/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-scaffold)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://yeongseon.github.io/azure-functions-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

다른 언어: [English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

프로덕션 수준의 Azure Functions Python v2 프로젝트를 위한 스캐폴딩 CLI.

## 왜 사용해야 할까

새로운 Azure Functions 프로젝트를 시작하려면 보일러플레이트 설정이 필요합니다: `host.json`, `function_app.py`, 디렉터리 구조, 도구 설정, 테스트. `azure-functions-scaffold`는 한 번의 명령으로 프로덕션 수준의 프로젝트 레이아웃을 생성하여, 처음부터 비즈니스 로직에 집중할 수 있게 합니다.

## 범위

- Azure Functions Python **v2 프로그래밍 모델**
- 데코레이터 기반 `func.FunctionApp()` 애플리케이션
- CLI 기반 프로젝트 생성 및 확장
- HTTP, Timer, Queue, Blob, Service Bus, LangGraph 트리거 템플릿

이 도구는 프로젝트 스캐폴드를 생성합니다. 런타임 라이브러리를 제공하지는 **않습니다**.

## 기능

- 의도 중심 생성 명령: `afs api new`, `afs worker <trigger>`, `afs ai agent`
- 프로젝트 확장 명령: `afs api add`, `afs advanced add`
- 선택적 통합: `--with-openapi`, `--with-validation`, `--with-doctor`
- 사전 설정 도구 수준: `--preset minimal|standard|strict`
- 파워 유저를 위한 고급 플래그 제어: `afs advanced new`
- 단축 별칭: `afs`를 `azure-functions-scaffold` 대신 사용 가능

## 설치

```bash
pip install azure-functions-scaffold
```

## 빠른 시작

다음 4단계 흐름으로 로컬 HTTP 함수를 생성하고 실행하세요:

1. CLI를 설치합니다.
2. 새 프로젝트를 생성합니다.
3. 프로젝트 의존성을 설치합니다.
4. 로컬 Functions 런타임을 시작합니다.

```bash
afs api new my-api
cd my-api
pip install -e .
func start
```

브라우저에서 `http://localhost:7071/api/health`를 여세요.

예상 응답:

```json
{"status": "healthy"}
```

프로젝트 이름은 영문자 또는 숫자로 시작해야 하며 문자, 숫자,
하이픈 또는 밑줄만 사용할 수 있습니다.

## 생성 결과

생성된 구조는 트리거 바인딩, 비즈니스 로직, 공통 런타임 관심사,
테스트를 분리하여 팀이 모든 엔드포인트를 `function_app.py`에 결합하지 않고도
확장할 수 있게 합니다.

```text
my-api/
|- function_app.py          # Azure Functions v2 entrypoint
|- host.json                # Runtime configuration
|- local.settings.json.example
|- pyproject.toml           # Dependencies and tooling config
|- app/
|  |- core/
|  |  |- config.py          # Application settings
|  |  `- logging.py         # Structured JSON logging
|  |- dependencies/
|  |  `- __init__.py        # Shared dependencies
|  |- functions/
|  |  |- health.py          # Health check (Blueprint)
|  |  `- users.py           # Users CRUD (Blueprint)
|  |- schemas/
|  |  `- users.py           # Pydantic request/response models
|  `- services/
|     |- health_service.py   # Health check logic
|     `- users_service.py    # Users business logic
`- tests/
   |- test_health.py        # Health endpoint tests
   `- test_users.py         # Users CRUD tests
```

이 구조가 효과적인 이유:

- 트리거별 코드는 `app/functions`에 유지합니다.
- 재사용 가능한 비즈니스 규칙은 `app/services`에 유지합니다.
- 모델 계약은 `app/schemas`에 유지합니다.
- 관측성 및 런타임 헬퍼는 `app/core`에 유지합니다.
- 통합 검증은 `tests`에 유지합니다.

## 템플릿

| 템플릿 | 명령어 | 사용 사례 |
| --- | --- | --- |
| http | `afs api new my-api` | REST API, 웹훅 |
| timer | `afs worker timer my-job` | 예약 작업, 크론 |
| queue | `afs worker queue my-worker` | 메시지 처리 (Azurite) |
| blob | `afs worker blob my-blob` | 파일 처리 (Azurite) |
| servicebus | `afs worker servicebus my-bus` | 엔터프라이즈 메시징 |

참고: `afs`는 `azure-functions-scaffold`의 줄임말입니다. 둘 다 동작합니다.

템플릿 기본값:

- `http`: 상태 확인 엔드포인트와 사용자 CRUD 서비스 모듈.
- `timer`: NCRONTAB 표현식 설정을 사용하는 예약 트리거.
- `queue`: 로컬 Azurite 개발에 바로 사용할 수 있는 Storage Queue 트리거.
- `blob`: 파일 수집 파이프라인을 위한 Blob 트리거 스캐폴드.
- `servicebus`: 개발용 자리표시자가 포함된 Service Bus 트리거 스캐폴드.

## 선택 기능

- `--with-openapi` - Swagger UI + OpenAPI 사양 엔드포인트
- `--with-validation` - Pydantic 요청/응답 검증
- `--with-doctor` - 상태 확인 진단
- `--with-db` - 데이터베이스 바인딩 (SQLAlchemy) *(계획 — 현재 미연결)*
- `--preset minimal|standard|strict` - 도구 구성 수준

의도 중심 명령은 일반적인 기능 조합을 미리 선택합니다. 세부 플래그를 직접 제어하려면 `afs advanced new <name>`을 사용하세요.

조합 예시:

```bash
afs api new my-api --preset strict --with-validation
afs api new my-api --preset strict --with-validation
afs worker timer my-job --preset minimal
afs advanced new my-api --with-openapi --with-validation
```

## 프로젝트 확장

기존 스캐폴딩 프로젝트에 함수를 추가합니다:

```bash
afs api add get-user --project-root ./my-api
afs advanced add timer cleanup --project-root ./my-api
afs advanced add queue sync-jobs --project-root ./my-api
afs advanced add blob ingest-reports --project-root ./my-api
afs advanced add servicebus process-events --project-root ./my-api
```

파일을 쓰기 전에 추가 내용을 미리 확인합니다:

```bash
afs advanced add servicebus process-events --project-root ./my-api --dry-run
```

일반적인 확장 흐름:

1. `afs api add <name>` 또는 `afs advanced add <trigger> <name>`으로 트리거를 추가합니다.
2. `app/services` 아래에 비즈니스 로직을 구현합니다.
3. 필요하면 `app/schemas`의 계약을 업데이트합니다.
4. `tests`에 테스트를 추가하거나 업데이트합니다.

## 배포

```bash
func azure functionapp publish <APP_NAME>
```

게시 전에:

- 프로덕션 연결에 필요한 앱 설정을 구성합니다.
- `host.json`과 함수 인증 수준을 검토합니다.
- 프로젝트 검증(`pytest`, 린트, 포맷팅)을 실행합니다.
- `func start`로 로컬 시작을 확인합니다.

## 문서

- 전체 문서: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
- 시작하기: [`docs/guide/getting-started.md`](docs/guide/getting-started.md)
- CLI 참조: [`docs/reference/cli.md`](docs/reference/cli.md)
- 프로젝트 구조: [`docs/guide/project-structure.md`](docs/guide/project-structure.md)
- 템플릿: [`docs/guide/templates.md`](docs/guide/templates.md)
- 문제 해결: [`docs/guide/troubleshooting.md`](docs/guide/troubleshooting.md)

## 개발

정식 진입점으로 Makefile 명령을 사용하세요:

```bash
make install
make check-all
make docs
make build
```

## 에코시스템

이 패키지는 **Azure Functions Python DX Toolkit**의 일부입니다.

| 패키지 | 역할 |
|---------|------|
| **azure-functions-scaffold** | 프로젝트 스캐폴딩 CLI |
| [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation) | 요청/응답 검증 및 직렬화 |
| [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi) | OpenAPI 사양 생성 및 Swagger UI |
| [azure-functions-langgraph](https://github.com/yeongseon/azure-functions-langgraph) | Azure Functions용 LangGraph 배포 어댑터 |
| [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging) | 구조화된 로깅 및 관측성 |
| [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor) | 배포 전 진단 CLI |
| [azure-functions-durable-graph](https://github.com/yeongseon/azure-functions-durable-graph) | Durable Functions 기반 그래프 런타임 *(계획)* |
| [azure-functions-python-cookbook](https://github.com/yeongseon/azure-functions-python-cookbook) | 레시피 및 예제 |

## 면책 조항

이 프로젝트는 독립적인 커뮤니티 프로젝트이며 Microsoft와 제휴되어 있지 않고,
Microsoft의 보증을 받거나 유지관리되지 않습니다.

Azure 및 Azure Functions는 Microsoft Corporation의 상표입니다.

## 라이선스

MIT
