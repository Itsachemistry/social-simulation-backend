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

@agent_bp.route('/list', methods=['GET'])
def list_agents():
    """返回所有可用的agent配置"""
    agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'agents.json')
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents = json.load(f)
    return jsonify({'status': 'success', 'agents': agents})
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
@agent_bp.route('/add', methods=['POST'])
def add_agent():
    """新增一个agent"""
    new_agent = request.json
    if not new_agent or 'agent_id' not in new_agent:
        return jsonify({'error': '缺少agent_id'}), 400
    agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'agents.json')
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents = json.load(f)
    # 检查重复
    if any(a['agent_id'] == new_agent['agent_id'] for a in agents):
        return jsonify({'error': 'agent_id已存在'}), 400
    agents.append(new_agent)
    with open(agents_path, 'w', encoding='utf-8') as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success'})

@agent_bp.route('/update/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """更新指定agent"""
    update_data = request.json
    agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'agents.json')
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents = json.load(f)
    found = False
    for agent in agents:
        if agent['agent_id'] == agent_id:
            agent.update(update_data)
            found = True
            break
    if not found:
        return jsonify({'error': '未找到该agent'}), 404
    with open(agents_path, 'w', encoding='utf-8') as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success'})

@agent_bp.route('/delete/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """删除指定agent"""
    agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'agents.json')
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents = json.load(f)
    new_agents = [a for a in agents if a['agent_id'] != agent_id]
    if len(new_agents) == len(agents):
        return jsonify({'error': '未找到该agent'}), 404
    with open(agents_path, 'w', encoding='utf-8') as f:
        json.dump(new_agents, f, ensure_ascii=False, indent=2)
    return jsonify({'status': 'success'}) 