#!/bin/bash

echo "========================================="
echo "Utility Monitor - Initialization Script"
echo "========================================="
echo ""

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data
echo "✓ Data directory created"
echo ""

# Create empty data files if they don't exist
if [ ! -f data/mentions.json ]; then
    echo "📝 Initializing mentions.json..."
    echo "[]" > data/mentions.json
    echo "✓ mentions.json created"
fi

if [ ! -f data/crawl_log.json ]; then
    echo "📝 Initializing crawl_log.json..."
    echo "[]" > data/crawl_log.json
    echo "✓ crawl_log.json created"
fi

echo ""
echo "✅ Initialization complete!"
echo ""
echo "To start the application:"
echo "  python app.py"
echo ""
echo "The app will be available at:"
echo "  http://localhost:5000"
echo ""
echo "========================================="
