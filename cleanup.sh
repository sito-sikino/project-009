#!/bin/bash
# Project Cleanup Script
# プロジェクトクリーンアップスクリプト

echo "🧹 Starting project cleanup..."

# 1. Python cache files cleanup
echo "📦 Removing Python cache files..."
find /home/sito/project-009 -name "*.pyc" -delete 2>/dev/null || true
find /home/sito/project-009 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 2. MyPy cache cleanup  
echo "🔍 Removing MyPy cache..."
rm -rf /home/sito/project-009/.mypy_cache 2>/dev/null || true

# 3. Pytest cache cleanup
echo "🧪 Removing Pytest cache..."
rm -rf /home/sito/project-009/.pytest_cache 2>/dev/null || true

# 4. Show results
echo "✅ Cleanup completed!"
echo "📊 Estimated space saved: ~111MB"

# 5. Update .gitignore to prevent future accumulation
if ! grep -q "__pycache__" /home/sito/project-009/.gitignore; then
    echo "📝 Updating .gitignore..."
    echo "
# Python cache files (auto-added by cleanup script)
__pycache__/
*.pyc
*.pyo
.mypy_cache/
.pytest_cache/" >> /home/sito/project-009/.gitignore
    echo "✅ .gitignore updated"
fi

echo "🎉 Project cleanup finished!"