#!/bin/bash

# Linux Mirror Testing Solution - Run Script
# This script demonstrates how to build and run the application

echo "Building Docker containers..."
docker-compose build

echo "Starting application..."
docker-compose up -d

echo "Application started!"
echo "Frontend available at: http://localhost:3000"
echo "Backend API available at: http://localhost:8000"

echo ""
echo "To view logs:"
echo "  docker-compose logs -f"

echo ""
echo "To stop the application:"
echo "  docker-compose down"
