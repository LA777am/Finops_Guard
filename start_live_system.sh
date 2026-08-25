#!/bin/bash

# FinOps Guardian - Live System Startup Script
# This script starts all components needed for live updates

echo "======================================================================"
echo "🛡️  FinOps Guardian - Live System Startup"
echo "======================================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please create .env with DATABASE_URL"
    exit 1
fi

echo "✅ Environment file found"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi
echo ""

# Create necessary directories
mkdir -p data/synthetic
mkdir -p ml/artifacts
mkdir -p logs

echo "📁 Directories created"
echo ""

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "generate_live_stream.py" 2>/dev/null
pkill -f "run_pipeline_continuous.py" 2>/dev/null
pkill -f "uvicorn backend.main:app" 2>/dev/null
pkill -f "streamlit run dashboard/app.py" 2>/dev/null
sleep 2
echo ""

# Start live data generator
echo "🔴 Starting live data stream generator..."
nohup python3 data/synthetic/generate_live_stream.py --interval 60 > logs/data_stream.log 2>&1 &
DATA_PID=$!
echo "   PID: $DATA_PID"
echo "   Log: logs/data_stream.log"
sleep 2
echo ""

# Start continuous ML pipeline
echo "🧠 Starting continuous ML pipeline..."
nohup python3 ml/run_pipeline_continuous.py --interval 60 > logs/pipeline.log 2>&1 &
PIPELINE_PID=$!
echo "   PID: $PIPELINE_PID"
echo "   Log: logs/pipeline.log"
sleep 2
echo ""

# Start FastAPI Backend
echo "⚡ Starting FastAPI Backend..."
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
echo "   Log: logs/backend.log"
sleep 3
echo ""

# Start Streamlit dashboard
echo "📊 Starting Streamlit dashboard..."
nohup streamlit run dashboard/app.py --server.port 8501 > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   PID: $DASHBOARD_PID"
echo "   Log: logs/dashboard.log"
echo "   URL: http://localhost:8501"
sleep 3
echo ""

echo "======================================================================"
echo "✅ ALL SYSTEMS RUNNING"
echo "======================================================================"
echo ""
echo "📊 Process IDs:"
echo "   Data Stream:  $DATA_PID"
echo "   ML Pipeline:  $PIPELINE_PID"
echo "   Backend API:  $BACKEND_PID"
echo "   Dashboard:    $DASHBOARD_PID"
echo ""
echo "📝 Logs:"
echo "   tail -f logs/data_stream.log"
echo "   tail -f logs/pipeline.log"
echo "   tail -f logs/backend.log"
echo "   tail -f logs/dashboard.log"
echo ""
echo "🌐 API Docs: http://localhost:8000/docs"
echo "🌐 Dashboard: http://localhost:8501"
echo ""
echo "🛑 To stop all processes:"
echo "   ./stop_live_system.sh"
echo ""
echo "======================================================================"
