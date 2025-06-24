"""
Google text-embedding-004専用クライアント
langchain-google-genai統合パターン実装
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class GoogleEmbeddingClient:
    """
    Google text-embedding-004専用クライアント
    
    Features:
    - text-embedding-004使用
    - 768次元ベクトル生成
    - 2,048トークン制限対応
    - task_type設定対応
    - エラーハンドリング・リトライ機能
    """
    
    def __init__(self, api_key: str = None, task_type: str = "RETRIEVAL_DOCUMENT"):
        """
        クライアント初期化
        
        Args:
            api_key: Gemini API Key
            task_type: embedding用途 ("RETRIEVAL_DOCUMENT", "SEMANTIC_SIMILARITY", etc.)
        """
        self.api_key = api_key if api_key else os.getenv('GEMINI_API_KEY')
        self.task_type = task_type
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # GoogleGenerativeAIEmbeddings初期化
        self.client = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004",
            google_api_key=self.api_key,
            task_type=self.task_type
        )
        
        # 設定
        self.max_tokens = 2048
        self.max_chars = self.max_tokens * 4  # トークン数概算
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # ログ
        self.logger = logging.getLogger(__name__)
    
    async def embed_query(self, text: str) -> Optional[List[float]]:
        """
        クエリ用embedding生成 (RETRIEVAL_QUERY task_type)
        
        Args:
            text: 検索クエリテキスト
            
        Returns:
            List[float]: 768次元embedding
        """
        return await self._generate_embedding_with_retry(text, "RETRIEVAL_QUERY")
    
    async def embed_documents(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        文書用embedding生成 (RETRIEVAL_DOCUMENT task_type)
        
        Args:
            texts: 文書テキストリスト
            
        Returns:
            List[Optional[List[float]]]: embedding一覧
        """
        results = []
        for text in texts:
            embedding = await self._generate_embedding_with_retry(text, "RETRIEVAL_DOCUMENT")
            results.append(embedding)
        return results
    
    async def embed_semantic_similarity(self, text: str) -> Optional[List[float]]:
        """
        セマンティック類似度用embedding生成
        
        Args:
            text: 入力テキスト
            
        Returns:
            List[float]: 768次元embedding
        """
        return await self._generate_embedding_with_retry(text, "SEMANTIC_SIMILARITY")
    
    async def _generate_embedding_with_retry(self, text: str, task_type: str) -> Optional[List[float]]:
        """
        リトライ機能付きembedding生成
        
        Args:
            text: 入力テキスト
            task_type: embedding用途
            
        Returns:
            List[float]: 768次元embedding
        """
        if not text.strip():
            return None
        
        # テキスト長制限
        truncated_text = self._truncate_text(text)
        
        # task_typeに応じてクライアント設定変更
        if task_type != self.task_type:
            temp_client = GoogleGenerativeAIEmbeddings(
                model="text-embedding-004",
                google_api_key=self.api_key,
                task_type=task_type
            )
        else:
            temp_client = self.client
        
        # リトライ実行
        for attempt in range(self.max_retries):
            try:
                embedding = await asyncio.to_thread(
                    temp_client.embed_query,
                    truncated_text
                )
                
                # 768次元確認
                if len(embedding) == 768:
                    self.logger.debug(f"Embedding generated successfully: {len(embedding)} dimensions")
                    return embedding
                else:
                    self.logger.warning(f"Unexpected embedding dimension: {len(embedding)}")
                    return embedding  # 異なる次元でも返す
                
            except Exception as e:
                self.logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"All embedding generation attempts failed: {e}")
                    return None
        
        return None
    
    def _truncate_text(self, text: str) -> str:
        """
        text-embedding-004のトークン制限対応テキスト切り詰め
        
        Args:
            text: 入力テキスト
            
        Returns:
            str: 切り詰めテキスト
        """
        if len(text) <= self.max_chars:
            return text
        
        # 文字数制限で切り詰め
        truncated = text[:self.max_chars]
        
        # 単語境界で切り詰め (英語対応)
        if ' ' in truncated:
            truncated = truncated.rsplit(' ', 1)[0]
        
        self.logger.debug(f"Text truncated from {len(text)} to {len(truncated)} characters")
        return truncated
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        モデル情報取得
        
        Returns:
            Dict: モデル情報
        """
        return {
            "model": "text-embedding-004",
            "provider": "Google",
            "dimensions": 768,
            "max_tokens": self.max_tokens,
            "task_type": self.task_type,
            "api_endpoint": "generativelanguage.googleapis.com"
        }


# Factory Function
def create_embedding_client(api_key: str = None, task_type: str = "RETRIEVAL_DOCUMENT") -> GoogleEmbeddingClient:
    """
    GoogleEmbeddingClient生成
    
    Args:
        api_key: Gemini API Key
        task_type: embedding用途
        
    Returns:
        GoogleEmbeddingClient: 設定済みクライアント
    """
    return GoogleEmbeddingClient(api_key=api_key, task_type=task_type)