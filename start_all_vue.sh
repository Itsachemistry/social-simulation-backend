#!/bin/bash

# 社交仿真系统 - 一键启动 (Linux/macOS版本)

echo "================================"
echo "    社交仿真系统 - 一键启动"
echo "================================"
echo

# 检查是否存在虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ 未找到虚拟环境，请先运行 python -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活Python虚拟环境..."
source venv/bin/activate

# 检查后端依赖
echo "🔄 检查后端依赖..."
pip install -r requirements.txt > /dev/null 2>&1

# 启动后端服务器（后台运行）
echo "🚀 启动后端服务器..."
python run_server.py &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 切换到前端目录
cd frontend-vue

# 检查前端依赖
echo "🔄 检查前端依赖..."
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动Vue前端开发服务器（后台运行）
echo "🚀 启动Vue前端服务器..."
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend.pid

cd ..

echo
echo "✅ 前后端服务已启动！"
echo
echo "📍 后端API: http://localhost:5000"
echo "📍 前端页面: http://localhost:5173"
echo "📍 API文档: http://localhost:5000/api/visualization/options"
echo
echo "⚠️  请等待前端编译完成后再访问页面"
echo "💡 运行 ./stop_all.sh 来关闭所有服务"
