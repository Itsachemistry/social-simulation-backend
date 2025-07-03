#!/usr/bin/env python3
"""
测试_estimate_post_stance修复是否正确工作
验证Agent和AgentController使用相同的立场映射逻辑
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.agent import Agent
from src.agent_controller import AgentController

def test_stance_mapping_consistency():
    """测试立场映射一致性"""
    print("=== 测试立场映射一致性 ===")
    
    # 创建测试Agent
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.5,  # 中立立场
        "interests": ["测试"]
    }
    agent = Agent(agent_config)
    
    # 测试帖子数据
    test_posts = [
        {"id": "post_1", "stance": 1, "content": "支持患者的帖子"},  # group=1
        {"id": "post_2", "stance": 0, "content": "中立的帖子"},      # group=0
        {"id": "post_3", "stance": 2, "content": "支持医院的帖子"},  # group=2
        {"id": "post_4", "stance": 5, "content": "异常值的帖子"},    # 异常值
    ]
    
    # 创建AgentController（用于对比）
    agent_controller = AgentController([agent_config])
    
    print("帖子立场映射测试：")
    print("原始group值 -> Agent._estimate_post_stance -> 期望映射值")
    print("-" * 50)
    
    expected_mappings = {
        1: 0.0,  # 支持患者
        0: 0.5,  # 中立
        2: 1.0,  # 支持医院
        5: 0.5   # 异常值默认中立
    }
    
    for post in test_posts:
        # 使用Agent的方法
        agent_stance = agent._estimate_post_stance(post)
        expected_stance = expected_mappings[post['stance']]
        
        print(f"group={post['stance']:2d} -> {agent_stance:.1f} -> {expected_stance:.1f}")
        
        # 验证映射正确性
        assert abs(agent_stance - expected_stance) < 0.01, f"立场映射错误: {agent_stance} vs {expected_stance}"
    
    print("✅ 立场映射一致性测试通过！")

def test_impact_calculation():
    """测试影响计算是否使用真实立场数据"""
    print("\n=== 测试影响计算 ===")
    
    # 创建测试Agent
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.8,  # 偏向支持医院
        "interests": ["测试"]
    }
    agent = Agent(agent_config)
    
    # 测试帖子：支持患者的帖子（group=1，映射为0.0）
    post = {
        "id": "test_post",
        "stance": 1,  # group=1，支持患者
        "heat": 50,
        "content": "支持患者的帖子"
    }
    
    # 计算影响
    impact = agent._calculate_post_impact(post)
    
    print(f"Agent立场: {agent.stance:.1f} (偏向支持医院)")
    print(f"帖子group: {post['stance']} (支持患者)")
    print(f"估算帖子立场: {agent._estimate_post_stance(post):.1f}")
    print(f"立场相似度: {impact['stance_similarity']:.3f}")
    print(f"情绪变化: {impact['emotion_change']:.3f}")
    print(f"置信度变化: {impact['confidence_change']:.3f}")
    
    # 验证逻辑正确性
    expected_stance = 0.0  # group=1 应该映射为 0.0
    expected_similarity = 1.0 - abs(0.8 - 0.0)  # 1.0 - 0.8 = 0.2
    
    print(f"期望立场: {expected_stance:.1f}")
    print(f"期望相似度: {expected_similarity:.3f}")
    
    assert abs(agent._estimate_post_stance(post) - expected_stance) < 0.01, "立场映射错误"
    assert abs(impact['stance_similarity'] - expected_similarity) < 0.01, "相似度计算错误"
    
    print("✅ 影响计算测试通过！")

def test_consistency_with_agent_controller():
    """测试与AgentController的一致性"""
    print("\n=== 测试与AgentController的一致性 ===")
    
    # 创建测试Agent
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.3,  # 偏向支持患者
        "interests": ["测试"]
    }
    agent = Agent(agent_config)
    
    # 创建AgentController
    agent_controller = AgentController([agent_config])
    
    # 测试帖子
    post = {
        "id": "test_post",
        "stance": 2,  # group=2，支持医院
        "heat": 50,
        "content": "支持医院的帖子"
    }
    
    # 使用Agent的方法计算相似度
    agent_stance = agent._estimate_post_stance(post)
    agent_similarity = 1.0 - abs(agent.stance - agent_stance)
    
    # 使用AgentController的方法计算相似度
    controller_similarity = agent_controller._calculate_stance_similarity(agent, post)
    
    print(f"Agent立场: {agent.stance:.1f}")
    print(f"帖子group: {post['stance']}")
    print(f"Agent估算立场: {agent_stance:.1f}")
    print(f"Agent计算相似度: {agent_similarity:.3f}")
    print(f"Controller计算相似度: {controller_similarity:.3f}")
    
    # 验证一致性
    assert abs(agent_similarity - controller_similarity) < 0.01, f"相似度计算不一致: {agent_similarity} vs {controller_similarity}"
    
    print("✅ 与AgentController一致性测试通过！")

if __name__ == "__main__":
    test_stance_mapping_consistency()
    test_impact_calculation()
    test_consistency_with_agent_controller()
    print("\n🎉 所有测试通过！_estimate_post_stance修复成功！") 