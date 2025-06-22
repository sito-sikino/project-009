# Autonomous Speech System - テスト設計書

## テスト対象クラス: SimplifiedAutonomousSpeechSystem

### 1. フェーズ別動作テスト

#### 1.1 REST期間の完全無効化
- **シナリオ**: 00:00-06:59の間、自発発言が完全に無効
- **テスト**: `test_rest_period_speech_disabled`
- **期待値**: `_should_speak_autonomously()` → False

#### 1.2 MEETING期間のlounge除外
- **シナリオ**: 07:00-19:59の間、lounge以外で自発発言有効
- **テスト**: `test_meeting_period_excludes_lounge`
- **期待値**: `_get_available_channels()` → ["command_center", "development", "creation"]

#### 1.3 CONCLUSION期間のlounge限定
- **シナリオ**: 20:00-23:59の間、loungeのみで自発発言有効
- **テスト**: `test_conclusion_period_lounge_only`
- **期待値**: `_get_available_channels()` → ["lounge"]

### 2. チャンネル頻度優先度テスト

#### 2.1 LynQ development優位
- **シナリオ**: LynQがdevelopmentチャンネルで50%の頻度
- **テスト**: `test_lynq_development_frequency`
- **期待値**: 1000回テストで、LynQ in development ≈ 500回

#### 2.2 Paz creation優位
- **シナリオ**: Pazがcreationチャンネルで50%の頻度
- **テスト**: `test_paz_creation_frequency`
- **期待値**: 1000回テストで、Paz in creation ≈ 500回

#### 2.3 Spectra均等分散
- **シナリオ**: Spectraが全チャンネル均等参加
- **テスト**: `test_spectra_equal_distribution`
- **期待値**: 各チャンネルで同等の頻度

### 3. 基本機能テスト

#### 3.1 10秒ルール
- **シナリオ**: 前回の自発発言から10秒経過までは新規発言なし
- **テスト**: `test_ten_second_rule`
- **期待値**: `_can_post_autonomous_message()` → False (10秒未満時)

#### 3.2 環境別確率
- **シナリオ**: test環境100%, production環境33%
- **テスト**: `test_environment_probability`
- **期待値**: 環境に応じた確率適用

#### 3.3 会話中断回避
- **シナリオ**: アクティブな会話中のチャンネルは除外
- **テスト**: `test_conversation_interruption_avoidance`
- **期待値**: アクティブチャンネルが除外される

### 4. 統合テスト

#### 4.1 フェーズ切り替え
- **シナリオ**: 時刻変更でフェーズが正しく切り替わる
- **テスト**: `test_phase_transitions`
- **期待値**: 時刻に応じたフェーズ変更

#### 4.2 メッセージキューへの追加
- **シナリオ**: 自発発言がキューに正しく追加される
- **テスト**: `test_message_queue_integration`
- **期待値**: 正しい形式でキューに追加

## モック戦略

### 1. 時間モック
```python
@patch('autonomous_speech.datetime')
def test_with_time_mock(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 1, 8, 0)  # 08:00
```

### 2. ファイルシステムモック
```python
@patch('builtins.open', mock_open())
@patch('json.load')
@patch('json.dump')
```

### 3. ワークフローシステムモック
```python
@patch.object(SimplifiedAutonomousSpeechSystem, '_get_current_workflow_phase')
```

## テストファイル構造

```
tests/
├── unit/
│   ├── test_autonomous_speech_phase_control.py
│   ├── test_autonomous_speech_channel_frequency.py
│   ├── test_autonomous_speech_basic_functions.py
│   └── test_autonomous_speech_message_queue.py
└── integration/
    └── test_autonomous_speech_workflow_integration.py
```

## テストデータ

### チャンネル設定
```python
TEST_CHANNELS = {
    "command_center": 1383963657137946664,
    "lounge": 1383966355962990653,
    "development": 1383968516033478727,
    "creation": 1383981653046726728
}
```

### エージェント頻度設定
```python
AGENT_FREQUENCY = {
    "lynq": {"development": 0.5, "others": 0.25},
    "paz": {"creation": 0.5, "others": 0.25},
    "spectra": {"all": 0.33}  # 均等
}
```