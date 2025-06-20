"""
Google text-embedding-004使用例
project-009での実装パターンデモンストレーション
"""

import os
import asyncio
import time
from typing import List
from src.embedding_client import GoogleEmbeddingClient
from src.memory_system import DiscordMemorySystem


class EmbeddingUsageDemo:
    """text-embedding-004使用例デモクラス"""
    
    def __init__(self):
        """デモ初期化"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY環境変数が必要です")
        
        # 各用途別クライアント
        self.query_client = GoogleEmbeddingClient(
            api_key=self.api_key, 
            task_type="RETRIEVAL_QUERY"
        )
        
        self.document_client = GoogleEmbeddingClient(
            api_key=self.api_key, 
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        self.similarity_client = GoogleEmbeddingClient(
            api_key=self.api_key, 
            task_type="SEMANTIC_SIMILARITY"
        )
    
    async def basic_embedding_demo(self):
        """基本embedding生成デモ"""
        print("=== 基本embedding生成デモ ===")
        
        text = "Discord botの実装でLangGraphを使用する方法"
        
        print(f"入力テキスト: {text}")
        
        # embedding生成
        start_time = time.time()
        embedding = await self.query_client.embed_query(text)
        end_time = time.time()
        
        if embedding:
            print(f"Embedding生成成功:")
            print(f"- 次元数: {len(embedding)}")
            print(f"- 処理時間: {end_time - start_time:.3f}秒")
            print(f"- 最初の5値: {embedding[:5]}")
        else:
            print("Embedding生成失敗")
        
        print()
    
    async def task_type_comparison_demo(self):
        """task_type別embedding比較デモ"""
        print("=== task_type別embedding比較デモ ===")
        
        text = "LangGraphはマルチエージェントワークフローの実装に適している"
        
        print(f"入力テキスト: {text}")
        
        # 各task_typeでembedding生成
        query_embedding = await self.query_client.embed_query(text)
        doc_embedding = await self.document_client.embed_query(text)
        sim_embedding = await self.similarity_client.embed_semantic_similarity(text)
        
        # 比較
        if all([query_embedding, doc_embedding, sim_embedding]):
            # コサイン類似度計算
            query_doc_sim = self._cosine_similarity(query_embedding, doc_embedding)
            query_sim_sim = self._cosine_similarity(query_embedding, sim_embedding)
            doc_sim_sim = self._cosine_similarity(doc_embedding, sim_embedding)
            
            print(f"RETRIEVAL_QUERY vs RETRIEVAL_DOCUMENT: {query_doc_sim:.4f}")
            print(f"RETRIEVAL_QUERY vs SEMANTIC_SIMILARITY: {query_sim_sim:.4f}")
            print(f"RETRIEVAL_DOCUMENT vs SEMANTIC_SIMILARITY: {doc_sim_sim:.4f}")
        else:
            print("一部のembedding生成に失敗しました")
        
        print()
    
    async def batch_processing_demo(self):
        """バッチ処理デモ"""
        print("=== バッチ処理デモ ===")
        
        documents = [
            "Discord.pyを使用したボット開発の基本",
            "LangGraphでマルチエージェントシステムを構築する",
            "PostgreSQLとpgvectorでセマンティック検索を実装",
            "Redisを使用したキャッシュシステムの設計",
            "Gemini APIとtext-embedding-004の活用方法"
        ]
        
        print(f"処理対象文書数: {len(documents)}")
        
        # バッチ処理実行
        start_time = time.time()
        embeddings = await self.document_client.embed_documents(documents)
        end_time = time.time()
        
        successful_embeddings = [e for e in embeddings if e is not None]
        
        print(f"結果:")
        print(f"- 成功: {len(successful_embeddings)}/{len(documents)}")
        print(f"- 総処理時間: {end_time - start_time:.3f}秒")
        print(f"- 平均処理時間: {(end_time - start_time) / len(documents):.3f}秒/文書")
        
        print()
    
    async def memory_system_integration_demo(self):
        """Memory System統合デモ"""
        print("=== Memory System統合デモ ===")
        
        try:
            # Memory System初期化
            memory_system = DiscordMemorySystem(gemini_api_key=self.api_key)
            
            # テストデータ
            test_queries = [
                "LangGraphの使い方を教えて",
                "Discord botの設定方法",
                "pgvectorでの検索最適化"
            ]
            
            print("Memory System embedding生成テスト:")
            
            for query in test_queries:
                embedding = await memory_system.generate_embedding(query)
                if embedding:
                    print(f"✅ '{query}' - 次元数: {len(embedding)}")
                else:
                    print(f"❌ '{query}' - 生成失敗")
            
        except Exception as e:
            print(f"Memory System統合エラー: {e}")
        
        print()
    
    async def performance_benchmark_demo(self):
        """パフォーマンスベンチマークデモ"""
        print("=== パフォーマンスベンチマークデモ ===")
        
        # テストケース
        test_cases = [
            ("短いテキスト", "Hello world"),
            ("中程度テキスト", "Discord botの実装において、LangGraphを使用することで複雑なマルチエージェントワークフローを効率的に管理できます。"),
            ("長いテキスト", "This is a very long text. " * 100)  # 長いテキスト
        ]
        
        for case_name, text in test_cases:
            print(f"{case_name} ({len(text)}文字):")
            
            # 5回実行して平均計算
            times = []
            for _ in range(5):
                start_time = time.time()
                embedding = await self.query_client.embed_query(text)
                end_time = time.time()
                
                if embedding:
                    times.append(end_time - start_time)
            
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                print(f"  平均: {avg_time:.3f}秒, 最短: {min_time:.3f}秒, 最長: {max_time:.3f}秒")
            else:
                print("  すべての実行で失敗")
        
        print()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度計算"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


async def main():
    """メインデモ実行"""
    try:
        demo = EmbeddingUsageDemo()
        
        await demo.basic_embedding_demo()
        await demo.task_type_comparison_demo()
        await demo.batch_processing_demo()
        await demo.memory_system_integration_demo()
        await demo.performance_benchmark_demo()
        
        print("=== デモ完了 ===")
        
    except ValueError as e:
        print(f"設定エラー: {e}")
        print("GEMINI_API_KEY環境変数を設定してください")
        
    except Exception as e:
        print(f"デモ実行エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())