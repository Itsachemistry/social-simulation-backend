#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态阈值算法测试脚本
测试不同Agent状态和全局环境下的阈值变化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_controller import AgentController
from src.agent import Agent
from src.world_state import WorldState
import json
from datetime import datetime

def load_agent_configs():
    """加载Agent配置"""
    with open('config/agents.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['agents']

def create_test_posts():
    """创建测试帖子"""
    posts = [
        {
            "id": "post_001",
            "content": "今天天气真好，心情愉快！",
            "author_id": "user_001",
            "timestamp": datetime.now().isoformat(),
            "heat": 80,
            "likes": 50,
            "shares": 10,
            "is_event": False,
            "priority": 0,
            "emotion": 0.8
        },
        {
            "id": "post_002", 
            "content": "这个政策太不合理了，我很愤怒！",
            "author_id": "user_002",
            "timestamp": datetime.now().isoformat(),
            "heat": 60,
            "likes": 30,
            "shares": 20,
            "is_event": False,
            "priority": 0,
            "emotion": 0.2
        },
        {
            "id": "post_003",
            "content": "关于科技发展的最新消息",
            "author_id": "user_003",
            "timestamp": datetime.now().isoformat(),
            "heat": 40,
            "likes": 20,
            "shares": 5,
            "is_event": False,
            "priority": 0,
            "emotion": 0.5
        },
        {
            "id": "post_004",
            "content": "重大突发事件！需要大家关注！",
            "author_id": "leader_001",
            "timestamp": datetime.now().isoformat(),
            "heat": 95,
            "likes": 100,
            "shares": 50,
            "is_event": True,
            "priority": 1,
            "emotion": 0.3
        }
    ]
    return posts

def test_dynamic_threshold():
    """测试动态阈值算法"""
    print("🧪 开始测试动态阈值算法")
    print("=" * 50)
    
    # 1. 创建Agent控制器
    agent_configs = load_agent_configs()
    world_state = WorldState()
    agent_controller = AgentController(agent_configs, world_state)
    
    # 启用调试模式
    agent_controller._debug_threshold = True
    
    # 2. 创建测试帖子
    test_posts = create_test_posts()
    for post in test_posts:
        world_state.add_post(post)
    
    # 3. 获取所有Agent
    all_agents = []
    for agents in agent_controller.agents.values():
        all_agents.extend(agents)
    
    # 4. 测试不同场景下的阈值变化
    print("\n📊 场景1: 正常环境下的阈值")
    print("-" * 30)
    global_intensity = agent_controller.calculate_global_intensity_factor(test_posts)
    print(f"全局环境强度因子: {global_intensity:.2f}")
    
    for agent in all_agents:
        threshold = agent_controller._get_heat_threshold_for_agent(agent, global_intensity)
        print(f"{agent.agent_id} ({agent.agent_type}): {threshold}")
    
    # 5. 测试情绪变化对阈值的影响
    print("\n📊 场景2: 情绪变化对阈值的影响")
    print("-" * 30)
    
    # 选择一个Agent进行测试
    test_agent = all_agents[0]
    print(f"测试Agent: {test_agent.agent_id}")
    
    # 测试不同情绪状态
    emotion_states = [0.1, 0.3, 0.5, 0.7, 0.9]
    for emotion in emotion_states:
        test_agent.emotion = emotion
        threshold = agent_controller._get_heat_threshold_for_agent(test_agent, global_intensity)
        print(f"情绪值 {emotion:.1f}: 阈值 {threshold}")
    
    # 6. 测试置信度变化对阈值的影响
    print("\n📊 场景3: 置信度变化对阈值的影响")
    print("-" * 30)
    
    # 重置情绪
    test_agent.emotion = 0.5
    
    confidence_states = [0.1, 0.3, 0.5, 0.7, 0.9]
    for confidence in confidence_states:
        test_agent.confidence = confidence
        threshold = agent_controller._get_heat_threshold_for_agent(test_agent, global_intensity)
        print(f"置信度 {confidence:.1f}: 阈值 {threshold}")
    
    # 7. 测试全局环境强度变化
    print("\n📊 场景4: 全局环境强度变化对阈值的影响")
    print("-" * 30)
    
    # 重置状态
    test_agent.emotion = 0.5
    test_agent.confidence = 0.5
    
    intensity_factors = [0.5, 0.8, 1.0, 1.3, 1.8]
    for intensity in intensity_factors:
        threshold = agent_controller._get_heat_threshold_for_agent(test_agent, intensity)
        print(f"全局强度 {intensity:.1f}: 阈值 {threshold}")
    
    # 8. 测试性格特征的影响
    print("\n📊 场景5: 性格特征对阈值的影响")
    print("-" * 30)
    
    # 重置状态
    test_agent.emotion = 0.5
    test_agent.confidence = 0.5
    
    print(f"当前性格特征:")
    print(f"  活跃度: {test_agent.activity_level:.2f}")
    print(f"  情绪敏感度: {test_agent.emotion_sensitivity:.2f}")
    print(f"  立场坚定度: {test_agent.stance_firmness:.2f}")
    print(f"  信息渴求度: {test_agent.information_thirst:.2f}")
    print(f"  注意力持续时间: {test_agent.attention_span:.2f}")
    
    threshold = agent_controller._get_heat_threshold_for_agent(test_agent, global_intensity)
    print(f"最终阈值: {threshold}")
    
    print("\n✅ 动态阈值算法测试完成！")

def test_personalized_feed():
    """测试个性化信息流生成"""
    print("\n🧪 测试个性化信息流生成")
    print("=" * 50)
    
    # 创建Agent控制器
    agent_configs = load_agent_configs()
    world_state = WorldState()
    agent_controller = AgentController(agent_configs, world_state)
    
    # 添加测试帖子
    test_posts = create_test_posts()
    for post in test_posts:
        world_state.add_post(post)
    
    # 获取所有Agent
    all_agents = []
    for agents in agent_controller.agents.values():
        all_agents.extend(agents)
    
    # 计算全局强度
    global_intensity = agent_controller.calculate_global_intensity_factor(test_posts)
    
    # 为每个Agent生成个性化信息流
    for agent in all_agents:
        print(f"\n📱 {agent.agent_id} ({agent.agent_type}) 的个性化信息流:")
        print(f"  立场: {agent.stance:.2f}, 情绪: {agent.emotion:.2f}, 置信度: {agent.confidence:.2f}")
        
        personalized_posts = agent_controller._generate_personalized_feed(
            agent, test_posts, global_intensity
        )
        
        print(f"  筛选到 {len(personalized_posts)} 条帖子:")
        for i, post in enumerate(personalized_posts[:3]):  # 只显示前3条
            print(f"    {i+1}. 热度{post['heat']}: {post['content'][:30]}...")
        
        if len(personalized_posts) > 3:
            print(f"    ... 还有 {len(personalized_posts) - 3} 条帖子")

if __name__ == "__main__":
    test_dynamic_threshold()
    test_personalized_feed() 