from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json

agent_bp = Blueprint('agent', __name__)

AGENT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'agents.json')
POSTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'posts.json')
#加载agents，勇于初始化
def load_agents():
    if not os.path.exists(AGENT_CONFIG_PATH):
        return []
    with open(AGENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
#保存agent历史
def save_agents(agent_list):
    with open(AGENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(agent_list, f, ensure_ascii=False, indent=2)
#获取posts的time range
def get_post_time_range():
    if not os.path.exists(POSTS_PATH):
        return None, None
    with open(POSTS_PATH, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    timestamps = [p.get('timestamp') for p in posts if p.get('timestamp')]
    if not timestamps:
        return None, None
    timestamps = sorted(timestamps)
    return timestamps[0], timestamps[-1]
#获取加载agents
@agent_bp.route('/', methods=['GET'])
def get_agents():
    agents = load_agents()
    return jsonify(agents)
#添加agent“
# Agent对象属性说明：
# - agent_id: str, Agent唯一标识符
# - agent_type: str, Agent类型 ("opinion_leader" | "rule_based" | "regular_user")
# - name: str, Agent名称
# - personality: dict, 性格特征
#   - stance: str, 立场倾向 ("positive" | "negative" | "neutral")
#   - emotion: str, 情感倾向 ("happy" | "angry" | "sad" | "neutral")
#   - activity_level: int, 活跃度 (1-10)
#   - influence: int, 影响力 (1-10)
# - join_time: str, 加入时间 (ISO格式时间戳)
# - behavior_rules: dict, 行为规则配置

#   - topic_preferences: list, 话题偏好列表
#   - interaction_patterns: dict, 交互模式配置
# - status: str, Agent状态 ("active" | "inactive" | "suspended")
# - metadata: dict, 额外元数据信息
@agent_bp.route('/', methods=['POST'])
def add_agent():
    agents = load_agents()
    new_agent = request.json
    if not new_agent:
        return jsonify({'error': '请求体不能为空'}), 400
    # 检查agent_id唯一性
    if any(a['agent_id'] == new_agent['agent_id'] for a in agents):
        return jsonify({'error': 'agent_id已存在'}), 400
    # 校验join_time范围
    join_ts = new_agent.get('join_time') or new_agent.get('join_timestamp')
    if join_ts:
        try:
            join_dt = datetime.fromisoformat(str(join_ts))
        except Exception:
            return jsonify({'error': 'join_time格式错误，需为ISO格式字符串'}), 400
        min_ts, max_ts = get_post_time_range()
        if min_ts and max_ts:
            min_dt = datetime.fromisoformat(str(min_ts))
            max_dt = datetime.fromisoformat(str(max_ts))
            if not (min_dt <= join_dt <= max_dt):
                return jsonify({'error': f'join_time需在所有帖子时间戳范围内：{min_ts} ~ {max_ts}'}), 400
    agents.append(new_agent)
    save_agents(agents)
    return jsonify({'status': 'success', 'agent': new_agent})

@agent_bp.route('/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    agents = load_agents()
    update_data = request.json
    if not update_data:
        return jsonify({'error': '请求体不能为空'}), 400
    # 校验join_time范围
    join_ts = update_data.get('join_time') or update_data.get('join_timestamp')
    if join_ts:
        try:
            join_dt = datetime.fromisoformat(str(join_ts))
        except Exception:
            return jsonify({'error': 'join_time格式错误，需为ISO格式字符串'}), 400
        min_ts, max_ts = get_post_time_range()
        if min_ts and max_ts:
            min_dt = datetime.fromisoformat(str(min_ts))
            max_dt = datetime.fromisoformat(str(max_ts))
            if not (min_dt <= join_dt <= max_dt):
                return jsonify({'error': f'join_time需在所有帖子时间戳范围内：{min_ts} ~ {max_ts}'}), 400
    found = False
    for idx, agent in enumerate(agents):
        if agent['agent_id'] == agent_id:
            agents[idx].update(update_data)
            found = True
            break
    if not found:
        return jsonify({'error': '未找到指定agent_id'}), 404
    save_agents(agents)
    return jsonify({'status': 'success', 'agent': agents[idx]})

@agent_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    agents = load_agents()
    found = False
    for agent in agents:
        if agent['agent_id'] == agent_id:
            agent['is_active'] = False
            found = True
            break
    if not found:
        return jsonify({'error': '未找到指定agent_id'}), 404
    save_agents(agents)
    return jsonify({'status': 'success', 'agent_id': agent_id}) 