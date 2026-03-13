# azure-functions-scaffold

[![PyPI](https://img.shields.io/pypi/v/azure-functions-scaffold.svg)](https://pypi.org/project/azure-functions-scaffold/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/azure-functions-scaffold/)
[![CI](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml)
[![Release](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml)
[![Security Scans](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-scaffold/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-scaffold)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://yeongseon.github.io/azure-functions-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Read this in: [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

用于生产级 Azure Functions Python v2 项目的脚手架 CLI.

## 快速开始

使用以下 4 个步骤创建并运行本地 HTTP 函数:

1. 安装 CLI。
2. 生成一个新项目。
3. 安装项目依赖。
4. 启动本地 Functions 运行时。

```bash
pip install azure-functions-scaffold
azure-functions-scaffold new my-api
cd my-api
pip install -e .
func start
```

在浏览器中打开 `http://localhost:7071/api/hello`。

预期响应:

```text
Hello, World!
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
|  |  `- logging.py         # Structured JSON logging
|  |- functions/
|  |  `- http.py            # HTTP trigger (Blueprint)
|  |- schemas/
|  |  `- request_models.py  # Request/response models
|  `- services/
|     `- hello_service.py   # Business logic
`- tests/
   `- test_http.py          # Pytest tests
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
| http | `azure-functions-scaffold new my-api` | REST API、Webhook |
| timer | `azure-functions-scaffold new my-job --template timer` | 定时任务、Cron |
| queue | `azure-functions-scaffold new my-worker --template queue` | 消息处理 (Azurite) |
| blob | `azure-functions-scaffold new my-blob --template blob` | 文件处理 (Azurite) |
| servicebus | `azure-functions-scaffold new my-bus --template servicebus` | 企业消息传递 |

注意: `afs` 是 `azure-functions-scaffold` 的简称。两者都可用。

模板默认值:

- `http`: 公开 HTTP 端点和服务模块。
- `timer`: 使用 NCRONTAB 表达式设置的定时触发器。
- `queue`: 为本地 Azurite 开发准备好的 Storage Queue 触发器。
- `blob`: 用于文件摄取流水线的 Blob 触发器脚手架。
- `servicebus`: 带开发占位符的 Service Bus 触发器脚手架。

## 可选功能

- `--with-openapi` - Swagger UI + OpenAPI 规范端点
- `--with-validation` - Pydantic 请求/响应校验
- `--with-doctor` - 健康检查诊断
- `--preset minimal|standard|strict` - 工具配置等级
- `--interactive` - 引导式项目设置

组合示例:

```bash
azure-functions-scaffold new my-api --preset strict --with-validation
azure-functions-scaffold new my-api --with-openapi --with-validation
azure-functions-scaffold new my-api --template timer --preset minimal
```

## 扩展项目

向现有脚手架项目添加函数:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
azure-functions-scaffold add timer cleanup --project-root ./my-api
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

在写入文件前预览新增内容:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api --dry-run
```

常见扩展流程:

1. 使用 `azure-functions-scaffold add <trigger> <name>` 添加触发器。
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

## 生态系统

- Validation: [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation)
- OpenAPI: [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi)
- Logging: [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging)
- Doctor: [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor)
- Cookbook: [azure-functions-cookbook](https://github.com/yeongseon/azure-functions-cookbook)

## 文档

- 完整文档: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
- 快速开始: [`docs/quickstart.md`](docs/quickstart.md)
- CLI 参考: [`docs/cli.md`](docs/cli.md)
- 为什么采用此结构: [`docs/why.md`](docs/why.md)
- 安装: [`docs/installation.md`](docs/installation.md)
- 模板规范: [`docs/template_spec.md`](docs/template_spec.md)
- 故障排查: [`docs/troubleshooting.md`](docs/troubleshooting.md)

## 开发

使用 Makefile 命令作为标准入口:

```bash
make install
make check-all
make docs
make build
```

## 免责声明

本项目是独立的社区项目，与 Microsoft 没有关联，
也未获得 Microsoft 认可或维护。

Azure 和 Azure Functions 是 Microsoft Corporation 的商标。

## 许可证

MIT
