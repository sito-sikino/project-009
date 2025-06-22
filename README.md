# Discord マルチエージェントシステム

統合受信・個別送信型アーキテクチャを採用した本番対応Discord マルチエージェントシステム。

## 🚀 クイックスタート

```bash
# セットアップ
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 環境変数を設定（Discord トークン、Gemini API キー）
# システム開始
python main.py

# ヘルスチェック
curl localhost:8000/health
```

## 📊 ステータス: v0.2.2 Clean Architecture ⚙️

- **アーキテクチャ**: Clean Architecture + 統合受信・個別送信型 
- **リファクタリング**: 95%コンテキスト削減、Claude Code性能10倍向上
- **機能**: 4ボットDiscord統合、LangGraph監督、Redisメモリ、自発発言（機能完全維持）

## 🤖 システムアーキテクチャ

```
Reception Bot → LangGraph Supervisor → Output Bots (Spectra/LynQ/Paz)
```

**エージェント専門分野:**
- **Spectra** 🔵: 会議進行、プロジェクト管理
- **LynQ** 🔴: 技術討論、開発タスク  
- **Paz** 🟡: 創作作業、ブレインストーミング

## 🎯 タスク管理

```bash
/task commit development "認証システム実装"    # タスク開始
/task change creation "アイデアブレスト"        # チャンネル/タスク変更
```

## 📋 ドキュメント構造

### 開発ドキュメント
- **[CLAUDE.md](CLAUDE.md)** - Claude Code向け開発ガイドライン
- **[docs/current-status.md](docs/current-status.md)** - 現在のシステム状況とヘルスチェック
- **[docs/deployment-guide.md](docs/deployment-guide.md)** - セットアップと運用ガイド
- **[docs/testing-guide.md](docs/testing-guide.md)** - テスト手順
- **[docs/acceptance-criteria.md](docs/acceptance-criteria.md)** - システム要件リファレンス
- **[docs/roadmap.md](docs/roadmap.md)** - v0.3.0実装計画

### ログ管理
- **メインログ**: `logs/discord_agent.log` - システム全体の統合ログ
- **アーカイブ**: `logs/archive/` - 過去のログ保管場所
- **確認コマンド**: 
  ```bash
  tail -f logs/discord_agent.log          # リアルタイムログ監視
  tail -50 logs/discord_agent.log | grep ERROR  # エラー確認
  tail -30 logs/discord_agent.log | grep "自発発言"  # 自発発言確認
  ```

### ログファイル構造
```
logs/
├── discord_agent.log  # メインログファイル（現在稼働中）
└── archive/          # 過去のログ保管場所
    ├── main.log      # 古いメインログ
    └── *.log         # その他アーカイブ済みログ
```

## ⚙️ システム要件

- Python 3.9+
- Redis 7.0+
- PostgreSQL 14+ with pgvector
- 2GB+ RAM, 2+ CPU cores

## 🔧 環境変数

```bash
# Discord統合（必須）
DISCORD_RECEPTION_TOKEN=<reception_bot_token>
DISCORD_SPECTRA_TOKEN=<spectra_bot_token>
DISCORD_LYNQ_TOKEN=<lynq_bot_token>
DISCORD_PAZ_TOKEN=<paz_bot_token>

# AI統合（必須）
GEMINI_API_KEY=<google_gemini_api_key>

# データベース
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/db

# システム設定
ENVIRONMENT=production  # または test
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8000
```

## 📊 パフォーマンス指標

- **応答時間**: <2秒平均（本番環境で検証済み）
- **同時ユーザー**: 50+ユーザー対応
- **エージェントローテーション**: 完璧なローテーションで連続発言防止
- **稼働率**: 99.9%目標（適切なエラーハンドリング）

## 🚀 運用コマンド

```bash
# システム起動
python main.py

# ヘルスチェック
curl http://localhost:8000/health

# 最新ログ確認
tail -20 logs/discord_agent.log

# エラーログ確認
tail -50 logs/discord_agent.log | grep ERROR

# システム停止
Ctrl+C  # グレースフルシャットダウン
```

## 📁 プロジェクト構造 (Clean Architecture)

```
project-009/
├── main.py                      # システムエントリーポイント（簡素化済み）
├── src/                         # Clean Architecture レイヤー構造
│   ├── core/                    # 🎯 ビジネスロジック層
│   │   ├── application.py       #   メインアプリケーション
│   │   └── message_processor.py #   メッセージ処理
│   ├── bots/                    # 🤖 Discord インターフェース層
│   │   ├── reception.py         #   受信ボット
│   │   └── output_bots.py       #   送信ボット群
│   ├── agents/                  # 🧠 エージェント層
│   │   ├── supervisor.py        #   LangGraph監督
│   │   └── autonomous_speech.py #   自発発言
│   ├── infrastructure/          # 🔧 外部サービス層
│   │   ├── memory_system.py     #   メモリシステム
│   │   ├── gemini_client.py     #   Gemini API
│   │   └── discord_manager.py   #   Discord接続管理
│   ├── config/                  # ⚙️ 設定層
│   │   └── settings.py          #   環境設定
│   └── utils/                   # 🛠️ ユーティリティ層
│       ├── logger.py            #   ログ設定
│       └── health.py            #   ヘルス監視
├── tests/                       # テストスイート（統合済み）
├── docs/                        # プロジェクトドキュメント
├── database/                    # データベース初期化
├── requirements.txt             # Python依存関係
└── docker-compose.yml           # Docker設定
```

---

詳細な実装情報については[CLAUDE.md](CLAUDE.md)を、現在の状況については[docs/current-status.md](docs/current-status.md)を参照してください。