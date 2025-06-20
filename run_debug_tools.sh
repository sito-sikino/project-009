#!/bin/bash

echo "🔍 Discord Bot Debug Tools Runner"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if packages are installed
echo "📦 Checking package installation..."
python -c "import discord, aiohttp" 2>/dev/null || {
    echo "📦 Installing required packages..."
    pip install discord.py aiohttp python-dotenv requests
}

echo ""
echo "Choose a debugging tool to run:"
echo "1. Minimal Message Test (recommended first)"
echo "2. Message Event Troubleshooter (comprehensive)"
echo "3. Advanced Discord Debugger (full system analysis)"
echo "4. Run existing diagnose_message_intent.py"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🎯 Running Minimal Message Test..."
        python minimal_message_test.py
        ;;
    2)
        echo "🔍 Running Message Event Troubleshooter..."
        python message_event_troubleshooter.py
        ;;
    3)
        echo "🔧 Running Advanced Discord Debugger..."
        python advanced_discord_debugger.py
        ;;
    4)
        echo "🔍 Running existing diagnostic tool..."
        python diagnose_message_intent.py
        ;;
    *)
        echo "❌ Invalid choice. Running Minimal Message Test by default..."
        python minimal_message_test.py
        ;;
esac

echo ""
echo "🏁 Debug tool execution completed."
echo "📄 Check generated report files for detailed results."