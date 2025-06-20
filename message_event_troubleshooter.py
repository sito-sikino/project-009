#!/usr/bin/env python3
"""
Discord Message Event Troubleshooter
Step-by-step verification for Discord bots that connect but don't receive message events

This script focuses specifically on the "connects successfully but no message events" issue.
"""

import os
import sys
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import aiohttp
import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class MessageEventTroubleshooter:
    """
    Specialized troubleshooter for Discord message event issues.
    
    Focuses on the specific scenario where:
    - Bot connects successfully (on_ready fires)
    - Bot has proper intents configured
    - Bot receives zero message events
    """
    
    def __init__(self):
        self.token = os.getenv('DISCORD_RECEPTION_TOKEN')
        self.test_results = {}
        self.verification_steps = []
    
    async def run_verification(self):
        """Run step-by-step verification process"""
        logger.info("🔍 Discord Message Event Troubleshooter")
        logger.info("=" * 60)
        logger.info("Diagnosing: Bot connects but receives no message events")
        logger.info("=" * 60)
        
        # Step 1: Token and Application Type Verification
        await self.verify_token_type()
        
        # Step 2: Permissions and Scope Verification
        await self.verify_bot_permissions()
        
        # Step 3: Intent Configuration Verification
        await self.verify_intent_setup()
        
        # Step 4: Gateway Connection Analysis
        await self.verify_gateway_connection()
        
        # Step 5: Event Registration Verification
        await self.verify_event_registration()
        
        # Step 6: Guild and Channel Access Verification
        await self.verify_guild_access()
        
        # Step 7: Live Message Event Test
        await self.live_message_event_test()
        
        # Step 8: Generate specific recommendations
        self.generate_specific_recommendations()
    
    async def verify_token_type(self):
        """Step 1: Verify token type and application configuration"""
        logger.info("🔑 Step 1: Token and Application Type Verification")
        
        if not self.token:
            self.add_verification_result("token_exists", False, "No DISCORD_RECEPTION_TOKEN found")
            return
        
        # Analyze token format
        token_parts = self.token.split('.')
        token_analysis = {
            'parts_count': len(token_parts),
            'expected_parts': 3,
            'first_part_length': len(token_parts[0]) if token_parts else 0,
            'is_bot_token_format': len(token_parts) == 3 and len(token_parts[0]) > 20
        }
        
        # Test token with Discord API
        headers = {'Authorization': f'Bot {self.token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://discord.com/api/v10/users/@me',
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        user_data = await resp.json()
                        token_analysis.update({
                            'valid': True,
                            'bot_account': user_data.get('bot', False),
                            'username': user_data.get('username'),
                            'id': user_data.get('id'),
                            'verified': user_data.get('verified')
                        })
                        
                        self.add_verification_result(
                            "token_valid", 
                            True, 
                            f"Valid bot token for {user_data.get('username')}"
                        )
                        
                        if not user_data.get('bot'):
                            self.add_verification_result(
                                "token_type_error",
                                False,
                                "❌ CRITICAL: Token is for user account, not bot account!"
                            )
                    else:
                        error_text = await resp.text()
                        token_analysis.update({
                            'valid': False,
                            'http_status': resp.status,
                            'error': error_text
                        })
                        
                        self.add_verification_result(
                            "token_valid",
                            False,
                            f"Invalid token - HTTP {resp.status}: {error_text}"
                        )
        
        except Exception as e:
            token_analysis.update({'valid': False, 'error': str(e)})
            self.add_verification_result("token_test_error", False, f"Token test failed: {e}")
        
        self.test_results['token_analysis'] = token_analysis
        
        # Format verification
        if token_analysis['is_bot_token_format']:
            logger.info("✅ Token format appears correct")
        else:
            logger.warning("⚠️  Token format may be incorrect")
        
        logger.info(f"Token parts: {token_analysis['parts_count']}/3 expected")
    
    async def verify_bot_permissions(self):
        """Step 2: Verify bot permissions and OAuth2 scope"""
        logger.info("🛡️  Step 2: Bot Permissions and Scope Verification")
        
        if not self.token:
            self.add_verification_result("permissions_check", False, "No token for permission check")
            return
        
        headers = {'Authorization': f'Bot {self.token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get bot's application info
                async with session.get(
                    'https://discord.com/api/v10/oauth2/applications/@me',
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        app_data = await resp.json()
                        
                        permissions_info = {
                            'app_id': app_data.get('id'),
                            'app_name': app_data.get('name'),
                            'bot_public': app_data.get('bot_public'),
                            'bot_require_code_grant': app_data.get('bot_require_code_grant'),
                            'flags': app_data.get('flags')
                        }
                        
                        self.test_results['application_info'] = permissions_info
                        
                        logger.info(f"✅ Application: {app_data.get('name')}")
                        logger.info(f"✅ Bot Public: {app_data.get('bot_public')}")
                        logger.info(f"✅ Require Code Grant: {app_data.get('bot_require_code_grant')}")
                        
                        self.add_verification_result(
                            "application_accessible",
                            True,
                            f"Bot application accessible: {app_data.get('name')}"
                        )
                    else:
                        error_text = await resp.text()
                        self.add_verification_result(
                            "application_accessible",
                            False,
                            f"Cannot access application info - HTTP {resp.status}: {error_text}"
                        )
        
        except Exception as e:
            self.add_verification_result("application_check_error", False, f"Application check failed: {e}")
    
    async def verify_intent_setup(self):
        """Step 3: Comprehensive intent configuration verification"""
        logger.info("🎯 Step 3: Intent Configuration Deep Verification")
        
        # Test different intent configurations
        intent_configs = [
            ("minimal", {'message_content': True, 'guild_messages': True, 'guilds': True}),
            ("standard", {'message_content': True, 'guild_messages': True, 'guilds': True, 'dm_messages': True}),
            ("privileged", {'message_content': True, 'guild_messages': True, 'guilds': True, 'members': True, 'presences': True})
        ]
        
        for config_name, intent_settings in intent_configs:
            logger.info(f"Testing intent configuration: {config_name}")
            
            intents = discord.Intents.none()  # Start with no intents
            for intent_name, enabled in intent_settings.items():
                setattr(intents, intent_name, enabled)
            
            # Test gateway connection with these intents
            success = await self.test_intent_configuration(config_name, intents)
            
            self.add_verification_result(
                f"intent_config_{config_name}",
                success,
                f"Intent configuration '{config_name}' {'worked' if success else 'failed'}"
            )
    
    async def test_intent_configuration(self, config_name: str, intents: discord.Intents) -> bool:
        """Test a specific intent configuration"""
        if not self.token:
            return False
        
        try:
            client = discord.Client(intents=intents)
            
            connection_success = False
            
            @client.event
            async def on_ready():
                nonlocal connection_success
                connection_success = True
                logger.info(f"✅ {config_name} intents: Connection successful")
                await client.close()
            
            # Test connection with timeout
            await asyncio.wait_for(client.start(self.token), timeout=15.0)
            return connection_success
        
        except discord.LoginFailure:
            logger.error(f"❌ {config_name} intents: Login failed")
            return False
        except discord.PrivilegedIntentsRequired as e:
            logger.error(f"❌ {config_name} intents: Privileged intents required - {e}")
            return False
        except asyncio.TimeoutError:
            logger.warning(f"⚠️  {config_name} intents: Connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ {config_name} intents: Unexpected error - {e}")
            return False
    
    async def verify_gateway_connection(self):
        """Step 4: Detailed gateway connection analysis"""
        logger.info("🌉 Step 4: Gateway Connection Analysis")
        
        if not self.token:
            self.add_verification_result("gateway_test", False, "No token for gateway test")
            return
        
        # Test gateway info endpoint
        headers = {'Authorization': f'Bot {self.token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://discord.com/api/v10/gateway/bot',
                    headers=headers,
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        gateway_data = await resp.json()
                        
                        self.test_results['gateway_info'] = gateway_data
                        
                        logger.info(f"✅ Gateway URL: {gateway_data.get('url')}")
                        logger.info(f"✅ Shards: {gateway_data.get('shards', 1)}")
                        logger.info(f"✅ Session Start Limit: {gateway_data.get('session_start_limit', {})}")
                        
                        self.add_verification_result(
                            "gateway_info_accessible",
                            True,
                            "Gateway information accessible"
                        )
                        
                        # Check session limits
                        session_limit = gateway_data.get('session_start_limit', {})
                        remaining = session_limit.get('remaining', 0)
                        
                        if remaining < 5:
                            self.add_verification_result(
                                "session_limit_warning",
                                False,
                                f"⚠️  Low session start limit remaining: {remaining}"
                            )
                    else:
                        error_text = await resp.text()
                        self.add_verification_result(
                            "gateway_info_accessible",
                            False,
                            f"Cannot access gateway info - HTTP {resp.status}: {error_text}"
                        )
        
        except Exception as e:
            self.add_verification_result("gateway_info_error", False, f"Gateway info check failed: {e}")
    
    async def verify_event_registration(self):
        """Step 5: Event registration and handler verification"""
        logger.info("🎭 Step 5: Event Registration Verification")
        
        if not self.token:
            return
        
        # Create test client with comprehensive event logging
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        
        client = EventTestClient(intents=intents)
        
        try:
            # Test for 10 seconds
            await asyncio.wait_for(client.start(self.token), timeout=10.0)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.error(f"Event registration test error: {e}")
        
        # Analyze results
        events_received = client.events_received
        
        self.test_results['event_registration'] = {
            'events_received': events_received,
            'ready_fired': any(event[0] == 'on_ready' for event in events_received),
            'total_events': len(events_received)
        }
        
        ready_fired = any(event[0] == 'on_ready' for event in events_received)
        
        self.add_verification_result(
            "on_ready_fires",
            ready_fired,
            f"on_ready event {'fired' if ready_fired else 'did not fire'}"
        )
        
        logger.info(f"Events received during test: {len(events_received)}")
        for event_name, timestamp in events_received:
            logger.info(f"  - {event_name} at {timestamp}")
    
    async def verify_guild_access(self):
        """Step 6: Guild and channel access verification"""
        logger.info("🏰 Step 6: Guild and Channel Access Verification")
        
        if not self.token:
            return
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        
        client = discord.Client(intents=intents)
        
        guild_info = []
        
        @client.event
        async def on_ready():
            logger.info(f"Connected to {len(client.guilds)} guild(s)")
            
            for guild in client.guilds:
                permissions = guild.me.guild_permissions if guild.me else None
                
                guild_data = {
                    'name': guild.name,
                    'id': guild.id,
                    'member_count': guild.member_count,
                    'text_channels': len(guild.text_channels),
                    'bot_permissions': {
                        'read_messages': permissions.read_messages if permissions else False,
                        'send_messages': permissions.send_messages if permissions else False,
                        'read_message_history': permissions.read_message_history if permissions else False,
                        'view_channel': permissions.view_channel if permissions else False
                    } if permissions else None
                }
                
                guild_info.append(guild_data)
                
                logger.info(f"Guild: {guild.name}")
                logger.info(f"  Text channels: {len(guild.text_channels)}")
                
                if permissions:
                    logger.info(f"  Permissions:")
                    logger.info(f"    Read messages: {permissions.read_messages}")
                    logger.info(f"    Send messages: {permissions.send_messages}")
                    logger.info(f"    Read history: {permissions.read_message_history}")
                    logger.info(f"    View channel: {permissions.view_channel}")
                
                # Check specific channels
                for channel in guild.text_channels[:3]:  # Check first 3 channels
                    try:
                        channel_perms = channel.permissions_for(guild.me) if guild.me else None
                        if channel_perms:
                            logger.info(f"    #{channel.name}: read={channel_perms.read_messages}, view={channel_perms.view_channel}")
                    except Exception as e:
                        logger.warning(f"    #{channel.name}: Permission check failed - {e}")
            
            await client.close()
        
        try:
            await asyncio.wait_for(client.start(self.token), timeout=15.0)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.error(f"Guild access verification error: {e}")
        
        self.test_results['guild_access'] = guild_info
        
        if guild_info:
            self.add_verification_result(
                "has_guild_access",
                True,
                f"Bot has access to {len(guild_info)} guild(s)"
            )
            
            # Check if bot has necessary permissions
            has_message_perms = all(
                guild_data.get('bot_permissions', {}).get('read_messages', False)
                for guild_data in guild_info
            )
            
            self.add_verification_result(
                "has_message_permissions",
                has_message_perms,
                f"Bot {'has' if has_message_perms else 'lacks'} message reading permissions"
            )
        else:
            self.add_verification_result(
                "has_guild_access",
                False,
                "Bot has no guild access"
            )
    
    async def live_message_event_test(self):
        """Step 7: Live message event monitoring test"""
        logger.info("🎯 Step 7: Live Message Event Test")
        logger.info("Running 30-second live message monitoring...")
        logger.info("💡 Send a message containing 'test-event' in any channel the bot can see")
        
        if not self.token:
            return
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        intents.dm_messages = True
        
        client = LiveMessageTester(intents=intents)
        
        try:
            await asyncio.wait_for(client.start(self.token), timeout=30.0)
        except asyncio.TimeoutError:
            logger.info("⏰ Live test completed")
        except Exception as e:
            logger.error(f"Live test error: {e}")
        finally:
            if not client.is_closed():
                await client.close()
        
        # Analyze results
        self.test_results['live_test'] = {
            'messages_received': client.message_count,
            'raw_events_received': client.raw_event_count,
            'ready_fired': client.ready_fired,
            'test_duration': 30
        }
        
        success = client.message_count > 0
        
        self.add_verification_result(
            "live_message_events",
            success,
            f"Received {client.message_count} message events in live test"
        )
        
        self.add_verification_result(
            "live_raw_events",
            client.raw_event_count > 0,
            f"Received {client.raw_event_count} raw message events in live test"
        )
        
        logger.info(f"📊 Live Test Results:")
        logger.info(f"  Messages received: {client.message_count}")
        logger.info(f"  Raw events received: {client.raw_event_count}")
        logger.info(f"  Bot ready: {client.ready_fired}")
    
    def add_verification_result(self, step: str, success: bool, message: str):
        """Add a verification step result"""
        self.verification_steps.append({
            'step': step,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {message}")
    
    def generate_specific_recommendations(self):
        """Generate specific recommendations based on verification results"""
        logger.info("💡 Step 8: Generating Specific Recommendations")
        logger.info("=" * 60)
        
        # Analyze all verification results
        failed_steps = [step for step in self.verification_steps if not step['success']]
        successful_steps = [step for step in self.verification_steps if step['success']]
        
        recommendations = []
        
        # Token issues
        if any('token' in step['step'] for step in failed_steps):
            recommendations.append("🔑 REGENERATE BOT TOKEN: Go to Discord Developer Portal > Your App > Bot > Reset Token")
        
        # Application type issues
        if any('token_type_error' in step['step'] for step in failed_steps):
            recommendations.append("🤖 CREATE BOT APPLICATION: Ensure you're using a Bot token, not User token")
        
        # Permission issues
        if any('permissions' in step['step'] for step in failed_steps):
            recommendations.append("🛡️  CHECK BOT PERMISSIONS: Ensure bot has 'Read Messages' and 'View Channels' permissions")
        
        # Intent issues
        if any('intent' in step['step'] for step in failed_steps):
            recommendations.append("🎯 ENABLE MESSAGE CONTENT INTENT: Go to Discord Developer Portal > Your App > Bot > Privileged Gateway Intents")
        
        # Live test failures
        live_test_failed = any('live_message_events' in step['step'] for step in failed_steps)
        ready_successful = any('on_ready_fires' in step['step'] for step in successful_steps)
        
        if live_test_failed and ready_successful:
            recommendations.extend([
                "🔍 BOT CONNECTS BUT NO MESSAGES: This is the core issue!",
                "   • Verify Message Content Intent is enabled in Discord Developer Portal",
                "   • Check if bot has 'View Channel' permission in specific channels",
                "   • Ensure bot is not in a channel where it lacks read permissions",
                "   • Try inviting bot to a new test server with Administrator permissions",
                "   • Test in a different Discord client (web/desktop/mobile)"
            ])
        
        # No guild access
        if not any('has_guild_access' in step['step'] for step in successful_steps):
            recommendations.append("🏰 ADD BOT TO SERVER: Bot is not in any Discord servers")
        
        # Session limit issues
        if any('session_limit' in step['step'] for step in failed_steps):
            recommendations.append("⏰ WAIT FOR SESSION LIMIT RESET: Too many connection attempts")
        
        if not recommendations:
            recommendations.append("✅ ALL CHECKS PASSED: Issue may be environmental or code-related")
        
        # Save results to file
        report = {
            'verification_steps': self.verification_steps,
            'test_results': self.test_results,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('message_event_troubleshoot_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Display recommendations
        logger.info("📋 SPECIFIC RECOMMENDATIONS:")
        for rec in recommendations:
            logger.info(f"  {rec}")
        
        logger.info(f"\n📄 Detailed report saved to: message_event_troubleshoot_report.json")
        
        # Summary
        success_rate = len(successful_steps) / len(self.verification_steps) * 100 if self.verification_steps else 0
        logger.info(f"\n📊 VERIFICATION SUMMARY:")
        logger.info(f"  Success rate: {success_rate:.1f}% ({len(successful_steps)}/{len(self.verification_steps)})")
        logger.info(f"  Failed steps: {len(failed_steps)}")
        
        if live_test_failed and ready_successful:
            logger.info("\n🎯 CORE ISSUE IDENTIFIED:")
            logger.info("  Bot connects successfully but receives no message events")
            logger.info("  This indicates an Intent or Permission configuration issue")


class EventTestClient(discord.Client):
    """Test client for event registration verification"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events_received = []
    
    async def on_ready(self):
        self.events_received.append(('on_ready', time.time()))
    
    async def on_message(self, message):
        self.events_received.append(('on_message', time.time()))
    
    async def on_raw_message_create(self, payload):
        self.events_received.append(('on_raw_message_create', time.time()))
    
    async def on_guild_join(self, guild):
        self.events_received.append(('on_guild_join', time.time()))


class LiveMessageTester(discord.Client):
    """Live message testing client"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_count = 0
        self.raw_event_count = 0
        self.ready_fired = False
    
    async def on_ready(self):
        self.ready_fired = True
        logger.info(f"🎯 Live tester ready: {self.user}")
        logger.info(f"📊 Monitoring {len(self.guilds)} guilds")
        
        # Log available channels
        for guild in self.guilds:
            logger.info(f"🏰 {guild.name}:")
            for channel in guild.text_channels[:5]:  # Show first 5 channels
                logger.info(f"  📺 #{channel.name}")
    
    async def on_message(self, message):
        if message.author.bot:
            return
        
        self.message_count += 1
        logger.info(f"📨 MESSAGE #{self.message_count}: {message.content[:50]} (#{message.channel.name})")
        
        if 'test-event' in message.content.lower():
            await message.channel.send(f"🎯 Message event working! Count: {self.message_count}")
    
    async def on_raw_message_create(self, payload):
        self.raw_event_count += 1
        logger.info(f"📡 RAW EVENT #{self.raw_event_count}")


async def main():
    """Main troubleshooting function"""
    troubleshooter = MessageEventTroubleshooter()
    await troubleshooter.run_verification()


if __name__ == "__main__":
    print("🔍 Discord Message Event Troubleshooter")
    print("=" * 50)
    print("Specialized tool for diagnosing bots that connect but don't receive messages")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Troubleshooting interrupted by user")
    except Exception as e:
        print(f"\n❌ Troubleshooting failed: {e}")
        logger.exception("Troubleshooting failed")