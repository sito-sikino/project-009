# Testing Checklist - Discord Multi-Agent System v0.2.0

## Pre-Test Setup

### Environment Verification
- [ ] All environment variables set in `.env`
- [ ] Redis server running and accessible
- [ ] PostgreSQL server running with pgvector extension
- [ ] Discord bot tokens valid and permissions configured
- [ ] Python virtual environment activated

### System Initialization
- [ ] `python main.py` starts without errors
- [ ] All 4 Discord clients connect successfully
- [ ] Memory system initialization completes
- [ ] Health monitoring server starts (port 8000)

## Core System Tests

### 1. Discord Connectivity
- [ ] **Reception Client**: Receives messages in all target channels
- [ ] **Spectra Bot**: Can send messages when selected
- [ ] **LynQ Bot**: Can send messages when selected  
- [ ] **Paz Bot**: Can send messages when selected
- [ ] **No duplicate messages** across bots

### 2. Agent Selection & Response
- [ ] **User messages trigger appropriate agent selection**
- [ ] **Response content is coherent and agent-specific**
- [ ] **No "システム調整中" fallback messages**
- [ ] **Response time < 3 seconds for normal messages**

### 3. Memory System Integration
- [ ] **Hot Memory**: Recent conversations stored in Redis
- [ ] **Memory retrieval** works for context generation
- [ ] **Health API** reports memory system status
- [ ] **Graceful degradation** when memory unavailable

## Autonomous Speech System Tests

### 4. Basic Autonomous Speech
- [ ] **10-second intervals** in test mode (or 5-minute in production)
- [ ] **Speech probability** respected (100% test, 33% production)
- [ ] **Messages generated** and queued successfully
- [ ] **No consecutive speech** from same agent

### 5. Agent Rotation Logic
- [ ] **Different agents** selected across multiple autonomous speeches
- [ ] **90% weight reduction** for last speaker working
- [ ] **Channel-appropriate** agent selection
- [ ] **Personality messages** match selected agent

### 6. Workflow Integration
- [ ] **STANDBY phase** (00:00-06:59): No autonomous speech
- [ ] **ACTIVE phase** (07:00-19:59): Speech in command_center or task channels
- [ ] **FREE phase** (20:00-23:59): Speech in lounge
- [ ] **Phase transitions** handled correctly

## Daily Workflow Tests

### 7. Task Command Processing
- [ ] **`/task commit development "test task"`**: Creates task successfully
- [ ] **Task confirmation message**: Shows in command_center
- [ ] **Channel switching**: Autonomous speech moves to task channel
- [ ] **`/task change development "modified task"`**: Updates task

### 8. Workflow Events
- [ ] **07:00 Morning Meeting**: Spectra announces in command_center
- [ ] **20:00 Work Conclusion**: Spectra announces in lounge  
- [ ] **00:00 System Rest**: Paz announces in lounge
- [ ] **Event timing accuracy**: ±30 seconds tolerance

### 9. Phase Management
- [ ] **Current phase** reported correctly via status endpoints
- [ ] **Phase-specific behavior** follows workflow rules
- [ ] **Task mode override** works during ACTIVE phase
- [ ] **Sequential operation**: Only one active channel at a time

## Error Handling & Recovery

### 10. Connection Recovery
- [ ] **Redis disconnection**: System continues with degraded memory
- [ ] **PostgreSQL disconnection**: Falls back to hot memory only
- [ ] **Discord API errors**: Retries and error reporting
- [ ] **Rate limit handling**: Respects API limits gracefully

### 11. Graceful Shutdown
- [ ] **Ctrl+C termination**: All subsystems stop cleanly
- [ ] **Discord clients disconnect**: No hanging connections
- [ ] **Memory cleanup**: Redis/PostgreSQL connections closed
- [ ] **No zombie processes** remain

## Performance & Monitoring

### 12. Health API Tests
- [ ] **GET /health**: Returns overall system status
- [ ] **GET /health/ready**: Reports readiness for traffic
- [ ] **GET /metrics**: Prometheus metrics available
- [ ] **GET /status**: Detailed component status

### 13. Performance Metrics
- [ ] **Message processing time**: Recorded and reasonable
- [ ] **Memory usage**: Stable under normal load
- [ ] **CPU usage**: Reasonable for system capabilities
- [ ] **API call metrics**: Rate limiting working

## User Interaction Tests

### 14. Command Processing
- [ ] **Valid task commands**: Processed correctly
- [ ] **Invalid syntax**: Clear error messages
- [ ] **Channel validation**: Only valid channels accepted
- [ ] **User permissions**: Commands work for authorized users

### 15. Conversation Flow
- [ ] **Natural conversation**: Agents respond appropriately
- [ ] **Context awareness**: Previous messages considered
- [ ] **Agent personality**: Responses match character traits
- [ ] **No conversation loops**: Agents don't trigger each other

## Stress Testing

### 16. High Load Scenarios
- [ ] **Multiple simultaneous users**: System handles concurrent messages
- [ ] **Rapid message sequences**: No message dropping
- [ ] **Long conversation history**: Memory management effective
- [ ] **Extended runtime**: System stable over hours

### 17. Edge Cases
- [ ] **Empty messages**: Handled gracefully
- [ ] **Very long messages**: Truncated appropriately
- [ ] **Special characters**: Unicode handling correct
- [ ] **Bot mentions**: Proper response logic

## Integration Testing

### 18. End-to-End Workflows
- [ ] **Complete daily cycle**: 24-hour operation test
- [ ] **Task creation to completion**: Full workflow
- [ ] **Agent handoffs**: Smooth transitions between agents
- [ ] **Memory persistence**: Conversations survive restarts

### 19. API Integration
- [ ] **Gemini API**: Consistent response generation
- [ ] **Discord API**: All endpoints working
- [ ] **Embedding API**: Rate limiting respected
- [ ] **External monitoring**: Health checks responding

## Deployment Validation

### 20. Production Readiness
- [ ] **Environment configuration**: All production settings verified
- [ ] **Security**: No tokens or secrets exposed in logs
- [ ] **Monitoring**: All metrics and alerts configured
- [ ] **Documentation**: Deployment guides current

## Test Execution Notes

### Quick Test Command
```bash
# Start system in test mode
ENVIRONMENT=test python main.py

# Monitor health
curl http://localhost:8000/health

# Check logs
tail -f discord_agent.log
```

### Manual Test Actions
1. **Send user message**: Test agent selection
2. **Wait 10 seconds**: Verify autonomous speech
3. **Use `/task commit`**: Test task workflow
4. **Check different times**: Verify phase behavior

### Success Criteria
- ✅ **All core tests pass** (sections 1-9)
- ✅ **No critical errors** in logs
- ✅ **Health API reports healthy**
- ✅ **Autonomous speech working** with proper rotation
- ✅ **Task commands functional**

### Known Issues to Monitor
- ⚠️ **Cold memory disabled**: Expected limitation
- ⚠️ **Embedding rate limits**: Monitor quota usage
- ⚠️ **PostgreSQL function missing**: Expected for now

---

**Last Updated**: 2025-06-21  
**Version**: v0.2.0  
**Test Environment**: Both test and production modes