#!/usr/bin/env python3
"""
PostgreSQL Migration Runner for v0.3.0
長期記憶システム用データベースマイグレーション実行スクリプト
"""

import asyncio
import asyncpg
import os
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration(postgres_url: str, migration_file: Path) -> bool:
    """
    マイグレーションファイルを実行
    
    Args:
        postgres_url: PostgreSQL接続URL
        migration_file: マイグレーションファイルパス
        
    Returns:
        実行成功/失敗
    """
    try:
        logger.info(f"🔄 マイグレーション開始: {migration_file.name}")
        
        # PostgreSQL接続
        conn = await asyncpg.connect(postgres_url)
        
        try:
            # SQLファイル読み込み
            sql_content = migration_file.read_text(encoding='utf-8')
            
            # SQLを実行（複数ステートメント対応）
            await conn.execute(sql_content)
            
            logger.info(f"✅ マイグレーション完了: {migration_file.name}")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ マイグレーション失敗: {migration_file.name} - {e}")
        return False


async def check_database_connection(postgres_url: str) -> bool:
    """データベース接続テスト"""
    try:
        logger.info("🔍 データベース接続テスト開始")
        conn = await asyncpg.connect(postgres_url)
        
        # 基本クエリ実行
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            logger.info("✅ データベース接続成功")
            return True
        else:
            logger.error("❌ データベース接続テスト失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ データベース接続エラー: {e}")
        return False


async def check_pgvector_extension() -> bool:
    """pgvector拡張の確認"""
    postgres_url = os.getenv('POSTGRESQL_URL')
    if not postgres_url:
        logger.error("❌ POSTGRESQL_URL環境変数が設定されていません")
        return False
        
    try:
        conn = await asyncpg.connect(postgres_url)
        
        # pgvector拡張の存在確認
        result = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            )
        """)
        
        await conn.close()
        
        if result:
            logger.info("✅ pgvector拡張が利用可能")
            return True
        else:
            logger.warning("⚠️ pgvector拡張が見つかりません")
            logger.info("💡 拡張インストールコマンド: CREATE EXTENSION vector;")
            return False
            
    except Exception as e:
        logger.error(f"❌ pgvector確認エラー: {e}")
        return False


async def main():
    """メインマイグレーション実行"""
    
    # 環境変数確認
    postgres_url = os.getenv('POSTGRESQL_URL')
    if not postgres_url:
        logger.error("❌ POSTGRESQL_URL環境変数が設定されていません")
        return False
    
    # プロジェクトルート取得
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "migrations"
    
    if not migrations_dir.exists():
        logger.error(f"❌ マイグレーションディレクトリが見つかりません: {migrations_dir}")
        return False
    
    logger.info("🚀 PostgreSQL マイグレーション実行開始")
    
    # 1. データベース接続テスト
    if not await check_database_connection(postgres_url):
        return False
    
    # 2. pgvector拡張確認
    await check_pgvector_extension()
    
    # 3. マイグレーションファイル実行
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        logger.warning("⚠️ マイグレーションファイルが見つかりません")
        return False
    
    success_count = 0
    total_count = len(migration_files)
    
    for migration_file in migration_files:
        success = await run_migration(postgres_url, migration_file)
        if success:
            success_count += 1
        else:
            logger.error(f"❌ マイグレーション中断: {migration_file.name}")
            break
    
    # 4. 結果報告
    if success_count == total_count:
        logger.info(f"🎉 全マイグレーション完了: {success_count}/{total_count}")
        
        # テーブル作成確認
        await verify_table_creation(postgres_url)
        return True
    else:
        logger.error(f"❌ マイグレーション部分失敗: {success_count}/{total_count}")
        return False


async def verify_table_creation(postgres_url: str):
    """テーブル作成確認"""
    try:
        conn = await asyncpg.connect(postgres_url)
        
        # unified_memoriesテーブルの存在確認
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'unified_memories'
            )
        """)
        
        if table_exists:
            # テーブル構造確認
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'unified_memories'
                ORDER BY ordinal_position
            """)
            
            logger.info(f"✅ unified_memoriesテーブル作成確認: {len(columns)}カラム")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
                
            # インデックス確認
            indexes = await conn.fetch("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'unified_memories'
            """)
            
            logger.info(f"✅ インデックス作成確認: {len(indexes)}個")
            for idx in indexes:
                logger.info(f"  - {idx['indexname']}")
        else:
            logger.error("❌ unified_memoriesテーブルが作成されていません")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ テーブル確認エラー: {e}")


def sync_main():
    """同期バージョンのメイン関数"""
    return asyncio.run(main())


if __name__ == "__main__":
    import sys
    
    print("🗄️ PostgreSQL Migration Runner v0.3.0")
    print("=" * 50)
    
    success = sync_main()
    
    if success:
        print("\n🎉 マイグレーション成功！v0.3.0長期記憶システム準備完了")
        sys.exit(0)
    else:
        print("\n❌ マイグレーション失敗。エラーログを確認してください")
        sys.exit(1)