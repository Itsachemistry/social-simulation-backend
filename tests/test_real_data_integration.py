# 使用方法：
# 1. 启动虚拟环境（Windows）：
#    .\venv\Scripts\activate
# 2. 运行测试脚本：
#    python tests/test_real_data_integration.py
#    （或用pytest: pytest -s tests/test_real_data_integration.py）

import json
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.world_state import WorldState
from src.agent_controller import AgentController
from src.time_manager import TimeSliceManager

if not hasattr(sys.modules[__name__], "_stdout_redirected"):
    setattr(sys.modules[__name__], "_stdout_redirected", True)
    sys.stdout = open("real_data_integration_test_output.txt", "w", encoding="utf-8")

# 背景说明：
# 本测试围绕"医生将纱布留置在患者体内"事件展开，数据为网友在事件发展过程中的表态、站队、争吵。
# 目标：验证真实数据驱动下，系统能否正确完成帖子导入、时间片划分、agent推送组成功能、状态更新等核心流程。

def load_real_posts(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flat_posts = []
    def flatten(posts):
        for post in posts:
            # 处理时间戳
            if 't' in post:
                try:
                    post['timestamp'] = datetime.utcfromtimestamp(int(post['t'])).isoformat()
                except Exception:
                    post['timestamp'] = str(post['t'])
            # group->stance
            if 'group' in post:
                post['stance'] = post['group']
            flat_posts.append(post)
            if 'children' in post and post['children']:
                flatten(post['children'])
    flatten(data if isinstance(data, list) else [data])
    return flat_posts

def load_agents(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        agents = json.load(f)
    return agents['agents']

def preprocess_post(post):
    # 立场映射：1=支持患者(-1.0), 0=中立(0.0), 2=支持医院(1.0)
    stance_map = {1: -1.0, 0: 0.0, 2: 1.0}
    post['stance_score'] = stance_map.get(post.get('group', 0), 0.0)
    
    # 信息强度字段适配
    post['information_strength'] = post.get('strength', 1.0)
    
    # 情绪映射：正面(0.8), 负面(-0.8), 中性(0.0)
    emotion_map = {'正面': 0.8, '负面': -0.8, '中性': 0.0}
    post['emotion'] = emotion_map.get(post.get('coarse_emotion', '中性'), 0.0)
    
    # 情绪强度：基于情绪绝对值
    post['emotion_intensity'] = abs(post['emotion'])
    
    # 用户ID、帖子ID适配
    post['user_id'] = post.get('uid', '')
    post['post_id'] = post.get('id', '')
    return post

def test_real_data_integration():
    # 1. 加载真实数据
    posts = load_real_posts('data/data/3weibo_data_index_group_importance_withvirtual.json')
    posts = [preprocess_post(post) for post in posts]
    print(f"加载帖子总数: {len(posts)}")
    # 2. 加载agent配置
    agents = load_agents('config/agents.json')
    print(f"加载Agent总数: {len(agents)}")
    # 3. 导入WorldState
    world_state = WorldState()
    valid_count = 0
    for post in posts:
        try:
            world_state.add_post(post)
            valid_count += 1
        except Exception as e:
            print(f"跳过无效帖子: {e}")
    print(f"成功导入帖子数: {valid_count}")
    # 4. 时间片划分
    slice_size = 50  # 每片50条，便于分析
    time_manager = TimeSliceManager(world_state.get_all_posts(), slice_size=slice_size)
    print(f"总时间片数: {time_manager.total_slices}")
    # 5. 初始化AgentController
    agent_controller = AgentController(agents, world_state)
    # 新增：同步所有Agent的_last_emotion和_last_stance为当前状态
    for agent_type, agents_list in agent_controller.agents.items():
        for agent in agents_list:
            agent._last_emotion = agent.emotion
            agent._last_stance = agent.stance_score
            agent.stance_score = 0.0  # 初始化为中立立场
    # 输出所有Agent的初始状态
    print("\n[Agent初始状态]")
    for agent_type, agents in agent_controller.agents.items():
        if agent_type not in ["意见领袖", "普通用户"]:
            continue
        for agent in agents:
            summary = agent.get_status()
            print(f'Agent: {agent.agent_id}, 类型: {agent.agent_type}, 立场: {summary.get("stance_score")}, 情绪: {summary.get("emotion")}, 置信度: {summary.get("confidence")}, 活跃度: {getattr(agent, "activity_level", None)}, 已读: {summary.get("viewed_posts_count")}, 交互: {summary.get("interaction_count")}')
    # 6. 遍历每个时间片，推送个性化信息流并模拟状态更新
    prev_agent_states = {}
    for agent_type, agents_list in agent_controller.agents.items():
        if agent_type not in ["意见领袖", "普通用户"]:
            continue
        for agent in agents_list:
            prev_agent_states[agent.agent_id] = agent.get_status().copy()
    for slice_idx in range(min(4, time_manager.total_slices)):
        print(f'\n=== 时间片 {slice_idx+1}/{time_manager.total_slices} ===')
        current_slice_posts = time_manager.get_slice(slice_idx)
        all_posts = world_state.get_all_posts()
        # 推送组成功能
        all_agents = []
        for agent_type, agents_list in agent_controller.agents.items():
            if agent_type not in ["意见领袖", "普通用户"]:
                continue
            all_agents.extend(agents_list)
        results = agent_controller.run_time_slice(all_agents, world_state)
        # 输出每个agent的详细状态
        print("\n[Agent状态变化]")
        for agent_type, agents in agent_controller.agents.items():
            if agent_type not in ["意见领袖", "普通用户"]:
                continue
            for agent in agents:
                summary = agent.get_status()
                print(f'Agent: {agent.agent_id}, 类型: {agent.agent_type}, 立场: {summary.get("stance_score")}, 情绪: {summary.get("emotion")}, 置信度: {summary.get("confidence")}, 活跃度: {getattr(agent, "activity_level", None)}, 已读: {summary.get("viewed_posts_count")}, 交互: {summary.get("interaction_count")}')
                # 输出增量
                prev = prev_agent_states.get(agent.agent_id, {})
                delta = {}
                for key in ["stance_score", "emotion", "confidence", "viewed_posts_count", "interaction_count"]:
                    if key in summary and key in prev:
                        try:
                            val1, val2 = summary[key], prev[key]
                            # 确保数值类型
                            if key == "emotion":
                                val1 = float(val1) if val1 is not None else 0.0
                                val2 = float(val2) if val2 is not None else 0.0
                            elif key == "stance_score":
                                val1 = float(val1) if val1 is not None else 0.0
                                val2 = float(val2) if val2 is not None else 0.0
                            delta[key] = val1 - val2
                        except Exception:
                            delta[key] = "N/A"
                print(f'  属性增量: {delta}')
                # 新增：输出波动量
                e1 = summary.get("emotion", 0.0)
                e2 = prev.get("emotion", 0.0)
                s1 = summary.get("stance_score", 0.0)
                s2 = prev.get("stance_score", 0.0)
                e1 = float(e1) if e1 is not None else 0.0
                e2 = float(e2) if e2 is not None else 0.0
                s1 = float(s1) if s1 is not None else 0.0
                s2 = float(s2) if s2 is not None else 0.0
                delta_emotion = abs(e1 - e2)
                delta_stance = abs(s1 - s2)
                fluctuation = delta_emotion + delta_stance
                print(f'  波动量: {fluctuation:.3f} (情绪: {delta_emotion:.3f}, 立场: {delta_stance:.3f})')
                # 更新prev_agent_states
                prev_agent_states[agent.agent_id] = summary.copy()
        # 新增：输出发言判定
        for judge in results.get("action_judgements", []):
            if judge["agent_type"] not in ["意见领袖", "普通用户"]:
                continue
            print(f'Agent: {judge["agent_id"]}, 类型: {judge["agent_type"]}, 本时间片发言: {"是" if judge["action"] else "否"}，原因: {judge["reason"]}')

if __name__ == "__main__":
    test_real_data_integration() 