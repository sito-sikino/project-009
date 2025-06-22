# テストガイド - Discord Multi-Agent System

## 🎯 テスト概要

このガイドは、Discord Multi-Agent System v0.2.0+の包括的なテスト手順を提供します。

## 🔧 テスト前セットアップ

### 環境チェック
```bash
# 1. すべての環境変数を確認
grep -E "DISCORD_|GEMINI_|REDIS_|POSTGRESQL_" .env

# 2. データベース接続をチェック
redis-cli ping
psql -h localhost -U discord_agent_prod -d discord_agent_prod -c "SELECT 1;"

# 3. システム開始
python main.py
```

### システム初期化確認
- [ ] 4つのDiscordクライアントがすべて正常に接続
- [ ] メモリシステムが初期化（Redis必須、PostgreSQL任意）
- [ ] ヘルスAPIが応答: `curl localhost:8000/health`
- [ ] ログに「🚀 All components initialized successfully」が表示

## 🤖 自動テスト

### 1. システムヘルスチェック
```bash
# ヘルスエンドポイント確認
curl -s localhost:8000/health | grep -q "healthy\|unhealthy"
echo "Health check: $?"

# ログ確認（重要エラーなし）
! grep -q "ERROR.*critical\|FATAL" logs/discord_agent.log
echo "Critical error check: $?"

# プロセス確認
pgrep -f "python main.py" > /dev/null
echo "Process running: $?"
```

### 2. コンポーネント状況チェック
```bash
# 自発発言アクティビティをチェック
grep -c "自発発言実行" logs/discord_agent.log

# エージェントローテーションをチェック
grep "自発発言実行" logs/discord_agent.log | tail -5 | grep -o ": [a-z]*" | sort | uniq -c

# メッセージ処理をチェック
grep -c "Message processed successfully" logs/discord_agent.log
```

## 🎮 手動テスト

### 3. Discord統合テスト

#### **基本応答テスト**
Discordチャンネルでテスト:

**技術的質問（LynQを期待）**
```
"サーバーのパフォーマンスを改善する方法を教えて"
```

**創作的質問（Pazを期待）**  
```
"新しいUI デザインのアイデアを聞かせて"
```

**管理的質問（Spectraを期待）**
```
"今日のミーティングの進行をお願いします"
```

#### **自発発言テスト**
- [ ] 10秒（テストモード）または5分（本番モード）待機
- [ ] 自発メッセージが表示されることを確認
- [ ] 異なるエージェントがローテーションすることを確認（連続する同一エージェントメッセージなし）
- [ ] 適切なチャンネル使用を確認

#### **タスクコマンドテスト**
```
# タスク作成をテスト
/task commit development "認証システム実装"

# 期待値: command-centerでSpectraからの成功メッセージ
# 確認: 自発発言がdevelopmentチャンネルに切り替わる

# タスク変更をテスト（同一チャンネル）
/task change development "API設計"

# 期待値: タスク更新確認

# タスク変更をテスト（異なるチャンネル） 
/task change creation "アイデアブレスト"

# 期待値: チャンネル移行確認
# 確認: 自発発言がcreationチャンネルに切り替わる
```

### 4. エラーハンドリングテスト

#### **適切な劣化**
- [ ] Redisを一時的に切断 - システムは警告とともに継続
- [ ] 無効なコマンド構文 - 適切なエラーメッセージ
- [ ] レート制限シナリオ - 適切なバックオフ動作

#### **復旧テスト**
- [ ] システム再起動 - クリーンな起動/シャットダウン
- [ ] ネットワーク中断 - 再接続処理
- [ ] メモリ圧迫 - 適切なパフォーマンス劣化

## 📊 パフォーマンステスト

### 5. 負荷テスト
```bash
# 応答時間テスト（<2秒であるべき）
time curl -s localhost:8000/health

# メモリ使用量監視
free -h
ps aux | grep "python main.py"

# ログファイル増加（通常: 約500KB/日）
ls -lh logs/discord_agent.log
```

### 6. 同時ユーザーシミュレーション
複数のDiscordメッセージを同時送信:
- [ ] 応答時間が<3秒を維持
- [ ] メッセージ損失なし
- [ ] エージェント選択が正確性を維持
- [ ] システムクラッシュなし

## 🔍 テスト結果評価

### 成功基準
- [ ] **システム起動**: すべてのコンポーネントがエラーなしで初期化
- [ ] **エージェント選択**: 役割適切な応答で>90%精度
- [ ] **自発発言**: 適切なローテーションで定期間隔
- [ ] **タスクコマンド**: チャンネル移行を含むすべての形式が動作
- [ ] **パフォーマンス**: 通常メッセージで<2秒応答時間
- [ ] **安定性**: テスト期間中に重要エラーなし

### エラー監視
```bash
# 重要な問題をチェック
grep -E "ERROR|FATAL|❌" logs/discord_agent.log | grep -v "PostgreSQL.*connection"

# 許容される警告:
# - "PyNaCl is not installed" (音声は不要)
# - PostgreSQL接続エラー (cold memoryはv0.2.0で無効化)
```

## 🚨 既知の問題・回避策

### 期待される動作（バグではない）
- **PostgreSQLエラー**: v0.2.0でcold memory無効化、Redisのみ動作
- **Embedding レート制限**: 15 RPM制限によりメモリ操作で遅延の可能性
- **00:00システム休息**: 未実装、システムは通常動作を継続

### よくあるテスト失敗
1. **自発発言なし**: ENVIRONMENT変数とティック間隔を確認
2. **エージェント選択問題**: Gemini APIキーとクォータを確認
3. **タスクコマンドエラー**: コマンド形式とチャンネル名を確認
4. **接続問題**: Discord botトークンと権限を確認

## 📋 テスト実行ワークフロー

### クイックテスト（5分）
1. システム開始、初期化確認
2. 各タイプのメッセージを1つ送信（技術的/創作的/管理的）
3. 1回の自発発言サイクルを待機
4. 1つのタスクコマンドをテスト
5. エラーのログを確認

### 包括的テスト（30分）
1. すべての自動テストを実行
2. 完全な手動テストスイートを実行
3. エラーハンドリングテストを実行
4. パフォーマンスメトリクスを監視
5. 結果を文書化

### 本番検証（2時間）
1. 拡張ランタイムテスト
2. マルチユーザーシミュレーション
3. 完全ワークフローテスト（STANDBY→ACTIVE→FREE）
4. 高メッセージ量でのストレステスト
5. 復旧テスト

## 📈 テストレポート

### テスト結果テンプレート
```
# テスト結果 - [日付]
## 環境: [test/production]
## バージョン: v0.2.0
## 期間: [分]

### 自動テスト: [PASS/FAIL]
- システムヘルス: [PASS/FAIL]
- コンポーネント状況: [PASS/FAIL]

### 手動テスト: [PASS/FAIL]  
- エージェント選択: [%] 精度
- 自発発言: [PASS/FAIL]
- タスクコマンド: [PASS/FAIL]

### パフォーマンス:
- 平均応答時間: [秒]
- メモリ使用量: [GB]
- エラー数: [数]

### 発見された問題: [リスト]
### 推奨事項: [リスト]
```

---

**システム運用については`DEPLOYMENT_GUIDE.md`を参照**  
**現在のシステム状況については`CURRENT_STATUS.md`を参照**