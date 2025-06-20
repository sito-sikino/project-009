#!/usr/bin/env python3
"""
Quick Bot Status Check
Fast verification of bot token, intents, and basic connectivity
"""

import os
import sys
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

def check_token_validity():
    """Check if bot token is valid"""
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    
    if not token:
        print("❌ No DISCORD_RECEPTION_TOKEN found")
        return False
    
    print(f"🔑 Token length: {len(token)} characters")
    
    # Test token with Discord API
    headers = {'Authorization': f'Bot {token}'}
    
    try:
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token valid for bot: {data.get('username')} (ID: {data.get('id')})")
            print(f"✅ Bot account: {data.get('bot', False)}")
            print(f"✅ Verified: {data.get('verified', False)}")
            return True
        else:
            print(f"❌ Token validation failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.RequestException as e:
        print(f"❌ Network error during token validation: {e}")
        return False

def check_gateway_access():
    """Check Discord gateway access"""
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    
    if not token:
        return False
    
    headers = {'Authorization': f'Bot {token}'}
    
    try:
        response = requests.get('https://discord.com/api/v10/gateway/bot', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Gateway URL: {data.get('url')}")
            print(f"✅ Recommended shards: {data.get('shards', 1)}")
            
            session_limit = data.get('session_start_limit', {})
            print(f"✅ Session limit: {session_limit.get('remaining', 0)}/{session_limit.get('total', 0)}")
            
            return True
        else:
            print(f"❌ Gateway access failed: HTTP {response.status_code}")
            return False
    
    except requests.RequestException as e:
        print(f"❌ Network error during gateway check: {e}")
        return False

def check_basic_connectivity():
    """Check basic internet and Discord connectivity"""
    try:
        # Test general internet
        response = requests.get('https://www.google.com', timeout=5)
        if response.status_code == 200:
            print("✅ Internet connectivity: OK")
        else:
            print("⚠️  Internet connectivity: Limited")
        
        # Test Discord API
        response = requests.get('https://discord.com/api/v10/gateway', timeout=5)
        if response.status_code == 200:
            print("✅ Discord API connectivity: OK")
            return True
        else:
            print("❌ Discord API connectivity: Failed")
            return False
    
    except requests.RequestException as e:
        print(f"❌ Connectivity check failed: {e}")
        return False

def main():
    """Main status check"""
    print("🔍 Quick Bot Status Check")
    print("=" * 30)
    
    # Check environment
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check .env file
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file found")
    else:
        print(f"❌ .env file not found")
    
    print("\n🌐 Connectivity Check:")
    connectivity_ok = check_basic_connectivity()
    
    print("\n🔑 Token Validation:")
    token_ok = check_token_validity()
    
    print("\n🌉 Gateway Access:")
    gateway_ok = check_gateway_access()
    
    print("\n📊 Summary:")
    print("=" * 20)
    
    if connectivity_ok and token_ok and gateway_ok:
        print("✅ All basic checks passed!")
        print("💡 If your bot still doesn't receive messages, run:")
        print("   ./run_debug_tools.sh")
        print("   or")
        print("   python minimal_message_test.py")
    else:
        print("❌ Some basic checks failed:")
        if not connectivity_ok:
            print("   - Fix internet/network connectivity")
        if not token_ok:
            print("   - Fix bot token (regenerate in Discord Developer Portal)")
        if not gateway_ok:
            print("   - Check bot permissions and intents")
    
    print("\n🛠️  Available debugging tools:")
    print("   1. ./run_debug_tools.sh - Interactive tool selector")
    print("   2. python minimal_message_test.py - Simple message test")
    print("   3. python message_event_troubleshooter.py - Comprehensive diagnosis")

if __name__ == "__main__":
    main()