"""
Long-term Memory System with 3-API Batch Processing
3-API設計による長期記憶システム（価値判定・重複検出・embedding生成）
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import redis.asyncio as redis
import asyncpg
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from .deduplication_system import MinHashDeduplicator, MemoryItem, create_memory_item_from_dict
from .memory_system import ImprovedDiscordMemorySystem


@dataclass
class ProcessedMemory:
    """処理済み記憶（3-API処理後）"""
    id: str
    original_content: str
    structured_content: str
    timestamp: datetime
    channel_id: int
    user_id: str
    memory_type: str
    entities: List[Dict[str, str]]  # 抽出されたエンティティ
    importance_score: float
    progress_indicators: Dict[str, Any]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    minhash_signature: Optional[bytes] = None


@dataclass
class ProgressDifferential:
    """進捗差分（前日比較結果）"""
    date: datetime
    new_entities: List[str]
    progressed_entities: List[str]
    stagnant_entities: List[str]
    completed_tasks: List[str]
    new_skills: List[str]
    overall_summary: str


class LongTermMemoryProcessor:
    """3-API長期記憶処理システム"""
    
    def __init__(self,
                 redis_url: str = None,
                 postgres_url: str = None,
                 gemini_api_key: str = None):
        
        self.logger = logging.getLogger(__name__)
        
        # 基盤メモリシステム
        self.memory_system = ImprovedDiscordMemorySystem(
            redis_url=redis_url,
            postgres_url=postgres_url,
            gemini_api_key=gemini_api_key
        )
        
        # Gemini 2.0 Flash（統合分析用）
        self.gemini_flash = GoogleGenerativeAI(
            model="models/gemini-2.0-flash-exp",
            google_api_key=gemini_api_key,
            temperature=0.1
        )
        
        # Embedding client
        self.embeddings_client = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=gemini_api_key
        )
        
        # 重複検出システム
        self.deduplicator = MinHashDeduplicator(
            threshold=0.8,  # 高精度重複検出
            num_perm=128
        )
        
        # API使用量カウンター（1日3回制限）
        self.api_usage_count = 0
        self.last_processing_date = None
        
    async def initialize(self):
        """システム初期化"""
        await self.memory_system.initialize()
        self.logger.info("Long-term Memory Processor initialized")
    
    async def daily_memory_consolidation(self, 
                                       target_date: datetime = None) -> Tuple[List[ProcessedMemory], ProgressDifferential]:
        """
        日次記憶統合処理（3-API）
        
        Returns:
            (処理済み記憶一覧, 進捗差分)
        """
        if target_date is None:
            target_date = datetime.now()
        
        # API使用量チェック
        if not self._check_api_quota(target_date):
            raise RuntimeError("API使用量制限超過（1日3回制限）")
        
        self.logger.info(f"🧠 長期記憶化処理開始: {target_date.strftime('%Y-%m-%d')}")
        start_time = datetime.now()
        
        try:
            # 1. Redisからの記憶データ取得
            raw_memories = await self._fetch_daily_memories(target_date)
            self.logger.info(f"📊 取得記憶数: {len(raw_memories)}件")
            
            if not raw_memories:
                self.logger.warning("処理対象記憶なし")
                return [], ProgressDifferential(
                    date=target_date,
                    new_entities=[], progressed_entities=[], stagnant_entities=[],
                    completed_tasks=[], new_skills=[],
                    overall_summary="処理対象記憶なし"
                )
            
            # 2. API 1: Gemini 2.0 Flash統合分析
            processed_memories = await self._api1_unified_analysis(raw_memories)
            self.api_usage_count += 1
            self.logger.info(f"✅ API 1完了: {len(processed_memories)}件処理")
            
            # 3. MinHash重複除去（API不要）
            unique_memories = self._remove_duplicates(processed_memories)
            duplicate_ratio = (len(processed_memories) - len(unique_memories)) / len(processed_memories) * 100
            self.logger.info(f"🔍 重複除去: {duplicate_ratio:.1f}% ({len(unique_memories)}件残存)")
            
            # 4. API 2: 進捗差分生成
            progress_diff = await self._api2_progress_differential(unique_memories, target_date)
            self.api_usage_count += 1
            self.logger.info("✅ API 2完了: 進捗差分生成")
            
            # 5. API 3: バッチembedding生成
            final_memories = await self._api3_batch_embeddings(unique_memories)
            self.api_usage_count += 1
            self.logger.info(f"✅ API 3完了: {len(final_memories)}件embedding生成")
            
            # 6. PostgreSQL保存
            saved_count = await self._store_unified_memories(final_memories)
            self.logger.info(f"💾 PostgreSQL保存: {saved_count}件")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"🎉 長期記憶化完了: {processing_time:.1f}秒, API使用量: 3回")
            
            return final_memories, progress_diff
            
        except Exception as e:
            self.logger.error(f"❌ 長期記憶化エラー: {e}")
            raise
    
    async def _fetch_daily_memories(self, target_date: datetime) -> List[Dict[str, Any]]:
        """Redis から指定日の記憶データ取得"""
        date_key = target_date.strftime('%Y-%m-%d')
        
        # Redis接続
        redis_client = redis.from_url(self.memory_system.redis_url)
        
        # 日次記憶キー取得
        pattern = f"memory:{date_key}:*"
        keys = await redis_client.keys(pattern)
        
        memories = []
        for key in keys:
            data = await redis_client.hgetall(key)
            if data:
                # バイナリデータをデコード
                decoded_data = {k.decode(): v.decode() for k, v in data.items()}
                memories.append(decoded_data)
        
        await redis_client.close()
        return memories
    
    async def _api1_unified_analysis(self, raw_memories: List[Dict[str, Any]]) -> List[ProcessedMemory]:
        """API 1: Gemini 2.0 Flash統合分析"""
        self.logger.info("🔍 API 1: Gemini 2.0 Flash統合分析開始")
        
        # プロンプト構築
        analysis_prompt = self._build_unified_analysis_prompt(raw_memories)
        
        # Gemini 2.0 Flash実行
        response = await self.gemini_flash.ainvoke(analysis_prompt)
        
        # 応答パース
        processed_memories = self._parse_analysis_response(response, raw_memories)
        
        return processed_memories
    
    def _build_unified_analysis_prompt(self, raw_memories: List[Dict[str, Any]]) -> str:
        """統合分析プロンプト構築"""
        memories_json = json.dumps(raw_memories, ensure_ascii=False, indent=2)
        
        return f"""
# Discord記憶統合分析タスク

## 入力データ
以下は1日分のDiscord会話記憶データです：

```json
{memories_json}
```

## 分析要求

各記憶について以下を実行してください：

### 1. 価値判定（0.0-1.0）
- 0.8-1.0: 重要（技術習得、プロジェクト進展、重要決定）
- 0.5-0.7: 中程度（日常作業、議論、アイデア）
- 0.0-0.4: 低（雑談、重複情報）

### 2. エンティティ抽出
技術、人物、プロジェクト、スキル、ツール等を抽出
例: {{"name": "TypeScript", "type": "technology"}}

### 3. 記憶タイプ分類
- conversation: 通常会話
- task: タスク関連
- progress: 進捗報告
- learning: 学習記録
- decision: 意思決定

### 4. 構造化
内容を簡潔で検索しやすい形式に構造化

## 出力フォーマット
```json
[
  {{
    "id": "記憶ID",
    "structured_content": "構造化された内容",
    "memory_type": "分類",
    "entities": [
      {{"name": "エンティティ名", "type": "タイプ"}}
    ],
    "importance_score": 0.8,
    "progress_indicators": {{
      "skill_development": "習得技術",
      "project_advancement": "プロジェクト進展",
      "problem_resolution": "解決課題"
    }}
  }}
]
```

重要性0.4未満は除外してください。エンティティ抽出は包括的に行い、個別具体的要素（TypeScript、転職等）が検索できるようにしてください。
"""
    
    def _parse_analysis_response(self, response: str, raw_memories: List[Dict[str, Any]]) -> List[ProcessedMemory]:
        """分析応答パース"""
        try:
            # JSON部分抽出
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            json_content = response[json_start:json_end]
            
            analysis_results = json.loads(json_content)
            
            # ProcessedMemory作成
            processed_memories = []
            for result in analysis_results:
                # 元記憶データ検索
                original_memory = next(
                    (m for m in raw_memories if m.get('id') == result['id']),
                    None
                )
                
                if original_memory:
                    processed_memory = ProcessedMemory(
                        id=result['id'],
                        original_content=original_memory.get('content', ''),
                        structured_content=result['structured_content'],
                        timestamp=datetime.fromisoformat(original_memory.get('timestamp', datetime.now().isoformat())),
                        channel_id=int(original_memory.get('channel_id', 0)),
                        user_id=original_memory.get('user_id', ''),
                        memory_type=result['memory_type'],
                        entities=result['entities'],
                        importance_score=result['importance_score'],
                        progress_indicators=result.get('progress_indicators', {}),
                        metadata=original_memory.get('metadata', {})
                    )
                    processed_memories.append(processed_memory)
            
            return processed_memories
            
        except Exception as e:
            self.logger.error(f"分析応答パースエラー: {e}")
            return []
    
    def _remove_duplicates(self, processed_memories: List[ProcessedMemory]) -> List[ProcessedMemory]:
        """MinHash重複除去"""
        memory_items = []
        for memory in processed_memories:
            item = MemoryItem(
                id=memory.id,
                content=memory.structured_content,
                timestamp=memory.timestamp,
                channel_id=memory.channel_id,
                user_id=memory.user_id,
                memory_type=memory.memory_type,
                metadata=memory.metadata
            )
            memory_items.append(item)
        
        # 重複除去実行
        unique_items = self.deduplicator.batch_deduplicate(memory_items)
        
        # ProcessedMemory形式に戻す
        unique_ids = {item.id for item in unique_items}
        unique_memories = [m for m in processed_memories if m.id in unique_ids]
        
        # MinHashシグネチャ追加
        signatures = self.deduplicator.export_minhash_signatures()
        for memory in unique_memories:
            memory.minhash_signature = signatures.get(memory.id)
        
        return unique_memories
    
    async def _api2_progress_differential(self, 
                                        memories: List[ProcessedMemory], 
                                        target_date: datetime) -> ProgressDifferential:
        """API 2: 進捗差分生成"""
        self.logger.info("📈 API 2: 進捗差分生成開始")
        
        # 前日記憶取得
        previous_date = target_date - timedelta(days=1)
        previous_snapshot = await self._get_previous_memory_snapshot(previous_date)
        
        # 差分分析プロンプト
        diff_prompt = self._build_progress_diff_prompt(memories, previous_snapshot, target_date)
        
        # Gemini実行
        response = await self.gemini_flash.ainvoke(diff_prompt)
        
        # 差分結果パース
        progress_diff = self._parse_progress_diff_response(response, target_date)
        
        return progress_diff
    
    async def _api3_batch_embeddings(self, memories: List[ProcessedMemory]) -> List[ProcessedMemory]:
        """API 3: バッチembedding生成"""
        self.logger.info("🔗 API 3: バッチembedding生成開始")
        
        # 全テキスト結合
        texts = [memory.structured_content for memory in memories]
        
        # バッチembedding生成
        embeddings = await self.embeddings_client.aembed_documents(texts)
        
        # embedding割り当て
        for memory, embedding in zip(memories, embeddings):
            memory.embedding = embedding
        
        return memories
    
    async def _store_unified_memories(self, memories: List[ProcessedMemory]) -> int:
        """PostgreSQL統一記憶保存"""
        if not memories:
            return 0
        
        # PostgreSQL接続
        conn = await asyncpg.connect(self.memory_system.postgres_url)
        
        try:
            saved_count = 0
            for memory in memories:
                await conn.execute("""
                    INSERT INTO unified_memories (
                        id, timestamp, channel_id, user_id, message_id,
                        content, memory_type, metadata, embedding,
                        minhash_signature, entities, progress_type, importance_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (id) DO NOTHING
                """, 
                    memory.id,
                    memory.timestamp,
                    memory.channel_id,
                    memory.user_id,
                    None,  # message_id
                    memory.structured_content,
                    memory.memory_type,
                    json.dumps(memory.metadata),
                    memory.embedding,
                    memory.minhash_signature,
                    json.dumps(memory.entities),
                    memory.progress_indicators.get('project_advancement', ''),
                    memory.importance_score
                )
                saved_count += 1
            
            return saved_count
            
        finally:
            await conn.close()
    
    def _check_api_quota(self, target_date: datetime) -> bool:
        """API使用量制限チェック（1日3回）"""
        current_date = target_date.date()
        
        if self.last_processing_date != current_date:
            # 新しい日 - リセット
            self.api_usage_count = 0
            self.last_processing_date = current_date
            return True
        
        return self.api_usage_count < 3
    
    # 他のヘルパーメソッド（progress_diff関連）は簡略化して後で実装
    async def _get_previous_memory_snapshot(self, date: datetime) -> Dict[str, Any]:
        """前日記憶スナップショット取得（簡略版）"""
        return {"entities": [], "summary": "前日データなし"}
    
    def _build_progress_diff_prompt(self, memories, previous_snapshot, target_date) -> str:
        """進捗差分プロンプト構築（簡略版）"""
        return f"進捗差分を分析してください。日付: {target_date.strftime('%Y-%m-%d')}"
    
    def _parse_progress_diff_response(self, response: str, target_date: datetime) -> ProgressDifferential:
        """進捗差分応答パース（簡略版）"""
        return ProgressDifferential(
            date=target_date,
            new_entities=[],
            progressed_entities=[],
            stagnant_entities=[],
            completed_tasks=[],
            new_skills=[],
            overall_summary="進捗差分処理完了"
        )