#!/usr/bin/env python3
"""
Environment Setup Script
開発・テスト・本番環境の適切なセットアップ
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List


class EnvironmentSetup:
    """環境セットアップ管理"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        
    def setup_environment(self, env_type: str = "development") -> bool:
        """
        環境セットアップ実行
        
        Args:
            env_type: "development", "test", "production"
        """
        print(f"🚀 {env_type.upper()} 環境セットアップ開始")
        
        try:
            # 1. Python バージョン確認
            if not self._check_python_version():
                return False
            
            # 2. 仮想環境確認・作成
            if not self._setup_virtual_environment():
                return False
            
            # 3. 依存関係インストール
            if not self._install_dependencies():
                return False
            
            # 4. 環境変数テンプレート作成
            if not self._create_env_template(env_type):
                return False
            
            # 5. ディレクトリ構造確認
            if not self._create_required_directories():
                return False
            
            print(f"✅ {env_type.upper()} 環境セットアップ完了")
            return True
            
        except Exception as e:
            print(f"❌ 環境セットアップエラー: {e}")
            return False
    
    def _check_python_version(self) -> bool:
        """Python バージョン確認"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print(f"❌ Python 3.9+ が必要です。現在のバージョン: {version.major}.{version.minor}")
            return False
        
        print(f"✅ Python バージョン確認: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def _setup_virtual_environment(self) -> bool:
        """仮想環境セットアップ"""
        if self.venv_path.exists():
            print("📦 既存の仮想環境を確認中...")
            
            # 仮想環境の整合性チェック
            if not self._verify_venv_integrity():
                print("⚠️ 仮想環境に問題があります。再作成します...")
                shutil.rmtree(self.venv_path)
                return self._create_virtual_environment()
            else:
                print("✅ 既存の仮想環境は正常です")
                return True
        else:
            return self._create_virtual_environment()
    
    def _create_virtual_environment(self) -> bool:
        """仮想環境作成"""
        print("📦 仮想環境を作成中...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True, cwd=self.project_root)
            
            print("✅ 仮想環境作成完了")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 仮想環境作成失敗: {e}")
            return False
    
    def _verify_venv_integrity(self) -> bool:
        """仮想環境整合性チェック"""
        try:
            # アクティベーションスクリプトの存在確認
            if os.name == 'nt':  # Windows
                activate_script = self.venv_path / "Scripts" / "activate"
                python_executable = self.venv_path / "Scripts" / "python.exe"
            else:  # Unix/Linux/macOS
                activate_script = self.venv_path / "bin" / "activate"
                python_executable = self.venv_path / "bin" / "python"
            
            return activate_script.exists() and python_executable.exists()
            
        except Exception:
            return False
    
    def _install_dependencies(self) -> bool:
        """依存関係インストール"""
        if not self.requirements_file.exists():
            print(f"❌ requirements.txt が見つかりません: {self.requirements_file}")
            return False
        
        print("📚 依存関係をインストール中...")
        
        try:
            # 仮想環境のpipを使用
            if os.name == 'nt':  # Windows
                pip_executable = self.venv_path / "Scripts" / "pip"
            else:  # Unix/Linux/macOS
                pip_executable = self.venv_path / "bin" / "pip"
            
            # pip アップグレード
            subprocess.run([
                str(pip_executable), "install", "--upgrade", "pip"
            ], check=True, cwd=self.project_root)
            
            # requirements.txt からインストール
            subprocess.run([
                str(pip_executable), "install", "-r", str(self.requirements_file)
            ], check=True, cwd=self.project_root)
            
            print("✅ 依存関係インストール完了")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依存関係インストール失敗: {e}")
            return False
    
    def _create_env_template(self, env_type: str) -> bool:
        """環境変数テンプレート作成"""
        env_file = self.project_root / f".env.{env_type}.template"
        
        if env_type == "development":
            template_content = self._get_development_env_template()
        elif env_type == "test":
            template_content = self._get_test_env_template()
        elif env_type == "production":
            template_content = self._get_production_env_template()
        else:
            print(f"❌ 未知の環境タイプ: {env_type}")
            return False
        
        try:
            env_file.write_text(template_content, encoding='utf-8')
            print(f"✅ 環境変数テンプレート作成: {env_file.name}")
            
            # .env ファイルが存在しない場合はテンプレートをコピー
            env_actual = self.project_root / ".env"
            if not env_actual.exists():
                shutil.copy2(env_file, env_actual)
                print(f"📋 .env ファイル作成: {env_actual.name}")
                print("⚠️  実際の値を設定してください")
            
            return True
            
        except Exception as e:
            print(f"❌ 環境変数テンプレート作成エラー: {e}")
            return False
    
    def _get_development_env_template(self) -> str:
        """開発環境テンプレート"""
        return """# Discord Multi-Agent System - Development Environment
# 開発環境用設定

# Discord Bot Tokens (開発用ボット)
DISCORD_RECEPTION_TOKEN=your_dev_reception_token_here
DISCORD_SPECTRA_TOKEN=your_dev_spectra_token_here
DISCORD_LYNQ_TOKEN=your_dev_lynq_token_here
DISCORD_PAZ_TOKEN=your_dev_paz_token_here

# AI Integration
GEMINI_API_KEY=your_gemini_api_key_here

# Database (開発用)
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://dev_user:dev_password@localhost:5432/discord_agent_dev

# Channel IDs (開発用サーバー)
COMMAND_CENTER_CHANNEL_ID=your_dev_command_center_channel_id
LOUNGE_CHANNEL_ID=your_dev_lounge_channel_id
DEVELOPMENT_CHANNEL_ID=your_dev_development_channel_id
CREATION_CHANNEL_ID=your_dev_creation_channel_id

# System Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG
HEALTH_CHECK_PORT=8000
"""
    
    def _get_test_env_template(self) -> str:
        """テスト環境テンプレート"""
        return """# Discord Multi-Agent System - Test Environment
# テスト環境用設定（CI/CD、自動テスト用）

# Discord Bot Tokens (テスト用モック値)
DISCORD_RECEPTION_TOKEN=test_mock_reception_token_minimum_50_chars_long_for_testing
DISCORD_SPECTRA_TOKEN=test_mock_spectra_token_minimum_50_chars_long_for_testing_env
DISCORD_LYNQ_TOKEN=test_mock_lynq_token_minimum_50_chars_long_for_testing_env_ok
DISCORD_PAZ_TOKEN=test_mock_paz_token_minimum_50_chars_long_for_testing_env_done

# AI Integration (テスト用)
GEMINI_API_KEY=test_mock_gemini_api_key_for_testing_environment_only

# Database (テスト用)
REDIS_URL=redis://localhost:6379/1
POSTGRESQL_URL=postgresql://test_user:test_password@localhost:5432/discord_agent_test

# Channel IDs (テスト用)
COMMAND_CENTER_CHANNEL_ID=123456789012345678
LOUNGE_CHANNEL_ID=123456789012345679
DEVELOPMENT_CHANNEL_ID=123456789012345680
CREATION_CHANNEL_ID=123456789012345681

# System Configuration
ENVIRONMENT=test
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8001
"""
    
    def _get_production_env_template(self) -> str:
        """本番環境テンプレート"""
        return """# Discord Multi-Agent System - Production Environment
# 本番環境用設定（セキュリティ重要）

# Discord Bot Tokens (本番用ボット)
DISCORD_RECEPTION_TOKEN=your_production_reception_token_here
DISCORD_SPECTRA_TOKEN=your_production_spectra_token_here
DISCORD_LYNQ_TOKEN=your_production_lynq_token_here
DISCORD_PAZ_TOKEN=your_production_paz_token_here

# AI Integration
GEMINI_API_KEY=your_production_gemini_api_key_here

# Database (本番用)
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://prod_user:secure_password@localhost:5432/discord_agent_prod

# Channel IDs (本番用サーバー)
COMMAND_CENTER_CHANNEL_ID=your_prod_command_center_channel_id
LOUNGE_CHANNEL_ID=your_prod_lounge_channel_id
DEVELOPMENT_CHANNEL_ID=your_prod_development_channel_id
CREATION_CHANNEL_ID=your_prod_creation_channel_id

# System Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8000

# Production Security Settings
ALLOWED_GUILD_IDS=your_production_guild_id_here
MAX_CONCURRENT_USERS=100
API_RATE_LIMIT_PER_HOUR=1000
"""
    
    def _create_required_directories(self) -> bool:
        """必要ディレクトリ作成"""
        required_dirs = [
            self.project_root / "logs",
            self.project_root / "data",
            self.project_root / "scripts",
            self.project_root / "tests" / "integration",
            self.project_root / "tests" / "unit",
        ]
        
        try:
            for directory in required_dirs:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"📁 ディレクトリ確認: {directory.relative_to(self.project_root)}")
            
            return True
            
        except Exception as e:
            print(f"❌ ディレクトリ作成エラー: {e}")
            return False
    
    def verify_setup(self) -> bool:
        """セットアップ検証"""
        print("🔍 環境セットアップ検証開始")
        
        checks = [
            ("仮想環境", self._verify_venv_integrity()),
            ("依存関係", self._verify_dependencies()),
            ("環境変数", self._verify_environment_variables()),
            ("ディレクトリ", self._verify_directories()),
        ]
        
        success_count = 0
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}: 正常")
                success_count += 1
            else:
                print(f"❌ {check_name}: 問題あり")
        
        success_rate = (success_count / len(checks)) * 100
        print(f"📊 検証結果: {success_count}/{len(checks)} ({success_rate:.1f}%)")
        
        return success_count == len(checks)
    
    def _verify_dependencies(self) -> bool:
        """依存関係検証"""
        try:
            if os.name == 'nt':  # Windows
                pip_executable = self.venv_path / "Scripts" / "pip"
            else:  # Unix/Linux/macOS
                pip_executable = self.venv_path / "bin" / "pip"
            
            result = subprocess.run([
                str(pip_executable), "check"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _verify_environment_variables(self) -> bool:
        """環境変数検証"""
        env_file = self.project_root / ".env"
        return env_file.exists()
    
    def _verify_directories(self) -> bool:
        """ディレクトリ検証"""
        required_dirs = [
            self.project_root / "logs",
            self.project_root / "src",
            self.project_root / "tests",
        ]
        
        return all(directory.exists() for directory in required_dirs)


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Setup Script")
    parser.add_argument(
        "--env-type", 
        choices=["development", "test", "production"],
        default="development",
        help="Environment type to setup"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing setup"
    )
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup()
    
    if args.verify_only:
        success = setup.verify_setup()
    else:
        success = setup.setup_environment(args.env_type)
        if success:
            setup.verify_setup()
    
    if success:
        print("\n🎉 環境セットアップ成功！")
        print(f"💡 次のステップ: 'source venv/bin/activate' で仮想環境を有効化")
        return 0
    else:
        print("\n❌ 環境セットアップ失敗")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())