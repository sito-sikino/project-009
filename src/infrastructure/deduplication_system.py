"""
MinHash/LSH-based Deduplication System for Long-term Memory
datasketchライブラリを使用したAPI不要の重複検出システム
"""

import hashlib
import json
import logging
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from datasketch import MinHash, MinHashLSH


@dataclass
class MemoryItem:
    """記憶アイテム（重複検出用）"""
    id: str
    content: str
    timestamp: datetime
    channel_id: int
    user_id: str
    memory_type: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式への変換"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ContentNormalizer:
    """コンテンツ正規化（重複検出精度向上）"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """テキスト正規化"""
        # 1. 小文字化
        normalized = text.lower()
        
        # 2. URL除去
        normalized = re.sub(r'https?://[^\s]+', '', normalized)
        
        # 3. メンション除去
        normalized = re.sub(r'<@[!&]?[0-9]+>', '', normalized)
        
        # 4. 絵文字・記号の統一
        normalized = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', normalized)
        
        # 5. 連続空白を単一空白に
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 6. 前後空白除去
        return normalized.strip()
    
    @staticmethod
    def extract_shingles(text: str, k: int = 3) -> Set[str]:
        """k-gram shingles抽出（文字レベル）"""
        normalized = ContentNormalizer.normalize_text(text)
        if len(normalized) < k:
            return {normalized}
        
        shingles = set()
        for i in range(len(normalized) - k + 1):
            shingle = normalized[i:i + k]
            shingles.add(shingle)
        return shingles
    
    @staticmethod
    def extract_word_shingles(text: str, k: int = 2) -> Set[str]:
        """k-gram shingles抽出（単語レベル）"""
        normalized = ContentNormalizer.normalize_text(text)
        words = normalized.split()
        if len(words) < k:
            return {' '.join(words)}
        
        shingles = set()
        for i in range(len(words) - k + 1):
            shingle = ' '.join(words[i:i + k])
            shingles.add(shingle)
        return shingles


class MinHashDeduplicator:
    """MinHash/LSH重複検出システム"""
    
    def __init__(self, 
                 num_perm: int = 128,
                 threshold: float = 0.8,
                 char_shingle_size: int = 3,
                 word_shingle_size: int = 2):
        """
        初期化
        
        Args:
            num_perm: MinHashの順列数（精度vs速度のトレードオフ）
            threshold: 重複判定閾値（0.0-1.0）
            char_shingle_size: 文字レベルshingleサイズ
            word_shingle_size: 単語レベルshingleサイズ
        """
        self.num_perm = num_perm
        self.threshold = threshold
        self.char_shingle_size = char_shingle_size
        self.word_shingle_size = word_shingle_size
        
        # LSHインデックス（重複検出用）
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        
        # 記憶アイテム保存（ID -> MemoryItem）
        self.memory_items: Dict[str, MemoryItem] = {}
        
        # MinHash保存（ID -> MinHash）
        self.minhashes: Dict[str, MinHash] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def _create_minhash(self, content: str) -> MinHash:
        """コンテンツからMinHash生成"""
        minhash = MinHash(num_perm=self.num_perm)
        
        # 文字レベルshingles
        char_shingles = ContentNormalizer.extract_shingles(
            content, self.char_shingle_size
        )
        
        # 単語レベルshingles
        word_shingles = ContentNormalizer.extract_word_shingles(
            content, self.word_shingle_size
        )
        
        # 全shinglesを結合
        all_shingles = char_shingles.union(word_shingles)
        
        # MinHashに追加
        for shingle in all_shingles:
            minhash.update(shingle.encode('utf8'))
        
        return minhash
    
    def add_memory(self, memory_item: MemoryItem) -> bool:
        """
        記憶アイテム追加
        
        Returns:
            True: 新規追加, False: 重複検出により追加されず
        """
        # MinHash生成
        minhash = self._create_minhash(memory_item.content)
        
        # 重複チェック
        duplicates = self.lsh.query(minhash)
        
        if duplicates:
            # 重複検出
            duplicate_ids = list(duplicates)
            self.logger.info(
                f"重複検出: 新規アイテム '{memory_item.id}' は "
                f"既存アイテム {duplicate_ids} と重複"
            )
            return False
        
        # 新規追加
        self.lsh.insert(memory_item.id, minhash)
        self.memory_items[memory_item.id] = memory_item
        self.minhashes[memory_item.id] = minhash
        
        self.logger.debug(f"新規記憶追加: {memory_item.id}")
        return True
            
    
    def find_duplicates(self, content: str) -> List[str]:
        """指定コンテンツの重複アイテムID一覧取得"""
        try:
            minhash = self._create_minhash(content)
            duplicates = self.lsh.query(minhash)
            return list(duplicates)
        except Exception as e:
            self.logger.error(f"重複検索エラー: {e}")
            return []
    
    def batch_deduplicate(self, memory_items: List[MemoryItem]) -> List[MemoryItem]:
        """
        バッチ重複除去
        
        Args:
            memory_items: 重複除去対象記憶アイテム一覧
            
        Returns:
            重複除去済み記憶アイテム一覧
        """
        unique_items = []
        duplicates_count = 0
        
        self.logger.info(f"バッチ重複除去開始: {len(memory_items)}件")
        
        for item in memory_items:
            if self.add_memory(item):
                unique_items.append(item)
            else:
                duplicates_count += 1
        
        dedup_rate = (duplicates_count / len(memory_items)) * 100 if memory_items else 0
        
        self.logger.info(
            f"バッチ重複除去完了: "
            f"入力{len(memory_items)}件 → 出力{len(unique_items)}件 "
            f"(重複除去率: {dedup_rate:.1f}%)"
        )
        
        return unique_items
    
    def get_similarity(self, item_id1: str, item_id2: str) -> float:
        """2つのアイテム間の類似度計算"""
        if item_id1 not in self.minhashes or item_id2 not in self.minhashes:
            return 0.0
        
        minhash1 = self.minhashes[item_id1]
        minhash2 = self.minhashes[item_id2]
        
        return minhash1.jaccard(minhash2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """重複検出システムの統計情報取得"""
        return {
            "total_items": len(self.memory_items),
            "num_perm": self.num_perm,
            "threshold": self.threshold,
            "char_shingle_size": self.char_shingle_size,
            "word_shingle_size": self.word_shingle_size,
            "memory_types": list(set(item.memory_type for item in self.memory_items.values())),
            "oldest_item": min(
                (item.timestamp for item in self.memory_items.values()),
                default=None
            ),
            "newest_item": max(
                (item.timestamp for item in self.memory_items.values()),
                default=None
            )
        }
    
    def export_minhash_signatures(self) -> Dict[str, bytes]:
        """MinHashシグネチャをバイナリ形式でエクスポート（PostgreSQL保存用）"""
        signatures = {}
        for item_id, minhash in self.minhashes.items():
            # MinHashシグネチャをバイナリにシリアライズ
            signatures[item_id] = minhash.digest()
        return signatures
    
    def clear(self):
        """全データクリア"""
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.memory_items.clear()
        self.minhashes.clear()
        self.logger.info("重複検出システムクリア完了")


# ユーティリティ関数

def create_memory_item_from_dict(data: Dict[str, Any]) -> MemoryItem:
    """辞書からMemoryItem作成"""
    return MemoryItem(
        id=data['id'],
        content=data['content'],
        timestamp=datetime.fromisoformat(data['timestamp']),
        channel_id=int(data['channel_id']),
        user_id=str(data['user_id']),
        memory_type=data['memory_type'],
        metadata=data.get('metadata', {})
    )


def test_deduplication_system():
    """重複検出システムのテスト"""
    import uuid
    
    # テストデータ作成
    deduplicator = MinHashDeduplicator(threshold=0.7)
    
    # テストアイテム
    items = [
        MemoryItem(
            id=str(uuid.uuid4()),
            content="TypeScriptでReactアプリを開発しています",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user1",
            memory_type="conversation",
            metadata={}
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content="ReactアプリをTypeScriptで開発中です",
            timestamp=datetime.now(),
            channel_id=123,
            user_id="user1",
            memory_type="conversation",
            metadata={}
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content="Pythonでバックエンド実装しています",
            timestamp=datetime.now(),
            channel_id=456,
            user_id="user2",
            memory_type="task",
            metadata={}
        )
    ]
    
    # バッチ重複除去
    unique_items = deduplicator.batch_deduplicate(items)
    
    print(f"入力: {len(items)}件")
    print(f"出力: {len(unique_items)}件")
    print(f"統計: {deduplicator.get_statistics()}")
    
    return deduplicator


if __name__ == "__main__":
    # テスト実行
    test_deduplication_system()