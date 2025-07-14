#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试opinion_blocking屏蔽机制
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent import Agent, RoleType

def test_blocking_mechanism():
    """测试屏蔽机制"""
    print("=== 测试opinion_blocking屏蔽机制 ===\n")
    
    # 创建测试Agent
    agent_high_blocking = Agent('test_001', RoleType.ORDINARY_USER, 0.5, 0.8, 0.6, 0.0, 0.5, 0.5)  # 高屏蔽度
    agent_low_blocking = Agent('test_002', RoleType.ORDINARY_USER, 0.5, 0.2, 0.6, 0.0, 0.5, 0.5)   # 低屏蔽度
    agent_no_blocking = Agent('test_003', RoleType.ORDINARY_USER, 0.5, 0.0, 0.6, 0.0, 0.5, 0.5)    # 无屏蔽度
    
    print(f"Agent {agent_high_blocking.agent_id}: opinion_blocking={agent_high_blocking.opinion_blocking}")
    print(f"Agent {agent_low_blocking.agent_id}: opinion_blocking={agent_low_blocking.opinion_blocking}")
    print(f"Agent {agent_no_blocking.agent_id}: opinion_blocking={agent_no_blocking.opinion_blocking}")
    print()
    
    # 测试帖子
    test_posts = [
        {'user_id': 'user_001', 'stance_score': 0.6, 'content': '立场相近的帖子'},  # 差异0.1
        {'user_id': 'user_002', 'stance_score': 0.0, 'content': '立场中性的帖子'},  # 差异0.5
        {'user_id': 'user_003', 'stance_score': -0.8, 'content': '立场相反的帖子'}, # 差异1.3
        {'user_id': 'user_004', 'stance_score': 1.0, 'content': '极端立场的帖子'},  # 差异0.5
    ]
    
    agents = [agent_high_blocking, agent_low_blocking, agent_no_blocking]
    
    for i, post in enumerate(test_posts, 1):
        print(f"帖子{i}: user_id={post['user_id']}, stance_score={post['stance_score']}, content='{post['content']}'")
        stance_diff = abs(0.5 - post['stance_score'])  # Agent立场0.5
        print(f"  与Agent立场差异: {stance_diff:.1f}")
        
        for agent in agents:
            initial_blocked_count = len(agent.blocked_user_ids)
            agent.check_blocking(post)
            final_blocked_count = len(agent.blocked_user_ids)
            
            if final_blocked_count > initial_blocked_count:
                print(f"  {agent.agent_id}: 屏蔽了用户 {post['user_id']} (差异{stance_diff:.1f} > 0.7)")
            else:
                print(f"  {agent.agent_id}: 未屏蔽 (差异{stance_diff:.1f} <= 0.7 或 opinion_blocking=0)")
        print()
    
    # 显示最终屏蔽列表
    print("=== 最终屏蔽列表 ===")
    for agent in agents:
        print(f"{agent.agent_id}: 屏蔽了 {len(agent.blocked_user_ids)} 个用户 -> {agent.blocked_user_ids}")

if __name__ == "__main__":
    test_blocking_mechanism() 