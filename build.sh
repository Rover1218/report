#!/bin/bash
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setting up required directories..."
mkdir -p static/reports
mkdir -p static/uploads
mkdir -p static/fonts

echo "Build completed successfully"
