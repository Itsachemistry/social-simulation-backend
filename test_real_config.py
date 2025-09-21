#!/usr/bin/env python3
"""
直接测试前端配置格式是否能正确传递给后端
"""

import requests
import json

def test_frontend_config():
    """测试前端配置格式"""
    
    # 这是前端实际发送的配置格式
    config = {
        "w_pop": 0.7,
        "k": 2,
        "posts_per_slice": 50,
        "max_slices": 2,
        "enable_llm_test": True,
        "llm_full_monitoring": True,
        "skip_llm": False,
        "llm_config": {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "base_url": "https://www.chataiapi.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "enabled": True,
            "enabled_agents": ["agent_001", "agent_002"],
            "enabled_timeslices": [0, 1]
        }
    }
    
    agent_configs = [
        {
            "agent_id": "agent_001",
            "role_type": "ordinary_user",
            "current_emotion": 0.0,
            "current_stance": 0.0,
            "current_confidence": 0.5,
            "activity_level": 0.6,
            "attitude_firmness": 0.4,
            "viewpoint_blocking": 0.1
        },
        {
            "agent_id": "agent_002", 
            "role_type": "ordinary_user",
            "current_emotion": -0.2,
            "current_stance": -0.1,
            "current_confidence": 0.3,
            "activity_level": 0.5,
            "attitude_firmness": 0.3,
            "viewpoint_blocking": 0.3
        }
    ]
    
    payload = {
        "config": config,
        "agent_configs": agent_configs
    }
    
    print("🚀 发送仿真请求...")
    print(f"LLM配置: {config['llm_config']}")
    
    try:
        response = requests.post('http://localhost:5000/api/simulation/start', json=payload)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 仿真启动成功! ID: {result.get('simulation_id')}")
            return True
        else:
            print(f"❌ 仿真启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    test_frontend_config()
