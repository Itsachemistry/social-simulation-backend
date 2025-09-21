#!/usr/bin/env python3
"""
Blocking Mechanism 测试脚本
验证用户屏蔽功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import Agent, RoleType
from src.agent_controller import AgentController

def test_blocking_mechanism():
    """测试屏蔽机制"""
    print("=== Blocking Mechanism 测试 ===\n")
    
    # 创建一个具有较高屏蔽倾向的测试Agent
    test_agent = Agent(
        agent_id="test_agent",
        role_type=RoleType.ORDINARY_USER,
        attitude_firmness=0.8,
        opinion_blocking=0.5,  # 较高的屏蔽倾向
        activity_level=0.7,
        initial_emotion=0.2,
        initial_stance=0.8,  # 强烈支持立场
        initial_confidence=0.7
    )
    
    print(f"测试Agent状态:")
    print(f"- Agent ID: {test_agent.agent_id}")
    print(f"- 当前立场: {test_agent.current_stance:.2f}")
    print(f"- 屏蔽倾向: {test_agent.opinion_blocking:.2f}")
    print(f"- 初始屏蔽列表: {test_agent.blocked_user_ids}")
    print()
    
    # 创建测试帖子（不同立场）
    test_posts = [
        {
            "id": "post_1",
            "author_id": "user_001",
            "content": "支持立场的帖子",
            "stance_score": 0.9,  # 与Agent立场相近
            "information_strength": 0.8
        },
        {
            "id": "post_2", 
            "author_id": "user_002",
            "content": "中性立场的帖子",
            "stance_score": 0.0,  # 中性立场
            "information_strength": 0.7
        },
        {
            "id": "post_3",
            "author_id": "user_003", 
            "content": "强烈反对立场的帖子",
            "stance_score": -0.9,  # 与Agent立场强烈冲突
            "information_strength": 0.9
        },
        {
            "id": "post_4",
            "author_id": "user_004",
            "content": "另一个反对立场帖子", 
            "stance_score": -0.8,  # 与Agent立场冲突
            "information_strength": 0.6
        }
    ]
    
    print("测试帖子:")
    for post in test_posts:
        print(f"- {post['id']}: 立场={post['stance_score']:+.1f}, 作者={post['author_id']}")
    print()
    
    # 测试屏蔽逻辑
    print("=== 测试屏蔽逻辑 ===")
    for i, post in enumerate(test_posts):
        print(f"\n{i+1}. 处理帖子 {post['id']}:")
        print(f"   - 帖子立场: {post['stance_score']:+.2f}")
        print(f"   - Agent立场: {test_agent.current_stance:+.2f}")
        
        stance_diff = abs(test_agent.current_stance - post['stance_score'])
        print(f"   - 立场差异: {stance_diff:.2f}")
        
        # 调用屏蔽检查
        old_blocked_count = len(test_agent.blocked_user_ids)
        test_agent.check_blocking(post)
        new_blocked_count = len(test_agent.blocked_user_ids)
        
        if new_blocked_count > old_blocked_count:
            print(f"   ✅ 用户 {post['author_id']} 被屏蔽 (立场差异 {stance_diff:.2f} > 0.7)")
        else:
            print(f"   ⭕ 用户 {post['author_id']} 未被屏蔽 (立场差异 {stance_diff:.2f} <= 0.7)")
    
    print(f"\n最终屏蔽列表: {test_agent.blocked_user_ids}")
    
    # 测试信息流过滤
    print("\n=== 测试信息流过滤 ===")
    
    # 模拟过滤逻辑（不需要完整的AgentController）
    filtered_posts = []
    for post in test_posts:
        if post.get("author_id") not in test_agent.blocked_user_ids:
            filtered_posts.append(post)
            print(f"✅ 帖子 {post['id']} (作者: {post['author_id']}) 通过过滤")
        else:
            print(f"🚫 帖子 {post['id']} (作者: {post['author_id']}) 被屏蔽过滤")
    
    print(f"\n过滤结果:")
    print(f"- 原始帖子数: {len(test_posts)}")
    print(f"- 过滤后帖子数: {len(filtered_posts)}")
    print(f"- 被屏蔽帖子数: {len(test_posts) - len(filtered_posts)}")
    
    # 验证屏蔽机制的有效性
    print("\n=== 屏蔽机制有效性验证 ===")
    if len(test_agent.blocked_user_ids) > 0:
        print("✅ 屏蔽机制正常工作 - 检测到立场冲突并添加了屏蔽用户")
        print(f"   屏蔽条件: 立场差异 > 0.7 且 opinion_blocking > 0")
        print(f"   当前设置: opinion_blocking = {test_agent.opinion_blocking}")
    else:
        print("⚠️  屏蔽机制可能未生效 - 没有用户被屏蔽")
    
    if len(filtered_posts) < len(test_posts):
        print("✅ 信息流过滤正常工作 - 被屏蔽用户的帖子被过滤掉")
    else:
        print("⚠️  信息流过滤可能未生效 - 所有帖子都通过了过滤")

def test_different_blocking_levels():
    """测试不同屏蔽等级的效果"""
    print("\n" + "="*50)
    print("=== 不同屏蔽等级测试 ===")
    
    blocking_levels = [0.0, 0.2, 0.5, 0.8]
    
    # 固定的冲突帖子
    conflict_post = {
        "id": "conflict_post",
        "author_id": "conflicting_user", 
        "stance_score": -0.9,  # 强烈冲突
        "information_strength": 0.8
    }
    
    for blocking_level in blocking_levels:
        print(f"\n--- 测试 opinion_blocking = {blocking_level} ---")
        
        test_agent = Agent(
            agent_id=f"agent_blocking_{blocking_level}",
            role_type=RoleType.ORDINARY_USER,
            attitude_firmness=0.5,
            opinion_blocking=blocking_level,
            activity_level=0.7,
            initial_emotion=0.0,
            initial_stance=0.8,  # 强支持立场
            initial_confidence=0.6
        )
        
        print(f"Agent立场: {test_agent.current_stance:+.1f}")
        print(f"帖子立场: {conflict_post['stance_score']:+.1f}")
        print(f"立场差异: {abs(test_agent.current_stance - conflict_post['stance_score']):.2f}")
        
        # 测试屏蔽
        old_count = len(test_agent.blocked_user_ids)
        test_agent.check_blocking(conflict_post)
        new_count = len(test_agent.blocked_user_ids)
        
        if new_count > old_count:
            print(f"结果: ✅ 用户被屏蔽")
        else:
            print(f"结果: ⭕ 用户未被屏蔽")

if __name__ == "__main__":
    test_blocking_mechanism()
    test_different_blocking_levels()
    print("\n测试完成!")
