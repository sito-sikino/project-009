# 📋 Production Deployment Guide

**Discord Multi-Agent System** 本番環境デプロイメントガイド

## 🚀 デプロイメント概要

本システムは**統合受信・個別送信型アーキテクチャ**を採用し、以下の特徴を持つ本番レディなDiscord Multi-Agent Systemです：

- **4つのDiscord Bot**: 1受信 + 3送信（Spectra/LynQ/Paz）
- **LangGraph Supervisor**: エージェント選択・応答生成
- **Dual Memory System**: Redis Hot Memory + PostgreSQL Cold Memory
- **Google text-embedding-004**: セマンティック検索機能
- **Production Monitoring**: Prometheus メトリクス + ヘルスチェック

## 📋 Prerequisites

### 1. Discord Bot Setup
4つの個別のDiscord Botを作成する必要があります：

```
DISCORD_RECEPTION_TOKEN - Reception Bot（メッセージ受信専用）
DISCORD_SPECTRA_TOKEN  - Spectra Bot（画像生成・創作支援）
DISCORD_LYNQ_TOKEN     - LynQ Bot（技術サポート・開発支援）
DISCORD_PAZ_TOKEN      - Paz Bot（総合サポート・雑談）
```

### 2. API Keys
- **Gemini API Key**: Google AI Studio から取得
- **Discord Server ID**: 対象サーバーのID

### 3. Infrastructure Requirements

#### Minimum Production Requirements
- **CPU**: 2 vCPUs
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: 1Gbps

#### Recommended Production Setup
- **CPU**: 4 vCPUs
- **RAM**: 8GB  
- **Storage**: 50GB SSD
- **Network**: 10Gbps

## 🔧 Quick Start (Docker Compose)

### 1. Environment Setup

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd project-009

# 2. 本番環境設定ファイル作成
cp .env.production .env

# 3. 環境変数編集
nano .env
```

### 2. 必須環境変数設定

```bash
# Discord Configuration
DISCORD_RECEPTION_TOKEN=your_reception_bot_token
DISCORD_SPECTRA_TOKEN=your_spectra_bot_token
DISCORD_LYNQ_TOKEN=your_lynq_bot_token
DISCORD_PAZ_TOKEN=your_paz_bot_token
TARGET_GUILD_ID=your_server_id

# AI Service
GEMINI_API_KEY=your_gemini_api_key

# Database Security (REQUIRED)
POSTGRES_PASSWORD=your_secure_password_here
PGADMIN_DEFAULT_PASSWORD=your_pgadmin_password
```

### 3. Production Deployment

```bash
# 本番環境起動
docker-compose --profile production up -d

# ログ確認
docker-compose logs -f discord-agent

# ヘルスチェック確認
curl http://localhost:8000/health
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

| Endpoint | Purpose | Description |
|----------|---------|-------------|
| `/health` | Overall health | 全体的なシステム状態 |
| `/health/live` | Liveness probe | Kubernetes liveness用 |
| `/health/ready` | Readiness probe | Kubernetes readiness用 |
| `/metrics` | Prometheus metrics | Prometheusメトリクス |
| `/status` | Detailed status | 詳細ステータス情報 |

### Performance Thresholds

| Component | Target | Alert Threshold |
|-----------|--------|-----------------|
| Hot Memory | < 100ms | > 150ms |
| Cold Memory | < 3000ms | > 5000ms |
| Embedding | < 2000ms | > 3000ms |
| Error Rate | < 5% | > 10% |

### Example Health Check

```bash
# システム全体ヘルスチェック
curl -s http://localhost:8000/health | jq

# 詳細ステータス
curl -s http://localhost:8000/status | jq

# Prometheusメトリクス
curl http://localhost:8000/metrics
```

## 🛡️ Security Configuration

### 1. Database Security

```bash
# 強力なパスワード生成
openssl rand -base64 32

# 環境変数設定
export POSTGRES_PASSWORD="generated_strong_password"
```

### 2. Network Security

```bash
# Firewall設定例（UFW）
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # Health checks
sudo ufw deny 5432   # PostgreSQL (internal only)
sudo ufw deny 6379   # Redis (internal only)
```

### 3. Container Security

```yaml
# docker-compose.yml セキュリティ強化
services:
  discord-agent:
    user: "1000:1000"  # 非rootユーザー
    read_only: true     # 読み取り専用ファイルシステム
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## 📈 Production Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  discord-agent:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Database Scaling

```yaml
# PostgreSQL 本番設定
postgres:
  environment:
    - POSTGRES_SHARED_BUFFERS=1GB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=3GB
    - POSTGRES_MAINTENANCE_WORK_MEM=256MB
    - POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Memory System Connection Failed
```bash
# Redis接続確認
docker exec -it discord-agent-redis redis-cli ping

# PostgreSQL接続確認  
docker exec -it discord-agent-postgres pg_isready -U discord_agent
```

#### 2. Discord Bot Not Connecting
```bash
# Discord token確認
docker-compose exec discord-agent python -c "
import os
print('Reception Token:', 'OK' if os.getenv('DISCORD_RECEPTION_TOKEN') else 'MISSING')
print('Gemini API Key:', 'OK' if os.getenv('GEMINI_API_KEY') else 'MISSING')
"
```

#### 3. High Memory Usage
```bash
# メモリ使用量確認
docker stats discord-agent-app

# 詳細メトリクス
curl -s http://localhost:8000/status | jq '.system.memory_usage'
```

### Log Analysis

```bash
# アプリケーションログ
docker-compose logs -f discord-agent

# エラーログのみ
docker-compose logs discord-agent 2>&1 | grep ERROR

# パフォーマンスログ
docker-compose logs discord-agent 2>&1 | grep "processed successfully"
```

## 📦 Backup & Recovery

### Database Backup

```bash
# PostgreSQL バックアップ
docker exec -t discord-agent-postgres pg_dump -U discord_agent discord_agent > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis バックアップ
docker exec discord-agent-redis redis-cli BGSAVE
docker cp discord-agent-redis:/data/dump.rdb redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Recovery

```bash
# PostgreSQL リストア
docker exec -i discord-agent-postgres psql -U discord_agent discord_agent < backup_file.sql

# Redis リストア
docker cp redis_backup.rdb discord-agent-redis:/data/dump.rdb
docker-compose restart redis
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        run: |
          ssh ${{ secrets.PROD_HOST }} "
            cd /opt/discord-agent &&
            git pull origin main &&
            docker-compose --profile production up -d --build
          "
      
      - name: Health check
        run: |
          sleep 60
          curl -f http://${{ secrets.PROD_HOST }}:8000/health/ready
```

## 📊 Performance Monitoring

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'discord-agent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

主要メトリクス:
- `discord_agent_messages_total` - 処理メッセージ数
- `discord_agent_response_time_seconds` - 応答時間
- `discord_agent_memory_operations_total` - メモリ操作数
- `discord_agent_system_errors_total` - システムエラー数

## 🎯 Production Checklist

### Pre-deployment
- [ ] 全ての環境変数が設定済み
- [ ] Discord Botの権限が適切に設定
- [ ] データベースパスワードが強力
- [ ] SSL証明書が設定済み（必要に応じて）
- [ ] ファイアウォールが適切に設定
- [ ] バックアップ戦略が定義済み

### Post-deployment
- [ ] ヘルスチェックが通過
- [ ] 全ディスコードボットがオンライン
- [ ] メトリクスが収集されている
- [ ] ログが適切に出力されている
- [ ] パフォーマンス閾値が満たされている
- [ ] 監視アラートが設定済み

## 🆘 Support & Maintenance

### Regular Maintenance

```bash
# 週次メンテナンス
docker system prune -f           # 不要コンテナ削除
docker volume prune -f           # 不要ボリューム削除
docker-compose pull              # イメージ更新
docker-compose up -d             # サービス再起動
```

### Performance Tuning

```bash
# メモリ使用量最適化
echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf

# ネットワーク最適化
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
```

---

## 📞 Emergency Contacts

本番環境で問題が発生した場合：

1. **即座にヘルスチェック確認**: `curl http://localhost:8000/health`
2. **ログ確認**: `docker-compose logs -f discord-agent`
3. **システム再起動**: `docker-compose restart discord-agent`
4. **完全リセット**: `docker-compose down && docker-compose --profile production up -d`

**重要**: 本番環境での変更は必ずステージング環境でテスト後に実施してください。