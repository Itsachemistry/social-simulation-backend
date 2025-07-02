import json
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.world_state import WorldState
from src.agent_controller import AgentController
from src.time_manager import TimeSliceManager

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

def test_real_data_integration():
    # 1. 加载真实数据
    posts = load_real_posts('data/data/3weibo_data_index_group_importance_withvirtual.json')
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
    # 输出所有Agent的初始状态
    print("\n[Agent初始状态]")
    for agent_type, agents in agent_controller.agents.items():
        for agent in agents:
            summary = agent.get_state_summary()
            print(f'Agent: {agent.agent_id}, 类型: {agent.agent_type}, 立场: {summary.get("stance")}, 情绪: {summary.get("emotion")}, 置信度: {summary.get("confidence")}, 活跃度: {getattr(agent, "activity_level", None)}, 能量: {summary.get("energy")}, 已读: {summary.get("viewed_posts_count")}, 交互: {summary.get("interaction_count")}')
    # 6. 遍历每个时间片，推送个性化信息流并模拟状态更新
    for slice_idx in range(min(4, time_manager.total_slices)):
        print(f'\n=== 时间片 {slice_idx+1}/{time_manager.total_slices} ===')
        current_slice_posts = time_manager.get_slice(slice_idx)
        all_posts = world_state.get_all_posts()
        # 推送组成功能
        all_agents = []
        for agent_type, agents_list in agent_controller.agents.items():
            all_agents.extend(agents_list)
        results = agent_controller.run_time_slice(all_agents, world_state)
        # 输出每个agent的详细状态
        print("\n[Agent状态变化]")
        for agent_type, agents in agent_controller.agents.items():
            for agent in agents:
                summary = agent.get_state_summary()
                print(f'Agent: {agent.agent_id}, 类型: {agent.agent_type}, 立场: {summary.get("stance")}, 情绪: {summary.get("emotion")}, 置信度: {summary.get("confidence")}, 活跃度: {getattr(agent, "activity_level", None)}, 能量: {summary.get("energy")}, 已读: {summary.get("viewed_posts_count")}, 交互: {summary.get("interaction_count")}')

if __name__ == "__main__":
    test_real_data_integration() 