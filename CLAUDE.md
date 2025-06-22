# CLAUDE.md - Project-009 Discord Multi-Agent System

## 🚨 **Documentation Management Policy - MINIMAL ARCHITECTURE**

**CRITICAL**: This project uses **MINIMAL DOCUMENTATION ARCHITECTURE** to prevent context waste and information scatter.

### 📁 **Core Documents (6 files only)**

#### **Project Root Files**
1. **`CLAUDE.md`** - This file, project overview + documentation policy (Claude Code requirement)
2. **`README.md`** - Project overview for GitHub and general users

#### **Documentation Directory (`docs/`)**
3. **`docs/current-status.md`** - Current version, implementation status, quick health check
4. **`docs/deployment-guide.md`** - Operations manual, setup, troubleshooting
5. **`docs/testing-guide.md`** - Test procedures, validation, quality assurance
6. **`docs/acceptance-criteria.md`** - Requirements reference (simplified version)
7. **`docs/roadmap.md`** - Future implementation plans (v0.3.0+)

### 🚨 **NEVER READ THESE** (Removed in v0.2.2)
- `archive/` - **DELETED** - Old implementation files (95% context pollution source)
- `venv/` - **Git ignored** - Virtual environment files
- `logs/*.log` - **Git ignored** - Runtime log files
- Any files with version numbers in names

### 🎯 **Claude Code Workflow**
1. **Always start with**: `docs/current-status.md` (current version & status)
2. **For operations**: `docs/deployment-guide.md` 
3. **For testing**: `docs/testing-guide.md`
4. **For requirements**: `docs/acceptance-criteria.md` (reference only)
5. **For future work**: `docs/roadmap.md`

**Context Efficiency**: With this structure, you only need to read 1-2 files for any task instead of 10-20 scattered documents.

## 🚀 Project Overview - Discord Multi-Agent System

### **Current Version**: v0.2.2 (Clean Architecture Refactoring)
- **Status**: Clean Architecture implementation in progress
- **Architecture**: 統合受信・個別送信型 (Unified Reception, Individual Transmission)
- **Last Update**: 2025-06-22 JST

### **Core System**
- **4 Discord Bots**: Reception + Spectra/LynQ/Paz (output)
- **LangGraph Supervisor**: Agent selection and coordination  
- **Memory System**: Redis (hot) + PostgreSQL foundation (cold)
- **Autonomous Speech**: 10s test / 5min production intervals
- **Daily Workflow**: STANDBY/ACTIVE/FREE phase management
- **Performance**: <2s response time, 50+ concurrent users

### **Key Features**
- Multi-agent conversation with personality-specific responses
- Cross-channel task management (`/task commit`, `/task change`)
- Agent rotation system (prevents consecutive speech)
- Real-time health monitoring (port 8000)
- Production-ready error handling and recovery

## 📁 **File Structure & Navigation**

### **Clean Architecture Project Structure (v0.2.2)**
```
project-009/
├── CLAUDE.md                    # Claude Code guidance (root requirement)
├── README.md                    # GitHub project overview  
├── main.py                      # System entry point (simplified)
├── src/                         # Clean Architecture components
│   ├── container/               # 🔧 Dependency Injection Layer
│   │   └── system_container.py # DI Container for component management
│   ├── application/             # 🎯 Application Service Layer
│   │   └── discord_app_service.py # High-level business orchestration
│   ├── core/                    # 🏛️ Business Logic Layer
│   │   ├── message_processor.py # Message processing queue
│   │   └── daily_workflow.py    # Workflow management
│   ├── agents/                  # 🤖 Agent Logic Layer
│   │   ├── supervisor.py        # LangGraph agent selection
│   │   └── autonomous_speech.py # 10s/5min autonomous messaging
│   ├── bots/                    # 💬 Discord Interface Layer
│   │   ├── reception.py         # Reception bot (unified receiver)
│   │   └── output_bots.py       # 3 individual sender bots
│   ├── infrastructure/          # 🔌 External Services Layer
│   │   ├── memory_system.py     # Redis + PostgreSQL integration
│   │   ├── gemini_client.py     # Gemini API client
│   │   ├── embedding_client.py  # Text embedding API client
│   │   ├── message_router.py    # Message routing logic
│   │   └── system_lifecycle.py  # System lifecycle management
│   ├── config/                  # ⚙️ Configuration Layer
│   │   └── settings.py          # Environment configuration
│   └── utils/                   # 🛠️ Utility Layer
│       ├── logger.py            # Logging configuration
│       ├── health.py            # Health monitoring
│       └── monitoring.py        # Performance monitoring
├── tests/                       # Test Suite (Clean Architecture)
│   ├── unit/                    # Unit tests for each layer
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── docs/                        # Documentation (MINIMAL)
│   ├── current-status.md        # Current system status
│   ├── deployment-guide.md      # Operations manual
│   ├── testing-guide.md         # Test procedures
│   ├── acceptance-criteria.md   # Requirements reference
│   └── roadmap.md              # Implementation roadmap
├── logs/                        # Unified logging (Git ignored)
│   └── discord_agent.log        # Single log file
├── database/                    # Database initialization
│   └── init/                    # SQL initialization scripts
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Container orchestration
└── .gitignore                   # Git exclusions
```

### **Operations Commands**
```bash
# Start system
python main.py

# Check health
curl localhost:8000/health

# View logs
tail -f logs/discord_agent.log

# Stop system
Ctrl+C  # graceful shutdown
```

## 🤖 **Agent Roles & Behavior**

### **Discord Bots**
- **Reception Client**: Unified message reception (single listener)
- **Spectra Bot**: Meeting facilitation, project management (🔵)
- **LynQ Bot**: Technical discussions, development tasks (🔴)
- **Paz Bot**: Creative work, brainstorming (🟡)

### **Channel Specialization**
- **command-center**: All agents (Spectra 40%, LynQ 30%, Paz 30%)
- **development**: LynQ priority (50%, others 25%)
- **creation**: Paz priority (50%, others 25%)
- **lounge**: Equal distribution (33% each)

### **Daily Workflow Phases**
- **STANDBY** (00:00-06:59): No autonomous speech, user responses only
- **ACTIVE** (07:00-19:59): Meeting/work mode, task-based operation
- **FREE** (20:00-23:59): Social mode in lounge channel

## 🎯 **Task Management**

### **Task Commands**
```bash
# Start new task
/task commit development "認証システム実装"

# Change task within same channel
/task change development "API設計"

# Move task to different channel
/task change creation "アイデアブレスト"
```

### **Command Behavior**
- Tasks are sequential (one active channel at a time)
- Cross-channel migration supported (development → creation)
- Autonomous speech follows active task channel
- Task data stored in Redis with full history

## ⚙️ **Technical Specifications**

### **System Requirements**
- Python 3.9+
- Redis 7.0+ (hot memory)
- PostgreSQL 14+ with pgvector (cold memory foundation)
- 2GB+ RAM, 2+ CPU cores

### **Environment Variables**
```bash
# Discord Integration
DISCORD_RECEPTION_TOKEN=<reception_bot_token>
DISCORD_SPECTRA_TOKEN=<spectra_bot_token>
DISCORD_LYNQ_TOKEN=<lynq_bot_token>
DISCORD_PAZ_TOKEN=<paz_bot_token>

# AI Integration
GEMINI_API_KEY=<google_gemini_api_key>

# Database
REDIS_URL=redis://localhost:6379
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/db

# System Configuration
ENVIRONMENT=production  # or test
LOG_LEVEL=INFO
HEALTH_CHECK_PORT=8000
```

### **Performance Metrics**
- **Response Time**: <2s average (production validated)
- **Autonomous Speech**: 10s test / 5min production
- **Agent Rotation**: 90% weight reduction prevents consecutive speech
- **Memory Usage**: ~1.5GB normal operation
- **Concurrent Users**: 50+ simultaneous users supported

## 🚨 **Critical Implementation Principles**

### **TDD Workflow (Mandatory)**
1. **Explore Phase**: Understand requirements and existing code
2. **Red Phase**: Write failing tests first
3. **Green Phase**: Implement minimal code to pass tests
4. **Refactor Phase**: Improve code quality while maintaining tests

### **Development Rules**
- **Test-First**: Never implement without tests
- **Minimal Changes**: Only implement what's explicitly requested
- **No Hardcoding**: Use environment variables for all configuration
- **Error Handling**: Comprehensive error recovery mechanisms

### **Documentation Updates**
- Always update `CURRENT_STATUS.md` after major changes
- Keep documentation minimal and focused
- Archive old documents instead of deleting
- Use this file structure as the single source of truth

## 📋 **Quality Assurance**

### **Testing Strategy**
- Unit tests for individual components
- Integration tests for system interactions
- Production validation with Discord integration
- Performance testing under load

### **Success Criteria**
- Zero critical bugs in production
- <2s response time for normal messages  
- >90% agent selection accuracy
- Perfect autonomous speech rotation
- Graceful error handling and recovery

## 🔄 **Current Status: v0.2.0 Production Ready**

### **Validated Features**
- ✅ 4-bot Discord integration working
- ✅ LangGraph supervisor agent selection
- ✅ Redis memory system operational
- ✅ Autonomous speech with rotation logic
- ✅ Task commands with channel migration
- ✅ Health monitoring and metrics
- ✅ Production testing completed (15-message test)

### **Known Limitations**
- PostgreSQL search function temporarily disabled (foundation ready)
- Embedding API quota limited to 15 RPM (production compliant)
- 00:00 system rest period not yet implemented

### **Next Version (v0.3.0)**
- Complete PostgreSQL cold memory system
- Advanced LLM integration for agent selection
- Enhanced workflow automation
- Performance optimization for 100+ users

---

**For current system status and health, see [`docs/current-status.md`](docs/current-status.md)**  
**For operations and deployment, see [`docs/deployment-guide.md`](docs/deployment-guide.md)**  
**For testing procedures, see [`docs/testing-guide.md`](docs/testing-guide.md)**  
**For requirements reference, see [`docs/acceptance-criteria.md`](docs/acceptance-criteria.md)**  
**For future development, see [`docs/roadmap.md`](docs/roadmap.md)**