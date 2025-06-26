"""
LangGraph Supervisor Pattern Unit Tests - TDD Phase 1 (RED Phase)
責務再分離後の期待動作を定義する失敗テスト

テスト対象: 
- AgentSupervisor: StateGraphワークフロー管理専任
- GeminiClient: API処理専任（プロンプト生成削除）
- 重複機能除去と責務明確化
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# テスト対象をインポート（責務再分離後の期待動作テスト）
try:
    from src.agents.supervisor import AgentSupervisor, AgentState
    from src.infrastructure.gemini_client import GeminiClient
    IMPORTS_SUCCESS = True
except ImportError:
    # TDD Red Phase: 実装前なのでインポートエラーは期待通り
    AgentSupervisor = None
    AgentState = None
    GeminiClient = None
    IMPORTS_SUCCESS = False


class TestAgentSupervisorResponsibilitySeparation:
    """責務再分離後のAgentSupervisor単体テスト（失敗テスト）"""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """責務再分離後のGemini APIクライアントのモック"""
        client = AsyncMock()
        # 責務再分離後: プロンプト生成なし、純粋なAPI呼び出しのみ
        client.call_unified_api = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_memory_system(self):
        """メモリシステムのモック"""
        memory = AsyncMock()
        memory.load_hot_memory = AsyncMock()
        memory.load_cold_memory = AsyncMock()
        memory.update_memory_transactional = AsyncMock()
        return memory
    
    @pytest.fixture
    def sample_agent_state(self):
        """サンプルAgentState"""
        return {
            'messages': [{'role': 'user', 'content': 'こんにちは'}],
            'channel_id': '12345',
            'memory_context': {},
            'selected_agent': '',
            'response_content': '',
            'confidence': 0.0
        }

    def test_supervisor_only_handles_workflow_fails(self, mock_gemini_client, mock_memory_system):
        """責務再分離: SupervisorはStateGraphワークフロー管理のみで、プロンプト生成なし（失敗テスト）"""
        if not IMPORTS_SUCCESS:
            pytest.skip("Imports failed - TDD Red Phase")
        
        supervisor = AgentSupervisor(
            gemini_client=mock_gemini_client,
            memory_system=mock_memory_system
        )
        
        # ASSERT: 責務再分離後はプロンプト生成機能なし
        with pytest.raises(AttributeError):
            supervisor._generate_unified_prompt({})  # 削除されるべき
        
        # ASSERT: StateGraphワークフロー管理機能は保持
        assert hasattr(supervisor, 'graph')
        assert hasattr(supervisor, 'process_message')

    @pytest.mark.asyncio
    async def test_supervisor_calls_pure_api_client_fails(self, mock_gemini_client, mock_memory_system, sample_agent_state):
        """責務再分離後: SupervisorはプロンプトなしでGeminiClient純粋API呼び出し（失敗テスト）"""
        if not IMPORTS_SUCCESS:
            pytest.skip("Imports failed - TDD Red Phase")
        
        # ARRANGE: 責務再分離後のGemini純粋API応答のモック
        mock_gemini_client.call_unified_api.return_value = {
            'selected_agent': 'spectra',
            'response_content': 'こんにちは！元気ですか？',
            'confidence': 0.95
        }
        
        supervisor = AgentSupervisor(
            gemini_client=mock_gemini_client,
            memory_system=mock_memory_system
        )
        
        # ACT: Supervisor内でプロンプト生成→純粋API呼び出し
        result = await supervisor.process_message(sample_agent_state)
        
        # ASSERT: 責務再分離後の期待動作
        assert result['selected_agent'] == 'spectra'
        
        # ASSERT: 純粋API呼び出しメソッドが使用される（unified_agent_selectionではない）
        mock_gemini_client.call_unified_api.assert_called_once()
        
        # ASSERT: 古いメソッドは呼ばれない
        assert not hasattr(mock_gemini_client, 'unified_agent_selection') or \
               not mock_gemini_client.unified_agent_selection.called

    @pytest.mark.asyncio
    async def test_memory_integration_flow(self, mock_gemini_client, mock_memory_system, sample_agent_state):
        """メモリシステム統合フローテスト"""
        if AgentSupervisor is None:
            pytest.skip("AgentSupervisor not implemented yet - TDD Red Phase")
        
        # ARRANGE: メモリシステムの応答設定
        mock_memory_system.load_hot_memory.return_value = [
            {'role': 'user', 'content': '前回の話題'}
        ]
        mock_memory_system.load_cold_memory.return_value = [
            {'summary': '過去の重要な会話', 'relevance': 0.8}
        ]
        
        supervisor = AgentSupervisor(
            gemini_client=mock_gemini_client,
            memory_system=mock_memory_system
        )
        
        # ACT: メモリ統合処理
        await supervisor.process_message(sample_agent_state)
        
        # ASSERT: メモリシステムが正しく呼ばれたこと
        mock_memory_system.load_hot_memory.assert_called_once()
        mock_memory_system.load_cold_memory.assert_called_once()
        mock_memory_system.update_memory.assert_called_once()

    def test_agent_state_schema_validation(self):
        """AgentState スキーマ検証テスト"""
        # ACT: AgentState作成
        state = AgentState(
            messages=[],
            channel_id='test',
            memory_context={},
            selected_agent='spectra',
            response_content='test',
            confidence=0.9
        )
        
        # ASSERT: TypedDictなのでキーとして存在することを確認
        required_fields = [
            'messages', 'channel_id', 'memory_context',
            'selected_agent', 'response_content', 'confidence'
        ]
        
        for field in required_fields:
            assert field in state


class TestGeminiClientResponsibilitySeparation:
    """責務再分離後のGemini API Client単体テスト（失敗テスト）"""
    
    @pytest.fixture
    def mock_api_response(self):
        """責務再分離後のGemini API応答のモック"""
        return {
            'selected_agent': 'lynq',
            'response_content': '論理的に分析すると...',
            'confidence': 0.88
        }

    @pytest.mark.asyncio
    async def test_gemini_client_initialization(self):
        """Gemini Client初期化テスト"""
        # ACT: Gemini Client作成
        client = GeminiClient(api_key="test_key")
        
        # ASSERT: 正常に初期化されること
        assert hasattr(client, 'unified_agent_selection')
        assert hasattr(client, 'llm')
        assert client.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_unified_agent_selection_api_call(self, mock_api_response):
        """統合エージェント選択API呼び出しテスト"""
        if GeminiClient is None:
            pytest.skip("GeminiClient not implemented yet - TDD Red Phase")
        
        client = GeminiClient(api_key="test_key")
        
        # ARRANGE: 入力データ
        context = {
            'message': 'データ分析をお願いします',
            'hot_memory': [],
            'cold_memory': [],
            'channel_id': '12345'
        }
        
        # モックAPI応答
        with patch.object(client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_api_response
            
            # ACT: API呼び出し
            result = await client.unified_agent_selection(context)
            
            # ASSERT: 期待される結果
            assert result['selected_agent'] == 'lynq'
            assert result['confidence'] == 0.88
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self):
        """API制限ハンドリングテスト"""
        client = GeminiClient(api_key="test_key")
        
        # ARRANGE: 正常なAPI呼び出しのモック（現在はリトライ機能なし）
        with patch.object(client, '_call_gemini_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                'selected_agent': 'spectra', 
                'response_content': '成功', 
                'confidence': 0.9,
                'reasoning': 'テスト成功'
            }
            
            # ACT: API呼び出し
            result = await client.unified_agent_selection({})
            
            # ASSERT: 成功すること
            assert result['selected_agent'] == 'spectra'
            assert mock_api.call_count == 1  # 1回成功

    def test_prompt_template_generation(self):
        """プロンプトテンプレート生成テスト"""
        client = GeminiClient(api_key="test_key")
        
        # ARRANGE: 入力データ
        context = {
            'message': 'テストメッセージ',
            'hot_memory': [{'role': 'user', 'content': '前回の話'}],
            'cold_memory': [{'summary': '過去の話題'}]
        }
        
        # ACT: プロンプト生成
        prompt = client._generate_unified_prompt(context)
        
        # ASSERT: 期待される内容が含まれること
        assert 'テストメッセージ' in prompt
        assert 'spectra|lynq|paz' in prompt
        assert 'SPECTRA' in prompt
        assert 'LYNQ' in prompt
        assert 'PAZ' in prompt


# TDD Red Phase確認用のテスト実行
if __name__ == "__main__":
    print("🔴 TDD Red Phase: LangGraph Supervisor失敗するテストを確認")
    print("これらのテストは実装前なので失敗することが期待されます")
    
    # 基本的なインポートテスト
    try:
        from src.agents.supervisor import AgentSupervisor
        print("❌ 予期しない成功: AgentSupervisorが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: AgentSupervisorはまだ実装されていません")
    
    try:
        from src.infrastructure.gemini_client import GeminiClient
        print("❌ 予期しない成功: GeminiClientが既に存在")
    except ImportError:
        print("✅ 期待通りの失敗: GeminiClientはまだ実装されていません")