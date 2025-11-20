#!/bin/bash

# Script to run DJIA Enhanced Agent
echo "================================================"
echo "  DJIA Enhanced Agent - Startup Script"
echo "================================================"
echo ""

# Add local bin to PATH
export PATH=$PATH:/home/ubuntu/.local/bin

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env file with your Gemini API key:"
    echo ""
    echo "   GEMINI_API_KEY=your_api_key_here"
    echo "   GOOGLE_API_KEY=your_api_key_here"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if database exists
if [ ! -f "db/djia.db" ]; then
    echo "📊 Database not found. Initializing database..."
    python3 db/init_db.py
    echo "✓ Database initialized"
    echo ""
fi

# Start Streamlit
echo "🚀 Starting DJIA Enhanced Agent..."
echo ""
echo "   The app will open in your browser at:"
echo "   👉 http://localhost:8501"
echo ""
echo "   Features:"
echo "   ✅ Answer complex questions"
echo "   ✅ Auto-generate price charts"
echo "   ✅ Statistical analysis"
echo "   ✅ Multi-company comparisons"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "================================================"
echo ""

streamlit run app/main.py
