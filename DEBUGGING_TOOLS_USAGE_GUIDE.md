# Discord Bot Message Event Debugging Tools - Usage Guide

## Problem Summary
Your Discord bot **connects successfully** but **receives zero message events** despite Message Content Intent being enabled. This is a complex issue that requires systematic debugging.

## 🚀 Quick Start

### 1. Initial Status Check
Run this first to verify basic bot configuration:
```bash
python quick_bot_status_check.py
```

### 2. Simple Message Test
Test if your bot can receive messages with minimal configuration:
```bash
# Activate virtual environment first
source venv/bin/activate
python minimal_message_test.py
```

### 3. Interactive Tool Selection
Use the automated tool runner:
```bash
./run_debug_tools.sh
```

---

## 🛠️ Available Debugging Tools

### Tool 1: `quick_bot_status_check.py`
**Purpose**: Fast verification of basic bot setup
**Use when**: Starting diagnosis or verifying token/connectivity
**Runtime**: ~10 seconds

**What it checks**:
- Token validity
- Discord API connectivity 
- Gateway access
- Session limits

**Example output**:
```
✅ Token valid for bot: YOUR_BOT_NAME (ID: 123456789)
✅ Discord API connectivity: OK
✅ Gateway access: OK
```

### Tool 2: `minimal_message_test.py`
**Purpose**: Simplest possible message event test
**Use when**: You want to isolate the message reception issue
**Runtime**: 60 seconds of live monitoring

**What it does**:
- Uses minimal bot configuration
- Monitors for any message events
- Responds to "test" messages
- Logs all received messages

**Example usage**:
```bash
source venv/bin/activate
python minimal_message_test.py
# Send "test" in Discord channel while running
```

### Tool 3: `message_event_troubleshooter.py`
**Purpose**: Comprehensive step-by-step diagnosis
**Use when**: Basic tools don't reveal the issue
**Runtime**: ~2 minutes

**What it analyzes**:
- Token type validation (bot vs user token)
- Intent configuration testing
- Permission verification
- Gateway connection analysis
- Live message monitoring

### Tool 4: `advanced_discord_debugger.py`
**Purpose**: Full system analysis including network diagnostics
**Use when**: Suspected network, WSL2, or environment issues
**Runtime**: ~3-5 minutes

**What it includes**:
- Environment analysis (WSL2, Python version, etc.)
- Network connectivity testing
- Discord.py version compatibility
- Advanced intent testing
- Comprehensive reporting

---

## 📋 Systematic Debugging Process

### Step 1: Basic Verification
```bash
python quick_bot_status_check.py
```
**Expected result**: All checks should pass
**If failed**: Fix token or network issues before proceeding

### Step 2: Simple Message Test
```bash
source venv/bin/activate
python minimal_message_test.py
```
**During test**: Send "test" or "debug" in any channel the bot can see
**Expected result**: Bot responds and logs messages
**If failed**: Message event issue confirmed

### Step 3: Comprehensive Analysis
```bash
source venv/bin/activate
python message_event_troubleshooter.py
```
**Expected result**: Detailed analysis of all potential issues
**If failed**: Follow generated recommendations

### Step 4: Full System Diagnosis (if needed)
```bash
source venv/bin/activate
python advanced_discord_debugger.py
```
**Use when**: Previous tools don't identify the issue

---

## 📊 Understanding Results

### ✅ Success Indicators
- Token validation passes
- Bot connects (on_ready fires)
- Message events received in live tests
- Bot responds to test commands

### ❌ Failure Indicators
- Invalid token errors
- Privileged intents required errors
- Zero messages received in live tests
- Connection timeouts

### ⚠️ Warning Indicators
- WSL2 environment detected
- Low session limits
- Permission warnings
- Version compatibility issues

---

## 🔧 Common Solutions

### Issue: "Invalid Token"
**Solution**:
1. Go to Discord Developer Portal
2. Your Application → Bot → Reset Token
3. Update `.env` file with new token
4. Restart bot

### Issue: "Privileged Intents Required"
**Solution**:
1. Discord Developer Portal → Your Application → Bot
2. Enable "Message Content Intent" under Privileged Gateway Intents
3. Save changes
4. Wait 5-10 minutes for propagation

### Issue: "Bot Connects But No Messages"
**Most common issue - try these in order**:

1. **Verify Portal Settings**:
   - Message Content Intent enabled
   - Bot has proper server permissions

2. **Check Bot Permissions in Discord**:
   - View Channels: ✅
   - Read Messages: ✅
   - Send Messages: ✅

3. **Test in New Server**:
   - Create test server
   - Give bot Administrator permissions
   - Test message reception

4. **Wait for Propagation**:
   - Discord changes can take 15-30 minutes
   - Restart bot after making changes

### Issue: "Network Connectivity Problems"
**Solutions**:
- Test without VPN/proxy
- Check firewall settings
- If using WSL2, test on native Windows/Linux

---

## 📄 Generated Reports

The tools generate detailed reports:

- `discord_diagnosis_report.json` - Full technical details
- `discord_diagnosis_report.txt` - Human-readable summary  
- `message_event_troubleshoot_report.json` - Focused message event analysis

These reports contain:
- All test results
- Specific recommendations
- Environment details
- Failure analysis

---

## 🆘 Emergency Troubleshooting

If all tools show success but messages still don't work:

### 1. Create New Bot Application
Sometimes Discord applications get corrupted:
1. Create new application in Discord Developer Portal
2. Create new bot user
3. Enable Message Content Intent
4. Use new token

### 2. Test Different Environment
- Native Linux instead of WSL2
- Different Python version
- Different discord.py version

### 3. Use Bot Testing Servers
Join public bot testing servers to eliminate server-specific issues.

---

## 🚨 Red Flags (Call for Help)

Contact Discord support or seek advanced help if:

- All debugging tools pass ✅
- Bot connects successfully ✅  
- Intents properly configured ✅
- Still zero message events ❌

This indicates a rare Discord API issue or account-specific problem.

---

## 💡 Pro Tips

1. **Run tools in order**: Start with quick check, then minimal test
2. **Save reports**: Keep generated JSON files for support requests
3. **Test incrementally**: Fix one issue at a time
4. **Wait between changes**: Discord needs time to propagate changes
5. **Use test servers**: Create dedicated test server for debugging

---

## 📞 Getting Further Help

If you need additional support:

1. Run all debugging tools
2. Save the generated report files
3. Include your bot code (with tokens redacted)
4. Specify your environment details
5. List everything you've tried

The comprehensive reports will help support staff quickly identify the issue.

---

## 🔄 Quick Command Reference

```bash
# Basic status check
python quick_bot_status_check.py

# Simple message test (most useful)
source venv/bin/activate && python minimal_message_test.py

# Full troubleshooting
source venv/bin/activate && python message_event_troubleshooter.py

# Interactive tool selection
./run_debug_tools.sh

# System-wide diagnosis
source venv/bin/activate && python advanced_discord_debugger.py
```

Remember: The `minimal_message_test.py` is usually the most revealing test for the "connects but no messages" issue.