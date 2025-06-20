# Discord Multi-Agent System - Test Execution Guide

## 📋 Overview

This guide provides step-by-step instructions for executing the comprehensive test strategy for the Discord Multi-Agent System. It serves as the practical implementation guide for the TDD workflow.

## 🎯 Quick Start Checklist

### Pre-Implementation Setup
- [ ] Create project directory structure
- [ ] Install testing dependencies
- [ ] Set up mock frameworks
- [ ] Configure test databases
- [ ] Establish baseline metrics

### Daily TDD Workflow
- [ ] Run existing tests before starting work
- [ ] Write failing tests for new functionality
- [ ] Implement minimal code to pass tests
- [ ] Refactor while keeping tests green
- [ ] Validate acceptance criteria

## 📁 Test Environment Setup

### 1. Directory Structure Creation

```bash
# Create complete test structure
mkdir -p project-009/{tests/{unit,integration,e2e,fixtures},src,config,scripts,logs}
cd project-009

# Create test files
touch tests/__init__.py
touch tests/conftest.py
touch tests/fixtures/__init__.py

# Unit test files
touch tests/unit/test_discord_clients.py
touch tests/unit/test_langgraph_supervisor.py
touch tests/unit/test_gemini_client.py
touch tests/unit/test_memory_system.py
touch tests/unit/test_message_processor.py
touch tests/unit/test_message_router.py
touch tests/unit/test_autonomous_speech.py

# Integration test files
touch tests/integration/test_message_flow.py
touch tests/integration/test_memory_integration.py
touch tests/integration/test_orchestrator.py
touch tests/integration/test_parallel_clients.py
touch tests/integration/test_api_rate_limiting.py

# E2E test files
touch tests/e2e/test_discord_integration.py
touch tests/e2e/test_full_workflow.py
touch tests/e2e/test_performance.py
touch tests/e2e/test_load_testing.py

# Fixture files
touch tests/fixtures/discord_fixtures.py
touch tests/fixtures/gemini_fixtures.py
touch tests/fixtures/memory_fixtures.py
touch tests/fixtures/test_config.py
```

### 2. Dependencies Installation

```bash
# Create requirements-test.txt
cat > requirements-test.txt << 'EOF'
# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-benchmark>=4.0.0
pytest-timeout>=2.1.0

# Mocking and Fixtures
factory-boy>=3.3.0
freezegun>=1.2.0
responses>=0.23.0

# Performance Testing
memory-profiler>=0.61.0
psutil>=5.9.0

# Data Analysis
numpy>=1.24.0
pandas>=2.0.0

# Development Tools
black>=23.0.0
isort>=5.12.0
mypy>=1.5.0
flake8>=6.0.0

# Test Reporting
pytest-html>=3.2.0
pytest-json-report>=1.5.0
coverage[toml]>=7.2.0
EOF

pip install -r requirements-test.txt
```

### 3. pytest Configuration

```python
# tests/conftest.py
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from tests.fixtures.discord_fixtures import MockDiscordClient, MockDiscordMessage
from tests.fixtures.gemini_fixtures import GeminiResponseSimulator
from tests.fixtures.memory_fixtures import MockRedisClient, MockPostgreSQLClient

# Test environment setup
os.environ["ENV_MODE"] = "test"
os.environ["DEBUG_MODE"] = "true"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_discord_client():
    """Provide mock Discord client"""
    return MockDiscordClient()

@pytest.fixture
async def mock_redis_client():
    """Provide mock Redis client"""
    return MockRedisClient()

@pytest.fixture
async def mock_postgres_client():
    """Provide mock PostgreSQL client"""
    return MockPostgreSQLClient()

@pytest.fixture
def mock_gemini_client():
    """Provide mock Gemini client"""
    client = AsyncMock()
    client.unified_agent_selection = AsyncMock(
        side_effect=lambda context: GeminiResponseSimulator.unified_agent_selection_response(
            context.get("current_message", ""),
            context.get("channel", "command-center"),
            context.get("hot_memory", []),
            context.get("cold_memory", [])
        )
    )
    return client

@pytest.fixture
def test_message():
    """Provide test Discord message"""
    return MockDiscordMessage("Test message content")

@pytest.fixture
def mention_message():
    """Provide test mention message"""
    return MockDiscordMessage("@Spectra what do you think?", mentions=[MagicMock(id=12345)])

# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "load: Load testing")
    config.addinivalue_line("markers", "acceptance: Acceptance criteria tests")
    config.addinivalue_line("markers", "discord_api: Tests requiring real Discord API")

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on location"""
    for item in items:
        # Mark tests based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark slow tests
        if "load" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)
```

### 4. Test Configuration File

```python
# tests/fixtures/test_config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestConfig:
    """Central test configuration"""
    
    # Environment
    env_mode: str = "test"
    debug_mode: bool = True
    
    # Test execution
    use_real_discord: bool = False
    use_real_gemini: bool = False
    use_real_databases: bool = False
    
    # Performance testing
    response_time_limit: float = 9.0
    agent_accuracy_target: float = 0.95
    load_test_duration: int = 60
    concurrent_users: int = 10
    
    # Database testing
    test_redis_host: str = "localhost"
    test_redis_port: int = 6379
    test_redis_db: int = 1
    
    test_postgres_host: str = "localhost"
    test_postgres_port: int = 5432
    test_postgres_db: str = "test_discord_agent"
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """Load configuration from environment"""
        return cls(
            env_mode=os.getenv("TEST_ENV_MODE", "test"),
            debug_mode=os.getenv("DEBUG_MODE", "true").lower() == "true",
            use_real_discord=os.getenv("USE_REAL_DISCORD", "false").lower() == "true",
            use_real_gemini=os.getenv("USE_REAL_GEMINI", "false").lower() == "true",
            use_real_databases=os.getenv("USE_REAL_DATABASES", "false").lower() == "true",
        )

TEST_CONFIG = TestConfig.from_env()
```

## 🔄 TDD Implementation Workflow

### Phase 1: Test Design Implementation

#### Step 1: Create First Unit Test (Red Phase)

```python
# tests/unit/test_discord_clients.py - FIRST TEST EXAMPLE
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

class TestReceptionClient:
    """Test the unified message reception system"""
    
    @pytest.mark.asyncio
    async def test_on_message_queues_message_with_correct_priority(self):
        """
        RED PHASE TEST: This test will fail initially
        Tests that reception client queues messages with correct priority
        """
        # Arrange - This will fail because ReceptionClient doesn't exist yet
        from src.discord_clients import ReceptionClient  # This import will fail
        
        client = ReceptionClient()
        client.message_queue = asyncio.PriorityQueue()
        
        mention_message = MagicMock()
        mention_message.mentions = [MagicMock(id=12345)]
        mention_message.author.bot = False
        
        # Act - This will fail because on_message doesn't exist yet
        await client.on_message(mention_message)
        
        # Assert - This will fail because the method doesn't exist
        priority, message = await client.message_queue.get()
        assert priority == 1  # Mention priority
        assert message == mention_message

# Run this test to see it fail
# pytest tests/unit/test_discord_clients.py::TestReceptionClient::test_on_message_queues_message_with_correct_priority -v
```

#### Step 2: Implement Minimal Code (Green Phase)

```python
# src/discord_clients.py - MINIMAL IMPLEMENTATION
import asyncio
import discord

class ReceptionClient(discord.Client):
    """Minimal implementation to make the first test pass"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_queue = asyncio.PriorityQueue()
    
    async def on_message(self, message):
        """Minimal implementation - just queue with mention priority"""
        if message.mentions and not message.author.bot:
            priority = 1  # Mention priority
            await self.message_queue.put((priority, message))

# Run the test again to see it pass
# pytest tests/unit/test_discord_clients.py::TestReceptionClient::test_on_message_queues_message_with_correct_priority -v
```

#### Step 3: Add More Tests (Red Phase)

```python
# tests/unit/test_discord_clients.py - ADD MORE FAILING TESTS
class TestReceptionClient:
    # ... existing test ...
    
    @pytest.mark.asyncio
    async def test_on_message_handles_normal_messages(self):
        """Test that normal messages get priority 3"""
        from src.discord_clients import ReceptionClient
        
        client = ReceptionClient()
        normal_message = MagicMock()
        normal_message.mentions = []  # No mentions
        normal_message.author.bot = False
        
        await client.on_message(normal_message)
        
        priority, message = await client.message_queue.get()
        assert priority == 3  # Normal message priority
        assert message == normal_message
    
    @pytest.mark.asyncio
    async def test_on_message_ignores_bot_messages(self):
        """Test that bot messages are ignored"""
        from src.discord_clients import ReceptionClient
        
        client = ReceptionClient()
        bot_message = MagicMock()
        bot_message.author.bot = True
        
        await client.on_message(bot_message)
        
        # Queue should be empty
        assert client.message_queue.empty()

# Run tests to see new ones fail
# pytest tests/unit/test_discord_clients.py -v
```

#### Step 4: Expand Implementation (Green Phase)

```python
# src/discord_clients.py - EXPANDED IMPLEMENTATION
import asyncio
import discord

class ReceptionClient(discord.Client):
    """Expanded implementation to handle all message types"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_queue = asyncio.PriorityQueue()
        self.processed_message_ids = set()
    
    async def on_message(self, message):
        """Handle all message types with proper prioritization"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Prevent duplicate processing
        if message.id in self.processed_message_ids:
            return
        
        self.processed_message_ids.add(message.id)
        
        # Determine priority
        if message.mentions:
            priority = 1  # Mention priority
        else:
            priority = 3  # Normal message priority
        
        await self.message_queue.put((priority, message))

# Run all tests to see them pass
# pytest tests/unit/test_discord_clients.py -v
```

### Phase 2: Integration Test Implementation

#### Step 1: Create Integration Test Structure

```python
# tests/integration/test_message_flow.py - INTEGRATION TEST SKELETON
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock

class TestCompleteMessageFlow:
    """Integration tests for complete message processing pipeline"""
    
    @pytest.mark.asyncio
    async def test_mention_flow_completes_within_time_limit(self):
        """
        INTEGRATION TEST: Complete mention processing pipeline
        This will fail until all components are implemented
        """
        # This test will guide the integration of all components
        from src.main import DiscordMultiAgentSystem  # Will fail initially
        
        system = DiscordMultiAgentSystem()
        await system.setup_infrastructure()
        
        # Create test mention message
        mention_message = MagicMock()
        mention_message.content = "@Spectra what's our status?"
        mention_message.mentions = [MagicMock(id=system.spectra_bot_id)]
        
        # Measure processing time
        start_time = time.time()
        result = await system.process_complete_message_flow(mention_message)
        elapsed_time = time.time() - start_time
        
        # Assertions
        assert elapsed_time < 9.0
        assert result["success"] is True
        assert result["selected_agent"] == "spectra"

# This test will fail and guide the implementation of the main system
# pytest tests/integration/test_message_flow.py -v
```

### Phase 3: Test-Driven Component Development

#### Development Order Based on Dependencies

1. **Configuration System** (No dependencies)
2. **Memory System** (Independent)
3. **Gemini Client** (Independent)
4. **LangGraph Supervisor** (Depends on Gemini + Memory)
5. **Discord Clients** (Depends on Message Processing)
6. **Message Router** (Depends on all components)
7. **Main System** (Integrates everything)

#### Example: Memory System TDD

```python
# tests/unit/test_memory_system.py - MEMORY SYSTEM TDD
class TestHotMemory:
    """Test Redis-based hot memory system"""
    
    @pytest.mark.asyncio
    async def test_store_conversation_maintains_20_message_limit(self):
        """Test that hot memory keeps only 20 recent messages"""
        # RED PHASE: This will fail because HotMemory doesn't exist
        from src.memory_system import HotMemory
        
        memory = HotMemory()
        channel_id = "test_channel"
        
        # Store 25 messages
        for i in range(25):
            message_data = {"content": f"Message {i}", "timestamp": f"2025-06-19T10:{i:02d}:00"}
            await memory.store_conversation(channel_id, message_data)
        
        # Should only have 20 messages
        context = await memory.get_context(channel_id)
        assert len(context) == 20
        assert context[0]["content"] == "Message 24"  # Most recent first

# Implement minimal HotMemory to pass this test
# src/memory_system.py
import json
from typing import List, Dict, Any

class HotMemory:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or MockRedisClient()
    
    async def store_conversation(self, channel_id: str, message_data: Dict[str, Any]):
        key = f"channel:{channel_id}:messages"
        await self.redis_client.lpush(key, json.dumps(message_data))
        await self.redis_client.ltrim(key, 0, 19)  # Keep only 20 messages
    
    async def get_context(self, channel_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        key = f"channel:{channel_id}:messages"
        messages = await self.redis_client.lrange(key, 0, limit - 1)
        return [json.loads(msg) for msg in messages]
```

## 🎯 Test Execution Commands

### Daily Development Commands

```bash
# Quick unit test check (fast feedback)
pytest tests/unit/ -q --tb=line

# Specific component testing
pytest tests/unit/test_discord_clients.py -v
pytest tests/unit/test_langgraph_supervisor.py -v
pytest tests/unit/test_memory_system.py -v

# Integration testing
pytest tests/integration/ -v --tb=short

# Performance spot check
pytest tests/integration/test_message_flow.py::TestCompleteMessageFlow::test_mention_flow_completes_within_time_limit -v

# Coverage check
pytest tests/ --cov=src --cov-report=term-missing

# Quality gates
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
```

### Continuous Integration Commands

```bash
# Complete test suite
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Performance benchmark
pytest tests/e2e/test_performance.py -v --benchmark-autosave

# Load testing
pytest tests/e2e/test_load_testing.py -v -m load

# Acceptance criteria validation
pytest tests/ -m acceptance -v

# Test report generation
pytest tests/ --html=reports/test_report.html --self-contained-html
```

### Environment-Specific Testing

```bash
# Test environment (fast, mocked)
ENV_MODE=test pytest tests/ -v

# Development environment (slower, some real APIs)
ENV_MODE=development USE_REAL_DATABASES=true pytest tests/integration/ -v

# Production validation (careful, uses real APIs)
ENV_MODE=production USE_REAL_DISCORD=true pytest tests/e2e/test_discord_integration.py -v
```

## 📊 Test Metrics and Monitoring

### Test Execution Dashboard

```bash
#!/bin/bash
# scripts/test_dashboard.sh

echo "🎯 Discord Multi-Agent System - Test Dashboard"
echo "=============================================="

# Unit test metrics
echo "📊 Unit Tests:"
pytest tests/unit/ --tb=no -q | grep -E "(passed|failed|error)"

# Integration test metrics  
echo "📊 Integration Tests:"
pytest tests/integration/ --tb=no -q | grep -E "(passed|failed|error)"

# Coverage metrics
echo "📊 Coverage:"
pytest tests/ --cov=src --cov-report=term | grep -E "TOTAL.*%"

# Performance metrics
echo "📊 Performance:"
pytest tests/integration/test_message_flow.py::TestCompleteMessageFlow::test_mention_flow_completes_within_time_limit --tb=no -q

# Acceptance criteria status
echo "📊 Acceptance Criteria:"
pytest tests/ -m acceptance --tb=no -q | grep -E "(passed|failed|error)"

echo "=============================================="
echo "✅ Dashboard complete"
```

### Performance Tracking

```python
# scripts/performance_tracker.py
import json
import time
from datetime import datetime
from pathlib import Path

class PerformanceTracker:
    """Track test performance over time"""
    
    def __init__(self):
        self.results_file = Path("test_performance_history.json")
        self.load_history()
    
    def load_history(self):
        """Load historical performance data"""
        if self.results_file.exists():
            with open(self.results_file) as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def record_test_run(self, test_results: dict):
        """Record test execution results"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "results": test_results
        }
        self.history.append(entry)
        self.save_history()
    
    def save_history(self):
        """Save performance history"""
        with open(self.results_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def analyze_trends(self):
        """Analyze performance trends"""
        if len(self.history) < 2:
            return "Insufficient data for trend analysis"
        
        latest = self.history[-1]["results"]
        previous = self.history[-2]["results"]
        
        trends = {}
        for metric in latest:
            if metric in previous:
                change = latest[metric] - previous[metric]
                trends[metric] = {
                    "change": change,
                    "direction": "↑" if change > 0 else "↓" if change < 0 else "→"
                }
        
        return trends

# Usage in CI/CD
# python scripts/performance_tracker.py
```

## 🚀 Production Deployment Testing

### Pre-Deployment Checklist

```bash
#!/bin/bash
# scripts/pre_deployment_check.sh

echo "🚀 Pre-deployment Test Suite"
echo "============================"

# 1. Complete test suite
echo "1️⃣ Running complete test suite..."
pytest tests/ -v --cov=src --cov-min=80 || { echo "❌ Test suite failed"; exit 1; }

# 2. Performance validation
echo "2️⃣ Performance validation..."
pytest tests/e2e/test_performance.py -v || { echo "❌ Performance tests failed"; exit 1; }

# 3. Load testing
echo "3️⃣ Load testing..."
pytest tests/e2e/test_load_testing.py -v -m load || { echo "❌ Load tests failed"; exit 1; }

# 4. Security validation
echo "4️⃣ Security checks..."
python scripts/security_check.py || { echo "❌ Security validation failed"; exit 1; }

# 5. Acceptance criteria final check
echo "5️⃣ Acceptance criteria..."
pytest tests/ -m acceptance -v || { echo "❌ Acceptance criteria not met"; exit 1; }

echo "✅ All pre-deployment checks passed!"
echo "🚀 System ready for deployment"
```

### Post-Deployment Validation

```bash
#!/bin/bash
# scripts/post_deployment_validation.sh

echo "✅ Post-deployment Validation"
echo "============================="

# 1. Health check
echo "1️⃣ System health check..."
curl -f http://localhost:8080/health || { echo "❌ Health check failed"; exit 1; }

# 2. Live API testing
echo "2️⃣ Live API testing..."
ENV_MODE=production USE_REAL_DISCORD=true pytest tests/e2e/test_discord_integration.py::test_live_system_health -v

# 3. Performance monitoring
echo "3️⃣ Performance monitoring..."
python scripts/live_performance_monitor.py --duration=5

# 4. Error rate monitoring
echo "4️⃣ Error rate monitoring..."
python scripts/error_rate_monitor.py --duration=5

echo "✅ Post-deployment validation complete!"
```

## 🎬 Summary

This Test Execution Guide provides:

1. **Complete Setup Instructions**: Directory structure, dependencies, and configuration
2. **Step-by-Step TDD Workflow**: Red-Green-Refactor cycle with concrete examples
3. **Test Execution Commands**: Daily development and CI/CD commands
4. **Performance Monitoring**: Automated tracking and trend analysis
5. **Deployment Validation**: Pre and post-deployment test procedures

**Key Benefits**:
- **Immediate Action**: Every step is executable and practical
- **Quality Assurance**: Comprehensive validation at each phase
- **Performance Focus**: Continuous monitoring of key metrics
- **Production Ready**: Full deployment pipeline validation

**Next Steps**:
1. Execute the setup commands to create the test infrastructure
2. Begin with the first failing test for the Reception Client
3. Follow the TDD cycle: Red → Green → Refactor
4. Gradually build up the complete system following test guidance

This guide ensures that the Discord Multi-Agent System is built with quality, performance, and reliability from the ground up.