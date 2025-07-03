#!/usr/bin/env python3
"""
测试信息强度权重机制和完善的置信度更新逻辑
验证：
1. strength为null的帖子被完全过滤
2. strength值作为影响权重影响状态更新
3. 立场一致/不一致对置信度的不同影响
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.agent import Agent
from src.agent_controller import AgentController
from src.world_state import WorldState

def test_strength_filtering():
    """测试信息强度过滤机制"""
    print("=== 测试信息强度过滤机制 ===")
    
    # 创建测试Agent
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.5,  # 中立立场
        "interests": ["测试"]
    }
    agent = Agent(agent_config)
    
    # 测试帖子1：strength为null（应该被过滤）
    post_null = {
        "id": "post_null",
        "strength": None,
        "stance": 1,  # 支持患者
        "heat": 50,
        "content": "strength为null的帖子"
    }
    
    # 测试帖子2：strength为1.0（应该正常处理）
    post_weak = {
        "id": "post_weak",
        "strength": 1.0,
        "stance": 1,  # 支持患者
        "heat": 50,
        "content": "strength为1.0的帖子"
    }
    
    # 测试帖子3：strength为2.0（应该产生更大影响）
    post_strong = {
        "id": "post_strong",
        "strength": 2.0,
        "stance": 1,  # 支持患者
        "heat": 50,
        "content": "strength为2.0的帖子"
    }
    
    # 测试null值过滤
    result_null = agent.update_state(post_null)
    print(f"null值帖子结果: {result_null['status']}")
    assert result_null['status'] == 'filtered_by_strength', "null值帖子应该被过滤"
    
    # 测试正常帖子处理
    result_weak = agent.update_state(post_weak)
    result_strong = agent.update_state(post_strong)
    
    print(f"weak帖子结果: {result_weak['status']}")
    print(f"strong帖子结果: {result_strong['status']}")
    
    assert result_weak['status'] == 'updated', "weak帖子应该正常处理"
    assert result_strong['status'] == 'updated', "strong帖子应该正常处理"
    
    print("✅ 信息强度过滤测试通过！")

def test_confidence_logic():
    """测试完善后的置信度更新逻辑"""
    print("\n=== 测试置信度更新逻辑 ===")
    
    # 创建测试Agent（偏向支持医院）
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.8,  # 偏向支持医院
        "interests": ["测试"]
    }
    agent = Agent(agent_config)
    
    # 记录初始置信度
    initial_confidence = agent.confidence
    
    # 测试帖子1：立场一致（支持医院，应该提升置信度）
    post_consistent = {
        "id": "post_consistent",
        "strength": 2.0,
        "stance": 2,  # 支持医院，与Agent立场一致
        "heat": 50,
        "content": "支持医院的帖子"
    }
    
    # 测试帖子2：立场不一致（支持患者，应该降低置信度）
    post_inconsistent = {
        "id": "post_inconsistent",
        "strength": 2.0,
        "stance": 1,  # 支持患者，与Agent立场不一致
        "heat": 50,
        "content": "支持患者的帖子"
    }
    
    # 处理立场一致的帖子
    result_consistent = agent.update_state(post_consistent)
    confidence_after_consistent = agent.confidence
    delta_consistent = result_consistent['delta_confidence']
    
    # 重置Agent状态
    agent.confidence = initial_confidence
    agent.viewed_posts = []
    agent.interaction_history = []
    
    # 处理立场不一致的帖子
    result_inconsistent = agent.update_state(post_inconsistent)
    confidence_after_inconsistent = agent.confidence
    delta_inconsistent = result_inconsistent['delta_confidence']
    
    print(f"初始置信度: {initial_confidence:.3f}")
    print(f"立场一致帖子影响: {delta_consistent:.3f}")
    print(f"立场不一致帖子影响: {delta_inconsistent:.3f}")
    
    # 验证逻辑正确性
    assert delta_consistent > 0, "立场一致应该提升置信度"
    assert delta_inconsistent < 0, "立场不一致应该降低置信度"
    assert abs(delta_consistent) > abs(delta_inconsistent), "提升幅度应该大于降低幅度"
    
    print("✅ 置信度更新逻辑测试通过！")

def test_strength_weight_impact():
    """测试信息强度权重对状态更新的影响"""
    print("\n=== 测试信息强度权重影响 ===")
    
    # 创建测试Agent（偏向支持医院，与测试帖子立场不同）
    agent_config = {
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.8,  # 偏向支持医院，与帖子立场不同
        "interests": ["测试"]
    }
    
    # 测试不同强度值的帖子（支持患者，与Agent立场不同）
    test_posts = [
        {"id": "post_1", "strength": 1.0, "stance": 1, "heat": 50, "content": "强度1.0"},
        {"id": "post_2", "strength": 2.0, "stance": 1, "heat": 50, "content": "强度2.0"},
        {"id": "post_3", "strength": 3.0, "stance": 1, "heat": 50, "content": "强度3.0"},
    ]
    
    impacts = []
    
    for post in test_posts:
        agent = Agent(agent_config)  # 每次创建新的Agent确保状态一致
        impact = agent._calculate_post_impact(post)
        impacts.append(impact)
        
        print(f"强度{post['strength']}: 情绪变化={impact['emotion_change']:.3f}, 置信度变化={impact['confidence_change']:.3f}")
    
    # 验证强度权重的影响
    assert abs(impacts[1]['emotion_change']) > abs(impacts[0]['emotion_change']), "强度2.0应该比1.0产生更大影响"
    assert abs(impacts[2]['emotion_change']) > abs(impacts[1]['emotion_change']), "强度3.0应该比2.0产生更大影响"
    
    print("✅ 信息强度权重影响测试通过！")

def test_agent_controller_filtering():
    """测试AgentController中的筛选逻辑"""
    print("\n=== 测试AgentController筛选逻辑 ===")
    
    # 创建AgentController
    agent_configs = [{
        "agent_id": "test_agent",
        "type": "普通用户",
        "stance": 0.5,
        "interests": ["测试"]
    }]
    
    world_state = WorldState()
    agent_controller = AgentController(agent_configs, world_state)
    
    # 创建测试帖子
    test_posts = [
        {"id": "post_null", "strength": None, "stance": 1, "heat": 50, "content": "null强度"},
        {"id": "post_weak", "strength": 1.0, "stance": 1, "heat": 30, "content": "弱强度"},
        {"id": "post_strong", "strength": 2.0, "stance": 1, "heat": 30, "content": "强强度"},
    ]
    
    # 获取Agent
    agent = list(agent_controller.agents.values())[0][0]
    
    # 测试个性化信息流生成
    personalized_posts = agent_controller._generate_personalized_feed(agent, test_posts)
    
    print(f"原始帖子数量: {len(test_posts)}")
    print(f"筛选后帖子数量: {len(personalized_posts)}")
    
    # 验证null值帖子被过滤
    null_posts = [p for p in personalized_posts if p.get('strength') is None]
    assert len(null_posts) == 0, "null强度帖子应该被过滤"
    
    # 验证排序权重
    if len(personalized_posts) >= 2:
        weight1 = personalized_posts[0].get('heat', 0) * personalized_posts[0].get('strength', 1.0)
        weight2 = personalized_posts[1].get('heat', 0) * personalized_posts[1].get('strength', 1.0)
        assert weight1 >= weight2, "应该按综合权重排序"
    
    print("✅ AgentController筛选逻辑测试通过！")

def main():
    """运行所有测试"""
    print("🧪 开始测试信息强度权重机制")
    print("=" * 50)
    
    try:
        test_strength_filtering()
        test_confidence_logic()
        test_strength_weight_impact()
        test_agent_controller_filtering()
        
        print("\n🎉 所有测试通过！")
        print("\n📋 改进总结：")
        print("1. ✅ strength为null的帖子被完全过滤")
        print("2. ✅ strength值作为影响权重影响状态更新")
        print("3. ✅ 立场一致/不一致对置信度有不同影响")
        print("4. ✅ 移除了硬性热度阈值过滤")
        print("5. ✅ 信息强度权重影响帖子排序")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 