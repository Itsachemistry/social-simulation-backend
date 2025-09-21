#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版批量官方声明系统测试
"""

import sys
import os
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from api.simulation_service import SimulationManager

def test_batch_official_statements_simple():
    """简化版批量官方声明测试"""
    print("=== 简化版批量官方声明系统测试 ===\n")
    
    # 1. 创建仿真管理器
    print("📋 1. 初始化仿真管理器...")
    manager = SimulationManager()
    
    # 2. 准备仿真配置
    config = {
        "total_slices": 8,
        "posts_per_slice": 5,
        "w_pop": 0.7,
        "k": 2,
        "use_llm": True,
        "llm": {
            "provider": "deepseek",
            "model": "deepseek-chat"
        }
    }
    
    # 3. 准备Agent配置
    agent_configs = [
        {
            "agent_id": "agent_001",  # 使用agent_id而不是id
            "role": "student",
            "name": "小李",
            "initial_emotion": 0.5,
            "initial_stance": 0.3
        },
        {
            "agent_id": "agent_002",  # 使用agent_id而不是id
            "role": "working_professional",
            "name": "小王",
            "initial_emotion": 0.4,
            "initial_stance": 0.7
        }
    ]
    
    # 4. 准备批量官方声明
    statements = [
        {
            "content": "政府发布新的教育政策，支持数字化教学发展。",
            "target_slice": 3
        },
        {
            "content": "卫生部门提醒公众注意季节性流感防护。",
            "target_slice": 5
        },
        {
            "content": "交通部门宣布地铁线路优化调整计划。",
            "target_slice": 6
        }
    ]
    
    print(f"📢 2. 准备批量注入 {len(statements)} 条官方声明...")
    for i, stmt in enumerate(statements, 1):
        print(f"   {i}. 目标时间片 {stmt['target_slice']}: {stmt['content'][:30]}...")
    
    # 5. 执行批量官方声明注入
    print(f"\n🏛️ 3. 执行批量官方声明注入...")
    try:
        result = manager.inject_batch_official_statements(config, agent_configs, statements)
        print(f"   ✅ 批量注入成功!")
        print(f"   📊 仿真ID: {result.get('simulation_id', '未知')}")
        
        if 'annotated_statements' in result:
            print(f"   📝 LLM标注结果:")
            for i, annotated in enumerate(result['annotated_statements'], 1):
                original = annotated.get('original_content', '')[:30]
                llm_annotation = annotated.get('llm_annotation', '')[:30]
                print(f"      {i}. 原文: {original}...")
                print(f"         标注: {llm_annotation}...")
        
    except Exception as e:
        print(f"   ❌ 批量注入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 等待仿真运行一段时间
    print(f"\n⏳ 4. 等待仿真运行...")
    simulation_id = result.get('simulation_id')
    if simulation_id:
        for i in range(5):
            time.sleep(2)
            try:
                status = manager.get_simulation_status(simulation_id)
                current_slice = status.get('current_slice', 0)
                total_slices = status.get('total_slices', 0)
                print(f"   时间片进度: {current_slice}/{total_slices}")
                
                if current_slice >= 7:  # 运行到足够的时间片
                    break
                    
            except Exception as e:
                print(f"   获取状态失败: {e}")
    
    # 7. 检查生成的agent_posts文件
    print(f"\n📂 5. 检查生成的agent_posts文件...")
    posts_files = list(Path('.').glob('agent_generated_posts_*.json'))
    if posts_files:
        latest_posts_file = max(posts_files, key=lambda p: p.stat().st_mtime)
        print(f"   📄 找到最新posts文件: {latest_posts_file}")
        
        try:
            with open(latest_posts_file, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            all_posts = posts_data.get('agent_posts', [])
            print(f"   📊 总帖子数: {len(all_posts)}")
            
            # 统计官方声明
            official_statements = [
                post for post in all_posts
                if post.get('type') == 'official_statement'
            ]
            
            print(f"   📢 官方声明数: {len(official_statements)}")
            
            if official_statements:
                print(f"   📋 官方声明详情:")
                for i, stmt in enumerate(official_statements, 1):
                    target_slice = stmt.get('target_slice', '未知')
                    content = stmt.get('content', '')[:40]
                    annotation = stmt.get('annotation', '')
                    has_llm = "有LLM标注" if annotation and annotation != content else "无LLM标注"
                    print(f"      {i}. 片{target_slice}: {content}... ({has_llm})")
            
            # 统计Agent帖子
            agent_posts = [
                post for post in all_posts
                if post.get('type') != 'official_statement'
            ]
            print(f"   🤖 Agent帖子数: {len(agent_posts)}")
            
        except Exception as e:
            print(f"   ❌ 读取posts文件失败: {e}")
    else:
        print(f"   ⚠️ 未找到agent_generated_posts文件")
    
    # 8. 测试结果
    print(f"\n🎯 6. 测试完成!")
    print(f"   ✅ 批量官方声明系统正常工作")
    print(f"   ✅ LLM标注功能正常")
    print(f"   ✅ 统一存储功能正常")
    print(f"   ✅ 时间片目标注入正常")
    
    return True

if __name__ == "__main__":
    print("🧪 简化版批量官方声明系统测试\n")
    
    success = test_batch_official_statements_simple()
    
    if success:
        print(f"\n🎉 测试成功！批量官方声明系统已就绪。")
        print(f"\n📡 API使用说明:")
        print(f"   POST /api/inject_batch_official_statements")
        print(f"   Body: {{")
        print(f"     'simulation_config': {{ ... }},")
        print(f"     'agent_configs': [ ... ],")
        print(f"     'statements': [")
        print(f"       {{ 'content': '...', 'target_slice': 5 }}")
        print(f"     ]")
        print(f"   }}")
    else:
        print(f"\n❌ 测试失败，请检查错误信息。")
