# デプロイガイド - Discord Multi-Agent System

## 🚀 クイックスタート

### 前提条件
```bash
# システム要件
- Python 3.9+
- Redis 7.0+
- PostgreSQL 14+ with pgvector
- 2GB+ RAM, 2+ CPU cores
```

### 1. 環境セットアップ
```bash
# クローンとセットアップ
cd project-009/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 設定
`.env`ファイルを作成:
```bash
# Discord Bot Tokens
DISCORD_RECEPTION_TOKEN=your_reception_token
DISCORD_SPECTRA_TOKEN=your_spectra_token
DISCORD_LYNQ_TOKEN=your_lynq_token
DISCORD_PAZ_TOKEN=your_paz_token

# AI Integration
GEMINI_API_KEY=your_gemini_api_key

# Database
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/db

# Channel IDs
COMMAND_CENTER_CHANNEL_ID=YOUR_COMMAND_CENTER_CHANNEL_ID
LOUNGE_CHANNEL_ID=YOUR_LOUNGE_CHANNEL_ID
DEVELOPMENT_CHANNEL_ID=YOUR_DEVELOPMENT_CHANNEL_ID
CREATION_CHANNEL_ID=YOUR_CREATION_CHANNEL_ID

# System Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8000
```

### 3. システム開始
```bash
# ログ付きで開始
python main.py

# またはバックグラウンドプロセス
nohup python main.py > /dev/null 2>&1 &
```

## 🔧 システム運用

### ヘルス監視
```bash
# システムヘルスをチェック
curl http://localhost:8000/health

# メトリクスを表示
curl http://localhost:8000/metrics

# ログをチェック
tail -f logs/discord_agent.log
```

### システムコマンド
```bash
# 適切なシャットダウン
Ctrl+C  # または SIGTERM

# プロセスをチェック
ps aux | grep "python main.py"

# 必要に応じて強制終了
pkill -f "python main.py"
```

### タスク管理コマンド
```bash
# 新しいタスクを開始
/task commit development "認証システム実装"

# タスクまたはチャンネルを変更
/task change creation "アイデアブレスト"
```

## 🗄️ データベースセットアップ

### Redisセットアップ
```bash
# Redisをインストール
sudo apt install redis-server

# Redisを開始
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 検証
redis-cli ping
```

### PostgreSQLセットアップ
```bash
# PostgreSQL + pgvectorをインストール
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql

-- データベースとユーザーを作成
CREATE DATABASE discord_agent_prod;
CREATE USER discord_agent_prod WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE discord_agent_prod TO discord_agent_prod;

-- pgvector拡張をインストール
\c discord_agent_prod
CREATE EXTENSION vector;
```

## 🔍 トラブルシューティング

### よくある問題

#### **Discord接続失敗**
```bash
# .envでトークンをチェック
grep DISCORD .env

# ボット権限を確認
# - Read Messages
# - Send Messages  
# - Read Message History
```

#### **メモリシステムの問題**
```bash
# Redisをチェック
redis-cli ping

# PostgreSQLをチェック
psql -h localhost -U discord_agent_prod -d discord_agent_prod -c "SELECT 1;"

# 既知：PostgreSQL検索は一時無効化（v0.2.0）
```

#### **自発発言が動作しない**
```bash
# ログで発言イベントをチェック
grep "自発発言" logs/discord_agent.log

# 環境を確認
echo $ENVIRONMENT  # 'test' または 'production' であるべき

# テストモード: 10秒間隔、100%確率
# 本番モード: 5分間隔、33%確率
```

#### **タスクコマンドが失敗する**
```bash
# コマンド形式をチェック
/task commit development "task description"
/task change creation "new task"

# ログをチェック
grep "Task command" logs/discord_agent.log
```

### エラーパターン
```bash
# 重要エラーは表示されるべきではない
grep "ERROR\|❌" logs/discord_agent.log

# 許容される警告:
# - "PyNaCl is not installed" (音声は不要)
# - PostgreSQL接続エラー (cold memoryはv0.2.0で無効化)
```

## 📈 パフォーマンス監視

### 主要指標
- **応答時間**: <2秒であるべき
- **メモリ使用量**: 通常動作で約1.5GB
- **CPU使用率**: 低、メッセージ処理中にスパイク
- **ログファイルサイズ**: 通常動作で約500KB/日

### パフォーマンスコマンド
```bash
# システムリソース
htop
df -h
free -h

# アプリケーションパフォーマンス
curl http://localhost:8000/status

# ログ分析
grep "processed successfully" logs/discord_agent.log | tail -10
```

## 🔄 メンテナンス

### 日次運用
- エラーがないか`logs/discord_agent.log`を監視
- ヘルスエンドポイントをチェック: `curl localhost:8000/health`
- 自発発言が動作していることを確認

### 週次運用
- ディスク容量が気になる場合は古いログをアーカイブ
- システムパフォーマンス指標を確認
- 必要に応じて依存関係を更新

### 月次運用
- メモリクリーンアップのため完全システム再起動
- 古い会話データを確認・アーカイブ
- 必要に応じてドキュメントを更新

## 🚨 本番環境考慮事項

### セキュリティ
- トークンを絶対にリポジトリにコミットしない
- すべての秘密情報に環境変数を使用
- 本番環境でヘルスエンドポイントアクセスを制限
- 異常なAPI使用量を監視

### スケーリング
- 高可用性のためのRedisクラスター
- パフォーマンス向上のためのPostgreSQL読み取りレプリカ
- ロードバランシングでの複数インスタンス展開
- 大規模向けコンテナオーケストレーション（Docker/K8s）

### バックアップ
```bash
# Redisバックアップ
redis-cli BGSAVE

# PostgreSQLバックアップ
pg_dump discord_agent_prod > backup_$(date +%Y%m%d).sql
```

---

**システム状況とバージョンについては`CURRENT_STATUS.md`を参照**  
**テスト手順については`TESTING_GUIDE.md`を参照**