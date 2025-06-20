# Discord Bot Message Content Intent Troubleshooting Guide

## Issue Summary
Discord bot connects successfully but `on_message` events are not firing. This is typically caused by missing **Message Content Intent** configuration.

## Required Actions

### Step 1: Discord Developer Portal Configuration (CRITICAL)

For **each of your 4 Discord bots**, you must:

1. **Navigate to Discord Developer Portal**
   - Go to https://discord.com/developers/applications
   - Sign in with your Discord account

2. **Configure Each Bot Application:**
   
   **Bot 1: RECEIVER (Reception Bot)**
   - Select your RECEIVER bot application
   - Go to "Bot" section
   - Scroll to "Privileged Gateway Intents"
   - ✅ **Enable "Message Content Intent"**
   - Save changes
   
   **Bot 2: SPECTRA**  
   - Select your SPECTRA bot application
   - Go to "Bot" section
   - ⚠️ **Note**: Output bots don't need Message Content Intent
   
   **Bot 3: LYNQ**
   - Same as SPECTRA - no Message Content Intent needed
   
   **Bot 4: PAZ**
   - Same as SPECTRA - no Message Content Intent needed

3. **Important Notes:**
   - **ONLY the RECEIVER bot needs Message Content Intent** (it's the only one receiving messages)
   - If your bot is in 100+ servers, you need Discord verification
   - If your bot is in <100 servers, you can enable it directly

### Step 2: Verify Code Configuration

The code has been updated with explicit intent configuration:

```python
# In src/discord_clients.py (ReceptionClient)
intents = discord.Intents.default()
intents.message_content = True  # ✅ Required for message content
intents.guild_messages = True   # ✅ Required for server messages  
intents.guilds = True          # ✅ Required for server info
```

### Step 3: Run Diagnostic Test

```bash
cd /home/sito/project-009
source venv/bin/activate
python diagnose_message_intent.py
```

**Expected Results:**
- ✅ Bot connects successfully
- ✅ Shows server and channel information
- ✅ `on_message` events fire when you send test messages
- ✅ Bot responds to messages starting with "test"

**If diagnostic fails:**
- ❌ `on_message` events don't fire → Message Content Intent not enabled in Developer Portal
- ❌ Permission errors → Check bot permissions in Discord server
- ❌ Connection fails → Check bot token validity

### Step 4: Test in Discord

1. **Send test message:** Type `test hello` in any monitored channel
2. **Expected response:** Bot should reply with "🟢 Message Content Intent 正常動作確認！on_messageイベント受信成功"
3. **Check logs:** Should see detailed message processing logs

### Step 5: Common Issues & Solutions

#### Issue: "on_message not firing"
**Cause:** Message Content Intent not enabled in Developer Portal  
**Solution:** Enable Message Content Intent for RECEIVER bot in Developer Portal

#### Issue: "Forbidden/Missing Permissions" 
**Cause:** Bot lacks required permissions in Discord server
**Solution:** 
- Check bot role permissions in Discord server
- Ensure bot has "View Channels", "Read Messages", "Send Messages" permissions

#### Issue: "Bot appears offline"
**Cause:** Invalid bot token or network issues
**Solution:**
- Verify token in .env file matches Developer Portal
- Check network connectivity

#### Issue: "Message content is empty/null"
**Cause:** Message Content Intent enabled in code but not in Developer Portal
**Solution:** Enable Message Content Intent in Developer Portal

### Step 6: Production System Testing

After fixing the intent issue, test the full system:

```bash
cd /home/sito/project-009
source venv/bin/activate
python main.py
```

**Expected behavior:**
1. ✅ All 4 bots connect successfully
2. ✅ RECEIVER bot receives messages and adds them to priority queue
3. ✅ LangGraph supervisor processes messages
4. ✅ Appropriate output bot (Spectra/LynQ/Paz) sends response
5. ✅ Logs show complete message flow

## Verification Checklist

- [ ] Message Content Intent enabled for RECEIVER bot in Developer Portal
- [ ] Bot tokens are valid and correctly configured in .env
- [ ] Bot has proper permissions in Discord server
- [ ] Diagnostic script successfully receives messages
- [ ] Production system processes messages end-to-end
- [ ] All 4 bots connect without errors
- [ ] Message processing loop operates correctly

## Additional Resources

- [Discord Message Content Intent Documentation](https://support-dev.discord.com/hc/en-us/articles/4404772028055)
- [Discord.py Intents Guide](https://discordpy.readthedocs.io/en/stable/intents.html)
- [Discord Developer Portal](https://discord.com/developers/applications)

## Support

If issues persist after following this guide:
1. Check Discord Developer Portal settings again
2. Verify bot tokens are current and valid  
3. Test with diagnostic script to isolate the problem
4. Review Discord.py documentation for version-specific requirements