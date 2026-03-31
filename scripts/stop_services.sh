#!/bin/bash
# Stop local backend/frontend services for breast-cancer-ai

lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

echo "Stopped services on ports 8000 and 8080 (if any)."
