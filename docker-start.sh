#!/bin/bash
# PepperAI Docker Startup Script for Linux/macOS

echo "Starting PepperAI Docker Environment..."
echo

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running again."
    exit 1
fi

# Create necessary directories
mkdir -p backups logs

echo "Building and starting PepperAI services..."
docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo
    echo "✅ PepperAI is starting up!"
    echo
    echo "🌐 Web Interface: http://localhost"
    echo "🔍 Health Check: http://localhost/health"
    echo
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo
    echo "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are healthy
    if curl -s http://localhost/health >/dev/null 2>&1; then
        echo "✅ PepperAI is ready! Open http://localhost in your browser."
    else
        echo "⚠️  Services are starting up. Please wait a moment and check http://localhost"
    fi
else
    echo "❌ Failed to start PepperAI. Check the logs above for errors."
    exit 1
fi

echo
