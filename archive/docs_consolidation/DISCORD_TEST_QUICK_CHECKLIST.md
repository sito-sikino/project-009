# Discord Test Quick Checklist - v0.2.0

## 🔧 Claude Code確認項目

### システム起動確認
- [x] `main.py` エラーなし起動 ✅
- [x] 4つのDiscordクライアント接続成功 ✅
- [x] Memory System初期化完了 ✅ (Redis正常、PostgreSQL既知制限)
- [x] Health API応答確認 ✅

### ログ監視
- [x] JSON dumps エラー解消確認 ✅ **完全解消**
- [x] Autonomous speech エラーなし ✅ **15回実行成功**
- [x] Agent selection正常動作 ✅ **ローテーション確認**
- [x] Task command処理エラーなし ✅ **修正完了**

---

## 🎮 ユーザー手動テスト項目

### 基本応答テスト
- [ ] **通常メッセージ**: 適切なエージェント応答
- [ ] **技術的質問**: LynQ選択確認
- [ ] **創作系質問**: Paz選択確認
- [ ] **会議進行**: Spectra選択確認

### 自発発言テスト  
- [x] **10秒間隔**: 自発発言発生確認 ✅ (ログで確認済み)
- [x] **エージェント切り替え**: 連続発言なし ✅ (Spectra→LynQ→Paz→LynQ→Spectra→Paz確認)
- [x] **チャンネル適正**: 現在フェーズに応じたチャンネル ✅ (developmentチャンネル適正)

### タスクコマンドテスト
- [x] **`/task commit development "認証システム実装"`**: 成功メッセージ ✅
- [x] **チャンネル切り替え**: developmentでの自発発言開始 ✅
- [x] **`/task change development "API設計"`**: 同チャンネル内タスク変更成功 ✅
- [ ] **`/task change creation "アイデアブレスト"`**: **部門間移動テスト** 🔧 **FIXED**

### フェーズ動作確認
- [ ] **現在時刻フェーズ**: 適切な動作モード
- [ ] **STANDBY期間**: 自発発言停止（該当時間のみ）
- [ ] **ACTIVE/FREE期間**: 自発発言有効

---

## ⚡ 緊急確認ポイント

### エラー監視
- [ ] "システム調整中" メッセージなし
- [ ] JSON dumps エラーなし  
- [ ] Agent selection失敗なし
- [ ] Memory system接続エラーなし

### 応答品質
- [ ] 応答時間 < 3秒
- [ ] エージェント個性維持
- [ ] 重複応答なし
- [ ] 適切な日本語応答

## 🚀 テスト実行手順

1. **Claude Code**: システム起動・ログ確認
2. **ユーザー**: 通常メッセージ送信テスト
3. **Claude Code**: 応答ログ・エラーチェック
4. **ユーザー**: タスクコマンド実行
5. **Claude Code**: コマンド処理ログ確認
6. **ユーザー**: 10秒待機・自発発言確認