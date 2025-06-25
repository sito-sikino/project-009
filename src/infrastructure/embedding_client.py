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
        バッチ文書embedding生成 (最大250件、15RPM制限対応)

        Args:
            texts: 文書テキストリスト

        Returns:
            List[Optional[List[float]]]: 各文書の768次元embedding
        """
        start_time = asyncio.get_event_loop().time()
        self.logger.info(f"Starting batch embedding for {len(texts)} documents")

        if not texts:
            self.logger.debug("Empty batch provided, returning empty list")
            return []

        batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '250'))
        if len(texts) > batch_size:
            self.logger.error(f"Batch size validation failed: {len(texts)} > {batch_size}")
            raise ValueError(f"Batch size exceeds limit: {len(texts)} > {batch_size}")

        invalid_items = []
        for i, text in enumerate(texts):
            if not isinstance(text, str):
                invalid_items.append(f"index {i}: {type(text)}")

        if invalid_items:
            error_msg = f"Non-string items found at {', '.join(invalid_items)}"
            self.logger.error(f"Type validation failed: {error_msg}")
            raise TypeError(error_msg)

        rpm_limit = int(os.getenv('EMBEDDING_RPM_LIMIT', '15'))
        delay_per_item = 60.0 / rpm_limit if len(texts) > 1 else 0
        self.logger.debug(f"Rate limit: {rpm_limit} RPM, delay per item: {delay_per_item:.2f}s")

        try:
            self.logger.debug("Attempting batch processing with aembed_documents")
            batch_client = GoogleGenerativeAIEmbeddings(
                model="text-embedding-004",
                google_api_key=self.api_key,
                task_type="RETRIEVAL_DOCUMENT"
            )

            embeddings = await asyncio.to_thread(batch_client.aembed_documents, texts)

            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(f"Batch embedding completed successfully in {elapsed_time:.2f}s")

            if len(texts) > 1:
                await asyncio.sleep(delay_per_item * len(texts))

            return embeddings

        except Exception as e:
            self.logger.warning(f"Batch processing failed, falling back to individual processing: {e}")

            results = []
            failed_count = 0

            for i, text in enumerate(texts):
                try:
                    embedding = await self._generate_embedding_with_retry(text, "RETRIEVAL_DOCUMENT")
                    results.append(embedding)

                    if embedding is None:
                        failed_count += 1
                        self.logger.warning(f"Failed to generate embedding for item {i}")

                except Exception as item_error:
                    self.logger.error(f"Individual processing failed for item {i}: {item_error}")
                    results.append(None)
                    failed_count += 1

                if delay_per_item > 0:
                    await asyncio.sleep(delay_per_item)

            elapsed_time = asyncio.get_event_loop().time() - start_time
            success_count = len(texts) - failed_count
            self.logger.info(
                f"Fallback processing completed: {success_count}/{len(texts)} successful in {elapsed_time:.2f}s"
            )

            return results

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
