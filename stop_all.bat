@echo off
chcp 65001 >nul
echo ================================
echo    社交仿真系统 - 一键关闭
echo ================================
echo.

echo 🔄 正在关闭前后端服务...

REM 关闭Node.js进程 (Vue前端)
echo 🛑 关闭Vue前端服务器...
taskkill /f /im node.exe >nul 2>&1

REM 关闭Python进程 (Flask后端)  
echo 🛑 关闭Flask后端服务器...
taskkill /f /im python.exe >nul 2>&1

REM 关闭相关的命令行窗口
echo 🛑 关闭相关窗口...
taskkill /f /fi "WindowTitle eq 社交仿真后端*" >nul 2>&1
taskkill /f /fi "WindowTitle eq 社交仿真前端*" >nul 2>&1

echo.
echo ✅ 所有服务已关闭！
echo.
echo 💡 按任意键关闭此窗口...
pause >nul
