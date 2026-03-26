#!/bin/bash

# ── Config ──────────────────────────────────────────────
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8000
VENV="$DIR/venv"
SERVER="$DIR/server.py"
URL="http://localhost:$PORT"
# ────────────────────────────────────────────────────────

echo "🔍 Trivy Dashboard"
echo "──────────────────"

# Check venv exists
if [ ! -d "$VENV" ]; then
  echo "❌ Virtual environment not found at $VENV"
  echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install fastapi uvicorn aiofiles"
  exit 1
fi

# Check server.py exists
if [ ! -f "$SERVER" ]; then
  echo "❌ server.py not found in $DIR"
  exit 1
fi

# Check trivy is installed
if ! command -v trivy &> /dev/null; then
  echo "❌ Trivy not found. Install it first:"
  echo "   sudo apt install trivy"
  exit 1
fi

# Kill any existing process on the port
EXISTING=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$EXISTING" ]; then
  echo "⚠️  Port $PORT already in use — killing existing process..."
  kill -9 $EXISTING 2>/dev/null
  sleep 1
fi

# Start the server in the background
echo "🚀 Starting server on port $PORT..."
source "$VENV/bin/activate"
cd "$DIR"
uvicorn server:app --host 0.0.0.0 --port $PORT > /tmp/trivy-dashboard.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server..."
for i in {1..20}; do
  if curl -s "$URL" > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# Check it actually started
if ! kill -0 $SERVER_PID 2>/dev/null; then
  echo "❌ Server failed to start. Check logs:"
  cat /tmp/trivy-dashboard.log
  exit 1
fi

echo "✅ Server running (PID $SERVER_PID)"

# Open browser
echo "🌐 Opening browser at $URL"
if command -v xdg-open &> /dev/null; then
  xdg-open "$URL"
elif command -v gnome-open &> /dev/null; then
  gnome-open "$URL"
fi

echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Keep script running and show logs
tail -f /tmp/trivy-dashboard.log &
TAIL_PID=$!

# On Ctrl+C, kill everything cleanly
trap "echo ''; echo '🛑 Stopping...'; kill $SERVER_PID $TAIL_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait $SERVER_PID
