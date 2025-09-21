@echo off
chcp 65001 >nul
echo ================================
echo    社交仿真系统 - 一键启动
echo ================================
echo.

REM 检查是否存在虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 未找到虚拟环境，请先运行 python -m venv venv
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 🔄 激活Python虚拟环境...
call venv\Scripts\activate

REM 检查后端依赖
echo 🔄 检查后端依赖...
pip install -r requirements.txt >nul 2>&1

REM 启动后端服务器（新窗口）
echo 🚀 启动后端服务器...
start "社交仿真后端" cmd /c "call venv\Scripts\activate.bat && D:/social_simulation_engine/venv/Scripts/python.exe run_server.py"

REM 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 3 >nul

REM 检查前端依赖并启动
echo 🔄 检查前端依赖...
cd frontend-vue
if not exist "node_modules" (
    echo 📦 安装前端依赖...
    npm install
)

REM 启动Vue前端开发服务器（新窗口）
echo 🚀 启动Vue前端服务器...
start "社交仿真前端" cmd /c "cd frontend-vue && npx vite --port 8080"

cd ..

echo.
echo ✅ 前后端服务已启动！
echo.
echo 📍 后端API: http://localhost:5000
echo 📍 前端页面: http://localhost:8080 (Vue开发服务器)
echo 📍 API文档: http://localhost:5000/api/visualization/options
echo.
echo ⚠️  请等待前端编译完成后再访问页面
echo 💡 按任意键关闭此窗口...
pause >nul
