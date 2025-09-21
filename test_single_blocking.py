#!/usr/bin/env python3
"""
单次屏蔽机制测试
验证屏蔽->跳过->移除的完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import Agent, RoleType

def test_single_blocking_mechanism():
    """测试单次屏蔽机制"""
    print("=== 单次屏蔽机制测试 ===\n")
    
    # 创建测试Agent
    agent = Agent(
        agent_id="test_agent",
        role_type=RoleType.ORDINARY_USER,
        attitude_firmness=0.5,
        opinion_blocking=0.3,
        activity_level=0.7,
        initial_emotion=0.0,
        initial_stance=0.8,  # 强支持立场
        initial_confidence=0.6
    )
    
    # 创建测试帖子序列
    test_posts = [
        {
            "id": "post_1",
            "author_id": "user_conflict",
            "content": "强烈反对立场的帖子1",
            "stance_score": -0.9,  # 强烈冲突，会触发屏蔽
            "information_strength": 0.8
        },
        {
            "id": "post_2", 
            "author_id": "user_neutral",
            "content": "中性帖子",
            "stance_score": 0.1,
            "information_strength": 0.7
        },
        {
            "id": "post_3",
            "author_id": "user_conflict",  # 同一个被屏蔽的用户
            "content": "强烈反对立场的帖子2",
            "stance_score": -0.8,
            "information_strength": 0.9
        },
        {
            "id": "post_4",
            "author_id": "user_conflict",  # 同一个用户的第三个帖子
            "content": "强烈反对立场的帖子3", 
            "stance_score": -0.7,
            "information_strength": 0.6
        }
    ]
    
    print(f"Agent初始状态:")
    print(f"- 立场: {agent.current_stance:.2f}")
    print(f"- 屏蔽倾向: {agent.opinion_blocking:.2f}")
    print(f"- 屏蔽列表: {agent.blocked_user_ids}")
    print()
    
    print("=== 模拟阅读流程 ===")
    
    for i, post in enumerate(test_posts, 1):
        print(f"\n{i}. 处理帖子 {post['id']} (作者: {post['author_id']})")
        print(f"   立场: {post['stance_score']:+.1f}")
        
        # 模拟新的单次屏蔽逻辑
        post_author = post.get('author_id')
        if post_author and post_author in agent.blocked_user_ids:
            # 单次屏蔽：跳过此帖子并从屏蔽列表中移除该用户
            agent.blocked_user_ids.remove(post_author)
            print(f"   🚫 [单次屏蔽] 跳过已屏蔽用户 {post_author} 的帖子")
            print(f"   ✅ 将用户 {post_author} 从屏蔽列表移除")
            print(f"   📝 当前屏蔽列表: {agent.blocked_user_ids}")
            continue  # 跳过，不更新任何状态
        
        # 正常处理帖子
        print(f"   📖 正常阅读帖子")
        
        # 模拟情绪立场更新（简化版）
        old_emotion = agent.current_emotion
        old_stance = agent.current_stance
        
        # 简单的情绪更新逻辑
        stance_diff = abs(agent.current_stance - post['stance_score'])
        if stance_diff > 0.5:
            agent.current_emotion -= 0.1  # 立场冲突导致负面情绪
        
        print(f"   📊 状态更新: 情绪 {old_emotion:.2f} -> {agent.current_emotion:.2f}")
        
        # 检查是否需要屏蔽（在处理完帖子后）
        old_blocked_count = len(agent.blocked_user_ids)
        agent.check_blocking(post)
        new_blocked_count = len(agent.blocked_user_ids)
        
        if new_blocked_count > old_blocked_count:
            print(f"   ⚠️  将用户 {post_author} 添加到屏蔽列表")
            print(f"   📝 当前屏蔽列表: {agent.blocked_user_ids}")
        else:
            print(f"   ✅ 未触发新屏蔽")
    
    print("\n=== 测试结果分析 ===")
    print(f"最终屏蔽列表: {agent.blocked_user_ids}")
    
    # 预期结果分析
    print("\n预期行为:")
    print("1. post_1: user_conflict被屏蔽")
    print("2. post_2: user_neutral正常处理") 
    print("3. post_3: user_conflict被跳过，从屏蔽列表移除")
    print("4. post_4: user_conflict又可以正常处理，可能再次被屏蔽")

def test_multiple_users_blocking():
    """测试多用户屏蔽场景"""
    print("\n" + "="*50)
    print("=== 多用户屏蔽测试 ===")
    
    agent = Agent(
        agent_id="multi_test_agent",
        role_type=RoleType.ORDINARY_USER,
        attitude_firmness=0.6,
        opinion_blocking=0.4,
        activity_level=0.8,
        initial_emotion=0.2,
        initial_stance=0.7,
        initial_confidence=0.5
    )
    
    posts = [
        {"id": "p1", "author_id": "user_a", "stance_score": -0.8, "information_strength": 0.8},
        {"id": "p2", "author_id": "user_b", "stance_score": -0.9, "information_strength": 0.7},
        {"id": "p3", "author_id": "user_a", "stance_score": -0.7, "information_strength": 0.9},  # user_a第二次
        {"id": "p4", "author_id": "user_c", "stance_score": 0.1, "information_strength": 0.6},
        {"id": "p5", "author_id": "user_b", "stance_score": -0.8, "information_strength": 0.8},  # user_b第二次
        {"id": "p6", "author_id": "user_a", "stance_score": -0.9, "information_strength": 0.7},  # user_a第三次
    ]
    
    print(f"Agent立场: {agent.current_stance:.2f}")
    blocked_history = []
    
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post['id']} (作者: {post['author_id']}, 立场: {post['stance_score']:+.1f})")
        
        # 单次屏蔽检查
        if post['author_id'] in agent.blocked_user_ids:
            agent.blocked_user_ids.remove(post['author_id'])
            blocked_history.append(f"跳过 {post['author_id']}")
            print(f"   🚫 跳过被屏蔽用户，移除 {post['author_id']}")
            continue
        
        # 正常处理
        blocked_history.append(f"处理 {post['author_id']}")
        print(f"   📖 正常处理")
        
        # 检查屏蔽
        old_list = agent.blocked_user_ids.copy()
        agent.check_blocking(post)
        if len(agent.blocked_user_ids) > len(old_list):
            new_blocked = [u for u in agent.blocked_user_ids if u not in old_list]
            print(f"   ⚠️  新增屏蔽: {new_blocked}")
        
        print(f"   📝 当前屏蔽: {agent.blocked_user_ids}")
    
    print(f"\n处理历史: {blocked_history}")
    print(f"最终屏蔽列表: {agent.blocked_user_ids}")

if __name__ == "__main__":
    test_single_blocking_mechanism()
    test_multiple_users_blocking()
    print("\n✅ 单次屏蔽机制测试完成!")
