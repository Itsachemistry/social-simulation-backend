#!/bin/bash

# 社交仿真系统 - 一键关闭 (Linux/macOS版本)

echo "================================"
echo "    社交仿真系统 - 一键关闭"
echo "================================"
echo

echo "🔄 正在关闭前后端服务..."

# 关闭后端服务器
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "🛑 关闭Flask后端服务器 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
fi

# 关闭前端服务器
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "🛑 关闭Vue前端服务器 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
fi

# 强制关闭可能残留的进程
echo "🛑 清理残留进程..."
pkill -f "python run_server.py" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo
echo "✅ 所有服务已关闭！"
