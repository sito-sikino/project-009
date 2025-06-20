#!/usr/bin/env python3
"""
MULTI-CLIENT CONFLICT DIAGNOSTIC
Identifies specific issues causing Discord bots to connect but stay offline
"""

import os
import sys
import asyncio
import logging
import discord
import psutil
import threading
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiClientDiagnostic:
    """Diagnostic tool for multi-client Discord bot issues"""
    
    def __init__(self):
        self.results = {}
        self.tokens = {
            'reception': os.getenv('DISCORD_RECEPTION_TOKEN'),
            'spectra': os.getenv('DISCORD_SPECTRA_TOKEN'),
            'lynq': os.getenv('DISCORD_LYNQ_TOKEN'),
            'paz': os.getenv('DISCORD_PAZ_TOKEN')
        }
        
    async def run_full_diagnostic(self):
        """Run comprehensive diagnostic"""
        print("🔍 MULTI-CLIENT CONFLICT DIAGNOSTIC")
        print("=" * 60)
        
        # Test 1: Token validation
        await self.test_token_conflicts()
        
        # Test 2: Single client test
        await self.test_single_client()
        
        # Test 3: Simulate multi-client conflict
        await self.test_multi_client_conflict()
        
        # Test 4: Event loop analysis
        await self.test_event_loop_conflicts()
        
        # Generate report
        self.generate_report()
        
    async def test_token_conflicts(self):
        """Test if multiple tokens are causing conflicts"""
        print("\n🔑 Test 1: Token Conflict Analysis")
        print("-" * 40)
        
        results = {}
        
        for name, token in self.tokens.items():
            if token:
                # Check if token is being reused
                token_prefix = token[:20] if len(token) > 20 else token
                results[name] = {
                    'exists': True,
                    'length': len(token),
                    'prefix': token_prefix,
                    'unique': True  # Will check for duplicates
                }
            else:
                results[name] = {'exists': False}
        
        # Check for duplicate tokens
        token_values = [info.get('prefix') for info in results.values() if info.get('exists')]
        for name, info in results.items():
            if info.get('exists'):
                prefix = info['prefix']
                if token_values.count(prefix) > 1:
                    info['unique'] = False
                    print(f"⚠️  DUPLICATE TOKEN DETECTED: {name}")
        
        # Validate each token
        for name, info in results.items():
            if info.get('exists'):
                print(f"✅ {name}: Token exists (length: {info['length']})")
                if not info['unique']:
                    print(f"❌ {name}: DUPLICATE TOKEN - This causes conflicts!")
            else:
                print(f"❌ {name}: Token missing")
        
        self.results['tokens'] = results
        
    async def test_single_client(self):
        """Test single client connection"""
        print("\n🔗 Test 2: Single Client Connection Test")
        print("-" * 40)
        
        token = self.tokens['reception']
        if not token:
            print("❌ No reception token for testing")
            return
        
        class TestClient(discord.Client):
            def __init__(self):
                intents = discord.Intents.all()
                super().__init__(intents=intents)
                self.connected = False
                self.ready = False
                
            async def on_connect(self):
                self.connected = True
                print("✅ Single client: Gateway connected")
                
            async def on_ready(self):
                self.ready = True
                print(f"✅ Single client: Ready as {self.user}")
                await self.close()  # Close immediately after ready
        
        client = TestClient()
        
        try:
            print("🚀 Testing single client connection...")
            await asyncio.wait_for(client.start(token), timeout=30.0)
            
            self.results['single_client'] = {
                'connected': client.connected,
                'ready': client.ready,
                'success': client.connected and client.ready
            }
            
            if client.connected and client.ready:
                print("✅ Single client test: SUCCESS")
            else:
                print("❌ Single client test: FAILED")
                
        except asyncio.TimeoutError:
            print("⏰ Single client test: TIMEOUT")
            self.results['single_client'] = {'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"❌ Single client test: ERROR - {e}")
            self.results['single_client'] = {'success': False, 'error': str(e)}
            
    async def test_multi_client_conflict(self):
        """Test multi-client conflicts"""
        print("\n⚔️  Test 3: Multi-Client Conflict Simulation")
        print("-" * 40)
        
        # Only test with 2 clients to avoid overwhelming
        tokens_to_test = [
            ('reception', self.tokens['reception']),
            ('spectra', self.tokens['spectra'])
        ]
        
        # Filter out missing tokens
        valid_tokens = [(name, token) for name, token in tokens_to_test if token]
        
        if len(valid_tokens) < 2:
            print("⚠️  Need at least 2 tokens for multi-client test")
            return
        
        class ConflictTestClient(discord.Client):
            def __init__(self, name):
                intents = discord.Intents.all()
                super().__init__(intents=intents)
                self.name = name
                self.connected = False
                self.ready = False
                self.connect_time = None
                self.ready_time = None
                
            async def on_connect(self):
                self.connected = True
                self.connect_time = datetime.now()
                print(f"🔗 {self.name}: Gateway connected at {self.connect_time}")
                
            async def on_ready(self):
                self.ready = True
                self.ready_time = datetime.now()
                print(f"✅ {self.name}: Ready as {self.user} at {self.ready_time}")
                
            async def on_disconnect(self):
                print(f"🔌 {self.name}: Disconnected")
        
        clients = []
        results = {}
        
        # Create clients
        for name, token in valid_tokens:
            client = ConflictTestClient(name)
            clients.append((name, client, token))
        
        try:
            print(f"🚀 Starting {len(clients)} clients simultaneously...")
            
            # Start all clients at the same time (THIS CAUSES THE CONFLICT)
            start_tasks = []
            for name, client, token in clients:
                start_tasks.append(client.start(token))
            
            # Run for 30 seconds to see what happens
            await asyncio.wait_for(
                asyncio.gather(*start_tasks, return_exceptions=True),
                timeout=30.0
            )
            
        except asyncio.TimeoutError:
            print("⏰ Multi-client test completed (timeout)")
        except Exception as e:
            print(f"❌ Multi-client test error: {e}")
        
        # Analyze results
        for name, client, token in clients:
            results[name] = {
                'connected': client.connected,
                'ready': client.ready,
                'connect_time': client.connect_time,
                'ready_time': client.ready_time
            }
            
            status = "SUCCESS" if client.connected and client.ready else "FAILED"
            print(f"📊 {name}: {status} (Connected: {client.connected}, Ready: {client.ready})")
            
            # Close clients
            try:
                await client.close()
            except:
                pass
        
        self.results['multi_client'] = results
        
        # Check for conflicts
        ready_count = sum(1 for r in results.values() if r['ready'])
        connected_count = sum(1 for r in results.values() if r['connected'])
        
        print(f"\n📊 Multi-Client Results:")
        print(f"   Connected: {connected_count}/{len(clients)}")
        print(f"   Ready: {ready_count}/{len(clients)}")
        
        if ready_count < len(clients):
            print("❌ MULTI-CLIENT CONFLICT DETECTED!")
            print("   Not all clients became ready - this indicates event loop conflicts")
        else:
            print("✅ No obvious multi-client conflicts detected")
            
    async def test_event_loop_conflicts(self):
        """Test event loop conflicts"""
        print("\n🔄 Test 4: Event Loop Conflict Analysis")
        print("-" * 40)
        
        # Check current event loop
        try:
            loop = asyncio.get_running_loop()
            print(f"✅ Current event loop: {loop}")
            print(f"✅ Loop is running: {loop.is_running()}")
            
            # Check for multiple event loops
            thread_count = threading.active_count()
            print(f"✅ Active threads: {thread_count}")
            
            # Check system resources
            process = psutil.Process()
            print(f"✅ Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            print(f"✅ CPU usage: {process.cpu_percent()}%")
            print(f"✅ Open file descriptors: {process.num_fds()}")
            
            self.results['event_loop'] = {
                'loop_exists': True,
                'loop_running': loop.is_running(),
                'thread_count': thread_count,
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'file_descriptors': process.num_fds()
            }
            
        except Exception as e:
            print(f"❌ Event loop analysis failed: {e}")
            self.results['event_loop'] = {'error': str(e)}
    
    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "=" * 60)
        print("📋 DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Token analysis
        token_results = self.results.get('tokens', {})
        duplicate_tokens = [name for name, info in token_results.items() 
                          if info.get('exists') and not info.get('unique', True)]
        
        if duplicate_tokens:
            print("❌ CRITICAL ISSUE: Duplicate tokens detected!")
            print(f"   Affected bots: {', '.join(duplicate_tokens)}")
            print("   FIX: Use unique tokens for each bot")
        
        # Single vs multi-client comparison
        single_success = self.results.get('single_client', {}).get('success', False)
        multi_results = self.results.get('multi_client', {})
        multi_success_count = sum(1 for r in multi_results.values() if r.get('ready', False))
        multi_total = len(multi_results)
        
        print(f"\n📊 Connection Analysis:")
        print(f"   Single client: {'✅ SUCCESS' if single_success else '❌ FAILED'}")
        print(f"   Multi-client: {multi_success_count}/{multi_total} successful")
        
        if single_success and multi_success_count < multi_total:
            print("\n❌ CRITICAL ISSUE: Multi-client event loop conflict detected!")
            print("   Single client works, but multiple clients fail")
            print("   FIX: Run clients in separate processes or use different architecture")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if duplicate_tokens:
            print("   1. Generate unique tokens for each bot in Discord Developer Portal")
        
        if single_success and multi_success_count < multi_total:
            print("   2. CRITICAL: Separate reception and output bots into different processes")
            print("   3. Use message queues (Redis/RabbitMQ) for inter-process communication")
            print("   4. Run only reception client in main process")
        
        if not single_success:
            print("   1. Check Discord Developer Portal bot configuration")
            print("   2. Verify all required intents are enabled")
            print("   3. Check network connectivity and firewall settings")
        
        print("\n🛠️  IMMEDIATE FIXES:")
        print("   1. Run isolated_reception_test.py to test single client")
        print("   2. Update main.py to use only reception client")
        print("   3. Implement separate output bot processes")
        
        print("=" * 60)

async def main():
    """Main diagnostic function"""
    diagnostic = MultiClientDiagnostic()
    await diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()