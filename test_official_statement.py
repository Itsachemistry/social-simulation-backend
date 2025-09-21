#!/usr/bin/env python3
"""
官方声明系统测试脚本
测试新的官方舆论干预功能
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:5000/api/simulation"

def test_official_statement_system():
    """测试官方声明系统的完整流程"""
    
    print("=== 官方声明系统测试 ===")
    
    # 1. 获取配置面板数据
    print("\n1. 获取配置面板数据...")
    response = requests.get(f"{BASE_URL}/official_statement/config_panel")
    if response.status_code == 200:
        panel_data = response.json()
        print(f"✅ 找到 {len(panel_data['simulations'])} 个可用仿真")
        print(f"✅ 支持 {len(panel_data['statement_types'])} 种声明类型")
        
        if not panel_data['simulations']:
            print("❌ 没有可用的仿真，请先运行一个基础仿真")
            return
            
        # 选择第一个仿真进行测试
        test_simulation = panel_data['simulations'][0]
        print(f"📝 使用仿真: {test_simulation['id']} ({test_simulation['name']})")
        
    else:
        print(f"❌ 获取配置面板失败: {response.status_code}")
        return
    
    # 2. 获取仿真详情
    print(f"\n2. 获取仿真详情...")
    sim_id = test_simulation['id']
    response = requests.get(f"{BASE_URL}/official_statement/simulation_details/{sim_id}")
    if response.status_code == 200:
        sim_details = response.json()
        print(f"✅ 仿真时间片数: {sim_details['simulation']['total_time_slices']}")
        print(f"✅ Agent数量: {sim_details['simulation']['agent_count']}")
    else:
        print(f"❌ 获取仿真详情失败: {response.status_code}")
        return
    
    # 3. 注入官方声明
    print(f"\n3. 注入官方声明...")
    statement_config = {
        "content": "【官方澄清】经核实，网传相关信息不属实，请广大网友理性判断，不信谣不传谣。",
        "target_time_slice": min(2, sim_details['simulation']['total_time_slices'] - 1),  # 选择安全的时间片
        "statement_type": "refutation",  # 辟谣声明
        "authority_level": "high"        # 高权威
    }
    
    payload = {
        "original_simulation_id": sim_id,
        "statement_config": statement_config
    }
    
    response = requests.post(f"{BASE_URL}/inject_official_statement", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 官方声明注入成功!")
        print(f"📝 新仿真ID: {result['new_simulation_id']}")
        print(f"📝 原仿真ID: {result['original_simulation_id']}")
        print(f"📝 声明内容: {result['statement_data']['content'][:50]}...")
        
        # 监控新仿真的状态
        new_sim_id = result['new_simulation_id']
        print(f"\n4. 监控新仿真状态...")
        
        for i in range(30):  # 最多等待30秒
            response = requests.get(f"{BASE_URL}/status/{new_sim_id}")
            if response.status_code == 200:
                status = response.json()
                sim_status = status['data']['status']
                print(f"   仿真状态: {sim_status}")
                
                if sim_status == "completed":
                    print("✅ 仿真完成!")
                    break
                elif sim_status == "error":
                    print(f"❌ 仿真出错: {status['data'].get('error', '未知错误')}")
                    break
                    
            time.sleep(1)
        
    else:
        print(f"❌ 注入官方声明失败: {response.status_code}")
        print(f"错误信息: {response.text}")

if __name__ == "__main__":
    test_official_statement_system()
