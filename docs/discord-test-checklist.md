# Discord実動テストチェックリスト v0.2.2

## 🚀 **テスト前準備**

### **✅ 環境セットアップ確認**
```bash
# 1. 依存関係インストール確認
pip install -r requirements.txt

# 2. 環境変数設定確認 (.env ファイル)
DISCORD_RECEPTION_TOKEN=<reception_bot_token>
DISCORD_SPECTRA_TOKEN=<spectra_bot_token>  
DISCORD_LYNQ_TOKEN=<lynq_bot_token>
DISCORD_PAZ_TOKEN=<paz_bot_token>
GEMINI_API_KEY=<gemini_api_key>

# チャンネルID (必要に応じて)
COMMAND_CENTER_CHANNEL_ID=<channel_id>
LOUNGE_CHANNEL_ID=<channel_id>
DEVELOPMENT_CHANNEL_ID=<channel_id>
CREATION_CHANNEL_ID=<channel_id>

# システム設定
ENVIRONMENT=test  # テスト用に設定
LOG_LEVEL=INFO
```

### **✅ システム起動テスト**
```bash
# 1. Clean Architecture コンパイルチェック
python3 -m py_compile main.py

# 2. システム起動
python main.py

# 期待される起動ログ:
# 🚀 Starting Discord Multi-Agent System v0.2.2
# 🏗️ Architecture: Clean Architecture + 統合受信・個別送信型
# 🔧 Initializing System Container...
# ✅ System Container initialized with dependency injection
# 🎯 Creating Application Service...
# ✅ Discord Application Service created
# 🔄 Setting up System Lifecycle Manager...
# ✅ System Lifecycle Manager ready
# ▶️ Starting main application loop...
```

---

## 🧪 **Discord機能テストチェックリスト**

### **Phase 1: 基本接続テスト (5分)**

#### **1.1 Bot接続確認**
- [ ] **Reception Bot**: オンライン状態確認
- [ ] **Spectra Bot** 🔵: オンライン状態確認  
- [ ] **LynQ Bot** 🔴: オンライン状態確認
- [ ] **Paz Bot** 🟡: オンライン状態確認

**テスト方法**: Discordサーバーでボット一覧確認

#### **1.2 基本応答テスト**
- [ ] **任意チャンネルでメッセージ送信**: "こんにちは"
- [ ] **応答確認**: いずれかのボットから返答があること
- [ ] **ログ確認**: `logs/discord_agent.log` で処理ログ確認

---

### **Phase 2: エージェント選択テスト (10分)**

#### **2.1 チャンネル別エージェント優先度**

**🔧 #development チャンネル (LynQ優先)**
- [ ] メッセージ送信: "Pythonの非同期処理について教えて"
- [ ] **期待**: LynQ Bot 🔴 が50%の確率で応答
- [ ] **3回テスト**: LynQの応答頻度確認

**🎨 #creation チャンネル (Paz優先)**  
- [ ] メッセージ送信: "新しいアイデアを考えよう"
- [ ] **期待**: Paz Bot 🟡 が50%の確率で応答
- [ ] **3回テスト**: Pazの応答頻度確認

**🏢 #command-center チャンネル (均等分散)**
- [ ] メッセージ送信: "プロジェクトの進捗確認"
- [ ] **期待**: 3ボット均等に応答
- [ ] **3回テスト**: 分散状況確認

#### **2.2 エージェント連続防止確認**
- [ ] 同じボットが連続応答しないこと確認
- [ ] 前回応答ボットの重み90%削減確認

---

### **Phase 3: タスク管理機能テスト (10分)**

#### **3.1 Task Commit テスト**
```bash
/task commit development "認証システム実装"
```
- [ ] **Spectra応答**: command-centerでタスク登録確認メッセージ
- [ ] **ログ確認**: タスク登録ログ記録

#### **3.2 Task Change テスト**  
```bash
/task change creation "UIデザイン検討"  
```
- [ ] **Spectra応答**: タスク変更確認メッセージ
- [ ] **チャンネル移動**: creationチャンネルへの移動確認

#### **3.3 コマンドエラーハンドリング**
```bash
/task invalid format
```
- [ ] **エラーメッセージ**: 適切な形式説明表示

---

### **Phase 4: 自発発言システムテスト (15分)**

#### **4.1 TEST環境での自発発言 (10秒間隔)**
- [ ] **待機**: システム起動後10秒待機
- [ ] **自発発言確認**: いずれかのボットから自動メッセージ
- [ ] **間隔確認**: 10秒間隔で継続的な自発発言
- [ ] **ローテーション確認**: 異なるボットが順次発言

#### **4.2 フェーズ別動作確認**

**STANDBY期間 (00:00-06:59)**
- [ ] 自発発言停止確認
- [ ] ユーザーメッセージには応答確認

**ACTIVE期間 (07:00-19:59)**  
- [ ] タスクベースチャンネルでの自発発言
- [ ] loungeチャンネル除外確認

**FREE期間 (20:00-23:59)**
- [ ] loungeチャンネル優先の自発発言

---

### **Phase 5: メモリ・履歴システムテスト (10分)**

#### **5.1 会話継続性テスト**
- [ ] メッセージ1: "私の名前はテスターです"
- [ ] メッセージ2: "私の名前を覚えていますか？"
- [ ] **期待**: 前の会話を参照した応答

#### **5.2 チャンネル別記憶確認**
- [ ] 異なるチャンネルでの会話分離確認
- [ ] チャンネル固有の文脈保持確認

---

### **Phase 6: エラーハンドリング・復旧テスト (10分)**

#### **6.1 システム負荷テスト**
- [ ] **同時メッセージ**: 3-5人で同時メッセージ送信
- [ ] **応答確認**: 全メッセージに適切な応答
- [ ] **パフォーマンス**: 2秒以内の応答時間維持

#### **6.2 シャットダウンテスト**
- [ ] **Ctrl+C**: 優雅なシャットダウン確認
- [ ] **終了ログ**: 適切なクリーンアップログ確認
- [ ] **再起動**: 正常な再起動確認

---

## 📊 **テスト結果記録テンプレート**

### **システム基本情報**
- **テスト日時**: ___________
- **テスト環境**: test/production
- **参加者数**: ___人
- **テスト時間**: ___分

### **Phase別結果**
- **Phase 1 基本接続**: ✅ / ❌
- **Phase 2 エージェント選択**: ✅ / ❌  
- **Phase 3 タスク管理**: ✅ / ❌
- **Phase 4 自発発言**: ✅ / ❌
- **Phase 5 メモリシステム**: ✅ / ❌
- **Phase 6 エラーハンドリング**: ✅ / ❌

### **発見した問題**
1. ____________________
2. ____________________
3. ____________________

### **パフォーマンス**
- **平均応答時間**: ____秒
- **同時接続ユーザー**: ____人
- **エラー発生回数**: ____回

---

## 🚨 **トラブルシューティング**

### **よくある問題と解決方法**

#### **1. ボットがオンラインにならない**
```bash
# 解決方法:
1. .envファイルのトークン確認
2. Discordアプリでボット権限確認
3. ログ確認: tail -f logs/discord_agent.log
```

#### **2. 自発発言が動作しない**
```bash
# 確認事項:
1. ENVIRONMENT=test 設定確認
2. daily_workflow動作ログ確認  
3. autonomous_speech初期化ログ確認
```

#### **3. タスクコマンドが反応しない**
```bash
# 確認事項:
1. コマンド形式確認: /task commit channel "task"
2. command-centerチャンネルでの応答確認
3. Spectraボットの動作状況確認
```

#### **4. エージェント選択が偏る**
```bash
# 確認事項:
1. LangGraph supervisor動作ログ確認
2. チャンネルごとの重み設定確認
3. 複数回テストでの統計確認
```

---

## ✅ **テスト完了条件**

### **必須要件 (All Must Pass)**
- [ ] 4ボット全て正常接続
- [ ] 基本メッセージ応答正常
- [ ] タスクコマンド動作正常
- [ ] エラーなくシャットダウン可能

### **推奨要件 (Best Effort)**
- [ ] エージェント選択確率がチャンネル別期待値に近い
- [ ] 自発発言が適切な間隔で動作
- [ ] 会話履歴が適切に保持
- [ ] 5人同時接続で安定動作

**🎯 必須要件全クリア = Discord実動テスト合格!**