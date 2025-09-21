#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试前端API获取仿真列表"""

import sys
sys.path.append('.')

from simulation_log_extractor import create_frontend_api_adapter
import json

def test_frontend_api():
    """测试前端API"""
    print("=== 测试frontend_adapter ===")
    
    try:
        # 创建前端API适配器
        frontend_adapter = create_frontend_api_adapter()
        
        result = frontend_adapter['get_simulation_list']()
        simulations = result.get('simulations', [])
        
        print(f"获取到 {len(simulations)} 个仿真")
        print()
        
        for sim in simulations:
            print(f"仿真ID: {sim['id']}")
            print(f"名称: {sim['name']}")
            print(f"状态: {sim.get('status', '未知')}")
            print(f"Agent数量: {sim.get('agent_count', 0)}")
            print(f"时间片数量: {sim.get('total_time_slices', 0)}")
            print("-" * 50)
            
        # 检查最新仿真
        latest_sim_id = "sim_20250730_211556"
        latest_sim = None
        for sim in simulations:
            if sim['id'] == latest_sim_id:
                latest_sim = sim
                break
                
        if latest_sim:
            print(f"✅ 找到最新仿真: {latest_sim_id}")
            print(f"   状态: {latest_sim.get('status')}")
            print(f"   Agent数量: {latest_sim.get('agent_count')}")
            print(f"   时间片数量: {latest_sim.get('total_time_slices')}")
        else:
            print(f"❌ 未找到最新仿真: {latest_sim_id}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_api()
