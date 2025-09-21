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
from src.services import DataLoader, flatten_posts_recursive, filter_valid_posts, generate_context, make_prompt
from datetime import datetime, timedelta

def create_test_agents():
    """创建测试Agent"""
    agents = [
        Agent('agent_001', RoleType.ORDINARY_USER, 0.4, 0.1, 0.6, 0.0, 0.0, 0.5),
        Agent('agent_002', RoleType.ORDINARY_USER, 0.3, 0.3, 0.8, -0.2, -0.1, 0.3),
        Agent('agent_003', RoleType.OPINION_LEADER, 0.8, 0.2, 0.9, 0.3, 0.5, 0.7),
        Agent('agent_004', RoleType.ORDINARY_USER, 0.5, 0.0, 0.7, 0.1, 0.2, 0.6)
    ]
    
    # 暂时不配置LLM，专注于完善prompt模板
    # for agent in agents:
    #     agent.configure_llm(
    #         api_key="test_key",
    #         endpoint="https://api.openai.com/v1/chat/completions",
    #         model="gpt-3.5-turbo"
    #     )
    
    return agents

def simulate_leader_briefing_interaction(leader, macro_summary, time_slice_index):
    # 构造简报帖子
    briefing_post = {
        'id': f'briefing_{time_slice_index}',
        'content': f"简报：本时间片全体平均情绪={macro_summary['average_emotion']:.2f}，平均立场={macro_summary['average_stance']:.2f}",
        'emotion_score': macro_summary['average_emotion'],
        'stance_score': macro_summary['average_stance'],
        'information_strength': 1.0
    }
    # leader用轻推算法（假设有apply_environmental_nudge方法）
    if hasattr(leader, 'apply_environmental_nudge'):
        leader.apply_environmental_nudge({
            'average_stance_score': macro_summary['average_stance'],
            'average_emotion_score': macro_summary['average_emotion']
        })
    else:
        leader.update_emotion_and_stance(briefing_post, time_slice_index=time_slice_index)
    return briefing_post

def main(w_pop=0.7, k=2, save_log=False):
    print("=== 社交模拟引擎测试（重构版）===")
    print("使用src中提供的标准接口，专注于测试核心算法")
    print(f"\n[参数] w_pop={w_pop}, k={k}")
    
    # 存储Agent生成的帖子
    agent_generated_posts = []
    
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
    num_timeslices = 4  # 恢复4个时间片测试发帖流程
    time_manager = TimeSliceManager(normalized_posts, posts_per_timeslice)
    print(f"✅ 时间片大小: {posts_per_timeslice}")
    print(f"✅ 总时间片数: {time_manager.total_slices}")
    print(f"✅ 本次测试运行: {num_timeslices} 个时间片")
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
    # 读取prompt模板
    with open('data/agent_prompt_template.txt', 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    for timeslice in range(min(num_timeslices, time_manager.total_slices)):
        print(f"\n--- 时间片 {timeslice + 1} ---")
        for agent in agent_controller.agents:
            agent.snapshot_state()
        current_posts = time_manager.get_slice(timeslice)
        print(f"处理 {len(current_posts)} 条帖子")
        # 新增：统计每个Agent阅读的帖子数量
        agent_read_counts = {}
        agent_post_scores = {}
        post_read_by_agents = {}
        all_agent_scores = agent_controller.update_agent_emotions(current_posts)
        for agent in agent_controller.agents:
            personalized_feed, post_scores = agent_controller._generate_personalized_feed(agent, current_posts)
            agent_read_counts[agent.agent_id] = len(personalized_feed)
            agent_post_scores[agent.agent_id] = post_scores
            for idx, (pid, score_pop, score_rel, final_score, prob) in enumerate(post_scores):
                if pid not in post_read_by_agents:
                    post_read_by_agents[pid] = []
                if personalized_feed and any(p.get('id', p.get('post_id', 'unknown')) == pid for p in personalized_feed):
                    post_read_by_agents[pid].append((agent.agent_id, final_score, prob))
        # === 新增：宏观统计简报 ===
        macro_summary = agent_controller.compute_macro_summary()
        print(f"[宏观简报] {macro_summary}")
        # === 新增：leader与简报互动 ===
        briefing_post, leader_statuses = agent_controller.leader_read_briefing(timeslice)
        for leader_id, leader_status in leader_statuses:
            print(f"[Leader] {leader_id} 读简报后状态: {leader_status}")
        
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
                print(f"       情绪波动: {abs(agent.current_emotion - agent.last_emotion):.3f}")
                print(f"       立场波动: {abs(agent.current_stance - agent.last_stance):.3f}")
                
                # 模拟LLM调用生成文本内容
                try:
                    # 使用现有的generate_text方法（跳过LLM调用，使用模拟内容）
                    generated_content = agent.generate_text(skip_llm=True)
                    print(f"    [Generated Content] {generated_content}")
                    
                    # 构造标准格式的帖子JSON（启用LLM标注以保持一致性）
                    post_json = agent_controller.build_post_json(
                        agent, 
                        generated_content, 
                        current_posts, 
                        use_llm_annotation=True  # 启用LLM标注
                    )
                    print(f"    [Post JSON] {post_json}")
                    
                    # 将生成的帖子添加到存储列表
                    agent_generated_posts.append({
                        'timeslice': timeslice + 1,
                        'agent_id': agent.agent_id,
                        'post_data': post_json,
                        'agent_state_when_posting': {
                            'emotion': agent.current_emotion,
                            'stance': agent.current_stance,
                            'confidence': agent.current_confidence
                        }
                    })
                    
                    # 检查帖子JSON的关键字段是否完整
                    required_fields = ['id', 'mid', 'author_id', 'content', 't']
                    missing_fields = [f for f in required_fields if f not in post_json]
                    if missing_fields:
                        print(f"    [警告] 帖子JSON缺少字段: {missing_fields}")
                    else:
                        print(f"    [验证] 帖子JSON格式完整 ✅")
                        
                except Exception as e:
                    print(f"    [错误] 发帖流程失败: {e}")
            else:
                print(f"    -> 不发帖")
        # 新增：输出每个agent本时间片实际阅读的帖子数
        print("[阅读统计] 本时间片每个agent实际阅读的帖子数：")
        for agent in agent_controller.agents:
            print(f"  {agent.agent_id}: {len(getattr(agent, 'viewed_posts', []))} 条")
        print(f"\n[分析] 本时间片每个帖子被选中的情况：")
        for pid, agent_list in post_read_by_agents.items():
            if agent_list:
                agent_str = ", ".join([f"{aid}(Final={fs:.3f},P={prob:.2f})" for aid, fs, prob in agent_list])
                print(f"  帖子{pid}: 被 {len(agent_list)} 个Agent选中 -> {agent_str}")
    
    print("\n=== 模拟完成 ===")
    
    # 总结Agent生成的帖子
    if agent_generated_posts:
        print(f"\n📝 Agent生成帖子统计:")
        print(f"   总共生成 {len(agent_generated_posts)} 条帖子")
        
        # 按时间片分组统计
        from collections import defaultdict
        posts_by_timeslice = defaultdict(list)
        for post_record in agent_generated_posts:
            posts_by_timeslice[post_record['timeslice']].append(post_record)
        
        for ts, posts_in_ts in posts_by_timeslice.items():
            print(f"\n   时间片 {ts}: {len(posts_in_ts)} 条帖子")
            for post_record in posts_in_ts:
                post_data = post_record['post_data']
                agent_state = post_record['agent_state_when_posting']
                print(f"     - {post_record['agent_id']}: {post_data['content'][:50]}...")
                print(f"       ID: {post_data['id']}, 父帖: {post_data.get('pid', 'None')}")
                print(f"       发帖时状态: 情绪={agent_state['emotion']:.3f}, 立场={agent_state['stance']:.3f}")
        
        # 保存Agent生成的帖子到文件
        import json
        with open('agent_generated_posts.json', 'w', encoding='utf-8') as f:
            json.dump(agent_generated_posts, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Agent生成的帖子已保存到: agent_generated_posts.json")
        
        # 验证帖子数据格式
        print(f"\n🔍 数据格式验证:")
        sample_post = agent_generated_posts[0]['post_data']
        required_fields = ['id', 'mid', 'author_id', 'content', 't']
        for field in required_fields:
            if field in sample_post:
                print(f"   ✅ {field}: {sample_post[field]}")
            else:
                print(f"   ❌ 缺少字段: {field}")
    else:
        print(f"\n📝 本次模拟中没有Agent决定发帖")

if __name__ == "__main__":
    import sys
    with open('test_with_config_output.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        main() 