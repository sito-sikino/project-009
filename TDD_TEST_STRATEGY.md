# Discord Multi-Agent System - TDD Test Strategy

## 📖 Overview

This document outlines a comprehensive Test-Driven Development (TDD) strategy for the Discord Multi-Agent System (project-009) based on the 統合受信・個別送信型アーキテクチャ.

**Architecture Under Test:**
- 1 Reception Bot + 3 Individual Sending Bots (Spectra/LynQ/Paz)
- LangGraph Supervisor Pattern with Gemini 2.0 Flash API
- Redis Hot Memory + PostgreSQL Cold Memory
- asyncio.gather() parallel client execution

## 🎯 Testing Philosophy

### TDD Workflow Alignment
This strategy follows the project's mandatory TDD workflow:
1. **Phase 1**: 調査とテスト設計 (EXPLORE & TEST DESIGN) 🕵️‍♂️🧪
2. **Phase 2**: Red Phase - テスト作成と失敗確認 (TEST FIRST) 🔴
3. **Phase 3**: Green Phase - 最小実装とリファクタリング (IMPLEMENT & REFACTOR) 🟢
4. **Phase 4**: 統合検証とドキュメント化 (INTEGRATE & DOCUMENT) ✅

### Core Testing Principles
- **Test First**: Never implement without failing tests
- **Component Isolation**: Each component testable in isolation
- **Real Dependencies**: Test against actual Discord/Gemini APIs when possible
- **Performance Validation**: 9-second response time requirement
- **Quality Metrics**: 95% agent selection accuracy target

## 📁 Test Structure & Organization

### Directory Structure
```
project-009/
├── tests/
│   ├── unit/                           # Isolated component tests
│   │   ├── test_discord_clients.py      # Reception/Output bot tests
│   │   ├── test_langgraph_supervisor.py # LangGraph workflow tests
│   │   ├── test_gemini_client.py        # Gemini API integration tests
│   │   ├── test_memory_system.py        # Redis/PostgreSQL tests
│   │   ├── test_message_processor.py    # Priority queue tests
│   │   ├── test_message_router.py       # Routing logic tests
│   │   └── test_autonomous_speech.py    # Autonomous behavior tests
│   │
│   ├── integration/                    # Component interaction tests
│   │   ├── test_message_flow.py         # Complete message pipeline
│   │   ├── test_memory_integration.py   # Hot→Cold memory transition
│   │   ├── test_orchestrator.py         # LangGraph supervisor integration
│   │   ├── test_parallel_clients.py     # Multi-client coordination
│   │   └── test_api_rate_limiting.py    # Rate limit handling
│   │
│   ├── e2e/                           # End-to-end system tests
│   │   ├── test_discord_integration.py  # Real Discord API tests
│   │   ├── test_full_workflow.py        # Complete user scenarios
│   │   ├── test_performance.py          # Performance benchmarks
│   │   └── test_load_testing.py         # System under load
│   │
│   ├── fixtures/                      # Test data and utilities
│   │   ├── __init__.py
│   │   ├── discord_fixtures.py         # Mock Discord objects
│   │   ├── gemini_fixtures.py          # Mock Gemini responses
│   │   ├── memory_fixtures.py          # Test data for memory systems
│   │   └── test_config.py              # Test environment configuration
│   │
│   └── conftest.py                    # Pytest configuration & shared fixtures
```

### Test Naming Conventions
```python
# Pattern: test_[component]_[action]_[condition]_[expected_result]

# Unit Tests
def test_reception_client_processes_message_when_mentioned_should_prioritize()
def test_langgraph_supervisor_selects_agent_when_context_provided_should_choose_spectra()
def test_gemini_client_handles_rate_limit_when_exceeded_should_exponential_backoff()

# Integration Tests  
def test_message_flow_processes_mention_when_user_mentions_spectra_should_complete_in_9_seconds()
def test_memory_integration_migrates_data_when_daily_cutoff_should_preserve_context()

# E2E Tests
def test_full_workflow_handles_user_interaction_when_real_discord_message_should_respond_correctly()
```

## 🧪 Component-Level Test Design

### 1. Discord Client Layer Tests

#### 1.1 Reception Client Tests (`tests/unit/test_discord_clients.py`)

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.discord_clients import ReceptionClient

class TestReceptionClient:
    """Tests for the unified message reception system"""
    
    @pytest.fixture
    async def reception_client(self):
        client = ReceptionClient()
        client.message_queue = asyncio.PriorityQueue()
        return client
    
    @pytest.mark.asyncio
    async def test_on_message_prioritizes_mentions_over_normal_messages(self, reception_client):
        """Mentions should get priority 1, normal messages priority 3"""
        # Arrange
        mention_message = MagicMock()
        mention_message.mentions = [MagicMock(id=12345)]  # Bot mentioned
        normal_message = MagicMock()
        normal_message.mentions = []
        
        # Act
        await reception_client.on_message(mention_message)
        await reception_client.on_message(normal_message)
        
        # Assert
        first_priority, first_msg = await reception_client.message_queue.get()
        second_priority, second_msg = await reception_client.message_queue.get()
        
        assert first_priority == 1  # Mention
        assert second_priority == 3  # Normal
        assert first_msg == mention_message
    
    @pytest.mark.asyncio
    async def test_duplicate_message_handling_prevents_processing_same_message_twice(self, reception_client):
        """Should track message IDs to prevent duplicate processing"""
        # Test implementation for duplicate message detection
        pass
    
    @pytest.mark.asyncio
    async def test_bot_message_filtering_ignores_own_messages(self, reception_client):
        """Should not process messages from the bot itself"""
        # Test implementation for bot message filtering
        pass
```

#### 1.2 Output Bot Tests

```python
class TestOutputBots:
    """Tests for individual agent sending bots"""
    
    @pytest.mark.asyncio 
    async def test_spectra_bot_sends_message_with_correct_identity(self):
        """Spectra bot should maintain its unique personality in messages"""
        pass
    
    @pytest.mark.asyncio
    async def test_output_queue_processing_handles_redis_queue_correctly(self):
        """Should process Redis output queues in correct order"""
        pass
    
    @pytest.mark.asyncio
    async def test_parallel_bot_execution_prevents_message_conflicts(self):
        """Multiple bots should not interfere with each other"""
        pass
```

### 2. LangGraph Supervisor Tests (`tests/unit/test_langgraph_supervisor.py`)

```python
class TestLangGraphSupervisor:
    """Tests for the LangGraph workflow orchestration"""
    
    @pytest.fixture
    def supervisor(self):
        from src.langgraph_supervisor import AgentSupervisor
        return AgentSupervisor()
    
    @pytest.mark.asyncio
    async def test_load_hot_memory_node_retrieves_recent_context(self, supervisor):
        """Should load last 20 messages from Redis"""
        # Arrange
        mock_state = {"messages": [], "channel_id": "test_channel"}
        
        # Act
        result = await supervisor.load_hot_memory_node(mock_state)
        
        # Assert
        assert "hot_memory" in result
        assert len(result["hot_memory"]) <= 20
    
    @pytest.mark.asyncio
    async def test_unified_select_generate_node_chooses_appropriate_agent(self, supervisor):
        """Should select correct agent based on context and generate response"""
        # Test scenarios:
        # - Technical discussion → LynQ
        # - Creative brainstorming → Paz  
        # - Meeting facilitation → Spectra
        pass
    
    @pytest.mark.asyncio
    async def test_workflow_state_management_preserves_context_between_nodes(self, supervisor):
        """State should be properly passed between workflow nodes"""
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling_recovers_from_node_failures(self, supervisor):
        """Should handle individual node failures gracefully"""
        pass
```

### 3. Gemini API Integration Tests (`tests/unit/test_gemini_client.py`)

```python
class TestGeminiClient:
    """Tests for Gemini 2.0 Flash API integration"""
    
    @pytest.mark.asyncio
    async def test_unified_agent_selection_returns_valid_agent_and_response(self):
        """Should return both agent selection and generated response"""
        # Test the 50% API reduction feature
        pass
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling_implements_exponential_backoff(self):
        """Should handle 15 RPM limit with exponential backoff"""
        pass
    
    @pytest.mark.asyncio
    async def test_api_error_recovery_retries_failed_requests(self):
        """Should retry failed API calls with appropriate delays"""
        pass
    
    @pytest.mark.asyncio
    async def test_response_parsing_extracts_agent_and_content_correctly(self):
        """Should parse Gemini response into structured format"""
        pass
```

### 4. Memory System Tests (`tests/unit/test_memory_system.py`)

```python
class TestMemorySystem:
    """Tests for Redis Hot Memory + PostgreSQL Cold Memory"""
    
    class TestHotMemory:
        """Redis-based current day memory tests"""
        
        @pytest.mark.asyncio
        async def test_store_conversation_limits_to_20_messages(self):
            """Should maintain rolling window of 20 messages per channel"""
            pass
        
        @pytest.mark.asyncio
        async def test_get_context_returns_chronological_order(self):
            """Messages should be returned in correct chronological order"""
            pass
        
        @pytest.mark.asyncio
        async def test_channel_isolation_keeps_contexts_separate(self):
            """Different channels should have isolated contexts"""
            pass
    
    class TestColdMemory:
        """PostgreSQL-based long-term memory tests"""
        
        @pytest.mark.asyncio
        async def test_semantic_search_finds_relevant_memories(self):
            """Vector search should return contextually relevant memories"""
            pass
        
        @pytest.mark.asyncio
        async def test_daily_migration_preserves_important_data(self):
            """Hot→Cold migration should preserve essential information"""
            pass
        
        @pytest.mark.asyncio
        async def test_embedding_generation_creates_valid_vectors(self):
            """Should generate proper embeddings for semantic search"""
            pass
```

### 5. Message Processing Tests (`tests/unit/test_message_processor.py`)

```python
class TestMessageProcessor:
    """Tests for priority queue and message routing"""
    
    @pytest.mark.asyncio
    async def test_priority_queue_orders_messages_correctly(self):
        """Priority: Mention (1) > Normal (3) > Autonomous (5)"""
        pass
    
    @pytest.mark.asyncio
    async def test_message_deduplication_prevents_duplicate_processing(self):
        """Should track and prevent duplicate message processing"""
        pass
    
    @pytest.mark.asyncio
    async def test_queue_overflow_handling_manages_high_volume(self):
        """Should handle queue overflow gracefully"""
        pass
```

## 🔗 Integration Test Scenarios

### 1. Complete Message Flow (`tests/integration/test_message_flow.py`)

```python
class TestCompleteMessageFlow:
    """End-to-end message processing pipeline tests"""
    
    @pytest.mark.asyncio
    async def test_mention_flow_completes_within_9_seconds(self):
        """Reception → LangGraph → Agent Selection → Response → Sending"""
        # Arrange
        start_time = time.time()
        mock_mention_message = create_mention_message("@Spectra what do you think?")
        
        # Act
        result = await process_complete_message_flow(mock_mention_message)
        
        # Assert
        elapsed_time = time.time() - start_time
        assert elapsed_time < 9.0
        assert result["selected_agent"] == "spectra"
        assert result["response_sent"] is True
    
    @pytest.mark.asyncio
    async def test_normal_message_flow_selects_appropriate_agent(self):
        """System should choose correct agent based on context"""
        test_cases = [
            ("Let's brainstorm new ideas", "paz"),
            ("We need to debug this logic", "lynq"), 
            ("How should we organize this meeting?", "spectra")
        ]
        
        for message_content, expected_agent in test_cases:
            result = await process_complete_message_flow(
                create_normal_message(message_content)
            )
            assert result["selected_agent"] == expected_agent
    
    @pytest.mark.asyncio
    async def test_error_propagation_handles_failures_gracefully(self):
        """Errors should be contained and not crash the system"""
        pass
```

### 2. Memory Integration Tests (`tests/integration/test_memory_integration.py`)

```python
class TestMemoryIntegration:
    """Tests for Hot→Cold memory coordination"""
    
    @pytest.mark.asyncio
    async def test_daily_migration_preserves_context_continuity(self):
        """Day boundary should not lose important context"""
        pass
    
    @pytest.mark.asyncio
    async def test_combined_memory_access_provides_complete_context(self):
        """Should access both hot and cold memory for complete picture"""
        pass
    
    @pytest.mark.asyncio
    async def test_memory_performance_meets_timing_requirements(self):
        """Memory access should not exceed performance budgets"""
        pass
```

### 3. Parallel Client Tests (`tests/integration/test_parallel_clients.py`)

```python
class TestParallelClients:
    """Tests for asyncio.gather() multi-client coordination"""
    
    @pytest.mark.asyncio
    async def test_simultaneous_client_startup_all_clients_connect(self):
        """All 4 Discord clients should start successfully"""
        pass
    
    @pytest.mark.asyncio
    async def test_message_coordination_prevents_response_conflicts(self):
        """Only selected agent should respond to messages"""
        pass
    
    @pytest.mark.asyncio
    async def test_client_failure_isolation_system_continues_operating(self):
        """Individual client failures shouldn't crash entire system"""
        pass
```

### 4. API Rate Limiting Tests (`tests/integration/test_api_rate_limiting.py`)

```python
class TestAPIRateLimiting:
    """Tests for Gemini API rate limit handling"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_compliance_stays_within_15_rpm(self):
        """Should never exceed 15 requests per minute"""
        pass
    
    @pytest.mark.asyncio
    async def test_priority_queue_respects_rate_limits(self):
        """High priority messages should get preference under rate limits"""
        pass
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_recovers_from_rate_limit_errors(self):
        """Should implement proper backoff strategy"""
        pass
```

## 🎭 End-to-End Test Plans

### 1. Real Discord Integration (`tests/e2e/test_discord_integration.py`)

```python
class TestDiscordIntegration:
    """Tests against real Discord API"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_real_mention_triggers_appropriate_response(self):
        """Test with actual Discord bot tokens and channels"""
        pass
    
    @pytest.mark.e2e 
    @pytest.mark.asyncio
    async def test_individual_bot_identities_maintain_unique_personas(self):
        """Each bot should display correctly in Discord"""
        pass
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_channel_specific_behavior_matches_specifications(self):
        """Different channels should trigger appropriate behaviors"""
        pass
```

### 2. Performance Benchmarks (`tests/e2e/test_performance.py`)

```python
class TestPerformance:
    """Performance and timing validation"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_consistently_under_9_seconds(self):
        """95% of responses should be under 9 seconds"""
        response_times = []
        for _ in range(100):
            start = time.time()
            await process_test_message()
            response_times.append(time.time() - start)
        
        percentile_95 = np.percentile(response_times, 95)
        assert percentile_95 < 9.0
    
    @pytest.mark.performance
    @pytest.mark.asyncio  
    async def test_agent_selection_accuracy_exceeds_95_percent(self):
        """Agent selection should be correct 95% of the time"""
        pass
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_access_performance_within_budget(self):
        """Memory operations should meet timing requirements"""
        pass
```

### 3. Load Testing (`tests/e2e/test_load_testing.py`)

```python
class TestLoadTesting:
    """System behavior under load"""
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_messages_system_handles_gracefully(self):
        """System should handle multiple simultaneous messages"""
        pass
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_memory_pressure_doesnt_degrade_performance(self):
        """System should maintain performance under memory pressure"""
        pass
```

## 🎪 Mock & Stub Strategy

### Discord API Mocking

```python
# tests/fixtures/discord_fixtures.py
import discord
from unittest.mock import MagicMock, AsyncMock

class MockDiscordMessage:
    """Mock Discord message for testing"""
    
    def __init__(self, content: str, author_id: int = 12345, mentions: list = None):
        self.id = 67890
        self.content = content
        self.author = MagicMock()
        self.author.id = author_id
        self.author.display_name = "TestUser"
        self.mentions = mentions or []
        self.channel = MagicMock()
        self.channel.id = 98765
        self.guild = MagicMock()
        self.guild.id = 11111

def create_mention_message(content: str) -> MockDiscordMessage:
    """Create a mock message that mentions a bot"""
    mock_bot = MagicMock()
    mock_bot.id = 12345  # Bot's user ID
    return MockDiscordMessage(content, mentions=[mock_bot])

def create_normal_message(content: str) -> MockDiscordMessage:
    """Create a mock normal message"""
    return MockDiscordMessage(content)

class MockDiscordClient:
    """Mock Discord client for testing"""
    
    def __init__(self):
        self.user = MagicMock()
        self.user.id = 12345
        self.is_ready = AsyncMock(return_value=True)
        self.send_message = AsyncMock()
```

### Gemini API Response Simulation

```python
# tests/fixtures/gemini_fixtures.py
import json
from typing import Dict, Any

class MockGeminiResponse:
    """Mock Gemini API responses for testing"""
    
    @staticmethod
    def unified_agent_selection_response(agent: str, content: str) -> Dict[str, Any]:
        """Mock response for unified agent selection + generation"""
        return {
            "selected_agent": agent,
            "response_content": content,
            "confidence": 0.95,
            "reasoning": f"Selected {agent} because of context analysis"
        }
    
    @staticmethod
    def error_response(error_type: str = "rate_limit") -> Dict[str, Any]:
        """Mock error responses from Gemini"""
        error_responses = {
            "rate_limit": {"error": "Rate limit exceeded", "retry_after": 60},
            "api_error": {"error": "Internal API error", "code": 500},
            "invalid_request": {"error": "Invalid request format", "code": 400}
        }
        return error_responses.get(error_type, error_responses["api_error"])

# Mock conversation contexts
MOCK_CONTEXTS = {
    "technical_discussion": [
        {"role": "user", "content": "How should we implement the database schema?"},
        {"role": "assistant", "content": "Let's analyze the requirements first..."}
    ],
    "creative_brainstorm": [
        {"role": "user", "content": "I need ideas for the user interface design"},
        {"role": "assistant", "content": "What if we tried a completely different approach..."}
    ],
    "meeting_facilitation": [
        {"role": "user", "content": "Can we organize today's priorities?"},
        {"role": "assistant", "content": "Let me help structure our discussion..."}
    ]
}
```

### Database Operation Stubs

```python
# tests/fixtures/memory_fixtures.py
import pytest
import asyncio
from unittest.mock import AsyncMock

class MockRedisClient:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {}
        self.get = AsyncMock(side_effect=self._get)
        self.set = AsyncMock(side_effect=self._set)
        self.lpush = AsyncMock(side_effect=self._lpush)
        self.lrange = AsyncMock(side_effect=self._lrange)
    
    async def _get(self, key: str):
        return self.data.get(key)
    
    async def _set(self, key: str, value: str):
        self.data[key] = value
    
    async def _lpush(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)
    
    async def _lrange(self, key: str, start: int, end: int):
        return self.data.get(key, [])[start:end+1]

class MockPostgreSQLClient:
    """Mock PostgreSQL client for testing"""
    
    def __init__(self):
        self.memories = []
        self.execute = AsyncMock(side_effect=self._execute)
        self.fetch = AsyncMock(side_effect=self._fetch)
    
    async def _execute(self, query: str, params: list = None):
        # Simulate database operations
        if query.startswith("INSERT"):
            self.memories.append({"id": len(self.memories), "data": params})
        return True
    
    async def _fetch(self, query: str, params: list = None):
        # Simulate search results
        return self.memories[:5]  # Return top 5 results
```

### Async Operation Mocking

```python
# tests/fixtures/async_fixtures.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_async_queue():
    """Mock asyncio.PriorityQueue for testing"""
    queue = MagicMock()
    queue.put = AsyncMock()
    queue.get = AsyncMock()
    queue.empty = MagicMock(return_value=False)
    return queue

@pytest.fixture
def mock_event_loop():
    """Mock event loop for testing"""
    loop = MagicMock()
    loop.run_until_complete = MagicMock()
    loop.create_task = MagicMock()
    return loop

class MockAsyncContext:
    """Mock async context manager"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
```

## ✅ Acceptance Criteria Definition

### Functional Requirements Validation

```python
# Acceptance criteria as test cases
class TestAcceptanceCriteria:
    """Validation of all functional requirements"""
    
    @pytest.mark.acceptance
    async def test_unified_reception_single_bot_receives_all_messages(self):
        """AC-001: Only reception bot should receive Discord messages"""
        pass
    
    @pytest.mark.acceptance  
    async def test_individual_sending_three_bots_send_independently(self):
        """AC-002: Three separate bots send messages with unique identities"""
        pass
    
    @pytest.mark.acceptance
    async def test_langgraph_integration_supervisor_pattern_orchestrates(self):
        """AC-003: LangGraph supervisor coordinates all agent decisions"""
        pass
    
    @pytest.mark.acceptance
    async def test_api_efficiency_50_percent_reduction_achieved(self):
        """AC-004: Unified processing reduces API calls by 50%"""
        pass
    
    @pytest.mark.acceptance
    async def test_memory_system_hot_cold_integration_works(self):
        """AC-005: Two-tier memory system functions correctly"""
        pass
    
    @pytest.mark.acceptance
    async def test_response_time_95_percent_under_9_seconds(self):
        """AC-006: 95% of responses complete within 9 seconds"""
        pass
    
    @pytest.mark.acceptance
    async def test_agent_selection_95_percent_accuracy(self):
        """AC-007: Agent selection accuracy exceeds 95%"""
        pass
    
    @pytest.mark.acceptance
    async def test_parallel_execution_asyncio_gather_coordination(self):
        """AC-008: All clients run in parallel without conflicts"""
        pass
```

### Performance Thresholds

```python
# Performance acceptance criteria
PERFORMANCE_REQUIREMENTS = {
    "response_time": {
        "target": 9.0,  # seconds
        "percentile": 95,
        "measurement": "end_to_end_response_time"
    },
    "agent_selection_accuracy": {
        "target": 0.95,  # 95%
        "measurement": "correct_selections / total_selections"
    },
    "api_efficiency": {
        "target": 0.50,  # 50% reduction
        "baseline": "traditional_multi_call_approach",
        "measurement": "api_calls_per_response"
    },
    "memory_access": {
        "hot_memory": 0.1,  # seconds
        "cold_memory": 3.0,  # seconds
        "measurement": "memory_operation_duration"
    },
    "rate_limit_compliance": {
        "target": 15,  # requests per minute
        "measurement": "gemini_api_calls_per_minute"
    }
}
```

### Quality Metrics

```python
# Quality acceptance criteria
QUALITY_REQUIREMENTS = {
    "code_coverage": {
        "unit_tests": 0.90,      # 90% minimum
        "integration_tests": 0.80, # 80% minimum
        "critical_path": 1.00     # 100% for critical paths
    },
    "test_performance": {
        "unit_test_speed": 0.1,   # seconds per test
        "integration_test_speed": 1.0,  # seconds per test
        "e2e_test_speed": 10.0    # seconds per test
    },
    "reliability": {
        "uptime": 0.999,          # 99.9% uptime target
        "error_rate": 0.001,      # 0.1% error rate maximum
        "recovery_time": 30.0     # seconds to recover from errors
    }
}
```

## 🏃‍♂️ Test Execution Workflow

### Development Workflow Integration

```bash
# Pre-commit test workflow
#!/bin/bash
# scripts/pre_commit_tests.sh

echo "🧪 Running pre-commit test suite..."

# 1. Unit tests (fast feedback)
echo "1️⃣ Unit tests..."
python -m pytest tests/unit/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

# 2. Integration tests (component interaction)
echo "2️⃣ Integration tests..."
python -m pytest tests/integration/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed"
    exit 1
fi

# 3. Code quality checks
echo "3️⃣ Code quality..."
black --check src/ tests/
isort --check-only src/ tests/
mypy src/

# 4. Coverage check
echo "4️⃣ Coverage check..."
python -m pytest tests/ --cov=src --cov-min=80

echo "✅ All pre-commit tests passed!"
```

### Continuous Integration Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_discord_agent
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: python -m pytest tests/unit/ -v
    
    - name: Run integration tests
      run: python -m pytest tests/integration/ -v
      env:
        REDIS_HOST: localhost
        POSTGRES_HOST: localhost
        POSTGRES_PASSWORD: test_password
    
    - name: Run E2E tests (limited)
      run: python -m pytest tests/e2e/ -m "not discord_api" -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Test Environment Management

```python
# tests/fixtures/test_config.py
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class TestConfig:
    """Test environment configuration"""
    
    # Environment settings
    env_mode: str = "test"
    debug_mode: bool = True
    
    # Mock settings
    use_real_discord: bool = False
    use_real_gemini: bool = False
    use_real_databases: bool = False
    
    # Performance test settings
    response_time_limit: float = 9.0
    load_test_duration: int = 60  # seconds
    concurrent_users: int = 10
    
    # Database test settings
    test_redis_host: str = "localhost"
    test_redis_port: int = 6379
    test_postgres_host: str = "localhost"
    test_postgres_port: int = 5432
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """Load test configuration from environment variables"""
        return cls(
            env_mode=os.getenv("TEST_ENV_MODE", "test"),
            use_real_discord=os.getenv("USE_REAL_DISCORD", "false").lower() == "true",
            use_real_gemini=os.getenv("USE_REAL_GEMINI", "false").lower() == "true",
            use_real_databases=os.getenv("USE_REAL_DATABASES", "false").lower() == "true",
        )

# Global test configuration
TEST_CONFIG = TestConfig.from_env()
```

## 🎯 Implementation Roadmap

### Phase 1: Test Infrastructure Setup
1. **Test Structure Creation** (1-2 days)
   - Create directory structure
   - Set up pytest configuration
   - Implement basic fixtures

2. **Mock Framework Implementation** (2-3 days)
   - Discord API mocks
   - Gemini API response simulation
   - Database operation stubs

3. **Test Utilities Development** (1-2 days)
   - Helper functions
   - Test data generators
   - Performance measurement tools

### Phase 2: Unit Test Implementation ✅ COMPLETED
1. **Core Component Tests** ✅ COMPLETED
   - ✅ Discord clients (Reception Client + Priority Queue)
   - ✅ LangGraph supervisor (StateGraph + Gemini Integration)
   - ✅ Output Bots (Spectra/LynQ/Paz + MessageRouter)
   - ✅ Message processing (Priority Queue + Routing)

2. **API Integration Tests** ✅ COMPLETED
   - ✅ Gemini client tests (Unified agent selection)
   - ✅ Rate limiting tests (15RPM compliance)
   - ✅ Error handling tests (Fallback mechanisms)

### Phase 3: Integration Test Development
1. **Message Flow Tests** (5-7 days)
   - Complete pipeline testing
   - Error propagation
   - Performance validation

2. **System Integration Tests** (3-5 days)
   - Memory integration
   - Parallel client coordination
   - API rate limiting

### Phase 4: E2E Test Implementation
1. **Discord Integration Tests** (3-4 days)
   - Real API testing
   - Bot identity validation
   - Channel behavior testing

2. **Performance & Load Tests** (2-3 days)
   - Response time validation
   - Load testing
   - Stress testing

### Phase 5: Test Automation & CI/CD
1. **CI/CD Pipeline Setup** (2-3 days)
   - GitHub Actions workflow
   - Test environment provisioning
   - Coverage reporting

2. **Monitoring & Reporting** (1-2 days)
   - Test result tracking
   - Performance trend analysis
   - Quality metrics dashboard

## 📊 Success Metrics

### Test Coverage Targets
- **Unit Tests**: 90% code coverage minimum
- **Integration Tests**: 80% critical path coverage
- **E2E Tests**: 100% user scenario coverage

### Performance Benchmarks
- **Response Time**: 95% under 9 seconds
- **Agent Selection**: 95% accuracy
- **API Efficiency**: 50% reduction in calls
- **Memory Performance**: Hot < 0.1s, Cold < 3s

### Quality Gates
- All tests must pass before merge
- Code coverage must meet targets
- Performance benchmarks must be satisfied
- No critical security vulnerabilities

## 🔧 Tools & Technologies

### Testing Framework
- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance testing

### Mocking & Fixtures
- **unittest.mock**: Standard mocking library
- **pytest-mock**: Enhanced pytest mocking
- **factory_boy**: Test data generation
- **freezegun**: Time manipulation for tests

### Performance Testing
- **pytest-benchmark**: Performance measurement
- **locust**: Load testing (if needed)
- **memory_profiler**: Memory usage analysis

### CI/CD Integration
- **GitHub Actions**: Continuous integration
- **codecov**: Coverage reporting
- **pre-commit**: Git hooks for quality

---

## 🎬 Conclusion

This comprehensive TDD test strategy provides:

1. **Complete Test Coverage**: Unit, integration, and E2E tests for all components
2. **Performance Validation**: Ensures 9-second response time and 95% accuracy requirements
3. **Quality Assurance**: Maintains high code quality and reliability standards
4. **Automation Support**: Full CI/CD integration with automated quality gates
5. **Scalable Architecture**: Test structure that grows with the system

The strategy is designed to be **immediately actionable** and supports the project's TDD workflow requirements. Each test case is concrete and specific to the Discord Multi-Agent System architecture.

**Next Steps**: Begin Phase 1 implementation by creating the test directory structure and implementing basic fixtures according to this strategy.