#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask服务器启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 启动社交仿真引擎API服务器...")
    print("📍 服务器地址: http://localhost:5000")
    print("📚 API文档: http://localhost:5000/api/visualization/options")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 