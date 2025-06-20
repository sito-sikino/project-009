#!/usr/bin/env python3
"""
Production Environment Setup Script
統合受信・個別送信型アーキテクチャ本番環境セットアップ
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class ProductionSetup:
    """
    本番環境セットアップマネージャー
    
    責務:
    - 環境変数検証・設定
    - Discord Bot設定検証
    - 依存関係インストール
    - システム起動確認
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.required_env_vars = [
            "DISCORD_RECEPTION_TOKEN",
            "DISCORD_SPECTRA_TOKEN", 
            "DISCORD_LYNQ_TOKEN",
            "DISCORD_PAZ_TOKEN",
            "GEMINI_API_KEY",
            "TARGET_GUILD_ID"
        ]
        self.optional_env_vars = [
            "REDIS_URL",
            "POSTGRESQL_URL",
            "LOG_LEVEL",
            "ENVIRONMENT"
        ]
    
    def validate_environment(self) -> bool:
        """環境変数検証"""
        print("🔍 Environment Variables Validation...")
        
        missing_vars = []
        for var in self.required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                print(f"❌ Missing required environment variable: {var}")
            else:
                # トークンは部分表示
                value = os.getenv(var)
                if "TOKEN" in var or "KEY" in var:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
        
        # オプション環境変数
        for var in self.optional_env_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value}")
            else:
                print(f"🟡 Optional {var}: Not set (using defaults)")
        
        if missing_vars:
            print(f"\n❌ Setup failed: Missing {len(missing_vars)} required environment variables")
            print("Please set the following environment variables:")
            for var in missing_vars:
                print(f"export {var}=<your_value>")
            return False
        
        print("✅ Environment validation passed")
        return True
    
    def check_dependencies(self) -> bool:
        """依存関係確認"""
        print("\n📦 Dependencies Check...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        try:
            # pip freeze で現在のパッケージ確認
            result = subprocess.run([
                sys.executable, "-m", "pip", "freeze"
            ], capture_output=True, text=True, check=True)
            
            installed_packages = {
                line.split("==")[0].lower(): line.split("==")[1] 
                for line in result.stdout.strip().split("\n") 
                if "==" in line
            }
            
            # requirements.txt読み込み
            with open(requirements_file, 'r') as f:
                required_packages = [
                    line.strip() for line in f.readlines() 
                    if line.strip() and not line.startswith("#")
                ]
            
            missing_packages = []
            for package in required_packages:
                package_name = package.split("==")[0].split(">=")[0].split("~=")[0].lower()
                if package_name not in installed_packages:
                    missing_packages.append(package)
                else:
                    print(f"✅ {package_name}: {installed_packages[package_name]}")
            
            if missing_packages:
                print(f"❌ Missing packages: {missing_packages}")
                print("Run: pip install -r requirements.txt")
                return False
            
            print("✅ All dependencies satisfied")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Dependency check failed: {e}")
            return False
    
    def validate_discord_tokens(self) -> bool:
        """Discord Token検証"""
        print("\n🤖 Discord Bot Tokens Validation...")
        
        tokens = {
            "Reception Bot": os.getenv("DISCORD_RECEPTION_TOKEN"),
            "Spectra Bot": os.getenv("DISCORD_SPECTRA_TOKEN"),
            "LynQ Bot": os.getenv("DISCORD_LYNQ_TOKEN"),
            "Paz Bot": os.getenv("DISCORD_PAZ_TOKEN")
        }
        
        for bot_name, token in tokens.items():
            if not token:
                print(f"❌ {bot_name}: Token missing")
                return False
            
            # トークン形式の基本チェック
            if len(token) < 50:
                print(f"❌ {bot_name}: Token too short (possible invalid format)")
                return False
            
            print(f"✅ {bot_name}: Token format valid")
        
        print("✅ All Discord tokens validated")
        return True
    
    def validate_gemini_api(self) -> bool:
        """Gemini API Key検証"""
        print("\n🧠 Gemini API Key Validation...")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY missing")
            return False
        
        # API Key形式の基本チェック
        if len(api_key) < 20:
            print("❌ Gemini API Key too short")
            return False
        
        print("✅ Gemini API Key format validated")
        return True
    
    def create_systemd_service(self) -> bool:
        """Systemd Service File作成"""
        print("\n⚙️ Creating systemd service file...")
        
        service_content = f"""[Unit]
Description=Discord Multi-Agent System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10

# Environment Variables
Environment=DISCORD_RECEPTION_TOKEN={os.getenv('DISCORD_RECEPTION_TOKEN', '')}
Environment=DISCORD_SPECTRA_TOKEN={os.getenv('DISCORD_SPECTRA_TOKEN', '')}
Environment=DISCORD_LYNQ_TOKEN={os.getenv('DISCORD_LYNQ_TOKEN', '')}
Environment=DISCORD_PAZ_TOKEN={os.getenv('DISCORD_PAZ_TOKEN', '')}
Environment=GEMINI_API_KEY={os.getenv('GEMINI_API_KEY', '')}
Environment=TARGET_GUILD_ID={os.getenv('TARGET_GUILD_ID', '')}
Environment=LOG_LEVEL={os.getenv('LOG_LEVEL', 'INFO')}
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.project_root / "deploy" / "discord-multi-agent.service"
        service_file.parent.mkdir(exist_ok=True)
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Systemd service file created: {service_file}")
        print("To install: sudo cp deploy/discord-multi-agent.service /etc/systemd/system/")
        print("To enable: sudo systemctl enable discord-multi-agent")
        print("To start: sudo systemctl start discord-multi-agent")
        
        return True
    
    def create_env_template(self) -> bool:
        """環境変数テンプレート作成"""
        print("\n📝 Creating environment template...")
        
        env_template = """# Discord Multi-Agent System Environment Variables
# Copy this to .env and fill in your values

# Discord Bot Tokens (4 separate bots required)
DISCORD_RECEPTION_TOKEN=your_reception_bot_token_here
DISCORD_SPECTRA_TOKEN=your_spectra_bot_token_here
DISCORD_LYNQ_TOKEN=your_lynq_bot_token_here
DISCORD_PAZ_TOKEN=your_paz_bot_token_here

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Discord Server Configuration
TARGET_GUILD_ID=your_discord_server_id_here

# Optional: Memory System (if implemented)
# REDIS_URL=redis://localhost:6379
# POSTGRESQL_URL=postgresql://user:password@localhost/discord_agent

# Optional: Logging
# LOG_LEVEL=INFO
# ENVIRONMENT=production
"""
        
        env_file = self.project_root / ".env.template"
        with open(env_file, 'w') as f:
            f.write(env_template)
        
        print(f"✅ Environment template created: {env_file}")
        return True
    
    def create_startup_script(self) -> bool:
        """起動スクリプト作成"""
        print("\n🚀 Creating startup script...")
        
        startup_script = """#!/bin/bash
# Discord Multi-Agent System Startup Script

set -e

echo "🤖 Starting Discord Multi-Agent System..."

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | xargs)
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment"
    source venv/bin/activate
fi

# Run the application
echo "🚀 Starting application..."
python main.py
"""
        
        startup_file = self.project_root / "start.sh"
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod(startup_file, 0o755)
        
        print(f"✅ Startup script created: {startup_file}")
        return True
    
    async def test_system_connectivity(self) -> bool:
        """システム接続テスト"""
        print("\n🔌 Testing system connectivity...")
        
        try:
            # Import test (基本的な動作確認)
            from src.discord_clients import ReceptionClient
            from src.langgraph_supervisor import AgentSupervisor
            from src.output_bots import SpectraBot, LynQBot, PazBot
            from src.message_router import MessageRouter
            
            print("✅ All core modules importable")
            
            # Basic initialization test
            from src.message_processor import PriorityQueue
            from src.gemini_client import GeminiClient
            
            priority_queue = PriorityQueue()
            gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
            supervisor = AgentSupervisor(gemini_client=gemini_client)
            
            print("✅ Core components initialization successful")
            return True
            
        except Exception as e:
            print(f"❌ System connectivity test failed: {e}")
            return False
    
    def run_setup(self, create_service: bool = False) -> bool:
        """完全セットアップ実行"""
        print("🚀 Discord Multi-Agent System Production Setup")
        print("=" * 50)
        
        steps = [
            ("Environment Validation", self.validate_environment),
            ("Dependencies Check", self.check_dependencies),
            ("Discord Tokens Validation", self.validate_discord_tokens),
            ("Gemini API Validation", self.validate_gemini_api),
            ("System Connectivity Test", self.test_system_connectivity),
            ("Environment Template Creation", self.create_env_template),
            ("Startup Script Creation", self.create_startup_script),
        ]
        
        if create_service:
            steps.append(("Systemd Service Creation", self.create_systemd_service))
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if asyncio.iscoroutinefunction(step_func):
                result = asyncio.run(step_func())
            else:
                result = step_func()
            
            if not result:
                print(f"\n❌ Setup failed at: {step_name}")
                return False
        
        print("\n" + "=" * 50)
        print("✅ Production setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Copy .env.template to .env and fill in your values")
        print("2. Run: ./start.sh")
        print("3. Monitor logs for successful startup")
        
        if create_service:
            print("4. Install systemd service for automatic startup")
        
        return True


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Discord Multi-Agent System Production Setup")
    parser.add_argument("--service", action="store_true", help="Create systemd service file")
    parser.add_argument("--check-only", action="store_true", help="Only validate environment, don't create files")
    
    args = parser.parse_args()
    
    setup = ProductionSetup()
    
    if args.check_only:
        # 検証のみ実行
        valid_env = setup.validate_environment()
        valid_deps = setup.check_dependencies()
        valid_tokens = setup.validate_discord_tokens()
        valid_api = setup.validate_gemini_api()
        
        if all([valid_env, valid_deps, valid_tokens, valid_api]):
            print("\n✅ All validations passed - ready for production!")
            sys.exit(0)
        else:
            print("\n❌ Validation failed - fix issues before deployment")
            sys.exit(1)
    else:
        # 完全セットアップ実行
        success = setup.run_setup(create_service=args.service)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()