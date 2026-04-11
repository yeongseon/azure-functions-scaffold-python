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

其他语言: [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

用于生产级 Azure Functions Python v2 项目的脚手架 CLI.

## 为什么使用它

启动新的 Azure Functions 项目意味着设置样板文件：`host.json`、`function_app.py`、目录结构、工具配置和测试。`azure-functions-scaffold` 通过一个命令生成生产级项目布局，让你从一开始就专注于业务逻辑。

## 范围

- Azure Functions Python **v2 编程模型**
- 基于装饰器的 `func.FunctionApp()` 应用
- CLI 驱动的项目生成与扩展
- HTTP、Timer、Queue、Blob、Service Bus 和 LangGraph 触发器模板

此工具用于生成项目脚手架，**不**提供运行时库。

## 功能

- 意图驱动的生成命令: `afs api new`、`afs worker <trigger>`、`afs ai agent`
- 项目扩展命令: `afs api add`、`afs advanced add`
- 可选集成: `--with-openapi`、`--with-validation`、`--with-doctor`
- 预设工具级别: `--preset minimal|standard|strict`
- 面向高级用户的细粒度参数控制: `afs advanced new`
- 短别名: `afs` 可替代 `azure-functions-scaffold`

## 安装

```bash
pip install azure-functions-scaffold
```

## 快速开始

使用以下 4 个步骤创建并运行本地 HTTP 函数:

1. 安装 CLI。
2. 生成一个新项目。
3. 安装项目依赖。
4. 启动本地 Functions 运行时。

```bash
afs api new my-api
cd my-api
pip install -e .
func start
```

在浏览器中打开 `http://localhost:7071/api/health`。

预期响应:

```json
{"status": "healthy"}
```

项目名称必须以字母或数字开头，并且只能使用字母、数字、
连字符或下划线。

## 生成结果

生成的布局将触发器绑定、业务逻辑、共享运行时关注点和测试分离，
使团队可以在不把所有内容都耦合到 `function_app.py` 的情况下
扩展端点。

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

此布局的优势:

- 将触发器特定代码放在 `app/functions` 中。
- 将可复用的业务规则放在 `app/services` 中。
- 将模型契约放在 `app/schemas` 中。
- 将可观测性与运行时辅助放在 `app/core` 中。
- 将集成检查放在 `tests` 中。

## 模板

| 模板 | 命令 | 使用场景 |
| --- | --- | --- |
| http | `afs api new my-api` | REST API、Webhook |
| timer | `afs worker timer my-job` | 定时任务、Cron |
| queue | `afs worker queue my-worker` | 消息处理 (Azurite) |
| blob | `afs worker blob my-blob` | 文件处理 (Azurite) |
| servicebus | `afs worker servicebus my-bus` | 企业消息传递 |

注意: `afs` 是 `azure-functions-scaffold` 的简称。两者都可用。

模板默认值:

- `http`: 健康检查端点和用户 CRUD 服务模块。
- `timer`: 使用 NCRONTAB 表达式设置的定时触发器。
- `queue`: 为本地 Azurite 开发准备好的 Storage Queue 触发器。
- `blob`: 用于文件摄取流水线的 Blob 触发器脚手架。
- `servicebus`: 带开发占位符的 Service Bus 触发器脚手架。

## 可选功能

- `--with-openapi` - Swagger UI + OpenAPI 规范端点
- `--with-validation` - Pydantic 请求/响应校验
- `--with-doctor` - 健康检查诊断
- `--with-db` - 数据库绑定 (SQLAlchemy) *(计划中 — 当前未启用)*
- `--preset minimal|standard|strict` - 工具配置等级

意图驱动命令会预先选择常见功能组合。如果需要直接控制参数，请使用 `afs advanced new <name>`。

组合示例:

```bash
afs api new my-api --preset strict --with-validation
afs api new my-api --preset strict --with-validation
afs worker timer my-job --preset minimal
afs advanced new my-api --with-openapi --with-validation
```

## 扩展项目

向现有脚手架项目添加函数:

```bash
afs api add get-user --project-root ./my-api
afs advanced add timer cleanup --project-root ./my-api
afs advanced add queue sync-jobs --project-root ./my-api
afs advanced add blob ingest-reports --project-root ./my-api
afs advanced add servicebus process-events --project-root ./my-api
```

在写入文件前预览新增内容:

```bash
afs advanced add servicebus process-events --project-root ./my-api --dry-run
```

常见扩展流程:

1. 使用 `afs api add <name>` 或 `afs advanced add <trigger> <name>` 添加触发器。
2. 在 `app/services` 下实现业务逻辑。
3. 必要时更新 `app/schemas` 中的契约。
4. 在 `tests` 中新增或更新测试。

## 部署

```bash
func azure functionapp publish <APP_NAME>
```

发布前:

- 设置生产连接所需的应用配置。
- 检查 `host.json` 与函数授权级别。
- 运行项目检查（`pytest`、lint 和格式化）。
- 使用 `func start` 在本地验证启动。

## 文档

- 完整文档: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
- 快速开始: [`docs/guide/getting-started.md`](docs/guide/getting-started.md)
- CLI 参考: [`docs/reference/cli.md`](docs/reference/cli.md)
- 项目结构: [`docs/guide/project-structure.md`](docs/guide/project-structure.md)
- 模板: [`docs/guide/templates.md`](docs/guide/templates.md)
- 故障排查: [`docs/guide/troubleshooting.md`](docs/guide/troubleshooting.md)

## 开发

使用 Makefile 命令作为标准入口:

```bash
make install
make check-all
make docs
make build
```

## 生态系统

本包是 **Azure Functions Python DX Toolkit** 的一部分。

| 包 | 角色 |
|---------|------|
| **azure-functions-scaffold** | 项目脚手架 CLI |
| [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation) | 请求/响应校验与序列化 |
| [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi) | OpenAPI 规范生成与 Swagger UI |
| [azure-functions-langgraph](https://github.com/yeongseon/azure-functions-langgraph) | Azure Functions 的 LangGraph 部署适配器 |
| [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging) | 结构化日志与可观测性 |
| [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor) | 部署前诊断 CLI |
| [azure-functions-durable-graph](https://github.com/yeongseon/azure-functions-durable-graph) | 基于 Durable Functions 的图运行时 *(计划中)* |
| [azure-functions-python-cookbook](https://github.com/yeongseon/azure-functions-python-cookbook) | 食谱与示例 |

## 免责声明

本项目是独立的社区项目，与 Microsoft 没有关联，
也未获得 Microsoft 认可或维护。

Azure 和 Azure Functions 是 Microsoft Corporation 的商标。

## 许可证

MIT
