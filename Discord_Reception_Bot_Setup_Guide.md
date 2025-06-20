# Discord Reception Bot Setup Guide
## Complete Guide for Multi-Agent System (Bot 4/4 - Reception Bot)

This guide provides step-by-step instructions for setting up a Discord bot specifically designed for message reception in a multi-agent system architecture (1 reception bot + 3 sending bots).

## Table of Contents
1. [Discord Developer Portal Setup](#discord-developer-portal-setup)
2. [Required Permissions and Intents](#required-permissions-and-intents)
3. [Bot Configuration Best Practices](#bot-configuration-best-practices)
4. [Security Considerations](#security-considerations)
5. [Reception Bot Specific Requirements](#reception-bot-specific-requirements)
6. [Code Examples](#code-examples)
7. [Troubleshooting](#troubleshooting)

## Discord Developer Portal Setup

### Step 1: Create Bot Application
1. Navigate to [Discord Developer Portal](https://discord.com/developers/applications)
2. Log in with your Discord account
3. Click **"New Application"** button
4. Enter application name (e.g., "MultiAgent-Reception-Bot")
5. Click **"Create"** and confirm

### Step 2: Configure Bot Settings
1. In the left sidebar, click **"Bot"**
2. Click **"Add Bot"** if not already created
3. Configure bot settings:
   - **Username**: Choose a descriptive name (e.g., "ReceptionBot", "MessageListener", "AgentReceiver")
   - **Avatar**: Upload a suitable icon (optional)
   - **Public Bot**: Set to OFF (recommended for multi-agent systems)
   - **Require OAuth2 Code Grant**: Set to OFF

### Step 3: Generate Bot Token
1. In the Bot section, click **"Reset Token"**
2. Confirm the action
3. Copy the token immediately (you won't see it again)
4. Store securely in environment variables

### Step 4: Enable Privileged Gateway Intents
**Critical for Message Reception:**
1. Scroll down to **"Privileged Gateway Intents"**
2. Enable the following intents:
   - ✅ **Message Content Intent** (Required for reading message content)
   - ✅ **Server Members Intent** (Recommended for user management)
   - ✅ **Presence Intent** (Optional, for user status)

**Important**: For bots in 100+ servers, these intents require approval from Discord.

## Required Permissions and Intents

### Gateway Intents (Code Level)
Your reception bot requires these intents in code:

```python
import discord
from discord.ext import commands

# Required intents for message reception
intents = discord.Intents.default()
intents.message_content = True      # Read message content
intents.guilds = True              # Access guild information
intents.guild_messages = True      # Receive message events
intents.guild_members = True       # Access member information (optional)
intents.mentions = True            # Detect mentions

bot = commands.Bot(command_prefix='!', intents=intents)
```

### Bot Permissions (Discord Level)
Required permissions for the reception bot:

#### Essential Permissions:
- ✅ **View Channels** - See channels where messages are sent
- ✅ **Read Message History** - Access previous messages
- ✅ **Read Messages** - Receive new messages

#### Optional but Recommended:
- ✅ **Send Messages** - For acknowledgments or error messages
- ✅ **Use External Emojis** - For reaction-based acknowledgments
- ✅ **Add Reactions** - For message processing indicators

#### NOT Required (Reception Bot Only):
- ❌ **Manage Messages** - Not needed for reception-only
- ❌ **Manage Channels** - Not needed for reception-only
- ❌ **Administrator** - Avoid for security

### Permission Calculator
Use Discord's permission calculator: `https://discordapi.com/permissions.html`

**Recommended Permission Integer**: `68608` (Read Messages + View Channels + Read Message History)

## Bot Configuration Best Practices

### Naming Conventions
For a 4-bot multi-agent system:

1. **Reception Bot**: 
   - `"AgentReception"`, `"MessageListener"`, `"CentralReceiver"`
   - Clear indication of reception role

2. **Sending Bots**:
   - `"Agent-Alpha"`, `"Agent-Beta"`, `"Agent-Gamma"`
   - or `"Lynq-Bot"`, `"Paz-Bot"`, `"Spectra-Bot"`

### Configuration Structure
```
Multi-Agent System:
├── Reception Bot (Bot 1)
│   ├── Receives ALL messages
│   ├── Detects @mentions
│   ├── Manages priority queue
│   └── Routes to appropriate sender
├── Sending Bot A (Bot 2)
├── Sending Bot B (Bot 3)
└── Sending Bot C (Bot 4)
```

### Environment Variables
Create a `.env` file for each bot:

```env
# Reception Bot Configuration
DISCORD_RECEPTION_BOT_TOKEN=your_reception_bot_token_here
TARGET_GUILD_ID=your_server_id_here
RECEPTION_CHANNEL_IDS=channel1,channel2,channel3

# Multi-Agent System Configuration
AGENT_ALPHA_WEBHOOK_URL=webhook_url_for_agent_alpha
AGENT_BETA_WEBHOOK_URL=webhook_url_for_agent_beta
AGENT_GAMMA_WEBHOOK_URL=webhook_url_for_agent_gamma

# Priority Queue Configuration
PRIORITY_QUEUE_CHANNEL=priority_channel_id
HIGH_PRIORITY_ROLES=role1,role2,role3
```

## Security Considerations

### Bot Token Security
1. **Never share tokens publicly**
2. **Use environment variables** (.env files with .gitignore)
3. **Regenerate tokens if compromised**
4. **Enable 2FA** on your Discord account
5. **Use separate tokens** for each bot in the system

### Access Control
```python
# Example secure token handling
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_RECEPTION_BOT_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("Discord token not found in environment variables")
```

### Permission Principle
- **Least Privilege**: Only grant necessary permissions
- **Role-Based Access**: Use Discord roles for permission management
- **Regular Audits**: Review bot permissions periodically

### Multi-Bot Security
1. **Separate Tokens**: Each bot should have its own token
2. **Isolated Permissions**: Reception bot shouldn't have sending permissions
3. **Secure Communication**: Use encrypted channels between bots
4. **Rate Limiting**: Implement rate limiting to prevent abuse

## Reception Bot Specific Requirements

### Core Functionality Requirements

#### 1. Message Reception
```python
@bot.event
async def on_message(message):
    # Ignore messages from bots (including self)
    if message.author.bot:
        return
    
    # Process all messages in monitored channels
    if message.channel.id in MONITORED_CHANNELS:
        await process_message(message)
```

#### 2. @Mention Detection
```python
@bot.event
async def on_message(message):
    # Check for mentions of any bot in the system
    bot_mentions = []
    
    # Check for direct bot mentions
    for mention in message.mentions:
        if mention.id in SYSTEM_BOT_IDS:
            bot_mentions.append(mention.id)
    
    # Check for role mentions
    for role in message.role_mentions:
        if role.id in PRIORITY_ROLES:
            await add_to_priority_queue(message)
    
    # Route based on mentions
    if bot_mentions:
        await route_to_appropriate_bot(message, bot_mentions)
```

#### 3. Priority Queue Implementation
```python
import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QueuedMessage:
    message: discord.Message
    priority: int
    timestamp: datetime
    target_bot: str

class PriorityQueue:
    def __init__(self):
        self.high_priority = deque()
        self.normal_priority = deque()
        self.low_priority = deque()
    
    async def add_message(self, message, priority=1):
        queued_msg = QueuedMessage(
            message=message,
            priority=priority,
            timestamp=datetime.utcnow(),
            target_bot=await determine_target_bot(message)
        )
        
        if priority >= 3:
            self.high_priority.append(queued_msg)
        elif priority >= 2:
            self.normal_priority.append(queued_msg)
        else:
            self.low_priority.append(queued_msg)
    
    async def get_next_message(self):
        if self.high_priority:
            return self.high_priority.popleft()
        elif self.normal_priority:
            return self.normal_priority.popleft()
        elif self.low_priority:
            return self.low_priority.popleft()
        return None
```

#### 4. Bot Routing Logic
```python
async def determine_target_bot(message):
    """Determine which sending bot should handle the message"""
    
    # Check for explicit bot mentions
    for mention in message.mentions:
        if mention.id == LYNQ_BOT_ID:
            return "lynq"
        elif mention.id == PAZ_BOT_ID:
            return "paz"
        elif mention.id == SPECTRA_BOT_ID:
            return "spectra"
    
    # Content-based routing
    content_lower = message.content.lower()
    
    if any(keyword in content_lower for keyword in ['help', 'support', 'question']):
        return "lynq"  # Helper bot
    elif any(keyword in content_lower for keyword in ['moderate', 'report', 'issue']):
        return "paz"   # Moderation bot
    elif any(keyword in content_lower for keyword in ['analyze', 'data', 'insight']):
        return "spectra"  # Analysis bot
    
    # Default routing (round-robin or load balancing)
    return await get_least_busy_bot()
```

### OAuth2 URL Generation
1. Go to **OAuth2 > URL Generator**
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select permissions (use minimal required permissions)
4. Copy the generated URL
5. Visit URL to add bot to server

**Example URL Structure:**
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=68608&scope=bot%20applications.commands
```

## Code Examples

### Complete Reception Bot Template
```python
import discord
from discord.ext import commands, tasks
import os
import asyncio
import logging
from datetime import datetime
from collections import deque
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.mentions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Priority queue for message processing
message_queue = deque()

# Configuration
MONITORED_CHANNELS = [int(x) for x in os.getenv('MONITORED_CHANNELS', '').split(',') if x]
PRIORITY_ROLES = [int(x) for x in os.getenv('PRIORITY_ROLES', '').split(',') if x]
SYSTEM_BOT_IDS = [int(x) for x in os.getenv('SYSTEM_BOT_IDS', '').split(',') if x]

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Monitoring {len(MONITORED_CHANNELS)} channels')
    
    # Start message processing loop
    process_queue.start()

@bot.event
async def on_message(message):
    """Main message reception handler"""
    
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Only process messages from monitored channels
    if message.channel.id not in MONITORED_CHANNELS:
        return
    
    # Determine priority
    priority = await calculate_priority(message)
    
    # Add to processing queue
    await add_to_queue(message, priority)
    
    # Log reception
    logger.info(f"Received message from {message.author} in #{message.channel.name} (Priority: {priority})")

async def calculate_priority(message):
    """Calculate message priority based on various factors"""
    priority = 1  # Default priority
    
    # High priority for mentions
    if bot.user in message.mentions:
        priority = 3
    
    # High priority for priority roles
    if any(role.id in PRIORITY_ROLES for role in message.author.roles):
        priority = max(priority, 3)
    
    # Medium priority for role mentions
    if message.role_mentions:
        priority = max(priority, 2)
    
    # Urgent keywords
    urgent_keywords = ['urgent', 'emergency', 'critical', 'help']
    if any(keyword in message.content.lower() for keyword in urgent_keywords):
        priority = max(priority, 2)
    
    return priority

async def add_to_queue(message, priority):
    """Add message to processing queue"""
    queue_item = {
        'message': message,
        'priority': priority,
        'timestamp': datetime.utcnow(),
        'target_bot': await determine_target_bot(message)
    }
    
    message_queue.append(queue_item)
    
    # Sort queue by priority (high priority first)
    sorted_queue = sorted(message_queue, key=lambda x: x['priority'], reverse=True)
    message_queue.clear()
    message_queue.extend(sorted_queue)

async def determine_target_bot(message):
    """Determine which bot should handle the message"""
    # Implementation depends on your specific bot logic
    # This is a placeholder for your routing logic
    return "default"

@tasks.loop(seconds=1)
async def process_queue():
    """Process messages from the queue"""
    if not message_queue:
        return
    
    # Get next message
    queue_item = message_queue.popleft()
    
    try:
        # Route to appropriate bot
        await route_message_to_bot(queue_item)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Re-add to queue with lower priority if failed
        queue_item['priority'] = max(1, queue_item['priority'] - 1)
        message_queue.append(queue_item)

async def route_message_to_bot(queue_item):
    """Route message to the appropriate sending bot"""
    # Implementation depends on your inter-bot communication method
    # This could be webhooks, API calls, database updates, etc.
    
    message = queue_item['message']
    target_bot = queue_item['target_bot']
    
    logger.info(f"Routing message to {target_bot}: {message.content[:50]}...")
    
    # Example: Send to webhook
    # await send_to_webhook(target_bot, message)

# Status commands for monitoring
@bot.command(name='queue_status')
@commands.has_permissions(administrator=True)
async def queue_status(ctx):
    """Check queue status"""
    embed = discord.Embed(title="Reception Bot Queue Status", color=0x00ff00)
    embed.add_field(name="Messages in Queue", value=len(message_queue), inline=True)
    embed.add_field(name="Bot Status", value="🟢 Online", inline=True)
    embed.add_field(name="Monitored Channels", value=len(MONITORED_CHANNELS), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='clear_queue')
@commands.has_permissions(administrator=True)
async def clear_queue(ctx):
    """Clear the message queue"""
    message_queue.clear()
    await ctx.send("✅ Message queue cleared!")

# Error handling
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"An error occurred in {event}: {args}, {kwargs}")

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_RECEPTION_BOT_TOKEN')
    if not TOKEN:
        raise ValueError("DISCORD_RECEPTION_BOT_TOKEN not found in environment variables")
    
    bot.run(TOKEN)
```

### Environment Variables Template (.env)
```env
# Discord Bot Configuration
DISCORD_RECEPTION_BOT_TOKEN=your_bot_token_here
TARGET_GUILD_ID=your_server_id_here

# Channel Configuration
MONITORED_CHANNELS=123456789012345678,234567890123456789,345678901234567890

# Priority Configuration
PRIORITY_ROLES=111111111111111111,222222222222222222
SYSTEM_BOT_IDS=333333333333333333,444444444444444444,555555555555555555

# Multi-Agent System Configuration
AGENT_ALPHA_WEBHOOK=https://discord.com/api/webhooks/your_webhook_here
AGENT_BETA_WEBHOOK=https://discord.com/api/webhooks/your_webhook_here
AGENT_GAMMA_WEBHOOK=https://discord.com/api/webhooks/your_webhook_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=reception_bot.log
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Missing Permissions" Error
**Problem**: Bot can't read messages or access channels
**Solution**: 
- Check bot permissions in Discord server
- Verify Gateway Intents are enabled in Developer Portal
- Ensure bot has "View Channels" permission

#### 2. "Privileged Intent" Error
**Problem**: Bot can't access message content
**Solution**:
- Enable "Message Content Intent" in Developer Portal
- Add `intents.message_content = True` in code
- For 100+ servers, apply for privileged intent approval

#### 3. Bot Not Receiving Messages
**Problem**: `on_message` event not firing
**Solution**:
- Verify `intents.guild_messages = True`
- Check if bot is in the correct channels
- Ensure bot isn't ignoring its own messages

#### 4. Queue Not Processing
**Problem**: Messages stuck in queue
**Solution**:
- Check `process_queue` task is running
- Verify error handling isn't breaking the loop
- Monitor logs for processing errors

#### 5. Rate Limiting Issues
**Problem**: Bot hitting Discord rate limits
**Solution**:
- Implement proper rate limiting
- Use `asyncio.sleep()` between API calls
- Queue messages instead of immediate processing

### Debug Commands
```python
@bot.command(name='debug_info')
@commands.has_permissions(administrator=True)
async def debug_info(ctx):
    """Get debug information"""
    embed = discord.Embed(title="Debug Information", color=0xff9900)
    embed.add_field(name="Latency", value=f"{bot.latency:.2f}ms", inline=True)
    embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    embed.add_field(name="Intents", value=str(bot.intents), inline=False)
    
    await ctx.send(embed=embed)
```

### Monitoring and Logging
```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reception_bot.log'),
        logging.StreamHandler()
    ]
)

# Log important events
@bot.event
async def on_message(message):
    if not message.author.bot and message.channel.id in MONITORED_CHANNELS:
        logger.info(f"Message received: {message.author} in #{message.channel.name}: {message.content[:100]}")
```

## Final Checklist

### Before Deployment:
- [ ] Bot token securely stored in environment variables
- [ ] All required intents enabled in Developer Portal
- [ ] Bot permissions configured correctly
- [ ] Monitoring channels specified
- [ ] Priority roles configured
- [ ] Queue processing implemented
- [ ] Error handling in place
- [ ] Logging configured
- [ ] Bot added to Discord server with correct permissions

### Security Checklist:
- [ ] Bot token not in source code
- [ ] .env file in .gitignore
- [ ] Minimal permissions granted
- [ ] 2FA enabled on Discord account
- [ ] Rate limiting implemented
- [ ] Input validation in place

### Testing Checklist:
- [ ] Bot responds to mentions
- [ ] Priority queue working
- [ ] Message routing functional
- [ ] Queue status commands work
- [ ] Error handling tested
- [ ] Rate limiting tested

This guide provides a comprehensive foundation for setting up your Discord reception bot in a multi-agent system. Customize the routing logic and queue processing based on your specific requirements.