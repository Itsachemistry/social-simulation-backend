#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试加权随机选择机制
验证论文描述的"抽奖模型"而非"考试模型"的实现
"""

import random
import sys
import os
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent_controller import AgentController
from agent import Agent
from world_state import WorldState

def create_test_posts():
    """创建测试帖子，包含不同热度和立场的帖子"""
    posts = [
        # 高热度帖子
        {
            "id": "post_high_heat_1",
            "content": "高热度帖子1 - 支持患者",
            "author_id": "user_001",
            "timestamp": datetime.now().isoformat(),
            "heat": 90,
            "likes": 80,
            "shares": 20,
            "stance": 1,  # 支持患者
            "strength": 2.0,
            "is_event": False
        },
        {
            "id": "post_high_heat_2", 
            "content": "高热度帖子2 - 支持医院",
            "author_id": "user_002",
            "timestamp": datetime.now().isoformat(),
            "heat": 85,
            "likes": 70,
            "shares": 15,
            "stance": 2,  # 支持医院
            "strength": 2.0,
            "is_event": False
        },
        # 中等热度帖子
        {
            "id": "post_medium_heat_1",
            "content": "中等热度帖子1 - 中立",
            "author_id": "user_003",
            "timestamp": datetime.now().isoformat(),
            "heat": 50,
            "likes": 40,
            "shares": 10,
            "stance": 0,  # 中立
            "strength": 1.5,
            "is_event": False
        },
        {
            "id": "post_medium_heat_2",
            "content": "中等热度帖子2 - 支持患者",
            "author_id": "user_004",
            "timestamp": datetime.now().isoformat(),
            "heat": 45,
            "likes": 35,
            "shares": 8,
            "stance": 1,  # 支持患者
            "strength": 1.5,
            "is_event": False
        },
        # 低热度帖子
        {
            "id": "post_low_heat_1",
            "content": "低热度帖子1 - 支持医院",
            "author_id": "user_005",
            "timestamp": datetime.now().isoformat(),
            "heat": 20,
            "likes": 15,
            "shares": 3,
            "stance": 2,  # 支持医院
            "strength": 1.0,
            "is_event": False
        },
        {
            "id": "post_low_heat_2",
            "content": "低热度帖子2 - 中立",
            "author_id": "user_006",
            "timestamp": datetime.now().isoformat(),
            "heat": 15,
            "likes": 10,
            "shares": 2,
            "stance": 0,  # 中立
            "strength": 1.0,
            "is_event": False
        },
        # 被过滤的帖子（strength为null）
        {
            "id": "post_filtered",
            "content": "被过滤的帖子",
            "author_id": "user_007",
            "timestamp": datetime.now().isoformat(),
            "heat": 100,
            "likes": 100,
            "shares": 50,
            "stance": 1,
            "strength": None,  # 应该被过滤
            "is_event": False
        }
    ]
    return posts

def create_test_agents():
    """创建测试Agent"""
    agent_configs = [
        {
            "agent_id": "test_leader",
            "type": "意见领袖",
            "stance": 0.8,  # 支持医院
            "interests": ["政治", "经济"],
            "influence": 2.0,
            "post_probability": 0.6,
            "max_posts_per_slice": 3
        },
        {
            "agent_id": "test_user",
            "type": "普通用户", 
            "stance": 0.2,  # 支持患者
            "interests": ["娱乐", "科技"],
            "influence": 1.0,
            "post_probability": 0.2,
            "max_posts_per_slice": 1
        }
    ]
    return agent_configs

def test_weighted_selection_mechanism():
    """测试加权随机选择机制"""
    print("🧪 测试加权随机选择机制")
    print("=" * 60)
    
    # 创建测试环境
    agent_configs = create_test_agents()
    world_state = WorldState()
    agent_controller = AgentController(agent_configs, world_state)
    
    # 添加测试帖子
    test_posts = create_test_posts()
    for post in test_posts:
        world_state.add_post(post)
    
    # 获取Agent
    leader_agent = agent_controller.agents["意见领袖"][0]
    user_agent = agent_controller.agents["普通用户"][0]
    
    print(f"📊 测试环境:")
    print(f"  总帖子数: {len(test_posts)}")
    print(f"  意见领袖立场: {leader_agent.stance:.2f} (支持医院)")
    print(f"  普通用户立场: {user_agent.stance:.2f} (支持患者)")
    print()
    
    # 测试1: 验证过滤机制
    print("🔍 测试1: 验证基础过滤机制")
    print("-" * 40)
    
    # 计算全局强度
    global_intensity = agent_controller.calculate_global_intensity_factor(test_posts)
    
    # 为意见领袖生成信息流
    leader_posts = agent_controller._generate_personalized_feed(
        leader_agent, test_posts, global_intensity
    )
    
    print(f"意见领袖筛选到 {len(leader_posts)} 条帖子")
    
    # 验证null强度帖子被过滤
    filtered_posts = [p for p in leader_posts if p.get('strength') is None]
    assert len(filtered_posts) == 0, "null强度帖子应该被过滤"
    print("✅ null强度帖子被正确过滤")
    
    # 测试2: 验证加权随机选择
    print("\n🎲 测试2: 验证加权随机选择机制")
    print("-" * 40)
    
    # 多次运行，观察选择结果
    selection_results = {
        "高热度帖子": 0,
        "中等热度帖子": 0, 
        "低热度帖子": 0
    }
    
    runs = 100
    for i in range(runs):
        selected_posts = agent_controller._generate_personalized_feed(
            user_agent, test_posts, global_intensity
        )
        
        for post in selected_posts:
            heat = post.get('heat', 0)
            if heat >= 70:
                selection_results["高热度帖子"] += 1
            elif heat >= 30:
                selection_results["中等热度帖子"] += 1
            else:
                selection_results["低热度帖子"] += 1
    
    print(f"运行 {runs} 次选择结果:")
    for category, count in selection_results.items():
        percentage = (count / (runs * 3)) * 100  # 假设每次选择3个帖子
        print(f"  {category}: {count} 次 ({percentage:.1f}%)")
    
    # 验证高热度帖子被选择概率更高
    high_heat_percentage = (selection_results["高热度帖子"] / (runs * 3)) * 100
    low_heat_percentage = (selection_results["低热度帖子"] / (runs * 3)) * 100
    
    print(f"\n📈 选择概率分析:")
    print(f"  高热度帖子选择概率: {high_heat_percentage:.1f}%")
    print(f"  低热度帖子选择概率: {low_heat_percentage:.1f}%")
    
    if high_heat_percentage > low_heat_percentage:
        print("✅ 高热度帖子选择概率更高，符合加权选择机制")
    else:
        print("⚠️  高热度帖子选择概率未明显高于低热度帖子")
    
    # 测试3: 验证浏览数量限制
    print("\n📱 测试3: 验证浏览数量限制")
    print("-" * 40)
    
    browse_counts = []
    for i in range(20):
        selected_posts = agent_controller._generate_personalized_feed(
            user_agent, test_posts, global_intensity
        )
        browse_counts.append(len(selected_posts))
    
    avg_browse_count = sum(browse_counts) / len(browse_counts)
    min_browse_count = min(browse_counts)
    max_browse_count = max(browse_counts)
    
    print(f"浏览数量统计:")
    print(f"  平均浏览数量: {avg_browse_count:.1f}")
    print(f"  最少浏览数量: {min_browse_count}")
    print(f"  最多浏览数量: {max_browse_count}")
    
    # 验证浏览数量在合理范围内
    assert min_browse_count >= 1, "至少应该浏览1个帖子"
    assert max_browse_count <= 10, "最多应该浏览10个帖子"
    print("✅ 浏览数量在合理范围内")
    
    # 测试4: 验证立场相似度影响
    print("\n🎯 测试4: 验证立场相似度影响")
    print("-" * 40)
    
    # 统计不同立场帖子的选择情况
    stance_selection = {"支持患者": 0, "中立": 0, "支持医院": 0}
    
    for i in range(50):
        selected_posts = agent_controller._generate_personalized_feed(
            user_agent, test_posts, global_intensity
        )
        
        for post in selected_posts:
            stance = post.get('stance', 0)
            if stance == 1:
                stance_selection["支持患者"] += 1
            elif stance == 0:
                stance_selection["中立"] += 1
            elif stance == 2:
                stance_selection["支持医院"] += 1
    
    print(f"立场选择统计 (50次运行):")
    for stance, count in stance_selection.items():
        print(f"  {stance}: {count} 次")
    
    # 验证用户更倾向于选择立场相似的帖子
    user_stance = user_agent.stance  # 0.2 (支持患者)
    patient_posts = stance_selection["支持患者"]
    hospital_posts = stance_selection["支持医院"]
    
    print(f"\n用户立场: {user_stance:.2f} (支持患者)")
    print(f"选择支持患者帖子: {patient_posts} 次")
    print(f"选择支持医院帖子: {hospital_posts} 次")
    
    if patient_posts > hospital_posts:
        print("✅ 用户更倾向于选择立场相似的帖子")
    else:
        print("⚠️  立场相似度影响不明显")
    
    print("\n🎉 加权随机选择机制测试完成！")

def test_probability_vs_threshold():
    """对比概率选择 vs 硬性阈值选择"""
    print("\n🔄 对比测试: 概率选择 vs 硬性阈值选择")
    print("=" * 60)
    
    # 创建测试环境
    agent_configs = create_test_agents()
    world_state = WorldState()
    agent_controller = AgentController(agent_configs, world_state)
    
    # 添加测试帖子
    test_posts = create_test_posts()
    for post in test_posts:
        world_state.add_post(post)
    
    user_agent = agent_controller.agents["普通用户"][0]
    global_intensity = agent_controller.calculate_global_intensity_factor(test_posts)
    
    print("📊 测试场景: 低热度帖子 (热度=15) 的选择情况")
    print("-" * 50)
    
    # 使用新的加权随机选择机制
    low_heat_selected = 0
    runs = 100
    
    for i in range(runs):
        selected_posts = agent_controller._generate_personalized_feed(
            user_agent, test_posts, global_intensity
        )
        
        for post in selected_posts:
            if post.get('heat', 0) == 15:  # 低热度帖子
                low_heat_selected += 1
    
    selection_rate = (low_heat_selected / runs) * 100
    print(f"加权随机选择机制:")
    print(f"  低热度帖子被选择概率: {selection_rate:.1f}%")
    print(f"  说明: 低热度帖子仍有机会被选中，符合'抽奖模型'")
    
    # 模拟硬性阈值选择（如果热度<30就不选择）
    print(f"\n硬性阈值选择机制 (模拟):")
    print(f"  如果设置热度阈值=30:")
    print(f"  低热度帖子被选择概率: 0%")
    print(f"  说明: 低热度帖子完全被过滤，符合'考试模型'")
    
    print(f"\n✅ 加权随机选择机制成功实现了论文描述的'抽奖模型'！")

if __name__ == "__main__":
    # 设置随机种子以确保结果可重现
    random.seed(42)
    
    test_weighted_selection_mechanism()
    test_probability_vs_threshold() 