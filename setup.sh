#!/bin/bash

# Agentic Fact-Check System Setup Script
# This script helps you set up the system quickly

echo "🔍 Agentic Fact-Check System Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✅ pip found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file and add your API keys:"
    echo "   - OpenAI API Key (required)"
    echo "   - News API Key (recommended)"
    echo "   - Twitter Bearer Token (optional)"
    echo ""
    echo "   To edit: nano .env"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
mkdir -p data output

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys: nano .env"
echo "2. Test the system: python3 test_system.py"
echo "3. Run the fact-checker: python3 main.py"
echo ""
echo "For help, see README.md or visit the GitHub repository."
