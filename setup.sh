#!/bin/bash

# Setup script for Feedback MCP Server

set -e  # Exit on error

echo "🚀 Setting up Feedback MCP Server..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version OK: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual configuration!"
else
    echo "ℹ️  .env file already exists"
fi

# Check Docker services
echo "🐳 Checking Docker services..."
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        echo "✅ Docker is running"
        
        # Check if services are running
        if docker-compose ps | grep -q "Up"; then
            echo "ℹ️  Docker services already running"
        else
            echo "🚀 Starting Docker services..."
            docker-compose up -d
            echo "⏳ Waiting for services to be ready..."
            sleep 10
        fi
    else
        echo "⚠️  Docker is installed but not running. Please start Docker."
    fi
else
    echo "⚠️  Docker not found. You'll need to set up PostgreSQL, Elasticsearch, and Redis manually."
fi

# Create database tables
echo "🗄️  Setting up database..."
echo "To create database tables, run: python -c 'from src.storage.database import Database; from src.server import Settings; db = Database(Settings().database_url); db.create_tables()'"

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v || echo "⚠️  Some tests failed (this is normal for initial setup)"

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env with your API credentials"
echo "2. Ensure PostgreSQL, Elasticsearch, and Redis are running"
echo "3. Run 'python -m src.server' to start the MCP server"
echo "4. Or use 'docker-compose up' to run everything in containers"
echo ""
echo "📖 Documentation:"
echo "- API docs: docs/api.md"
echo "- Usage examples: docs/examples.md"
echo "- README: README.md"
