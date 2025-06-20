#!/bin/bash

echo "🔍 COMPREHENSIVE DISCORD BOT DIAGNOSIS"
echo "======================================"

# Create logs directory
mkdir -p logs

echo ""
echo "🔧 Step 1: Running quick bot status check..."
python3 quick_bot_status_check.py | tee logs/status_check.log

echo ""
echo "⚔️  Step 2: Running multi-client conflict diagnostic..."
python3 multi_client_conflict_diagnostic.py | tee logs/conflict_diagnostic.log

echo ""
echo "🔍 Step 3: Running isolated reception test (30 seconds)..."
echo "   Send 'isolated-test' in Discord during this test!"
timeout 30s python3 isolated_reception_test.py | tee logs/isolated_test.log

echo ""
echo "📋 DIAGNOSIS COMPLETE"
echo "===================="
echo "📄 Logs saved in logs/ directory:"
echo "   - logs/status_check.log"
echo "   - logs/conflict_diagnostic.log" 
echo "   - logs/isolated_test.log"

echo ""
echo "🛠️  IMMEDIATE ACTIONS:"
echo "1. Check the isolated test log - if it shows message reception, the fix works"
echo "2. Review conflict diagnostic for specific multi-client issues"
echo "3. If isolated test works, update your main.py to use only reception client"

echo ""
echo "💡 To test the fixed main.py:"
echo "   python3 main.py"
echo ""