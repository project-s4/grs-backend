#!/bin/bash
set -e

# Force Python 3.12 - try multiple approaches
echo "🔍 Detecting Python versions..."

# Try python3.12 first
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
    echo "✅ Using python3.12"
elif command -v python3.12.10 &> /dev/null; then
    PYTHON_CMD=python3.12.10
    echo "✅ Using python3.12.10"
else
    # Fallback: use python3 but verify it's 3.12
    PYTHON_CMD=python3
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '3\.\d+' | head -1)
    if [[ "$PYTHON_VERSION" != "3.12" ]]; then
        echo "⚠️  Warning: Python 3.12 not found, using $PYTHON_CMD (version: $PYTHON_VERSION)"
    else
        echo "✅ Using python3 (version 3.12)"
    fi
fi

# Show Python version and verify it's 3.12
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '3\.\d+' | head -1)
echo "📌 Detected Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    echo "❌ ERROR: Python 3.12 is required but got version $PYTHON_VERSION"
    echo "Render is using the wrong Python version. Please configure Render to use Python 3.12"
    exit 1
fi

# Upgrade pip
echo "📦 Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

echo "✅ Build completed successfully!"

