# 📚 Discord Multi-Agent System Documentation

**統合受信・個別送信型アーキテクチャ** 総合ドキュメンテーション

## 📋 Table of Contents

### 🎯 Core Documentation
- [**CLAUDE.md**](../CLAUDE.md) - プロジェクト主要ガイダンス（開発・TDD・アーキテクチャ）
- [**ACCEPTANCE_CRITERIA.md**](../ACCEPTANCE_CRITERIA.md) - 18項目の受け入れ基準

### 🚀 Deployment & Operations
- [**PRODUCTION_DEPLOYMENT_GUIDE.md**](../PRODUCTION_DEPLOYMENT_GUIDE.md) - 本番環境デプロイガイド
- [**PRODUCTION_IMPLEMENTATION_SUMMARY.md**](PRODUCTION_IMPLEMENTATION_SUMMARY.md) - 本番環境実装完了レポート

### 🧠 Memory System
- [**MEMORY_SYSTEM_IMPLEMENTATION_SUMMARY.md**](MEMORY_SYSTEM_IMPLEMENTATION_SUMMARY.md) - Memory System実装概要
- [**TEXT_EMBEDDING_004_IMPLEMENTATION_GUIDE.md**](TEXT_EMBEDDING_004_IMPLEMENTATION_GUIDE.md) - Google Embedding実装ガイド

### 🔍 Implementation & Verification
- [**IMPLEMENTATION_VERIFICATION_REPORT.md**](IMPLEMENTATION_VERIFICATION_REPORT.md) - 実装検証レポート

### 🧪 Testing & TDD
- [**TDD_IMPLEMENTATION_SUMMARY.md**](TDD_IMPLEMENTATION_SUMMARY.md) - TDD実装サマリー
- [**TDD_TEST_STRATEGY.md**](TDD_TEST_STRATEGY.md) - TDD戦略・手法
- [**TEST_EXAMPLES.md**](TEST_EXAMPLES.md) - テスト実装例
- [**TEST_EXECUTION_GUIDE.md**](TEST_EXECUTION_GUIDE.md) - テスト実行ガイド

## 🏗️ システム概要

### アーキテクチャ
```
Reception Bot (1) → LangGraph Supervisor → Output Bots (3)
     ↓                     ↓                      ↓
Priority Queue     Agent Selection       Individual Transmission
                       ↓
              Memory System (Redis+PostgreSQL)
```

### 主要コンポーネント
- **Discord Clients**: 4ボット（1受信 + 3送信）
- **LangGraph Supervisor**: エージェント選択・応答生成
- **Memory System**: Redis Hot Memory + PostgreSQL Cold Memory
- **Monitoring**: Health API + Prometheus メトリクス

## 📊 Implementation Status

| Component | Status | Progress |
|-----------|--------|----------|
| Core Discord Architecture | ✅ Complete | 100% |
| LangGraph Supervisor | ✅ Complete | 100% |
| Memory System | ✅ Complete | 100% |
| Production Features | ✅ Complete | 100% |
| AI Behavior Systems | ⚠️ Partial | 60% |
| **Overall** | **✅ Production Ready** | **85%** |

## 🎯 Quick Start

### Development
```bash
# 1. Environment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# Edit .env with your tokens

# 3. Run tests
python -m pytest tests/ -v

# 4. Start development
python main.py
```

### Production Deployment
```bash
# 1. Production configuration
cp .env.production .env
# Edit .env with production values

# 2. Deploy with Docker
docker-compose --profile production up -d

# 3. Health check
curl http://localhost:8000/health
```

## 📞 Quick Reference

### Health & Monitoring
- **Health Check**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`
- **Status**: `http://localhost:8000/status`

### Key Performance Targets
- **Hot Memory**: < 100ms
- **Cold Memory**: < 3000ms
- **Response Time**: 95% < 9 seconds
- **Agent Accuracy**: > 95%

## 🔗 External Links

### APIs & Services
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Google Gemini API](https://ai.google.dev/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

### Development Tools
- [Prometheus Metrics](http://localhost:8000/metrics)
- [pgAdmin Interface](http://localhost:8080) (development)
- [Redis Commander](http://localhost:8081) (development)

---

**📝 Note**: このドキュメントは自動更新されます。最新の実装状況は各個別ドキュメントを参照してください。

**🚀 Production Ready**: 本システムは本番環境デプロイ準備完了済みです。