#!/usr/bin/env python3
"""
Advanced Discord Bot Debugging Tool
Comprehensive investigation for Discord bots that connect but don't receive message events

This tool investigates:
1. Discord Token Issues
2. Discord.py Version Compatibility
3. Advanced Intent Configuration
4. Network/Connection Issues
5. Code Logic Problems
6. Discord API Changes
"""

import os
import sys
import asyncio
import logging
import json
import time
import socket
import subprocess
import platform
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('discord_debug.log')
    ]
)
logger = logging.getLogger(__name__)

class AdvancedDiscordDebugger:
    """
    Advanced Discord debugging system that systematically checks all potential
    issues that could prevent a bot from receiving message events.
    """
    
    def __init__(self):
        self.token = os.getenv('DISCORD_RECEPTION_TOKEN')
        self.debug_results = {}
        self.connection_tests = {}
        self.message_count = 0
        self.start_time = time.time()
        
    async def run_full_diagnosis(self):
        """Run comprehensive diagnostic tests"""
        logger.info("🔍 Starting Advanced Discord Bot Diagnosis")
        logger.info("=" * 80)
        
        # 1. Environment and Token Validation
        await self.test_environment_setup()
        
        # 2. Network and Connection Tests
        await self.test_network_connectivity()
        
        # 3. Discord API and Token Validation
        await self.test_discord_api_access()
        
        # 4. Discord.py Version and Compatibility
        await self.test_discord_py_compatibility()
        
        # 5. Intent Configuration Deep Dive
        await self.test_intent_configuration()
        
        # 6. Gateway Connection Analysis
        await self.test_gateway_connection()
        
        # 7. Event Handler Testing
        await self.test_event_handlers()
        
        # 8. Generate comprehensive report
        self.generate_diagnosis_report()
        
        # 9. Live message monitoring test
        await self.run_live_message_test()
    
    async def test_environment_setup(self):
        """Test 1: Environment and System Configuration"""
        logger.info("🔧 Test 1: Environment and System Configuration")
        
        results = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'is_wsl': 'microsoft' in platform.release().lower(),
            'environment_variables': {},
            'discord_py_version': discord.__version__,
            'working_directory': os.getcwd()
        }
        
        # Check critical environment variables
        env_vars = [
            'DISCORD_RECEPTION_TOKEN',
            'DISCORD_SPECTRA_TOKEN', 
            'DISCORD_LYNQ_TOKEN',
            'DISCORD_PAZ_TOKEN',
            'GEMINI_API_KEY'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            results['environment_variables'][var] = {
                'exists': value is not None,
                'length': len(value) if value else 0,
                'prefix': value[:10] + '...' if value and len(value) > 10 else value
            }
        
        # Check if token looks valid
        if self.token:
            results['token_format_check'] = {
                'length_valid': len(self.token) > 50,
                'has_dots': '.' in self.token,
                'parts_count': len(self.token.split('.')) if '.' in self.token else 0
            }
        
        self.debug_results['environment'] = results
        logger.info(f"✅ Python: {sys.version}")
        logger.info(f"✅ Platform: {platform.platform()}")
        logger.info(f"✅ Discord.py: {discord.__version__}")
        logger.info(f"✅ Token exists: {self.token is not None}")
        
        if results['is_wsl']:
            logger.warning("⚠️  WSL2 detected - potential networking issues")
    
    async def test_network_connectivity(self):
        """Test 2: Network and Connection Analysis"""
        logger.info("🌐 Test 2: Network Connectivity Analysis")
        
        results = {}
        
        # Test basic internet connectivity
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://www.google.com', timeout=10) as resp:
                    results['internet_access'] = resp.status == 200
        except Exception as e:
            results['internet_access'] = False
            results['internet_error'] = str(e)
        
        # Test Discord API connectivity
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://discord.com/api/v10/gateway', timeout=10) as resp:
                    if resp.status == 200:
                        gateway_data = await resp.json()
                        results['discord_api_access'] = True
                        results['gateway_url'] = gateway_data.get('url')
                    else:
                        results['discord_api_access'] = False
                        results['discord_api_status'] = resp.status
        except Exception as e:
            results['discord_api_access'] = False
            results['discord_api_error'] = str(e)
        
        # Test DNS resolution
        try:
            socket.gethostbyname('discord.com')
            results['dns_resolution'] = True
        except Exception as e:
            results['dns_resolution'] = False
            results['dns_error'] = str(e)
        
        # Check for proxy/VPN
        results['proxy_env'] = {
            'http_proxy': os.getenv('HTTP_PROXY'),
            'https_proxy': os.getenv('HTTPS_PROXY'),
            'no_proxy': os.getenv('NO_PROXY')
        }
        
        self.debug_results['network'] = results
        logger.info(f"✅ Internet Access: {results['internet_access']}")
        logger.info(f"✅ Discord API Access: {results['discord_api_access']}")
        logger.info(f"✅ DNS Resolution: {results['dns_resolution']}")
    
    async def test_discord_api_access(self):
        """Test 3: Discord API and Token Validation"""
        logger.info("🔑 Test 3: Discord API and Token Validation")
        
        if not self.token:
            logger.error("❌ No token available for testing")
            self.debug_results['discord_api'] = {'error': 'No token provided'}
            return
        
        results = {}
        
        # Test token validity by calling Discord API
        headers = {'Authorization': f'Bot {self.token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test /users/@me endpoint
                async with session.get(
                    'https://discord.com/api/v10/users/@me',
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        user_data = await resp.json()
                        results['token_valid'] = True
                        results['bot_info'] = {
                            'username': user_data.get('username'),
                            'id': user_data.get('id'),
                            'bot': user_data.get('bot'),
                            'verified': user_data.get('verified')
                        }
                    elif resp.status == 401:
                        results['token_valid'] = False
                        results['error'] = 'Invalid token'
                    else:
                        results['token_valid'] = False
                        results['error'] = f'HTTP {resp.status}'
                        results['response_text'] = await resp.text()
                
                # Test gateway connection info
                async with session.get(
                    'https://discord.com/api/v10/gateway/bot',
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        gateway_data = await resp.json()
                        results['gateway_info'] = gateway_data
                    else:
                        results['gateway_error'] = f'HTTP {resp.status}'
        
        except Exception as e:
            results['token_valid'] = False
            results['api_error'] = str(e)
        
        self.debug_results['discord_api'] = results
        
        if results.get('token_valid'):
            logger.info(f"✅ Token Valid: {results['bot_info']['username']}")
            logger.info(f"✅ Bot ID: {results['bot_info']['id']}")
        else:
            logger.error(f"❌ Token Invalid: {results.get('error', 'Unknown error')}")
    
    async def test_discord_py_compatibility(self):
        """Test 4: Discord.py Version and Compatibility"""
        logger.info("📦 Test 4: Discord.py Version and Compatibility")
        
        results = {
            'discord_py_version': discord.__version__,
            'python_version': sys.version,
            'version_compatibility': {},
            'gateway_version': None
        }
        
        # Check known compatibility issues
        discord_version = discord.__version__
        python_version = sys.version_info
        
        # Discord.py 2.3.2 compatibility checks
        if discord_version == '2.3.2':
            results['version_compatibility']['status'] = 'good'
            results['version_compatibility']['notes'] = 'Latest stable version'
        elif discord_version.startswith('2.'):
            results['version_compatibility']['status'] = 'acceptable'
            results['version_compatibility']['notes'] = 'Discord.py 2.x series'
        else:
            results['version_compatibility']['status'] = 'warning'
            results['version_compatibility']['notes'] = 'Older version, consider upgrading'
        
        # Python compatibility
        if python_version >= (3, 8):
            results['python_compatibility'] = 'good'
        else:
            results['python_compatibility'] = 'warning'
            results['python_notes'] = 'Discord.py 2.x requires Python 3.8+'
        
        # Check for import issues
        try:
            import discord.gateway
            results['gateway_import'] = True
        except ImportError as e:
            results['gateway_import'] = False
            results['gateway_import_error'] = str(e)
        
        self.debug_results['compatibility'] = results
        logger.info(f"✅ Discord.py Version: {discord_version}")
        logger.info(f"✅ Compatibility Status: {results['version_compatibility']['status']}")
    
    async def test_intent_configuration(self):
        """Test 5: Advanced Intent Configuration Analysis"""
        logger.info("🎯 Test 5: Advanced Intent Configuration Analysis")
        
        # Create intents exactly as in the main code
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        
        results = {
            'configured_intents': {},
            'intent_analysis': {},
            'gateway_intents': None
        }
        
        # Analyze all intents
        for intent_name in dir(intents):
            if not intent_name.startswith('_') and isinstance(getattr(intents, intent_name), bool):
                results['configured_intents'][intent_name] = getattr(intents, intent_name)
        
        # Critical intent analysis
        critical_intents = {
            'message_content': 'Required to read message content',
            'guild_messages': 'Required to receive guild messages',
            'guilds': 'Required for guild access',
            'dm_messages': 'Required for DM messages'
        }
        
        for intent, description in critical_intents.items():
            enabled = getattr(intents, intent)
            results['intent_analysis'][intent] = {
                'enabled': enabled,
                'description': description,
                'status': 'OK' if enabled else 'MISSING'
            }
        
        # Check gateway intents value
        results['gateway_intents'] = intents.value
        
        self.debug_results['intents'] = results
        
        logger.info("Intent Configuration:")
        for intent, analysis in results['intent_analysis'].items():
            status = "✅" if analysis['enabled'] else "❌"
            logger.info(f"  {status} {intent}: {analysis['enabled']}")
    
    async def test_gateway_connection(self):
        """Test 6: Gateway Connection Deep Analysis"""
        logger.info("🌉 Test 6: Gateway Connection Analysis")
        
        if not self.token:
            logger.error("❌ No token for gateway testing")
            return
        
        results = {}
        
        # Create a test client to check gateway connection
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        
        client = discord.Client(intents=intents)
        
        # Monitor connection events
        connection_events = []
        
        @client.event
        async def on_connect():
            connection_events.append(('connect', time.time()))
            logger.info("🔗 Client connected to Discord")
        
        @client.event
        async def on_ready():
            connection_events.append(('ready', time.time()))
            logger.info(f"✅ Client ready: {client.user}")
            logger.info(f"📊 Connected to {len(client.guilds)} guilds")
            
            # Collect guild information
            guild_info = []
            for guild in client.guilds:
                guild_info.append({
                    'name': guild.name,
                    'id': guild.id,
                    'member_count': guild.member_count,
                    'text_channels': len(guild.text_channels)
                })
            
            results['guilds'] = guild_info
            results['connection_events'] = connection_events
            results['client_user'] = str(client.user)
            
            # Close after collecting info
            await client.close()
        
        @client.event
        async def on_disconnect():
            connection_events.append(('disconnect', time.time()))
            logger.info("🔌 Client disconnected")
        
        try:
            # Test connection with timeout
            await asyncio.wait_for(client.start(self.token), timeout=30.0)
        except asyncio.TimeoutError:
            logger.error("❌ Gateway connection timeout")
            results['error'] = 'Connection timeout'
        except Exception as e:
            logger.error(f"❌ Gateway connection error: {e}")
            results['error'] = str(e)
        
        self.debug_results['gateway'] = results
    
    async def test_event_handlers(self):
        """Test 7: Event Handler Logic Testing"""
        logger.info("🎭 Test 7: Event Handler Logic Testing")
        
        results = {}
        
        # Test event handler registration
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        
        # Create test client with comprehensive event logging
        client = discord.Client(intents=intents)
        events_received = []
        
        # Register all possible events to see what we receive
        @client.event
        async def on_ready():
            events_received.append(('on_ready', time.time()))
            logger.info("📨 Event: on_ready")
        
        @client.event
        async def on_message(message):
            events_received.append(('on_message', time.time(), {
                'author': str(message.author),
                'content': message.content[:50],
                'channel': str(message.channel),
                'guild': str(message.guild) if message.guild else None
            }))
            logger.info(f"📨 Event: on_message from {message.author}")
        
        @client.event
        async def on_raw_message_create(payload):
            events_received.append(('on_raw_message_create', time.time()))
            logger.info("📨 Event: on_raw_message_create")
        
        @client.event
        async def on_guild_join(guild):
            events_received.append(('on_guild_join', time.time()))
            logger.info(f"📨 Event: on_guild_join - {guild.name}")
        
        @client.event
        async def on_error(event, *args, **kwargs):
            events_received.append(('on_error', time.time(), event))
            logger.error(f"📨 Event: on_error - {event}")
        
        results['event_handlers_registered'] = True
        results['events_received'] = events_received
        
        self.debug_results['event_handlers'] = results
        logger.info("✅ Event handlers configured for testing")
    
    async def run_live_message_test(self):
        """Test 8: Live Message Reception Test"""
        logger.info("🎯 Test 8: Live Message Reception Test")
        logger.info("⏰ Running 60-second live message monitoring...")
        
        if not self.token:
            logger.error("❌ No token for live testing")
            return
        
        # Create monitoring bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        intents.dm_messages = True
        
        client = LiveTestBot(intents=intents)
        
        try:
            # Run for 60 seconds
            await asyncio.wait_for(client.start(self.token), timeout=60.0)
        except asyncio.TimeoutError:
            logger.info("⏰ Live test completed")
            await client.close()
        except Exception as e:
            logger.error(f"❌ Live test error: {e}")
        
        # Collect results
        self.debug_results['live_test'] = {
            'messages_received': client.message_count,
            'events_logged': client.events_logged,
            'test_duration': 60
        }
        
        logger.info(f"📊 Live Test Results: {client.message_count} messages received")
    
    def generate_diagnosis_report(self):
        """Generate comprehensive diagnosis report"""
        logger.info("📋 Generating Comprehensive Diagnosis Report")
        logger.info("=" * 80)
        
        # Save detailed results to file
        with open('discord_diagnosis_report.json', 'w') as f:
            json.dump(self.debug_results, f, indent=2, default=str)
        
        # Generate human-readable report
        report = []
        report.append("🔍 DISCORD BOT DIAGNOSIS REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now()}")
        report.append("")
        
        # Environment Summary
        env_result = self.debug_results.get('environment', {})
        report.append("🔧 ENVIRONMENT:")
        report.append(f"  Python: {env_result.get('python_version', 'Unknown')}")
        report.append(f"  Platform: {env_result.get('platform', 'Unknown')}")
        report.append(f"  Discord.py: {env_result.get('discord_py_version', 'Unknown')}")
        report.append(f"  WSL2: {env_result.get('is_wsl', False)}")
        report.append("")
        
        # Network Summary
        net_result = self.debug_results.get('network', {})
        report.append("🌐 NETWORK:")
        report.append(f"  Internet: {'✅' if net_result.get('internet_access') else '❌'}")
        report.append(f"  Discord API: {'✅' if net_result.get('discord_api_access') else '❌'}")
        report.append(f"  DNS: {'✅' if net_result.get('dns_resolution') else '❌'}")
        report.append("")
        
        # Token Summary
        api_result = self.debug_results.get('discord_api', {})
        report.append("🔑 TOKEN:")
        report.append(f"  Valid: {'✅' if api_result.get('token_valid') else '❌'}")
        if api_result.get('bot_info'):
            report.append(f"  Bot: {api_result['bot_info']['username']}")
        report.append("")
        
        # Intent Summary
        intent_result = self.debug_results.get('intents', {})
        report.append("🎯 INTENTS:")
        if intent_result.get('intent_analysis'):
            for intent, analysis in intent_result['intent_analysis'].items():
                status = "✅" if analysis['enabled'] else "❌"
                report.append(f"  {intent}: {status}")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            report.append(f"  • {rec}")
        
        # Write report to file
        report_text = "\n".join(report)
        with open('discord_diagnosis_report.txt', 'w') as f:
            f.write(report_text)
        
        # Display report
        print("\n" + report_text)
        
        logger.info("📄 Detailed report saved to: discord_diagnosis_report.json")
        logger.info("📄 Summary report saved to: discord_diagnosis_report.txt")
    
    def generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on test results"""
        recommendations = []
        
        # Check environment issues
        env_result = self.debug_results.get('environment', {})
        if env_result.get('is_wsl'):
            recommendations.append("WSL2 detected: Consider testing on native Linux or Windows")
        
        # Check network issues
        net_result = self.debug_results.get('network', {})
        if not net_result.get('discord_api_access'):
            recommendations.append("Discord API inaccessible: Check firewall/proxy settings")
        
        # Check token issues
        api_result = self.debug_results.get('discord_api', {})
        if not api_result.get('token_valid'):
            recommendations.append("Invalid token: Regenerate bot token in Discord Developer Portal")
        
        # Check intent issues
        intent_result = self.debug_results.get('intents', {})
        if intent_result.get('intent_analysis'):
            for intent, analysis in intent_result['intent_analysis'].items():
                if not analysis['enabled'] and intent in ['message_content', 'guild_messages']:
                    recommendations.append(f"Enable {intent} intent in Discord Developer Portal")
        
        # Check compatibility issues
        compat_result = self.debug_results.get('compatibility', {})
        if compat_result.get('version_compatibility', {}).get('status') == 'warning':
            recommendations.append("Update Discord.py to latest version")
        
        if not recommendations:
            recommendations.append("All basic checks passed - issue may be in bot logic or Discord API changes")
        
        return recommendations


class LiveTestBot(discord.Client):
    """Special bot for live message testing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_count = 0
        self.events_logged = []
        self.start_time = time.time()
    
    async def on_ready(self):
        self.events_logged.append(('ready', time.time()))
        logger.info(f"🎯 Live Test Bot Ready: {self.user}")
        logger.info(f"📊 Monitoring {len(self.guilds)} guilds for messages...")
        
        # List channels we're monitoring
        for guild in self.guilds:
            logger.info(f"🏰 Guild: {guild.name}")
            for channel in guild.text_channels:
                logger.info(f"  📺 #{channel.name}")
    
    async def on_message(self, message):
        if message.author.bot:
            return
        
        self.message_count += 1
        self.events_logged.append(('message', time.time()))
        
        logger.info(f"📨 MESSAGE #{self.message_count}")
        logger.info(f"  Channel: #{message.channel.name}")
        logger.info(f"  Author: {message.author}")
        logger.info(f"  Content: {message.content[:100]}")
        
        # Respond to test messages
        if 'debug-test' in message.content.lower():
            await message.channel.send(f"🎯 Live Test Response #{self.message_count}")
    
    async def on_raw_message_create(self, payload):
        self.events_logged.append(('raw_message', time.time()))
        logger.info("📨 Raw message event received")


async def main():
    """Main diagnostic function"""
    debugger = AdvancedDiscordDebugger()
    await debugger.run_full_diagnosis()


if __name__ == "__main__":
    print("🔍 Advanced Discord Bot Debugger")
    print("=" * 50)
    print("This tool will perform comprehensive diagnostics on your Discord bot")
    print("to identify why it's not receiving message events.")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Diagnosis interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnosis failed: {e}")
        logger.exception("Diagnosis failed")