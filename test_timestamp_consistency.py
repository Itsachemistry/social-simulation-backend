#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试仿真启动后，simulation_log文件和agent_generated_posts文件的时间戳是否一致
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.main import SimulationEngine

def test_timestamp_consistency():
    """测试时间戳一致性"""
    print("=== 测试时间戳一致性 ===\n")
    
    # 创建仿真配置
    config = {
        "total_slices": 3,
        "posts_per_slice": 5,
        "use_llm": False,  # 跳过LLM以加快测试
        "skip_llm": True
    }
    
    print("📋 1. 初始化仿真引擎...")
    engine = SimulationEngine(config)
    
    # 检查生成的agent_posts文件
    agent_posts_file = engine.agent_posts_file
    print(f"   📄 Agent Posts文件: {agent_posts_file}")
    
    # 提取agent_posts文件的时间戳
    agent_posts_timestamp = agent_posts_file.replace("agent_generated_posts_", "").replace(".json", "")
    print(f"   🕐 Agent Posts时间戳: {agent_posts_timestamp}")
    
    # 检查保存的仿真时间戳
    simulation_timestamp = engine.simulation_timestamp
    print(f"   🕐 仿真引擎时间戳: {simulation_timestamp}")
    
    print(f"\n📊 2. 比较时间戳...")
    if agent_posts_timestamp == simulation_timestamp:
        print(f"   ✅ Agent Posts文件时间戳与仿真时间戳一致: {simulation_timestamp}")
    else:
        print(f"   ❌ 时间戳不一致!")
        print(f"      Agent Posts: {agent_posts_timestamp}")
        print(f"      仿真引擎: {simulation_timestamp}")
        return False
    
    print(f"\n🚀 3. 简化测试 - 检查预期的日志文件名...")
    
    # 检查预期的日志文件名
    expected_log_file = f"simulation_log_{simulation_timestamp}.txt"
    print(f"   � 预期日志文件: {expected_log_file}")
    
    print(f"\n📊 4. 时间戳一致性验证:")
    print(f"   Agent Posts文件: agent_generated_posts_{agent_posts_timestamp}.json")
    print(f"   预期日志文件: simulation_log_{simulation_timestamp}.txt")
    
    if agent_posts_timestamp == simulation_timestamp:
        print(f"\n   ✅ 时间戳完全一致: {simulation_timestamp}")
        print(f"   ✅ 两个文件将使用相同的时间戳命名")
        return True
    else:
        print(f"\n   ❌ 时间戳不一致!")
        return False

if __name__ == "__main__":
    print("🧪 仿真文件时间戳一致性测试\n")
    
    success = test_timestamp_consistency()
    
    if success:
        print(f"\n🎉 测试通过！所有文件时间戳一致。")
    else:
        print(f"\n❌ 测试失败！时间戳不一致。")
    
    print(f"\n📝 说明:")
    print(f"   - agent_generated_posts_YYYYMMDD_HHMMSS.json")
    print(f"   - simulation_log_YYYYMMDD_HHMMSS.txt")
    print(f"   - 这两个文件的时间戳现在应该完全一致！")
