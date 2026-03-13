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

他の言語: [English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md)

プロダクションレベルの Azure Functions Python v2 プロジェクトのためのスキャフォールディング CLI.

## なぜこのツールを使うのか

新しい Azure Functions プロジェクトを始めるには、ボイラープレートの設定が必要です: `host.json`、`function_app.py`、ディレクトリ構造、ツール設定、テスト。`azure-functions-scaffold` は一つのコマンドでプロダクションレベルのプロジェクトレイアウトを生成し、最初からビジネスロジックに集中できるようにします。

## スコープ

- Azure Functions Python **v2 プログラミングモデル**
- デコレータベースの `func.FunctionApp()` アプリケーション
- CLI 駆動のプロジェクト生成と拡張
- HTTP、Timer、Queue、Blob、Service Bus トリガー用テンプレート

このツールはプロジェクトスキャフォールドを生成します。ランタイムライブラリは提供**しません**。

## 機能

- プロジェクト生成のための `azure-functions-scaffold new` コマンド
- 5 つの組み込みテンプレート: HTTP、Timer、Queue、Blob、Service Bus
- 既存プロジェクト拡張のための `azure-functions-scaffold add` コマンド
- オプション統合: `--with-openapi`、`--with-validation`、`--with-doctor`
- プリセットツーリングレベル: `--preset minimal|standard|strict`
- `--interactive` によるガイド付きセットアップ
- ショートエイリアス: `afs` を `azure-functions-scaffold` の代わりに使用可能

## インストール

```bash
pip install azure-functions-scaffold
```

## クイックスタート

次の 4 ステップでローカル HTTP 関数を作成して実行します:

1. CLI をインストールします。
2. 新しいプロジェクトを生成します。
3. プロジェクトの依存関係をインストールします。
4. ローカル Functions ランタイムを起動します。

```bash
azure-functions-scaffold new my-api
cd my-api
pip install -e .
func start
```

ブラウザで `http://localhost:7071/api/hello` を開いてください。

期待されるレスポンス:

```text
Hello, World!
```

プロジェクト名は英数字で始める必要があり、使用できるのは文字、数字、
ハイフン、アンダースコアのみです。

## 生成される構成

生成されるレイアウトは、トリガーバインディング、ビジネスロジック、共有ランタイムの
関心事、テストを分離し、`function_app.py` にすべてを結合せずにチームが
エンドポイントを拡張できるようにします。

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

このレイアウトが機能する理由:

- トリガー固有のコードは `app/functions` に置きます。
- 再利用可能なビジネスルールは `app/services` に置きます。
- モデル契約は `app/schemas` に置きます。
- 可観測性とランタイムヘルパーは `app/core` に置きます。
- 統合チェックは `tests` に置きます。

## テンプレート

| テンプレート | コマンド | 用途 |
| --- | --- | --- |
| http | `azure-functions-scaffold new my-api` | REST API、Webhook |
| timer | `azure-functions-scaffold new my-job --template timer` | スケジュールタスク、Cron |
| queue | `azure-functions-scaffold new my-worker --template queue` | メッセージ処理 (Azurite) |
| blob | `azure-functions-scaffold new my-blob --template blob` | ファイル処理 (Azurite) |
| servicebus | `azure-functions-scaffold new my-bus --template servicebus` | エンタープライズメッセージング |

注: `afs` は `azure-functions-scaffold` の短縮形です。どちらも利用できます。

テンプレートの既定値:

- `http`: 公開 HTTP エンドポイントとサービスモジュール。
- `timer`: NCRONTAB 式設定を使用するスケジュールトリガー。
- `queue`: ローカル Azurite 開発向けに準備された Storage Queue トリガー。
- `blob`: ファイル取り込みパイプライン向け Blob トリガースキャフォールド。
- `servicebus`: 開発用プレースホルダー付きの Service Bus トリガースキャフォールド。

## オプション機能

- `--with-openapi` - Swagger UI + OpenAPI 仕様エンドポイント
- `--with-validation` - Pydantic リクエスト/レスポンス検証
- `--with-doctor` - ヘルスチェック診断
- `--preset minimal|standard|strict` - ツーリングレベル
- `--interactive` - ガイド付きプロジェクトセットアップ

組み合わせ例:

```bash
azure-functions-scaffold new my-api --preset strict --with-validation
azure-functions-scaffold new my-api --with-openapi --with-validation
azure-functions-scaffold new my-api --template timer --preset minimal
```

## プロジェクトの拡張

既存のスキャフォールド済みプロジェクトに関数を追加します:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
azure-functions-scaffold add timer cleanup --project-root ./my-api
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

ファイルを書き込む前に追加内容をプレビューします:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api --dry-run
```

一般的な拡張フロー:

1. `azure-functions-scaffold add <trigger> <name>` でトリガーを追加します。
2. `app/services` 配下にビジネスロジックを実装します。
3. 必要に応じて `app/schemas` の契約を更新します。
4. `tests` のテストを追加または更新します。

## デプロイ

```bash
func azure functionapp publish <APP_NAME>
```

公開前の確認:

- 本番接続に必要なアプリ設定を構成します。
- `host.json` と関数の認証レベルを確認します。
- プロジェクトのチェック（`pytest`、lint、format）を実行します。
- `func start` でローカル起動を確認します。

## ドキュメント

- 全文書: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
- はじめに: [`docs/guide/getting-started.md`](docs/guide/getting-started.md)
- CLI リファレンス: [`docs/reference/cli.md`](docs/reference/cli.md)
- プロジェクト構成: [`docs/guide/project-structure.md`](docs/guide/project-structure.md)
- テンプレート: [`docs/guide/templates.md`](docs/guide/templates.md)
- トラブルシューティング: [`docs/guide/troubleshooting.md`](docs/guide/troubleshooting.md)

## 開発

正規のエントリポイントとして Makefile コマンドを使用します:

```bash
make install
make check-all
make docs
make build
```

## エコシステム

- [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation) — リクエストとレスポンスのバリデーション
- [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi) — OpenAPI と Swagger UI
- [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging) — 構造化ロギング
- [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor) — 診断 CLI
- [azure-functions-python-cookbook](https://github.com/yeongseon/azure-functions-python-cookbook) — レシピとサンプル

## 免責事項

このプロジェクトは独立したコミュニティプロジェクトであり、Microsoft とは提携しておらず、
Microsoft による承認または保守の対象ではありません。

Azure および Azure Functions は Microsoft Corporation の商標です。

## ライセンス

MIT
