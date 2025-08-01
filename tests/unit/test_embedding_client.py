"""
Google text-embedding-004クライアントテスト
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from src.infrastructure.embedding_client import GoogleEmbeddingClient, create_embedding_client


class TestGoogleEmbeddingClient:
    """GoogleEmbeddingClientテストクラス"""
    
    def test_init_with_api_key(self):
        """API Key指定初期化テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.task_type == "RETRIEVAL_DOCUMENT"
        assert client.max_tokens == 2048
    
    def test_init_without_api_key_raises_error(self):
        """API Key未指定でエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
                GoogleEmbeddingClient()
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'env-test-key'})
    def test_init_from_environment(self):
        """環境変数からAPI Key取得テスト"""
        client = GoogleEmbeddingClient()
        assert client.api_key == "env-test-key"
    
    def test_truncate_text_short(self):
        """短いテキスト切り詰めテスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        text = "短いテキスト"
        result = client._truncate_text(text)
        assert result == text
    
    def test_truncate_text_long(self):
        """長いテキスト切り詰めテスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        long_text = "a " * 5000  # 長いテキスト生成
        result = client._truncate_text(long_text)
        assert len(result) < len(long_text)
        assert len(result) <= client.max_chars
    
    def test_get_model_info(self):
        """モデル情報取得テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        info = client.get_model_info()
        
        expected_info = {
            "model": "text-embedding-004",
            "provider": "Google",
            "dimensions": 768,
            "max_tokens": 2048,
            "task_type": "RETRIEVAL_DOCUMENT",
            "api_endpoint": "generativelanguage.googleapis.com"
        }
        
        assert info == expected_info
    
    @pytest.mark.asyncio
    async def test_embed_query_success(self):
        """クエリembedding生成成功テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        
        # モック設定
        mock_embedding = [0.1] * 768  # 768次元ベクトル
        
        with patch.object(client, '_generate_embedding_with_retry', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embedding
            
            result = await client.embed_query("test query")
            
            assert result == mock_embedding
            mock_embed.assert_called_once_with("test query", "RETRIEVAL_QUERY")
    
    
    @pytest.mark.asyncio
    async def test_embed_semantic_similarity_success(self):
        """セマンティック類似度embedding生成成功テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        
        mock_embedding = [0.3] * 768
        
        with patch.object(client, '_generate_embedding_with_retry', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = mock_embedding
            
            result = await client.embed_semantic_similarity("test text")
            
            assert result == mock_embedding
            mock_embed.assert_called_once_with("test text", "SEMANTIC_SIMILARITY")
    
    @pytest.mark.asyncio
    async def test_generate_embedding_with_retry_empty_text(self):
        """空テキストでのembedding生成テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        
        result = await client._generate_embedding_with_retry("", "RETRIEVAL_DOCUMENT")
        assert result is None
        
        result = await client._generate_embedding_with_retry("   ", "RETRIEVAL_DOCUMENT")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_embedding_with_retry_success(self):
        """embedding生成リトライ成功テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        
        mock_embedding = [0.4] * 768
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_embedding
            
            result = await client._generate_embedding_with_retry("test text", "RETRIEVAL_DOCUMENT")
            
            assert result == mock_embedding
            mock_to_thread.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embedding_with_retry_failure(self):
        """embedding生成リトライ失敗テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        client.max_retries = 2  # リトライ回数短縮
        client.retry_delay = 0.01  # 遅延短縮
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("API Error")
            
            result = await client._generate_embedding_with_retry("test text", "RETRIEVAL_DOCUMENT")
            
            assert result is None
            assert mock_to_thread.call_count == 2  # リトライ実行確認
    
    @pytest.mark.asyncio
    async def test_generate_embedding_with_retry_different_dimensions(self):
        """異なる次元数でのembedding生成テスト"""
        client = GoogleEmbeddingClient(api_key="test-key")
        
        mock_embedding = [0.5] * 1024  # 1024次元 (768ではない)
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_embedding
            
            result = await client._generate_embedding_with_retry("test text", "RETRIEVAL_DOCUMENT")
            
            assert result == mock_embedding  # 異なる次元でも返される
    
    def test_create_embedding_client_factory(self):
        """ファクトリ関数テスト"""
        client = create_embedding_client(api_key="test-key", task_type="SEMANTIC_SIMILARITY")
        
        assert isinstance(client, GoogleEmbeddingClient)
        assert client.api_key == "test-key"
        assert client.task_type == "SEMANTIC_SIMILARITY"
    
    @pytest.mark.asyncio
    async def test_embed_documents_batch_not_implemented(self):
        client = GoogleEmbeddingClient(api_key="test-key")
        assert hasattr(client, 'embed_documents_batch')
        assert callable(getattr(client, 'embed_documents_batch'))
    
    @pytest.mark.asyncio
    async def test_embed_documents_batch_size_limit_exceeded(self):
        client = GoogleEmbeddingClient(api_key="test-key")
        large_batch = [f"document {i}" for i in range(251)]
        with pytest.raises(ValueError, match="Batch size exceeds limit"):
            await client.embed_documents_batch(large_batch)
    
    @pytest.mark.asyncio
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_embed_documents_batch_rate_limit_compliance(self, mock_sleep):
        client = GoogleEmbeddingClient(api_key="test-key")
        rate_test_batch = [f"rate test doc {i}" for i in range(16)]
        
        with patch.object(client, '_generate_embedding_with_retry', return_value=[0.1] * 768):
            await client.embed_documents_batch(rate_test_batch)
        
        assert mock_sleep.called
    
    @pytest.mark.asyncio
    async def test_embed_documents_batch_empty_list(self):
        client = GoogleEmbeddingClient(api_key="test-key")
        empty_batch = []
        result = await client.embed_documents_batch(empty_batch)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_embed_documents_batch_validation_errors(self):
        client = GoogleEmbeddingClient(api_key="test-key")
        invalid_batch = ["valid doc", 123, None, "another doc"]
        with pytest.raises(TypeError, match="not a string"):
            await client.embed_documents_batch(invalid_batch)
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    async def test_embed_documents_batch_max_valid_size(self, mock_to_thread):
        client = GoogleEmbeddingClient(api_key="test-key")
        max_valid_batch = [f"document {i}" for i in range(250)]
        mock_to_thread.return_value = [[0.1] * 768] * 250
        
        result = await client.embed_documents_batch(max_valid_batch)
        assert len(result) == 250
        assert mock_to_thread.called


class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_embedding_generation(self):
        """実際のembedding生成テスト (GEMINI_API_KEYが設定されている場合のみ)"""
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set, skipping integration test")
        
        client = GoogleEmbeddingClient(api_key=api_key)
        
        # 実際のembedding生成
        result = await client.embed_query("Hello, world!")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 768  # text-embedding-004は768次元
        assert all(isinstance(x, (int, float)) for x in result)
    
