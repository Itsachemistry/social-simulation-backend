@echo off
REM 激活虚拟环境
call venv\Scripts\activate

REM 启动后端（新窗口）
start cmd /k python run_server.py

REM 启动前端静态服务器（新窗口）
cd fronted
start cmd /k python -m http.server 8080
cd ..

echo 前后端已启动，浏览器访问 http://localhost:8080/index.html
pause 