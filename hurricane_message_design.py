#!/usr/bin/env python3
"""
飓风消息功能实现和集成
在Agent Controller中添加强制广播消息功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def enhance_agent_controller_for_hurricane():
    """为Agent Controller添加飓风消息处理功能"""
    
    print("=== 飓风消息功能集成方案 ===\n")
    
    print("📋 现有系统分析:")
    print("✅ 事件注入API已存在: /api/simulation/inject_event")
    print("✅ world_state.inject_event() 方法已实现")
    print("✅ information_strength=1.0 可确保高优先级")
    print("✅ is_event=True 标记特殊帖子")
    print()
    
    print("🎯 需要增强的功能:")
    print("1. 在agent_controller.py中添加强制广播处理")
    print("2. 确保飓风消息绕过概率选择，强制被所有Agent阅读")
    print("3. 添加时间片指定功能")
    print()
    
    enhancement_code = '''
# 在 agent_controller.py 中添加以下方法:

def process_hurricane_messages(self, posts, agent):
    """
    处理飓风消息（强制广播）
    飓风消息会绕过正常的个性化筛选，强制被所有Agent阅读
    
    Args:
        posts: 当前时间片的所有帖子
        agent: 当前处理的Agent
    
    Returns:
        list: 飓风消息列表
    """
    hurricane_posts = [
        post for post in posts 
        if post.get('is_hurricane', False) or 
           post.get('force_read', False) or
           (post.get('is_event', False) and post.get('priority', 0) >= 999)
    ]
    
    if hurricane_posts:
        print(f"🚨 [飓风广播] Agent {agent.agent_id} 收到 {len(hurricane_posts)} 条紧急消息")
        
        for hurricane_post in hurricane_posts:
            # 强制阅读，不受屏蔽影响
            print(f"📻 强制广播: {hurricane_post.get('content', '')[:50]}...")
            
            # 添加到已读列表
            if not hasattr(agent, 'viewed_posts'):
                agent.viewed_posts = []
            agent.viewed_posts.append(hurricane_post)
            
            # 强制情绪立场更新
            agent.update_emotion_and_stance(
                hurricane_post, 
                time_slice_index=getattr(self, 'current_time_slice', 0)
            )
            
            # 飓风消息通常不触发屏蔽（官方来源）
            if not hurricane_post.get('author_id', '').startswith('system'):
                agent.check_blocking(hurricane_post)
    
    return hurricane_posts

# 修改 update_agent_emotions 方法，在处理开始时先处理飓风消息:

def update_agent_emotions(self, posts, time_slice_index=None, llm_config=None):
    """更新智能体情绪和立场（增强版 - 支持飓风消息）"""
    
    # 保存当前时间片索引
    self.current_time_slice = time_slice_index
    
    # 提取飓风消息和普通消息
    hurricane_posts = [
        post for post in posts 
        if post.get('is_hurricane', False) or 
           post.get('force_read', False) or
           (post.get('is_event', False) and post.get('priority', 0) >= 999)
    ]
    
    normal_posts = [
        post for post in posts 
        if not (post.get('is_hurricane', False) or 
                post.get('force_read', False) or
                (post.get('is_event', False) and post.get('priority', 0) >= 999))
    ]
    
    if hurricane_posts:
        print(f"🌪️ [时间片 {time_slice_index}] 检测到 {len(hurricane_posts)} 条飓风消息")
        print(f"📊 普通帖子: {len(normal_posts)} 条")
    
    # ... 现有的Agent处理逻辑 ...
    for agent in self.agents:
        # 1. 首先强制处理飓风消息
        if hurricane_posts:
            self.process_hurricane_messages(hurricane_posts, agent)
        
        # 2. 然后正常处理普通帖子 (现有逻辑)
        if normal_posts:
            personalized_feed, post_scores = self._generate_personalized_feed(agent, normal_posts)
            # ... 现有的单次屏蔽和情绪更新逻辑 ...
    '''
    
    print("💻 集成代码示例:")
    print(enhancement_code)
    
    print("\n🔧 API增强建议:")
    api_enhancement = '''
# 在 simulation_service.py 的 inject_event 方法中添加:

def inject_hurricane_message(self, simulation_id, message_content, target_time_slice=None):
    """
    注入飓风消息（强制广播）
    
    Args:
        simulation_id: 仿真ID
        message_content: 消息内容
        target_time_slice: 目标时间片（None表示立即广播）
    """
    hurricane_data = {
        "content": f"🚨 紧急广播：{message_content}",
        "author_id": "emergency_system",
        "is_hurricane": True,
        "is_event": True,
        "force_read": True,
        "priority": 999,
        "information_strength": 1.0,
        "popularity": 999,
        "target_time_slice": target_time_slice,
        "timestamp": time.time()
    }
    
    return self.inject_event(simulation_id, hurricane_data)
    '''
    
    print(api_enhancement)
    
    print("\n🎯 使用示例:")
    usage_example = '''
# 在仿真运行中注入飓风消息:

# 方法1: 通过API
POST /api/simulation/inject_hurricane
{
    "simulation_id": "sim_123",
    "content": "超强台风逼近，请立即撤离",
    "target_time_slice": 5,
    "emotion_impact": -0.8,
    "stance_impact": 0.0
}

# 方法2: 通过代码
engine = SocialSimulationEngine()
engine.inject_hurricane_message(
    "超强台风逼近，所有海边居民请立即撤离！",
    target_time_slice=3
)

# 方法3: 立即广播
engine.broadcast_emergency(
    "紧急通知：发现危险化学品泄漏，请避开xx区域"
)
    '''
    
    print(usage_example)

def create_simple_test():
    """创建简化的测试验证"""
    
    print("\n" + "="*50)
    print("=== 飓风消息概念验证 ===")
    
    # 模拟Agent状态
    class MockAgent:
        def __init__(self, agent_id):
            self.agent_id = agent_id
            self.current_emotion = 0.0
            self.current_stance = 0.0
            self.current_confidence = 0.5
            self.viewed_posts = []
            self.blocked_user_ids = []
        
        def update_emotion_and_stance(self, post, **kwargs):
            # 简化的情绪更新
            self.current_emotion += post.get('emotion_score', 0.0) * 0.3
            self.current_stance += post.get('stance_score', 0.0) * 0.2
            print(f"   {self.agent_id} 状态更新: 情绪={self.current_emotion:.3f}, 立场={self.current_stance:.3f}")
        
        def check_blocking(self, post):
            # 简化的屏蔽检查
            pass
    
    # 创建测试Agent
    agents = [MockAgent("agent_001"), MockAgent("agent_002")]
    
    # 创建测试帖子
    normal_posts = [
        {"id": "normal_1", "content": "普通帖子", "emotion_score": 0.1, "stance_score": 0.2},
        {"id": "normal_2", "content": "另一个普通帖子", "emotion_score": -0.1, "stance_score": -0.1}
    ]
    
    hurricane_posts = [
        {
            "id": "hurricane_001",
            "content": "🚨 紧急广播：超强台风即将登陆，请所有居民立即撤离！",
            "author_id": "emergency_system",
            "is_hurricane": True,
            "force_read": True,
            "emotion_score": -0.8,
            "stance_score": 0.0,
            "priority": 999
        }
    ]
    
    all_posts = normal_posts + hurricane_posts
    
    print(f"\n📋 测试场景:")
    print(f"- 普通帖子: {len(normal_posts)} 条")
    print(f"- 飓风消息: {len(hurricane_posts)} 条")
    print(f"- 测试Agent: {len(agents)} 个")
    
    # 模拟处理流程
    for agent in agents:
        print(f"\n--- 处理 {agent.agent_id} ---")
        
        # 1. 强制处理飓风消息
        for hurricane_post in hurricane_posts:
            print(f"🚨 强制广播: {hurricane_post['content'][:50]}...")
            agent.viewed_posts.append(hurricane_post)
            agent.update_emotion_and_stance(hurricane_post)
        
        # 2. 正常处理普通帖子（简化版概率选择）
        import random
        for post in normal_posts:
            # 简化的选择概率（50%）
            if random.random() < 0.5:
                print(f"📖 阅读普通帖子: {post['content']}")
                agent.viewed_posts.append(post)
                agent.update_emotion_and_stance(post)
            else:
                print(f"⏭️ 跳过帖子: {post['content']}")
        
        print(f"📊 {agent.agent_id} 总阅读帖子数: {len(agent.viewed_posts)}")
        
        # 验证飓风消息是否被阅读
        hurricane_read = [p for p in agent.viewed_posts if p.get('is_hurricane', False)]
        print(f"✅ 飓风消息阅读数: {len(hurricane_read)}/{len(hurricane_posts)} (应为100%)")

if __name__ == "__main__":
    enhance_agent_controller_for_hurricane()
    create_simple_test()
    print("\n🌪️ 飓风消息功能分析完成！")
