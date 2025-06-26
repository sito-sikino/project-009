# CLAUDE.md - Project-009 Discord マルチエージェントシステム

## 🚀 プロジェクト概要

### **システム仕様**
Discord上で3つのAIエージェント（SPECTRA・LYNQ・PAZ）が協調動作するマルチエージェントシステム。Clean ArchitectureとFail-fast原則により設計され、統合受信・個別送信型アーキテクチャを採用。

**現在のバージョン**: v0.3.0（長期記憶システム統合完了・本番稼働中）

### **プロジェクト固有コマンド集**
```bash
# システム運用（最重要）
alias start="python main.py"
alias health="curl localhost:8000/health && tail -f logs/discord_agent.log"
alias stop="pkill -f 'python main.py'"

# TDD開発サイクル
alias red="python -m pytest tests/ -x --tb=short -q"
alias green="python -m pytest tests/ -v --tb=short"
alias refactor="python -m pytest tests/ --cov=src/ --cov-report=term-missing"

# 品質チェック
alias lint="flake8 src/ tests/"
alias type="mypy src/"
alias security="bandit -r src/"

# Git自動化
alias commit-auto="git add -A && git commit -m \"$(git diff --cached --name-only | head -5 | xargs echo)\""
alias push-pr="git push origin $(git branch --show-current) && gh pr create --draft"

# デバッグ・監視
alias errors="tail -100 logs/discord_agent.log | grep -E '(ERROR|CRITICAL|FAIL)'"
alias speech="tail -100 logs/discord_agent.log | grep '自発発言'"
alias memory="redis-cli info memory && psql $POSTGRESQL_URL -c 'SELECT COUNT(*) FROM unified_memories;'"
```

### **TDD × MCP 必須ワークフロー**

#### **1. 情報収集フェーズ（必須）**
```bash
# 新機能実装前の必須調査
mcp__context7__resolve-library-id "discord.py"
mcp__context7__get-library-docs "/rapptz/discord.py" --topic "interactions"
mcp__brave-search__brave_web_search "discord.py 2025 best practices async"

# エラー調査・解決時
mcp__brave-search__brave_web_search "[specific error message] python solution"
mcp__context7__get-library-docs "/python/cpython" --topic "asyncio"
```

#### **2. TDD実装サイクル（自動実行）**
```bash
# Claude Codeが自動判断・実行するワークフロー
# ユーザー: "認証システムを実装してください"
# → Claude Code: 自動TDDサイクル実行

# Phase 1: MCP調査（自動）
# → context7 + brave_search で最新技術情報収集

# Phase 2: RED（自動）
# → 失敗するテストを自動作成
red  

# Phase 3: GREEN（自動）  
# → テストを通す最小実装を自動生成
green

# Phase 4: REFACTOR（自動）
# → 品質チェック、カバレッジ80%以上確認
refactor && lint && type && security
```

### **マルチモーダル活用パターン**
- **スクリーンショット**: `⌘⇧4` → `⌘V` でエラー画面・UI分析
- **デザインモック**: ドラッグ&ドロップでUI実装指示
- **ログファイル**: `tail -f logs/app.log | head -50` で大量データ分析
- **図表分析**: パフォーマンスグラフ・アーキテクチャ図の視覚的レビュー

### **並行処理戦略（複数Claude活用）**
```bash
# Git worktree で並行開発
git worktree add ../project-009-feature feature/new-agent
# → メインClaude: レビュー専任、サブClaude: 実装専任

# 役割分担パターン
# Claude A: 実装・コーディング担当
# Claude B: テスト作成・品質確認担当
# Claude C: アーキテクチャ・設計レビュー担当
```

### **アーキテクチャ特徴**
- **Clean Architecture**: 依存関係逆転、責務分離
- **Fail-fast原則**: エラー隠蔽禁止、即座停止
- **統合受信・個別送信**: 単一受信Bot、3つの専用送信Bot
- **完全設定管理**: settings.py完全中央化、ハードコード禁止

### **🤖 エージェント特性**
- **SPECTRA** 🔵: 統括進行、プロジェクト管理
  - **個性**: 冷静だが積極的、親しみやすい女性口調
  - **口調**: 「〜しよう」「〜してみる？」「〜だと思う」
  
- **LYNQ** 🔴: 技術分析、論理的解決
  - **個性**: 端的で論理重視、女性的だが感情控えめ
  - **口調**: 「〜を確認すると」「〜という構造」「〜が効率的」
  
- **PAZ** 🟡: 創造発想、アイデア展開
  - **個性**: 冷静で平和的、親しみやすい創造重視
  - **口調**: 「〜かもしれない」「〜してみない？」「〜だよね」

### **📁 重要ファイル構造**
```
src/
├── core/           # ビジネスロジック (application.py, message_processor.py)
├── agents/         # エージェント (supervisor.py, autonomous_speech.py)
├── bots/           # Discord接続 (reception.py, output_bots.py)
├── infrastructure/ # 外部サービス (memory_system.py, gemini_client.py)
└── config/         # 設定 (settings.py)

重要ログ: logs/discord_agent.log（統合ログファイル）
```

## ⚙️ 技術仕様・環境設定

### **必須環境変数**
```bash
# Discord統合（必須）
DISCORD_RECEPTION_TOKEN=<reception_bot_token>
DISCORD_SPECTRA_TOKEN=<spectra_bot_token>  
DISCORD_LYNQ_TOKEN=<lynq_bot_token>
DISCORD_PAZ_TOKEN=<paz_bot_token>
DISCORD_SPECTRA_BOT_ID=<spectra_bot_id>
DISCORD_LYNQ_BOT_ID=<lynq_bot_id>
DISCORD_PAZ_BOT_ID=<paz_bot_id>
COMMAND_CENTER_CHANNEL_ID=<channel_id>
LOUNGE_CHANNEL_ID=<channel_id>
DEVELOPMENT_CHANNEL_ID=<channel_id>
CREATION_CHANNEL_ID=<channel_id>

# AI統合（必須）
GEMINI_API_KEY=<google_gemini_api_key>

# パフォーマンス監視（必須）
HOT_MEMORY_TARGET_MS=<milliseconds>
COLD_MEMORY_TARGET_MS=<milliseconds>
EMBEDDING_TARGET_MS=<milliseconds>
ERROR_RATE_THRESHOLD=<float>
CIRCUIT_BREAKER_FAILURE_THRESHOLD=<int>
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=<int>

# データベース（オプション）
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/discord_agents

# システム設定（オプション）
ENVIRONMENT=production  # development/test/production
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8000
APP_VERSION=v0.3.0

# 長期記憶システム（v0.3.0実装済み・デフォルト有効）
LONG_TERM_MEMORY_ENABLED=true
VECTOR_SEARCH_ENABLED=true
DAILY_REPORT_ENABLED=true
```

### **システム要件**
- **Python**: 3.9以上
- **データベース**: Redis 7.0+, PostgreSQL 14+ with pgvector
- **ハードウェア**: 2GB+ RAM, 2+ CPU cores
- **依存関係**: discord.py, langgraph, langchain, datasketch

### **品質基準**
- **応答時間**: 2秒以内
- **テストカバレッジ**: 80%以上
- **静的解析**: flake8, mypy, bandit全チェック通過
- **セキュリティ**: 脆弱性ゼロ

## 🚀 自動ワークフロー制御（Claude Code一元管理）

### **1. 自動TDDサイクル**
**トリガー**: "実装してください", "機能追加", "修正", "改善"
```
ユーザー要求: "認証システムを実装してください"
↓
Claude Code自動実行:
1. MCP調査 → context7 + brave_search で最新技術収集
2. RED → 失敗テスト自動作成
3. GREEN → 最小実装自動生成  
4. REFACTOR → 品質チェック・カバレッジ80%確認
```

### **2. 自動エラー解決ループ**
**トリガー**: "エラー", "動かない", "失敗", "例外"
```
ユーザー要求: "このエラーを修正してください" 
↓
Claude Code自動実行:
1. エラー分析 → ログ解析、スタックトレース調査
2. MCP調査 → brave_search で解決策収集
3. 仮説検証 → 段階的デバッグ実装
4. 修正実装 → テスト確認・統合検証
```

### **3. 自動デプロイ検証**
**トリガー**: "コミット", "プルリクエスト", "デプロイ"
```
ユーザー要求: "本番環境にデプロイしてください"
↓
Claude Code自動実行:
1. 品質チェック → 全テスト・静的解析・カバレッジ確認
2. 環境検証 → 依存関係・設定・インフラ確認
3. 承認判定 → 100%(即承認) / 80%+(条件付き) / 79%以下(却下)
4. 結果報告 → 詳細レポート・次ステップ提示
```

### **利用例**
```bash
# 従来（削除済み・複雑）: /tdd-cycle, /fix-issue, /debug-loop, /deploy-check
# 新方式（シンプル・自動）: 自然言語で要求
"新しいログイン機能を追加してください"         → 自動TDDサイクル
"PostgreSQL接続エラーが発生しています"        → 自動エラー解決  
"変更をmainブランチにマージしたいです"        → 自動デプロイ検証
```

## 🔧 開発原則・品質基準

### **TDD開発原則（必須）**
1. **RED**: MCPで仕様調査 → 失敗するテストを先に作成
2. **GREEN**: テストを通す最小実装（ハードコーディングOK）
3. **REFACTOR**: MCPでベストプラクティス確認 → 品質向上

### **Fail-fast原則（必須）**
- エラー時即座停止、隠蔽無し
- 戦略的フォールバック6箇所のみ保持（システム継続性）
- データ整合性重視、不完全データでの処理禁止

### **MCP使用義務**
- **context7必須場面**: 新ライブラリ使用、APIアップデート対応
- **brave search必須場面**: エラー解決、パフォーマンス最適化、セキュリティ調査
- **情報鮮度ルール**: 48時間以内の情報使用必須

### **品質チェックリスト**
- [ ] テストファースト実装
- [ ] カバレッジ80%以上
- [ ] MCP情報収集完了（48時間以内）
- [ ] 全テストパス
- [ ] リント・型チェック通過
- [ ] セキュリティチェック通過

## 🎯 システム運用・タスク管理

### **基本システム運用**
```bash
# システム開始・監視
python main.py
curl localhost:8000/health
tail -f logs/discord_agent.log

# タスク管理コマンド
/task commit development "認証システム実装"
/task change creation "アイデアブレスト"

# システム停止
Ctrl+C  # グレースフルシャットダウン
```

### **エージェント運用・個性**
- **チャンネル特化**: command-center（Spectra中心）、development（LynQ中心）、creation（Paz中心）、lounge（均等）
- **自発発言**: 環境別間隔（test: 10秒、production: 5分）
- **タスク管理**: クロスチャンネル移行対応、Redis履歴保存

### **長期記憶システム（v0.3.0実装済み・稼働中）**
- **処理時刻**: 毎日06:00自動実行（3-API統合処理）
- **日報システム**: 記憶化完了次第自動送信
- **検索機能**: PostgreSQL pgvector完全実装
- **機能状態**: 完全実装済み・本番稼働中
- **設定状態**: LONG_TERM_MEMORY_ENABLED=true（デフォルト有効）

## 🚨 緊急時・デバッグ対応

### **緊急停止・復旧**
```bash
# システム緊急停止
pkill -f "python main.py" && docker-compose down

# ヘルス緊急確認  
curl localhost:8000/health && docker ps && redis-cli ping

# ログ緊急分析
tail -100 logs/discord_agent.log | grep -E "(ERROR|CRITICAL|FAIL)"
```

### **よくある問題と対応**
- **Discord接続失敗**: トークン確認、ボット権限確認
- **Redis/PostgreSQL接続**: サービス状態確認、URL設定確認
- **自発発言停止**: ENVIRONMENT設定確認、ログでエラー特定
- **テスト失敗**: MCP最新情報確認、依存関係更新

### **Claude Code自動制御ワークフロー**
Claude Codeが状況を自動判断し、適切なワークフローを実行します：
1. **新機能実装要求** → 自動TDDサイクル実行
2. **エラー・バグ報告** → 自動エラー解決ループ実行  
3. **コミット・デプロイ前** → 自動品質検証実行
4. **MCP情報収集** → 48時間以内最新情報を自動取得

## 📋 重要制約・注意事項

### **現在の制限事項（v0.3.0）**
- Embedding API: 15 RPM（設定値）、Google実制限あり
- Gemini 2.0 Flash: 通常利用（統合分析・進捗差分生成）
- 戦略的フォールバック: 6箇所保持（システム継続性のため）

### **Git & GitHub統合（Claude Code自動実行）**
GitHub連携は以下の条件で自動実行されます：
- **Issue修正要求**: Issue番号指定でTDD修正サイクル自動実行
- **PR作成要求**: 変更内容分析・適切なPR自動作成
- **デプロイ前検証**: 品質基準達成確認・承認判定自動実行

### **画像・UI活用パターン**
- エラー画面のスクリーンショット分析
- デザインモックからの実装指示
- パフォーマンスグラフの視覚的分析
- アーキテクチャ図での設計レビュー

---

## 🤖 **Claude Code自動制御仕様（詳細）**

### **1. 自動TDDサイクル（新機能・修正実装）**

**自動トリガー条件**:
- 「新機能実装」「機能追加」要求
- 「バグ修正」「Issue解決」要求
- 「改善」「リファクタリング」要求

**自動実行フロー**:
```
Phase 1: MCP情報収集（必須・自動）
├─ 関連ライブラリ最新ドキュメント (context7)
├─ ベストプラクティス調査 (brave_search) 
├─ 既存コード分析 (grep/glob)
└─ 48時間以内情報確認

Phase 2: TDD Red（自動テスト作成）
├─ 要件分析・テスト仕様設計
├─ 失敗テスト実装（基本・エッジ・統合）
├─ pytest実行・失敗確認
└─ Red段階完了確認

Phase 3: TDD Green（自動最小実装）
├─ MCPベストプラクティス適用
├─ テスト通過最小実装
├─ pytest実行・成功確認  
└─ Green段階完了確認

Phase 4: TDD Refactor（自動品質向上）
├─ flake8・mypy・bandit実行
├─ カバレッジ80%以上確認
├─ 全テスト・統合テスト実行
└─ 品質基準達成確認
```

### **2. 自動エラー解決ループ（デバッグ・修正）**

**自動トリガー条件**:
- エラーメッセージ・例外報告
- 「動かない」「失敗する」報告
- ログエラー・システム異常報告

**自動実行フロー**:
```
Phase 1: エラー分析（自動診断）
├─ ログ分析・エラー分類
├─ システム状態確認（ヘルス・プロセス・リソース）
├─ MCP最新解決策調査
└─ エラー種別特定（接続/メモリ/データ/依存関係）

Phase 2: 仮説検証（自動確認）
├─ 環境・設定・依存関係確認
├─ 外部サービス接続確認
├─ リソース・パフォーマンス確認
└─ 根本原因特定

Phase 3: 修正実装（自動修正）
├─ MCPベストプラクティス適用
├─ デバッグ強化実装
├─ エラーハンドリング改善
└─ 継続監視設定

Phase 4: 検証・記録（自動確認）
├─ 修正後動作確認
├─ デバッグレポート生成
├─ ナレッジ蓄積・共有
└─ 再発防止策実装
```

### **3. 自動デプロイ前検証（品質保証）**

**自動トリガー条件**:
- git commit前
- PR作成前  
- 本番デプロイ前

**自動実行フロー**:
```
Phase 1: コード品質確認（自動）
├─ 静的解析（flake8・mypy・bandit・radon）
├─ 依存関係セキュリティ監査
├─ ライセンス・脆弱性チェック
└─ 品質基準達成確認

Phase 2: 全テスト実行（自動）
├─ ユニット・統合・E2Eテスト
├─ カバレッジ80%以上確認
├─ パフォーマンステスト実行
└─ テスト基準達成確認

Phase 3: 環境・接続確認（自動）
├─ 本番環境設定検証
├─ 外部サービス疎通確認  
├─ リソース・負荷テスト
└─ 接続基準達成確認

Phase 4: デプロイ判定（自動）
├─ 総合結果評価（100%/80%以上/<80%）
├─ デプロイレポート自動生成
├─ 承認・条件付き・却下判定
└─ 次ステップ提示
```

### **4. 品質基準（自動評価基準）**

```
必須基準（Fail-fast）:
├─ テストカバレッジ ≥ 80%
├─ 静的解析 = 全チェック通過
├─ セキュリティ = 脆弱性ゼロ
├─ パフォーマンス = 応答<2秒・メモリ<1.5GB
└─ 外部サービス = 全接続確認

MCP活用基準:
├─ 48時間以内情報収集必須
├─ ベストプラクティス適用必須
├─ 技術検証・ライブラリ確認必須
└─ 根拠ある解決策選択必須

自動継続基準:
├─ 各段階で品質チェック実行
├─ 基準未達成時は即座停止・修正
├─ エラー時は自動回復・再試行
└─ 全工程完了まで自動継続
```

---

## 📖 詳細情報リンク

- **運用・トラブルシューティング**: `docs/運用ガイド.md`
- **要件リファレンス**: `docs/受入基準.md`
- **将来実装計画**: `docs/実装計画.md`

**重要**: Claude Codeは上記の自動制御仕様に基づいて動作します。手動カスタムコマンドは不要です。