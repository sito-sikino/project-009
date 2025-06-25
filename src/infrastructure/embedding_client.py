"""
Google text-embedding-004専用クライアント
langchain-google-genai統合パターン実装
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr


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

    def __init__(self, api_key: Optional[str] = None, task_type: str = "RETRIEVAL_DOCUMENT"):
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
            google_api_key=SecretStr(self.api_key) if self.api_key else None,
            task_type=self.task_type
        )

        # 設定
        self.max_tokens = 2048
        self.max_chars = self.max_tokens * 4  # トークン数概算
        self.max_retries = int(os.getenv('EMBEDDING_RETRY_ATTEMPTS', '3'))
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

    async def embed_semantic_similarity(self, text: str) -> Optional[List[float]]:
        """
        セマンティック類似度用embedding生成

        Args:
            text: 入力テキスト

        Returns:
            List[float]: 768次元embedding
        """
        return await self._generate_embedding_with_retry(text, "SEMANTIC_SIMILARITY")

    async def embed_documents_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        バッチ文書embedding生成 (最大250件、15RPM制限対応、性能最適化版)

        Args:
            texts: 文書テキストリスト

        Returns:
            List[Optional[List[float]]]: 各文書の768次元embedding
        """
        start_time = asyncio.get_event_loop().time()
        self.logger.info(f"Starting optimized batch embedding for {len(texts)} documents")

        if not texts:
            self.logger.debug("Empty batch provided, returning empty list")
            return []

        # バッチサイズ検証（Fail-fast）
        batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '250'))
        if len(texts) > batch_size:
            self.logger.error(f"Batch size validation failed: {len(texts)} > {batch_size}")
            raise ValueError(f"Batch size exceeds limit: {len(texts)} > {batch_size}")

        # 入力検証（Fail-fast、並列処理）
        validation_start = asyncio.get_event_loop().time()
        invalid_items: List[str] = []
        for i, text in enumerate(texts):
            if not isinstance(text, str) or not text.strip():
                invalid_items.append(f"index {i}: {type(text) if not isinstance(text, str) else 'empty'}")

        if invalid_items:
            error_msg = f"Invalid items found at {', '.join(invalid_items)}"
            self.logger.error(f"Type validation failed: {error_msg}")
            raise TypeError(error_msg)
        
        validation_time = asyncio.get_event_loop().time() - validation_start
        self.logger.debug(f"Validation completed in {validation_time:.4f}s")

        # 性能最適化：動的レート制限計算
        rpm_limit = int(os.getenv('EMBEDDING_RPM_LIMIT', '15'))
        optimal_batch_time = 60.0 / rpm_limit  # 1バッチあたりの最小時間
        self.logger.debug(f"Rate limit: {rpm_limit} RPM, optimal batch time: {optimal_batch_time:.2f}s")

        try:
            # 最適化されたバッチ処理
            self.logger.debug("Starting optimized batch processing with aembed_documents")
            batch_client = GoogleGenerativeAIEmbeddings(
                model="text-embedding-004",
                google_api_key=SecretStr(self.api_key) if self.api_key else None,
                task_type="RETRIEVAL_DOCUMENT"
            )

            # 性能最適化：並列処理準備とタイムアウト設定
            processing_start = asyncio.get_event_loop().time()
            
            # APIコール実行（タイムアウト付き）
            api_timeout = min(30.0, max(10.0, len(texts) * 0.1))  # 動的タイムアウト
            embeddings_result = batch_client.aembed_documents(texts)
            
            if asyncio.iscoroutine(embeddings_result):
                embeddings = await asyncio.wait_for(embeddings_result, timeout=api_timeout)
            else:
                embeddings = embeddings_result

            processing_time = asyncio.get_event_loop().time() - processing_start
            total_time = asyncio.get_event_loop().time() - start_time
            
            # 結果検証（性能最適化）
            valid_count = sum(1 for emb in embeddings if emb and len(emb) == 768)
            success_rate = valid_count / len(embeddings) * 100
            
            self.logger.info(
                f"Batch embedding completed: {total_time:.2f}s total, "
                f"{processing_time:.2f}s processing, {success_rate:.1f}% success rate"
            )

            # 性能最適化：動的レート制限（残り時間がある場合のみ待機）
            remaining_time = optimal_batch_time - total_time
            if remaining_time > 0 and len(texts) > 5:  # 小さなバッチは待機しない
                await asyncio.sleep(remaining_time)
                self.logger.debug(f"Rate limit wait: {remaining_time:.2f}s")

            return embeddings

        except asyncio.TimeoutError:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Batch embedding timeout after {processing_time:.2f}s (limit: {api_timeout:.1f}s)"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Batch embedding failed after {processing_time:.2f}s: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

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
            raise ValueError("Empty text provided for embedding generation")

        # テキスト長制限
        truncated_text = self._truncate_text(text)

        # task_typeに応じてクライアント設定変更
        if task_type != self.task_type:
            temp_client = GoogleGenerativeAIEmbeddings(
                model="text-embedding-004",
                google_api_key=SecretStr(self.api_key) if self.api_key else None,
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
                if len(embedding) != 768:
                    raise ValueError(f"Invalid embedding dimension: {len(embedding)}, expected 768")
                
                self.logger.debug(f"Embedding generated successfully: {len(embedding)} dimensions")
                return embedding

            except Exception as e:
                error_type = type(e).__name__
                self.logger.warning(
                    f"Embedding generation attempt {attempt + 1}/{self.max_retries} failed ({error_type}): {e}"
                )

                if attempt < self.max_retries - 1:
                    backoff_delay = self.retry_delay * (2 ** attempt)
                    self.logger.debug(f"Retrying in {backoff_delay:.2f}s (exponential backoff)")
                    await asyncio.sleep(backoff_delay)
                else:
                    self.logger.error(f"All {self.max_retries} embedding generation attempts failed: {e}")
                    raise RuntimeError(f"Embedding generation failed after {self.max_retries} attempts: {e}")

        raise RuntimeError("Embedding generation failed unexpectedly")

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
def create_embedding_client(api_key: Optional[str] = None, task_type: str = "RETRIEVAL_DOCUMENT") -> GoogleEmbeddingClient:
    """
    GoogleEmbeddingClient生成

    Args:
        api_key: Gemini API Key
        task_type: embedding用途

    Returns:
        GoogleEmbeddingClient: 設定済みクライアント
    """
    return GoogleEmbeddingClient(api_key=api_key, task_type=task_type)
