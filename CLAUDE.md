# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) への直接的な指示です。

## 📖 プロジェクト概要

**Project 009: Discord Multi-Agent Workflow System**

統合受信・個別送信型アーキテクチャによるタスク駆動型Discord Multi-Agent Systemの実装。
LangGraph Supervisor PatternとGemini 2.0 Flash APIを活用し、3体のAIエージェント（Spectra、LynQ、Paz）が日次ワークフローに基づいて協調動作するシステム。

### 主な特徴
- **統合受信**: 1つのボットがメッセージを一元管理
- **個別送信**: 3体のエージェントが独自のアイデンティティで応答
- **日次ワークフロー**: 自動日報生成・会議・タスク駆動実務・自由時間の4フェーズ
- **タスク管理**: `/task commit`/`/task change`コマンドによる動的タスク制御
- **LangGraph統合**: Supervisor Patternによる高度なオーケストレーション
- **2層メモリ**: Redis（Hot Memory）+ PostgreSQL（Cold Memory）
- **チャンネル特化**: development（LynQ）, creation（Paz）の専門性重視

### 日次スケジュール
- **00:00-06:59 REST**: 自発発言無効、ユーザー応答は全チャンネル有効
- **07:00 Report+Meeting**: 日報自動生成（Discord Embed）+ 会議開始
- **07:01-19:59 MEETING/WORK**: lounge以外で自発発言有効、`/task commit [channel] "[task]"`で実務モード切り替え
- **20:00-23:59 CONCLUSION**: loungeのみで自発発言有効、全チャンネルでユーザー応答有効

### エージェント役割
- **Spectra**: ワークフロー管理、全チャンネル均等参加
- **LynQ**: development重視（50%）、ロジカル思考・技術特化
- **Paz**: creation重視（50%）、発散思考・創作特化

## 🚨 【最優先】Claude Code 動作制御

### 🔔 作業完了通知
完了時には以下のコマンドを実行して、私（ユーザー）に通知すること：
```bash
powershell.exe -c "[System.Media.SystemSounds]::Beep.Play()"
```

### 🎯 作業方針の自動判断
- **複雑な問題**: 自動的に「think」「think hard」モードで拡張思考を実行
- **サブエージェント常時活用**: 調査フェーズでは常にサブエージェントを使用してメインコンテキスト容量を温存

## 🚨 必須動作原則

### 作業開始時の必須手順
1. **まず調査フェーズを実行** - いかなる実装も行う前に、必ず関連ファイルを読み込み、既存パターンを理解する
2. **テスト設計フェーズを実行** - 実装前に必ずテストシナリオとテスト構造を設計する
3. **テストファースト実装** - 必ずテストを先に書き、失敗を確認してから実装する
4. **段階的実装** - 一度に大量のコードを書かず、テスト単位で小さなステップで進める
5. **各ステップで検証** - 実装後は必ずテスト・Lint・型チェックを実行する

### 🚨 スコープ厳守の原則
- **指示された内容のみを実装する** - 親切心や推測による機能追加は禁止
- **最小限の変更で目的を達成する** - 過度な最適化や拡張は避ける

### 禁止事項
- ❌ **ハードコード禁止**: APIキー、トークン、パスワード等の機密情報や設定値の直接記述
- ❌ `.env`、`config/`、`settings/`以外での設定値管理
- ❌ **テストなしの実装**: いかなる機能もテストなしでの実装は禁止

## 🔄 TDD統合型必須ワークフロー

### Phase 1: 調査とテスト設計 (EXPLORE & TEST DESIGN) 🕵️‍♂️🧪

**調査とテスト設計フェーズを開始します**

#### 📁 実装前調査
1. **要件の明確化**: 何を作るのかを完全に理解
2. **既存コードの分析**: 関連ファイル・パターン・依存関係の把握
3. **インターフェース設計**: 入出力・API境界の定義
4. **関連URL検索・理解**
5. **依存関係調査**: サードパーティ・内部モジュールの特定

#### 🧪 テスト設計（TDD準備）
6. **テストシナリオの列挙**: 正常系・異常系・境界値
7. **テスト構造の設計**: ファイル配置・命名規則・共通設定
8. **モックとスタブの計画**: 外部依存の分離戦略
9. **受け入れ基準の定義**: 各機能の完了条件を明文化

#### 🌐 外部リソースの活用
10. **一次情報源を最優先**: 公式ドキュメント、GitHub、CHANGELOGを最新順に確認
11. **Context7 MCPツールを常に有効に使う**: 調査内容はContext7に保存しながら進める
12. **サブエージェント活用による調査の分散**: 公式ドキュメント調査・ファイル要約・依存スタック交換などにサブエージェントを使う

**🔒 フェーズ完了条件**
- ✅ 実装すべき機能の完全な理解
- ✅ テストケースの網羅的リスト作成
- ✅ テスト可能な設計の確立
- ✅ 絶対にコードの実装は行わない

### Phase 2: Red Phase - テスト作成と失敗確認 (TEST FIRST) 🔴

**Red Phaseを開始します - テストファースト実装**

#### 📝 テスト作成
1. **単体テストの作成**: 最小単位の機能テスト
   ```python
   def test_feature_x_should_return_y_when_z():
       # Arrange - 準備
       # Act - 実行
       # Assert - 検証
       assert False  # まず失敗するテスト
   ```

2. **統合テストの作成**: コンポーネント間の連携テスト
3. **E2Eテストの骨組み**: 必要に応じてエンドツーエンドシナリオ

#### 🔴 失敗確認（必須）
4. **全テスト実行**: `pytest -v`で失敗を確認
5. **失敗理由の文書化**: なぜ失敗するかを明確に記録
6. **カバレッジ基準設定**: 目標カバレッジ率の定義
7. **テストコミット**: 失敗するテストをコミット

**🚫 このフェーズでの禁止事項**
- ❌ 実装コードは一切書かない
- ❌ テストを通すための仮実装も禁止
- ❌ テストの期待値を推測で書かない

### Phase 3: Green Phase - 最小実装とリファクタリング (IMPLEMENT & REFACTOR) 🟢

**Green Phaseを開始します - テスト駆動実装**

#### 🟢 最小実装サイクル
各テストに対して以下のマイクロサイクルを実行：

1. **単一テストの選択**: 最も簡単なテストから開始
2. **最小実装**: テストを通す最小限のコード
   ```python
   def feature_x(z):
       return y  # ハードコードでもOK（最初は）
   ```
3. **テスト実行**: 選択したテストのみ通過確認
4. **増分コミット**: テストが通ったらすぐコミット
5. **次のテストへ**: 段階的に複雑なテストへ

#### ♻️ リファクタリングサイクル
6. **全テスト通過確認**: すべてのテストがGreen
7. **コード品質改善**:
   - 重複の除去
   - 命名の改善
   - 設計パターンの適用
   - SOLID原則の適用
8. **パフォーマンス最適化**: 必要に応じて
9. **継続的テスト実行**: リファクタリング中も常にGreen維持

#### 📊 品質メトリクス確認
- カバレッジ率: 目標値達成確認
- 複雑度: サイクロマティック複雑度のチェック
- コード品質: `black --check`, `flake8`, `mypy`の実行

### Phase 4: 統合検証とドキュメント化 (INTEGRATE & DOCUMENT) ✅

**統合検証フェーズを開始します - 完全性の確保**

#### 🔗 統合テスト実行
1. **全テストスイート実行**: 単体・統合・E2E全て
2. **クロステスト**: 他の機能との相互作用確認
3. **非機能要件テスト**: パフォーマンス・セキュリティ等
4. **要件定義適合確認**: 全要件項目との最終照合

#### 📚 ドキュメント生成
5. **APIドキュメント**: テストから自動生成
6. **使用例の作成**: テストケースを基にした実例
7. **変更履歴の記録**: 実装の経緯と判断理由
8. **README/CHANGELOG更新**: 必要に応じて

#### 🎯 最終検証
9. **受け入れ基準の確認**: Phase 1で定義した基準
10. **技術的負債の記録**: 将来の改善点を文書化
11. **最終品質チェック**: 
    ```bash
    black --check src/ && flake8 src/ && mypy src/
    ```

#### 💾 成果物の保存
12. **最終コミット**: 必要に応じて最終調整
13. **タスクリスト保存**: 完了したタスクリストをCLAUDE.mdに永続保存
14. **知識ベース更新**: 学んだパターンを記録

**重要**: このフェーズでは新たな実装は行わず、検証・確認・保存のみ実行

## 📋 TDD実行テンプレート

```markdown
## 🎯 機能: [機能名]

### Phase 1: 調査とテスト設計 ⏱️ 目安: 20%
- [ ] 要件理解完了
- [ ] 既存コード調査完了
- [ ] テストシナリオ一覧作成
- [ ] 受け入れ基準定義

### Phase 2: Red Phase ⏱️ 目安: 30%
- [ ] 単体テスト作成 `test_[機能]_unit.py`
- [ ] 統合テスト作成 `test_[機能]_integration.py`
- [ ] 全テスト失敗確認 🔴
- [ ] 失敗理由文書化

### Phase 3: Green Phase ⏱️ 目安: 40%
#### 実装サイクル
- [ ] テスト1: 最小実装 → 🟢
- [ ] テスト2: 機能追加 → 🟢
- [ ] テスト3: エッジケース対応 → 🟢
- [ ] 全テスト通過確認

#### リファクタリング
- [ ] コード品質改善
- [ ] パフォーマンス最適化
- [ ] 最終品質チェック（lint/type/coverage）

### Phase 4: 統合検証 ⏱️ 目安: 10%
- [ ] 統合テスト完全実行
- [ ] ドキュメント更新
- [ ] コミット作成
- [ ] 知識ベース更新
```

## 🚀 TDD成功のための追加原則

### テスト粒度の原則
- **単体テスト**: 1関数/1クラスメソッドごと
- **統合テスト**: 機能単位・API単位
- **E2Eテスト**: ユーザーシナリオ単位

### テスト速度の原則
- 単体テスト: < 0.1秒/テスト
- 統合テスト: < 1秒/テスト  
- E2Eテスト: < 10秒/テスト

### カバレッジ目標
- クリティカルパス: 100%
- ビジネスロジック: 95%以上
- ユーティリティ: 80%以上
- 新規コード: 90%以上

### 継続的フィードバック
- 各コミット前: 関連テスト実行
- プッシュ前: 全テスト実行
- マージ前: CI/CDでの完全検証

## 📋 要件定義（Discord Multi-Agent System）

### 🎯 システム概要
**統合受信・個別送信型アーキテクチャ**による設計済み最適Discord Multi-Agent System

```
🏗️ 統合受信・個別送信型アーキテクチャ（2025年Ultra Think調査済み最適設計）

┌─────────────────────────────────────────────────────────────┐
│                Discord Gateway Layer                        │
│            📨 Reception Bot (受信専用)                       │
│              - asyncio.gather()並行起動                     │
│              - 全メッセージ受信（on_messageイベント）          │
│              - 優先度判定・キューイング                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ asyncio.PriorityQueue（メッセージ管理）
┌─────────────────▼───────────────────────────────────────────┐
│            LangGraph Supervisor                             │
│              (Gemini 2.0 Flash API)                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │    統合エージェントルーター（50%API削減実現）         │    │
│  │                                                     │    │
│  │  1回のAPI呼び出しで:                                │    │
│  │  ├─ メッセージ分析                                   │    │
│  │  ├─ 適切エージェント選択(spectra/lynq/paz)           │    │
│  │  ├─ 応答内容生成                                     │    │
│  │  └─ 送信指示決定                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────────┘
                  │ 選択結果
┌─────────────────▼───────────────────────────────────────────┐
│              Output Distribution Layer                      │
│                                                             │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │🔵 Spectra Bot│🔴 LynQ Bot   │🟡 Paz Bot                │ │
│  │(送信専用)     │(送信専用)     │(送信専用)                │ │
│  │真の個別Bot   │真の個別Bot   │真の個別Bot               │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**設計済みアーキテクチャ方針:**
- **受信**: Reception Bot（1つ）で全メッセージ受信（asyncio.gather()設計採用）
- **処理**: LangGraph Supervisor Pattern（v0.4.8対応）で統合制御
- **送信**: 3つの独立Bot（Spectra/LynQ/Paz）で真の個別アイデンティティ
- **効率**: 1回のAPI呼び出しで選択+応答生成（重複処理排除設計）
- **技術方針**: 初心者実装可能・段階的開発・要件対応設計

### 🧠 メモリ・状態管理アーキテクチャ（最終確定版）

#### 2層統合メモリシステム（採用決定）

**🔥 Hot Memory（当日記憶）**
- **用途**: 当日の全活動統合管理
- **技術**: Redis Key-Value（JSON形式）
- **構造**: 単一記憶プール
- **アクセス速度**: 0.1秒以下
- **データ例**: 
  ```json
  "msg:001": {"channel":"command-center", "author":"太郎", 
             "content":"新機能提案", "importance":8}
  ```

**❄️ Cold Memory（長期記憶）**
- **用途**: 永続知識・経験・パターン保存
- **技術**: PostgreSQL + pgvector（テキストDB + ベクトル列）
- **構造**: 統合メモリテーブル（全チャンネル情報統合）
- **アクセス速度**: セマンティック検索 3秒程度（目安）
- **検索方式**: models/text-embedding-004によるベクトル類似度検索
- **テーブル設計**:
  ```sql
  CREATE TABLE memories (
      id UUID PRIMARY KEY,
      content JSONB NOT NULL,      -- 全情報統合
      summary TEXT NOT NULL,       -- 検索用要約
      date DATE NOT NULL,          -- 日付検索
      importance INT DEFAULT 5,    -- 重要度(1-10)
      tags TEXT[] DEFAULT '{}',    -- 分類タグ
      embedding vector(768),       -- セマンティック検索用
      created_at TIMESTAMP DEFAULT NOW()
  );
  ```

#### メモリアクセスパターン（常時全読み込み方式）
```python
# 簡素化統合システム（判定なし・常に両方アクセス）
async def load_all_memories(query: str):
    # 1. Hot Memory（Redis）- 常に読み込み
    hot_results = await redis_client.get_channel_context(limit=10)
    
    # 2. Cold Memory（PostgreSQL）- 常に読み込み
    embedding = await get_embedding(query)
    cold_results = await db.execute(
        "SELECT * FROM memories WHERE embedding <=> %s ORDER BY embedding <=> %s LIMIT 5",
        [embedding, embedding]
    )
    
    return {"hot": hot_results, "cold": cold_results}
```

#### 記憶アクセス方式（簡素化採用）
- **常時全記憶読み込み**: 判定ロジック廃止、毎回Hot+Cold Memory活用
- **実装利点**: 複雑な判定不要、一貫した高品質応答、デバッグ容易
- **性能**: 一定の処理時間（9秒）、予測可能なユーザー体験

#### 日次メモリライフサイクル（夜間バッチ処理）
```bash
# 06:55 自動メモリ移行バッチ
async def daily_memory_migration():
    # 1. Redis全データ取得
    yesterday_data = await redis.get_all_data()
    
    # 2. 要約生成・ベクトル化・重要度判定
    for data in yesterday_data:
        summary = await generate_summary(data)
        embedding = await get_embedding(summary)
        importance = calculate_importance(data)
        
        # 3. PostgreSQL統合テーブルに保存
        await db.execute("""
            INSERT INTO memories (content, summary, date, importance, embedding)
            VALUES (%s, %s, %s, %s, %s)
        """, [data, summary, yesterday, importance, embedding])
    
    # 4. 日報生成・Redisクリア
    await generate_daily_report()
    await redis.clear_all()

# 07:00 新しい1日開始
└─ 空のRedisで新たな当日記憶開始
```

#### Discordチャンネル別セッション管理
- **セッション定義**: DiscordチャンネルID = セッションID
- **コンテキスト管理**: チャンネル毎の独立した履歴・コンテキスト管理
- **状態保持**: シーケンシャル進行により競合状態なし

### 🤖 発言システム仕様（改良版）

#### 統合イベント駆動アーキテクチャ
1. **ユーザー応答（即時・最優先）**
   - メンション応答: 9秒以内の確実な応答
   - 通常発言応答: 統合AI処理による適切なBot選択
   - コマンド応答: `/commit`コマンドの即時処理

2. **自発的発言（低優先度）- 詳細仕様**
   - **基本周期**: 5分間隔のtickベーススケジューリング
   - **判定フロー**: tick → 確率判定 → Bot選択・発言
   - **発言確率**:
     - test環境: 100%（デバッグ・テスト用）
     - production環境: 33%（適度な自発性）
   - **Bot選択確率**: 
     - command-center: Spectra 50%, LynQ 30%, Paz 20%
     - creation: Paz 50%, Spectra 30%, LynQ 20%
     - development: LynQ 50%, Spectra 30%, Paz 20%
     - lounge: 各Bot 33%（均等）
   - **自律的タスク進行**: ユーザー不在でも意思決定以外は自律継続
     - アイデア展開・議論深化・方向性探索を継続実行
     - 20:00まで議論が自然に進展する設計

3. **実装方針（API削減効果適用）**
   - 別ロジック: ユーザー応答と自発発言を独立実装
   - API効率: 統合AI処理により1回のLLM使用（従来2回→1回）
   - 競合制御: 発言ロックによる重複防止

### 🔄 日次ワークフロー（ユーザー主導型）
**時間トリガー + ユーザー決定待機方式**

```
06:55 日報生成
  │ [時間トリガー]
  └─ Spectra: command-centerで前日活動サマリー作成
  ↓
07:00 command-center会議開始
  │ [時間トリガー]
  ├─ 全Bot参加（Spectra, LynQ, Paz）
  └─ 有機的タスク議論方式:
      ◆ 日報を起点とした自然な議論の流れ
      ◆ 連想・ブレスト・議論の継続的展開
      ◆ 各Botの個性を活かした多角的視点
      ◆ タスク決定を目的としつつも柔軟な進行
  ↓
ユーザー介入可能時間（最大20:00まで）
  ├─ /commit creation → creation チャンネルで作業開始
  ├─ /commit development → development チャンネルで作業開始
  └─ /commit task [内容] → 該当チャンネルで作業開始（唯一の作業開始トリガー）
  ↓
  [ユーザー不在時の自律的進行]
  └─ Bot間で議論継続・アイデア展開・方向性探索を継続
  ↓
20:00 作業終了
  │ [時間トリガー]
  └─ 当日作業の終了（作業していた場合）
  ↓
20:00 lounge開始
  │ [時間トリガー]
  └─ Social Sectorで自由な交流（20:00-0:00）
  ↓
0:00 当日終了
  └─ 全システム停止（翌日06:55まで休止）
```

**重要な仕様:**
- 人間の意思決定がない場合、20:00までcommand-centerで会議継続
- 人間は1名のみ（最終意思決定者）
- Bot同士は人間不在でも自律的に活動継続
- 会議は形式的手順ではなく、目的意識を持った有機的な議論
- ユーザー不在時も議論が停止せず、継続的に進展
- シーケンシャル進行: 常に1つのチャンネルのみアクティブ（同時進行なし）

## 📋 実装済み技術仕様

### 🛠️ 技術スタック
- **AI Engine**: Google Gemini 2.0 Flash API
- **Framework**: LangChain v0.3.25 + LangGraph v0.4.8  
- **Discord**: Discord.py + 統合受信・個別送信型アーキテクチャ (✅ 実装完了)
- **Database**: PostgreSQL + pgvector + Redis (✅ 実装完了)
- **Environment**: Python 3.9+ + venv

### ⚙️ 運用設定
- **自発発言システム**: AutonomousSpeechSystem (Context-Aware版) (✅ 稼働中)
- **環境別確率**: test: 100%, production: 33%
- **フェーズ制御**: REST無効, MEETING(command-center中心), CONCLUSION(loungeのみ)
- **チャンネル頻度**: LynQ→development 50%, Paz→creation 50%
- **文脈判定**: ConversationDetector削除、LangGraph統合判定採用

### 📁 Redis設計仕様
```python
# キー命名規則
"channel:{channel_id}:messages"     # チャンネル別メッセージ履歴
"channel:{channel_id}:context"      # チャンネル別コンテキスト
"daily:tasks"                       # 当日タスク管理
"daily:decisions"                   # 当日意思決定記録

# データ構造例
{
    "timestamp": "2025-06-19T10:30:45+09:00",
    "author": "user_name",
    "content": "message content",
    "bot_response": "selected_bot_name"
}
```


#### 📁 完全実装ファイル構成
```
project-009/
├── src/
│   ├── main.py                           # システム統合起動・asyncio.gather()
│   ├── config.py                         # 環境設定・定数管理
│   ├── discord_clients.py                # ReceptionClient（受信専用）
│   ├── output_bots.py                    # 個別送信Bot×3（Spectra/LynQ/Paz）
│   ├── langgraph_supervisor.py           # LangGraph Supervisor Pattern
│   ├── gemini_client.py                  # Gemini 2.0 Flash API統合
│   ├── message_processor.py              # 優先度キュー・ルーティング
│   ├── message_router.py                 # Redis Pub/Sub メッセージ配信
│   ├── memory_system.py                  # Redis + PostgreSQL 2層メモリ
│   ├── autonomous_speech.py              # 自発的発言システム
│   └── daily_workflow.py                 # 日次ワークフロー・スケジュール
├── tests/
│   ├── unit/                            # 単体テスト
│   ├── integration/                     # 統合テスト
│   └── e2e/                             # エンドツーエンドテスト
├── config/
│   ├── agents.json                      # エージェント設定
│   └── channels.json                    # チャンネル設定
├── scripts/
│   └── setup.sh                         # 環境セットアップスクリプト
├── .env                                 # 環境変数（4つのDiscordトークン）
├── requirements.txt                     # 依存関係
├── docker-compose.yml                   # PostgreSQL + Redis
└── README.md                            # プロジェクト説明・セットアップ手順
```

#### ⚙️ 核心実装コード（基本構造）
```python
import asyncio
import discord
from langgraph.graph import StateGraph, MessagesState
import aioredis

class DiscordMultiAgentSystem:
    def __init__(self):
        # 4つのDiscordクライアント
        self.reception_client = discord.Client(intents=discord.Intents.all())
        self.agents = {
            "spectra": discord.Client(intents=discord.Intents(guilds=True, messages=True)),
            "lynq": discord.Client(intents=discord.Intents(guilds=True, messages=True)),
            "paz": discord.Client(intents=discord.Intents(guilds=True, messages=True))
        }
        
    async def setup_infrastructure(self):
        self.redis = aioredis.from_url("redis://localhost:6379")
        self.message_queue = asyncio.PriorityQueue()
        await self.setup_langgraph()
        
    async def run_system(self):
        await self.setup_infrastructure()
        tasks = [self.reception_client.start(RECEPTION_TOKEN)]
        for agent_name, client in self.agents.items():
            token = os.getenv(f"{agent_name.upper()}_BOT_TOKEN")
            tasks.append(client.start(token))
        await asyncio.gather(*tasks, return_exceptions=True)
```

#### 🔄 メッセージ処理フロー
- **受信**: 統合受信クライアント（メッセージ一元管理）
- **キューイング**: asyncio.PriorityQueue（メンション > 通常 > 自発）
- **処理**: LangGraph Supervisor Pattern（エージェント選択・応答生成）
- **送信**: 個別エージェントクライアント（真の独立ボット）

#### 🎯 重要な実装特徴
- **完全な個別ボット**: 4つの独立したDiscordアカウント
- **@メンション対応**: 各エージェントへの直接メンション可能
- **オンライン状態**: 個別のオンライン/オフライン/入力中表示
- **API効率化**: 重複処理排除により50%のリソース削減
- **初心者対応**: 単一プロセス、理解しやすい構造

### 🎭 エージェント仕様

#### 🔵 Spectra Communicator - メタ進行役
- **コミュニティ主導**: 全チャンネルで会話の方向性を整理
- **メタ思考**: 議論の構造化・目的への収束管理
- **目的思考**: ゴールから逆算した会議進行
- **専任領域**: command-center統合運営（日報・タスク管理）

#### 🔴 LynQ - 論理収束役
- **収束思考**: アイデアの論理的整理・実現可能性検証
- **構造化**: 概念の体系化・技術的妥当性確認
- **品質保証**: 要件・設計の論理的一貫性チェック

#### 🟡 Paz - 発散創造役
- **発散思考**: 既存枠を超えた創造的アイデア生成
- **飛躍的発想**: 予想外の組み合わせ・革新的アプローチ
- **可能性探索**: 新しい視点・未開拓領域の提案

### 🏭 Discordチャンネル構成（3セクター4チャンネル）

#### Operation Sector（運営統制）
```
└── command-center      # 戦略決定・日報・タスク生成すべて
    ├── 🔵 Spectra: 全体方針の整理・意思決定プロセス進行
    ├── 🔴 LynQ: 方針の論理的妥当性検証・リスク分析
    └── 🟡 Paz: 革新的戦略・新しい方向性の提案
```

#### Production Sector（生産領域）
```
├── creation            # 創作関連（表現目的・テーマ・世界観・キャラ構想）
│   ├── 🔵 Spectra: テーマの方向性整理・設定の整合性管理
│   ├── 🟡 Paz: 創造的テーマ・独創的世界観・キャラクター創造
│   └── 🔴 LynQ: テーマの論理的構造化・設定の一貫性チェック
│
└── development         # 開発関連（要件定義・技術設計・アーキテクチャ）
    ├── 🔵 Spectra: 要件の優先度整理・技術選定プロセス進行
    ├── 🔴 LynQ: 要件の論理的分析・アーキテクチャの論理的設計
    └── 🟡 Paz: 革新的機能・新しいアーキテクチャパターン
```

#### Social Sector（交流領域）
```
└── lounge               # プライベートな本性空間・AIの素顔
    ├── 🔵 Spectra: 観察と内省に満ちた静かな対話を愉しむ思索者
    ├── 🔴 LynQ: 感覚や違和感をロジックで照らし直す誠実な探求者
    └── 🟡 Paz: 自由な連想と直感に従い、感情で世界を描く創造者
```

### 👤 ユーザーインタラクション要件

#### ユーザー関与パターン
1. **メンション対応**
   - `@Spectra` `@LynQ` `@Paz`: 対象Botが即時応答
   - 文脈に関わらず最優先で処理

2. **通常発言**
   - Botの発言と同等に扱う
   - 文脈に応じて適切なBotが即時対応（必須）
   - 応答者はオーケストレーターが一元決定

3. **`/commit` コマンド**
   - `/commit creation`: 会議内容をcreation部門へ専門化（command-centerで継続）
   - `/commit development`: 会議内容をdevelopment部門へ専門化（command-centerで継続）
   - `/commit task [内容]`: 具体的タスクを指定して該当チャンネルで作業開始（唯一の作業開始・チャンネル移動トリガー）

#### 人間・Bot平等原則
- 人間もBotも「参加者」として同じ扱い
- 発言権・優先度に差をつけない
- ただしcommand-centerでの最終決定権は人間のみ

### 📊 品質・性能要件（統合受信・個別送信型アーキテクチャ）
- **アーキテクチャ設計**: 統合受信・個別送信型アーキテクチャ（設計済み最適解）
- **Bot応答精度**: Supervisor Pattern統合判定による95%以上の精度目標
- **API効率化**: 統合エージェントルーターによる処理効率化（従来2回→1回）
- **処理時間**: Gemini 2.0 Flash平均2-4秒 + キューイング処理で9秒以内安定応答
- **制限対応**: 15 RPM/1,500 RPD制限への対応（指数バックオフ + 優先度キュー）
- **失敗回避**: 典型的失敗パターン回避設計
  - 設計方針: モノリシック設計回避 → マイクロサービス分離
  - 非同期処理: Threading問題回避 → asyncio完全採用  
  - API制限対応: Rate Limit違反回避 → Semaphore制御
  - 重複処理対策: メッセージID重複チェック実装
- **スケーラビリティ**: asyncio.gather()による水平スケーリング設計
- **保守性**: 統合受信・個別送信型による明確な責務分離
- **実装制約**: 実績あるパターンを採用、実験的機能は排除
- **セキュリティ**: 環境変数管理 + 最小権限原則遵守

## 📁 ファイル操作の優先順序

### 読み込み順序（統合受信・個別送信型アーキテクチャ）
1. `CLAUDE.md` 要件定義（最優先）
2. `requirements.txt` / `pyproject.toml`（2024年推奨依存関係）
3. `README.md` / `CHANGELOG.md`
4. `.env` / `.env.example`
5. **最新技術情報の確認**: LangGraph Supervisor Pattern公式ドキュメント
6. `src/langgraph_supervisor.py` (LangGraph Supervisor実装)
7. `src/message_processor.py` (統合メッセージ処理)
8. `src/discord_clients.py` (統合受信・個別送信Bot管理)
9. `src/message_router.py` (メッセージルーティング実装)
10. `src/memory_manager.py` (Redis/PostgreSQL統合管理)
11. `src/utils.py` (設定・ログ・実証済みパターン)
12. `test_discord_integration.py` (Discord統合テスト)
13. `logs/app.log` (構造化ログファイル)


## 🛠️ 開発コマンド一覧

### 🚀 セットアップ
```bash
# 1. 仮想環境
python3 -m venv venv && source venv/bin/activate

# 2. 依存関係
pip install -r requirements.txt

# 3. データベース
docker-compose up -d

# 4. 環境設定
cp .env.example .env
# .envファイルを編集してAPI Keys等を設定
```

### ▶️ 起動・実行
```bash
# Phase 4統合テスト実行
python test_discord_integration_proper.py

# LangGraph Orchestrator単体テスト
python -m pytest tests/integration/test_orchestrator.py

# メモリシステムテスト
python -m pytest tests/integration/test_memory_integration.py

# 統合システム起動（Phase 5実装後）
python src/main.py
ENV_MODE=test python src/main.py
```

### 🔧 開発・デバッグ
```bash
# コード品質チェック・フォーマット
black src/ && isort src/ && mypy src/

# Phase 4統合システムログ確認
tail -f logs/app.log | grep -E "(discord|orchestrator|priority_queue)"

# API使用量・制限状況確認
grep -E "(api_call|api_rate_limit)" logs/app.log | tail -10

# Discord統合テスト詳細実行
python test_discord_integration_proper.py -v

# データベース稼働確認
docker-compose logs postgres redis
```

### 📤 GitHubプッシュ手順
```bash
# リモートリポジトリ追加（初回のみ）
git remote add origin https://github.com/sito-sikino/project-009.git

# ブランチ作成・プッシュ
git push -u origin main

# タグプッシュ
git push origin --tags

# プッシュ確認
git remote -v
```

### 🗄️ 環境変数（.env）
```bash
# 環境設定
ENV_MODE=test                  # test/development/production

# Discord Bot Tokens（統合受信・個別送信型）
RECEPTION_BOT_TOKEN=your_reception_bot_token    # 受信専用Bot
SPECTRA_BOT_TOKEN=your_spectra_bot_token        # Spectra送信専用Bot
LYNQ_BOT_TOKEN=your_lynq_bot_token              # LynQ送信専用Bot  
PAZ_BOT_TOKEN=your_paz_bot_token                # Paz送信専用Bot
TARGET_GUILD_ID=your_discord_server_id

# Discord Channel Configuration（Phase 4対応）
COMMAND_CENTER_CHANNEL_ID=your_command_center_channel_id
CREATION_CHANNEL_ID=your_creation_channel_id
DEVELOPMENT_CHANNEL_ID=your_development_channel_id
LOUNGE_CHANNEL_ID=your_lounge_channel_id

# Gemini API Configuration
GEMINI_API_KEY=your_actual_api_key
GEMINI_TEMPERATURE=0.4
MAX_OUTPUT_TOKENS=1000

# Database Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=discord_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Debug
DEBUG_MODE=false
```

### 🐳 Docker管理
```bash
# サービス起動
docker-compose up -d

# ログ確認  
docker-compose logs -f postgres redis

# 停止
docker-compose down
```

---

## 📊 プロジェクト完了状況

### ✅ **実装完了済み** 
- **Phase 1-3**: 統合受信・個別送信型アーキテクチャ完全実装
- **Phase 4**: 2層メモリシステム (Redis + PostgreSQL) 完全実装  
- **Phase 5**: 簡素化版自発発言システム完全実装・稼働中

### 🎯 **現在の状況**: Discord Multi-Agent System **基本機能完全稼働中**

**稼働中システム**:
- ✅ 統合受信・個別送信 (Reception + Spectra/LynQ/Paz) 
- ✅ LangGraph Supervisor Pattern 
- ✅ 2層メモリシステム (Hot/Cold Memory)
- ✅ SimplifiedAutonomousSpeechSystem (AC-016 簡素化版)
- ✅ Daily Workflow System

### 🔄 **次のステップ選択肢**

#### Option A: 現在のまま運用継続 ✅ **推奨**
**判定**: AC-016 簡素化版が基本要件を満たし安定稼働中
- 現在のシステムで十分な機能性を確保
- 自発発言・フェーズ制御・エージェント頻度すべて正常動作
- 追加開発リスクなし

#### Option B: 統合版へアップグレード 🔄
**条件**: AC-015統合日次ワークフロー機能が必要な場合
- `AutonomousSpeechSystem` (統合版) への移行
- `/task commit`コマンド連携機能追加
- 日報生成システム統合
- 実務モード時のシステムプロンプト制御

**⚡ アップグレード必要作業**:
```python
# main.py 1行変更のみ
# from src.autonomous_speech import SimplifiedAutonomousSpeechSystem
from src.autonomous_speech import AutonomousSpeechSystem
# self.autonomous_speech = SimplifiedAutonomousSpeechSystem(...)
self.autonomous_speech = AutonomousSpeechSystem(channel_ids, environment, self.daily_workflow)
```

---

**このファイルの更新**: プロジェクト進行に合わせて継続的に更新し、新しいパターンや制約を追記してください。完了したタスクリストは上記セクションに保存されます。