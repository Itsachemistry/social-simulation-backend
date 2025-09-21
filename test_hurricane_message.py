#!/usr/bin/env python3
"""
飓风消息功能简化测试
直接测试Agent Controller的飓风消息处理功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent_controller import AgentController
from src.world_state import WorldState
from src.agent import Agent

def test_hurricane_message_integration():
    """测试飓风消息集成功能"""
    
    print("=== 飓风消息功能集成测试 ===\n")
    
    # 1. 创建基础组件
    world_state = WorldState()
    agent_controller = AgentController(world_state, None)
    
    # 2. 创建测试Agent
    test_agents = [
        {
            "agent_id": "citizen_001",
            "role_type": "ordinary_user",
            "attitude_firmness": 0.5,
            "opinion_blocking": 0.3,
            "activity_level": 0.7,
            "initial_emotion": 0.0,
            "initial_stance": 0.2,
            "initial_confidence": 0.5
        },
        {
            "agent_id": "leader_001", 
            "role_type": "opinion_leader",
            "attitude_firmness": 0.8,
            "opinion_blocking": 0.2,
            "activity_level": 0.9,
            "initial_emotion": 0.1,
            "initial_stance": 0.0,
            "initial_confidence": 0.8
        }
    ]
    
    # 添加Agent到控制器
    for agent_config in test_agents:
        agent = Agent.from_dict(agent_config)
        agent_controller.add_agent(agent)
    
    print(f"✅ 创建了 {len(agent_controller.agents)} 个测试Agent")
    
    # 3. 创建测试帖子（包含飓风消息）
    test_posts = [
        # 普通帖子
        {
            "id": "normal_001",
            "content": "今天天气不错，适合出门散步",
            "author_id": "user_123",
            "popularity": 50,
            "emotion_score": 0.3,
            "stance_score": 0.1,
            "information_strength": 0.5
        },
        {
            "id": "normal_002", 
            "content": "最近物价上涨太快了，生活压力很大",
            "author_id": "user_456",
            "popularity": 120,
            "emotion_score": -0.4,
            "stance_score": -0.3,
            "information_strength": 0.7
        },
        # 飓风消息（强制广播）
        {
            "id": "hurricane_001",
            "content": "🚨 紧急广播：超强台风'天鹅'即将于今晚登陆，请沿海地区所有居民立即撤离到安全地带！",
            "author_id": "emergency_system",
            "is_hurricane": True,
            "force_read": True,
            "is_event": True,
            "priority": 999,
            "popularity": 9999,
            "emotion_score": -0.8,
            "stance_score": 0.0,
            "information_strength": 1.0
        },
        {
            "id": "hurricane_002",
            "content": "📢 官方通知：台风紧急避难所已开放，地址：市体育馆、各区文化中心。请携带身份证件和必需品。",
            "author_id": "disaster_relief_center",
            "is_hurricane": True,
            "force_read": True,
            "is_event": True,
            "priority": 999,
            "popularity": 8888,
            "emotion_score": 0.2,
            "stance_score": 0.5,
            "information_strength": 1.0
        }
    ]
    
    print(f"📋 准备测试帖子:")
    normal_count = len([p for p in test_posts if not p.get('is_hurricane', False)])
    hurricane_count = len([p for p in test_posts if p.get('is_hurricane', False)])
    print(f"  - 普通帖子: {normal_count} 条")
    print(f"  - 飓风消息: {hurricane_count} 条")
    
    # 4. 执行处理并观察结果
    print(f"\n--- 开始处理时间片 0 ---")
    
    # 记录处理前状态
    print("📊 处理前Agent状态:")
    for agent in agent_controller.agents:
        print(f"  {agent.agent_id}: 情绪={agent.current_emotion:.3f}, 立场={agent.current_stance:.3f}, 置信度={agent.current_confidence:.3f}")
    
    # 调用更新方法
    try:
        agent_controller.update_agent_emotions(test_posts, time_slice_index=0)
        
        # 检查处理结果
        print(f"\n📊 处理后Agent状态:")
        for agent in agent_controller.agents:
            print(f"  {agent.agent_id}: 情绪={agent.current_emotion:.3f}, 立场={agent.current_stance:.3f}, 置信度={agent.current_confidence:.3f}")
            
            # 检查已读帖子
            viewed_posts = getattr(agent, 'viewed_posts', [])
            print(f"    已读帖子数: {len(viewed_posts)}")
            
            # 验证飓风消息是否被阅读
            hurricane_read = [p for p in viewed_posts if p.get('is_hurricane', False)]
            hurricane_total = len([p for p in test_posts if p.get('is_hurricane', False)])
            
            print(f"    飓风消息阅读: {len(hurricane_read)}/{hurricane_total} ({'✅ 全部' if len(hurricane_read) == hurricane_total else '❌ 缺失'})")
            
            # 显示阅读的帖子详情
            for i, post in enumerate(viewed_posts):
                post_type = "🚨 飓风" if post.get('is_hurricane', False) else "📰 普通"
                print(f"    读取{i+1}: {post_type} - {post.get('content', '')[:30]}...")
        
        print(f"\n✅ 飓风消息功能测试完成!")
        
        # 5. 功能验证总结
        print(f"\n=== 功能验证总结 ===")
        total_agents = len(agent_controller.agents)
        hurricane_posts_count = len([p for p in test_posts if p.get('is_hurricane', False)])
        
        successful_agents = 0
        for agent in agent_controller.agents:
            viewed_posts = getattr(agent, 'viewed_posts', [])
            hurricane_read = [p for p in viewed_posts if p.get('is_hurricane', False)]
            if len(hurricane_read) == hurricane_posts_count:
                successful_agents += 1
        
        success_rate = (successful_agents / total_agents) * 100 if total_agents > 0 else 0
        print(f"📈 飓风消息到达率: {successful_agents}/{total_agents} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("✅ 飓风消息功能运行正常 - 所有Agent都收到了紧急广播")
            return True
        else:
            print("❌ 飓风消息功能存在问题 - 部分Agent未收到紧急广播")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_hurricane_message_integration()
    if success:
        print("\n🌪️ 飓风消息功能集成成功!")
    else:
        print("\n⚠️ 飓风消息功能需要进一步调试")
