#!/usr/bin/env python3
"""
使用配置文件的仿真测试（重构版，调用src标准接口）
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent_controller import AgentController
from src.world_state import WorldState
from src.time_manager import TimeSliceManager
from src.agent import Agent, RoleType
from src.services import DataLoader, flatten_posts_recursive, filter_valid_posts

def create_test_agents():
    """创建测试Agent"""
    agents = [
        Agent('agent_001', RoleType.ORDINARY_USER, 0.4, 0.1, 0.6, 0.0, 0.0, 0.5),
        Agent('agent_002', RoleType.ORDINARY_USER, 0.3, 0.3, 0.4, -0.2, -0.1, 0.3),
        Agent('agent_003', RoleType.OPINION_LEADER, 0.8, 0.2, 0.9, 0.3, 0.5, 0.7),
        Agent('agent_004', RoleType.ORDINARY_USER, 0.5, 0.0, 0.7, 0.1, 0.2, 0.6)
    ]
    return agents

def main(w_pop=0.7, k=2, save_log=False):
    print("=== 社交模拟引擎测试（重构版）===")
    print("使用src中提供的标准接口，专注于测试核心算法")
    print(f"\n[参数] w_pop={w_pop}, k={k}")
    # 1. 使用DataLoader加载原始帖子数据
    print("\n1. 加载原始帖子数据...")
    data_loader = DataLoader()
    try:
        raw_posts = data_loader.load_post_data('data/postdata.json')
        print(f"✅ 成功加载 {len(raw_posts)} 条原始帖子")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    # 2. 展开嵌套帖子
    print("\n2. 展开嵌套帖子...")
    all_posts = flatten_posts_recursive(raw_posts)
    print(f"✅ 展开后共 {len(all_posts)} 条帖子")
    # 3. 过滤有效帖子
    print("\n3. 过滤有效帖子...")
    valid_posts = filter_valid_posts(all_posts)
    print(f"✅ 过滤后剩余 {len(valid_posts)} 条有效帖子")
    if not valid_posts:
        print("没有有效的帖子数据，退出测试")
        return
    # 4. 字段标准化
    print("\n4. 字段标准化...")
    world_state = WorldState()
    normalized_posts = [world_state.normalize_post(post) for post in valid_posts]
    print(f"✅ 完成 {len(normalized_posts)} 条帖子的标准化")
    # 5. 时间片划分
    print("\n5. 时间片划分...")
    posts_per_timeslice = 30
    num_timeslices = 4
    time_manager = TimeSliceManager(normalized_posts, posts_per_timeslice)
    print(f"✅ 时间片大小: {posts_per_timeslice}")
    print(f"✅ 总时间片数: {time_manager.total_slices}")
    # 6. 创建Agent控制器
    print("\n6. 创建Agent控制器...")
    agent_controller = AgentController(world_state, time_manager, w_pop=w_pop, k=k)
    # 7. 创建测试Agent
    print("\n7. 创建测试Agent...")
    test_agents = create_test_agents()
    for agent in test_agents:
        agent_controller.add_agent(agent)
        print(f"✅ 创建Agent: {agent}")
    # 8. 运行模拟
    print("\n8. 开始模拟...")
    for timeslice in range(min(num_timeslices, time_manager.total_slices)):
        print(f"\n--- 时间片 {timeslice + 1} ---")
        for agent in agent_controller.agents:
            agent.snapshot_state()
        current_posts = time_manager.get_slice(timeslice)
        print(f"处理 {len(current_posts)} 条帖子")
        # 新增：统计每个Agent阅读的帖子数量
        agent_read_counts = {}
        agent_post_scores = {}
        # 统计每个帖子被哪些agent选中
        post_read_by_agents = {}
        # 用新流程更新情绪，并收集分数
        all_agent_scores = agent_controller.update_agent_emotions(current_posts)
        for agent in agent_controller.agents:
            # 重新统计阅读数
            personalized_feed, post_scores = agent_controller._generate_personalized_feed(agent, current_posts)
            agent_read_counts[agent.agent_id] = len(personalized_feed)
            agent_post_scores[agent.agent_id] = post_scores
            for idx, (pid, score_pop, score_rel, final_score, prob) in enumerate(post_scores):
                if pid not in post_read_by_agents:
                    post_read_by_agents[pid] = []
                if personalized_feed and any(p.get('id', p.get('post_id', 'unknown')) == pid for p in personalized_feed):
                    post_read_by_agents[pid].append((agent.agent_id, final_score, prob))
        print(f"\n时间片 {timeslice + 1} 结束，Agent状态:")
        for agent in agent_controller.agents:
            emotion_fluctuation = abs(agent.current_emotion - agent.last_emotion)
            stance_fluctuation = abs(agent.current_stance - agent.last_stance)
            total_fluctuation = emotion_fluctuation + stance_fluctuation
            print(f"  {agent.agent_id}: 情绪={agent.current_emotion:.3f}(波动{emotion_fluctuation:.3f}), "
                  f"立场={agent.current_stance:.3f}(波动{stance_fluctuation:.3f}), "
                  f"置信度={agent.current_confidence:.3f}, 总波动={total_fluctuation:.3f}, "
                  f"本时间片阅读{agent_read_counts[agent.agent_id]}条帖子")
            if agent.should_post():
                print(f"    -> 决定发帖！")
            else:
                print(f"    -> 不发帖")
        # 输出每个帖子被哪些agent选中及分数
        print(f"\n[分析] 本时间片每个帖子被选中的情况：")
        for pid, agent_list in post_read_by_agents.items():
            if agent_list:
                agent_str = ", ".join([f"{aid}(Final={fs:.3f},P={prob:.2f})" for aid, fs, prob in agent_list])
                print(f"  帖子{pid}: 被 {len(agent_list)} 个Agent选中 -> {agent_str}")
    print("\n=== 模拟完成 ===")

if __name__ == "__main__":
    main() 