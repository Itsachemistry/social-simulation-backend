@echo off
echo ========================================
echo 社交仿真引擎 - 实时监控功能演示
echo ========================================
echo.

echo 🚀 启动实时监控测试...
echo.

echo 测试1: 基础实时监控功能
python test_realtime_monitoring.py
echo.

echo 测试2: 带发帖功能的实时监控
python test_realtime_posting.py
echo.

echo 📁 查看生成的日志文件...
dir simulation_log_*.txt /O:D
echo.

echo ✅ 实时监控功能演示完成！
echo 💡 您可以打开最新的 simulation_log_*.txt 文件查看详细日志
echo.

pause
