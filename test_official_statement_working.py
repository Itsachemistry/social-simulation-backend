#!/usr/bin/env python3
"""
使用已知仿真ID测试官方声明功能
"""

import requests
import json
from datetime import datetime

def test_official_statement_injection():
    """测试官方声明注入功能"""
    print("=== 官方声明注入功能测试 ===")
    
    # 使用已知的仿真ID
    simulation_id = "sim_20250730_110327"
    
    # 测试官方声明配置
    statement_config = {
        "title": "测试官方澄清声明",
        "content": "这是一个测试的官方澄清声明，用于验证LLM注解和帖子结构功能。",
        "statement_type": "clarification",
        "authority_level": "high",
        "target_time_slice": 2,
        "effect_config": {
            "emotion_impact": 0.3,
            "stance_impact": 0.2,
            "confidence_boost": 0.1
        }
    }
    
    print(f"1. 测试仿真ID: {simulation_id}")
    print(f"2. 声明类型: {statement_config['statement_type']}")
    print(f"3. 权威级别: {statement_config['authority_level']}")
    print(f"4. 声明内容: {statement_config['content'][:50]}...")
    
    # 发送官方声明注入请求
    url = "http://localhost:5000/api/simulation/inject_official_statement"
    payload = {
        "simulation_id": simulation_id,
        "content": statement_config["content"],
        "statement_type": statement_config["statement_type"],
        "authority_level": statement_config["authority_level"],
        "target_time_slice": statement_config["target_time_slice"],
        "custom_tags": [],
        "notes": "测试官方声明注入",
        "enable_tracking": True
    }
    
    print(f"\n5. 发送API请求到: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"6. HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 注入成功!")
            print(f"   - 状态: {result.get('status')}")
            print(f"   - 消息: {result.get('message')}")
            print(f"   - 新仿真ID: {result.get('new_simulation_id')}")
            print(f"   - 数据源: {result.get('source', '内存')}")
            
            # 显示声明数据
            if 'statement_data' in result:
                data = result['statement_data']
                print(f"\n7. 生成的声明数据:")
                print(f"   - 声明ID: {data.get('id')}")
                print(f"   - 帖子ID: {data.get('mid')}")
                print(f"   - 发布者: {data.get('name')}")
                print(f"   - 强制阅读: {data.get('force_read')}")
                print(f"   - 官方声明标记: {data.get('is_official_statement')}")
                
                # 显示LLM注解结果
                if 'llm_annotation' in data:
                    annotation = data['llm_annotation']
                    print(f"\n8. LLM注解结果:")
                    print(f"   - 情绪分数: {annotation.get('emotion_score')}")
                    print(f"   - 立场分数: {annotation.get('stance_score')}")
                    print(f"   - 立场类别: {annotation.get('stance_category')}")
                    print(f"   - 立场置信度: {annotation.get('stance_confidence')}")
                    print(f"   - 信息强度: {annotation.get('information_strength')}")
                    print(f"   - 关键词: {annotation.get('keywords')}")
                else:
                    print(f"\n8. ⚠️ 未找到LLM注解数据")
                
                print(f"\n完整响应数据:")
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
            print(f"\n✅ 官方声明注入测试成功!")
            return True
            
        else:
            print(f"❌ API请求失败")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（30秒）")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败，请确保API服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    test_official_statement_injection()
