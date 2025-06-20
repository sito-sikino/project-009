# Google text-embedding-004実装ガイド

## 概要

project-009でGoogle text-embedding-004を使用したembedding生成システムの実装ガイドです。OpenAI APIの代替として、Gemini APIとlangchain-google-genaiを活用したソリューションを提供します。

## text-embedding-004仕様

### 基本仕様
- **モデル名**: `text-embedding-004`
- **提供元**: Google (Gemini API)
- **次元数**: 768次元 (デフォルト)
- **最大入力**: 2,048トークン
- **API認証**: Gemini API Key使用

### 技術特性
- **パフォーマンス**: OpenAI text-embedding-3-smallと同等レベル
- **多言語対応**: 日本語を含む多言語サポート
- **task_type設定**: 用途別最適化対応
- **出力調整**: `output_dimensionality`で次元数変更可能

## 実装アーキテクチャ

### 1. 基本構成

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# 基本設定
embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    google_api_key=os.getenv('GEMINI_API_KEY'),
    task_type="RETRIEVAL_DOCUMENT"
)

# embedding生成
vector = await asyncio.to_thread(embeddings.embed_query, "テキスト")
```

### 2. task_type設定パターン

| task_type | 用途 | 説明 |
|-----------|------|------|
| `RETRIEVAL_QUERY` | 検索クエリ | セマンティック検索のクエリ側 |
| `RETRIEVAL_DOCUMENT` | 文書インデックス | セマンティック検索の文書側 |
| `SEMANTIC_SIMILARITY` | 類似度計算 | 一般的なテキスト類似度 |

### 3. Memory System統合

#### 変更前 (OpenAI)
```python
# OpenAI使用
self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)

response = await self.openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=text,
    encoding_format="float"
)
embedding = response.data[0].embedding
```

#### 変更後 (Google)
```python
# Google text-embedding-004使用
self.embeddings_client = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    google_api_key=gemini_api_key,
    task_type="RETRIEVAL_DOCUMENT"
)

embedding = await asyncio.to_thread(
    self.embeddings_client.embed_query, 
    text
)
```

## 実装手順

### Step 1: 依存関係確認

```bash
# 既にproject-009にインストール済み
pip install langchain-google-genai==2.0.5
```

### Step 2: 環境変数設定

```bash
# .env または環境変数
export GEMINI_API_KEY="your-gemini-api-key"
```

### Step 3: Memory System更新

主要変更ファイル: `/home/sito/project-009/src/memory_system.py`

```python
# 主要変更点
- import openai
+ from langchain_google_genai import GoogleGenerativeAIEmbeddings

- openai_api_key: str = None
+ gemini_api_key: str = None

- self.openai_client = openai.AsyncOpenAI(...)
+ self.embeddings_client = GoogleGenerativeAIEmbeddings(...)

- self.embedding_model = "text-embedding-3-small"
+ self.embedding_model = "text-embedding-004"
```

### Step 4: 専用クライアント作成

新規ファイル: `/home/sito/project-009/src/embedding_client.py`

```python
from src.embedding_client import GoogleEmbeddingClient

# 用途別クライアント作成
query_client = GoogleEmbeddingClient(task_type="RETRIEVAL_QUERY")
doc_client = GoogleEmbeddingClient(task_type="RETRIEVAL_DOCUMENT")

# embedding生成
query_vector = await query_client.embed_query("検索クエリ")
doc_vectors = await doc_client.embed_documents(["文書1", "文書2"])
```

## パフォーマンス最適化

### 1. トークン制限対応

```python
def _truncate_text(self, text: str) -> str:
    max_chars = 2048 * 4  # トークン数概算
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    # 単語境界で切り詰め
    if ' ' in truncated:
        truncated = truncated.rsplit(' ', 1)[0]
    
    return truncated
```

### 2. バッチ処理最適化

```python
async def embed_documents_batch(self, texts: List[str]) -> List[List[float]]:
    # 並列処理でバッチ処理高速化
    tasks = [self.embed_query(text) for text in texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### 3. リトライ機能

```python
async def _generate_embedding_with_retry(self, text: str) -> Optional[List[float]]:
    for attempt in range(self.max_retries):
        try:
            return await asyncio.to_thread(self.client.embed_query, text)
        except Exception as e:
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            else:
                self.logger.error(f"All attempts failed: {e}")
                return None
```

## エラーハンドリング

### 1. 一般的なエラーパターン

```python
try:
    embedding = await client.embed_query(text)
except Exception as e:
    if "API_KEY" in str(e):
        logger.error("API Key認証エラー")
    elif "QUOTA" in str(e):
        logger.error("API使用量制限エラー")
    elif "INVALID_REQUEST" in str(e):
        logger.error("リクエスト形式エラー")
    else:
        logger.error(f"予期しないエラー: {e}")
```

### 2. レート制限対応

```python
import asyncio
from functools import wraps

def rate_limit(calls_per_second: float):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## テスト戦略

### 1. 単体テスト

```python
# tests/unit/test_embedding_client.py
@pytest.mark.asyncio
async def test_embed_query_success():
    client = GoogleEmbeddingClient(api_key="test-key")
    
    with patch.object(client, '_generate_embedding_with_retry') as mock_embed:
        mock_embed.return_value = [0.1] * 768
        
        result = await client.embed_query("test query")
        assert len(result) == 768
```

### 2. 統合テスト

```python
@pytest.mark.integration
async def test_real_embedding_generation():
    if not os.getenv('GEMINI_API_KEY'):
        pytest.skip("GEMINI_API_KEY not set")
    
    client = GoogleEmbeddingClient()
    result = await client.embed_query("Hello, world!")
    
    assert result is not None
    assert len(result) == 768
```

### 3. パフォーマンステスト

```python
@pytest.mark.performance
async def test_embedding_performance():
    client = GoogleEmbeddingClient()
    
    start_time = time.time()
    results = await client.embed_documents(["text"] * 10)
    end_time = time.time()
    
    assert (end_time - start_time) < 30  # 30秒以内
    assert len(results) == 10
```

## 本番環境デプロイ

### 1. 環境変数設定

```bash
# 本番環境
export GEMINI_API_KEY="prod-gemini-key"
export REDIS_URL="redis://prod-redis:6379"
export POSTGRESQL_URL="postgresql://user:pass@prod-db:5432/discord_agent"
```

### 2. モニタリング設定

```python
import logging
import time

class EmbeddingMetrics:
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_latency = 0.0
    
    async def track_embedding_request(self, func, *args, **kwargs):
        self.request_count += 1
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            self.success_count += 1
            return result
        except Exception as e:
            self.error_count += 1
            raise
        finally:
            self.total_latency += (time.time() - start_time)
    
    def get_metrics(self):
        return {
            "requests": self.request_count,
            "success_rate": self.success_count / self.request_count if self.request_count > 0 else 0,
            "avg_latency": self.total_latency / self.request_count if self.request_count > 0 else 0
        }
```

### 3. ヘルスチェック

```python
async def health_check():
    try:
        client = GoogleEmbeddingClient()
        test_embedding = await client.embed_query("health check")
        return {
            "status": "healthy",
            "embedding_service": "operational",
            "dimensions": len(test_embedding) if test_embedding else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "embedding_service": "error",
            "error": str(e)
        }
```

## ベストプラクティス

### 1. セキュリティ

- **API Key管理**: 環境変数で管理、ソースコードにハードコーディング禁止
- **トークン制限**: 入力テキスト長の事前チェック実装
- **レート制限**: API呼び出し頻度の制御

### 2. パフォーマンス

- **キャッシュ活用**: 同一テキストのembedding結果をキャッシュ
- **バッチ処理**: 複数テキストの並列処理
- **非同期処理**: `asyncio.to_thread`でブロッキングを回避

### 3. 可用性

- **リトライ機能**: 指数バックオフによるリトライ
- **フォールバック**: 代替embedding生成手段の準備
- **監視・アラート**: 失敗率・レイテンシの監視

### 4. コスト最適化

- **トークン効率**: 不要な長文の事前カット
- **結果キャッシュ**: Redis等でembedding結果キャッシュ
- **用途別最適化**: task_type設定で精度向上

## 移行チェックリスト

- [ ] langchain-google-genai依存関係確認
- [ ] GEMINI_API_KEY環境変数設定
- [ ] memory_system.py OpenAI→Google変更
- [ ] embedding_client.py新規作成
- [ ] 単体テスト実装・実行
- [ ] 統合テスト実行
- [ ] パフォーマンステスト実行
- [ ] 本番環境デプロイ準備
- [ ] 監視・アラート設定
- [ ] ドキュメント更新

## トラブルシューティング

### よくある問題と解決方法

1. **API Key認証エラー**
   - GEMINI_API_KEY環境変数の設定確認
   - API Keyの有効性確認

2. **次元数不一致**
   - text-embedding-004は768次元
   - PostgreSQLのvectorカラム定義確認

3. **レート制限エラー**
   - リトライ機能の実装
   - API呼び出し頻度の調整

4. **メモリ使用量増加**
   - embedding結果のキャッシュ戦略見直し
   - バッチサイズの調整

---

このガイドに従ってtext-embedding-004を実装することで、project-009でGoogle Gemini APIを活用した高性能なembedding生成システムを構築できます。