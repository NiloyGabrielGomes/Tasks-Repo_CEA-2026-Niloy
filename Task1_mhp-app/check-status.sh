#!/bin/bash

echo "================================"
echo "MHP Project Status Check"
echo "================================"
echo ""

# Check Python
echo "✓ Checking Python..."
python --version

# Check Node
echo "✓ Checking Node.js..."
node --version

# Check Git
echo "✓ Checking Git..."
git --version

# Check current branch
echo ""
echo "Current Git branch:"
git branch --show-current

# Check remote
echo ""
echo "Remote repository:"
git remote -v

# Check backend virtual environment
echo ""
if [ -d "backend/venv" ]; then
    echo "✓ Backend virtual environment exists"
else
    echo "✗ Backend virtual environment NOT found"
fi

# Check backend dependencies
if [ -f "backend/requirements.txt" ]; then
    echo "✓ Backend requirements.txt exists"
else
    echo "✗ Backend requirements.txt NOT found"
fi

# Check frontend node_modules
if [ -d "frontend/node_modules" ]; then
    echo "✓ Frontend dependencies installed"
else
    echo "✗ Frontend dependencies NOT installed"
fi

echo ""
echo "================================"
echo "Setup check complete!"
echo "================================"
