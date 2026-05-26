#!/bin/bash

# FinOps Guardian - Stop Live System Script

echo "======================================================================"
echo "🛑 FinOps Guardian - Stopping Live System"
echo "======================================================================"
echo ""

echo "Stopping all processes..."
echo ""

# Stop data stream
echo "🔴 Stopping data stream generator..."
pkill -f "generate_live_stream.py"
sleep 1

# Stop ML pipeline
echo "🧠 Stopping ML pipeline..."
pkill -f "run_pipeline_continuous.py"
sleep 1

# Stop dashboard
echo "📊 Stopping dashboard..."
pkill -f "streamlit run dashboard/app.py"
sleep 1

echo ""
echo "======================================================================"
echo "✅ ALL PROCESSES STOPPED"
echo "======================================================================"
echo ""

# Check if any processes are still running
if pgrep -f "generate_live_stream.py" > /dev/null || \
   pgrep -f "run_pipeline_continuous.py" > /dev/null || \
   pgrep -f "streamlit run dashboard/app.py" > /dev/null; then
    echo "⚠️  Warning: Some processes may still be running"
    echo "   Use 'ps aux | grep finops' to check"
else
    echo "✅ All processes confirmed stopped"
fi

echo ""
