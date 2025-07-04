import random
from collections import defaultdict
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json

config_bp = Blueprint('config', __name__)

# 全局仿真配置（可替换为数据库或更复杂的存储）
simulation_config = {
    "start_time": None,
    "end_time": None,
    "stance_distribution": {},
    "sentiment_distribution": {},
    "event_description": "",
    "quantity": None  # 新增：允许前端传入总数量
}

POSTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'posts.json')

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

@config_bp.route('/config', methods=['POST', 'PUT'])
def set_simulation_config():
    data = request.json
    if not data:
        return jsonify({'error': '请求体不能为空或不是合法JSON'}), 400
    # 参数校验与更新
    if "start_time" in data:
        simulation_config["start_time"] = data["start_time"]
    if "end_time" in data:
        simulation_config["end_time"] = data["end_time"]
    if "stance_distribution" in data:
        simulation_config["stance_distribution"] = data["stance_distribution"]
    if "sentiment_distribution" in data:
        simulation_config["sentiment_distribution"] = data["sentiment_distribution"]
    if "event_description" in data:
        simulation_config["event_description"] = data["event_description"]
    if "quantity" in data:
        simulation_config["quantity"] = data["quantity"]
    return jsonify({"status": "success", "config": simulation_config})

@config_bp.route('/config', methods=['GET'])
def get_simulation_config():
    return jsonify(simulation_config)

@config_bp.route('/posts/timeline', methods=['GET'])
def get_posts_timeline():
    if not os.path.exists(POSTS_PATH):
        return jsonify({'error': '未找到帖子数据文件'}), 404
    with open(POSTS_PATH, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    timestamps = sorted(set(p.get('timestamp') for p in posts if p.get('timestamp')))
    if not timestamps:
        return jsonify({'error': '没有可用的时间戳'}), 404
    return jsonify({
        'min_timestamp': timestamps[0],
        'max_timestamp': timestamps[-1],
        'all_timestamps': timestamps
    })

@config_bp.route('/initial-params', methods=['GET'])
def get_initial_params():
    """
    提供给前端用于初始化配置界面的参数。
    """
    if not os.path.exists(POSTS_PATH):
        return jsonify({'error': '未找到帖子数据文件'}), 404

    with open(POSTS_PATH, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    if not posts:
        return jsonify({
            'total_quantity': 0,
            'available_stances': [],
            'available_sentiments': [],
            'stance_distribution': {},
            'sentiment_distribution': {}
        })

    all_stances = [p.get('stance') for p in posts if p.get('stance')]
    all_sentiments = [p.get('sentiment') for p in posts if p.get('sentiment')]
    stance_set = sorted(set(all_stances))
    sentiment_set = sorted(set(all_sentiments))

    # 统计比例
    from collections import Counter
    stance_counter = Counter(all_stances)
    sentiment_counter = Counter(all_sentiments)
    total = len(posts)
    stance_distribution = {k: round(v / total, 4) for k, v in stance_counter.items()}
    sentiment_distribution = {k: round(v / total, 4) for k, v in sentiment_counter.items()}

    return jsonify({
        'total_quantity': total,
        'available_stances': stance_set,
        'available_sentiments': sentiment_set,
        'stance_distribution': stance_distribution,
        'sentiment_distribution': sentiment_distribution
    })

# 复合配额填充算法：支持情感+立场+规模
def sample_posts_by_quota(posts, stance_distribution, sentiment_distribution, quantity):
    """
    posts: List[Dict]，每条帖子有 'stance' 和 'sentiment' 字段
    stance_distribution: Dict[str, float]
    sentiment_distribution: Dict[str, float]
    quantity: int
    返回：采样后的帖子列表和警告信息
    """
    random.shuffle(posts)
    selected_posts = []
    used_post_ids = set()
    warning_msgs = []
    # 1. 复合桶分组
    buckets = defaultdict(list)
    for post in posts:
        stance = post.get('stance')
        sentiment = post.get('sentiment')
        buckets[(sentiment, stance)].append(post)
    # 2. 计算目标配额
    target = {}
    for sentiment, s_ratio in sentiment_distribution.items():
        for stance, t_ratio in stance_distribution.items():
            target[(sentiment, stance)] = int(quantity * s_ratio * t_ratio)
    # 3. 第一阶段：完美匹配
    for key, target_num in target.items():
        bucket = buckets.get(key, [])
        if len(bucket) >= target_num:
            chosen = random.sample(bucket, target_num)
        else:
            chosen = bucket
            warning_msgs.append(f"组合{key}目标{target_num}，实际{len(bucket)}，已全部选取。")
        for post in chosen:
            if post['id'] not in used_post_ids:
                selected_posts.append(post)
                used_post_ids.add(post['id'])
    # 4. 第二阶段：单独补足情感
    def count_by(posts, field, value):
        return sum(1 for p in posts if p.get(field) == value)
    for sentiment, s_ratio in sentiment_distribution.items():
        target_num = int(quantity * s_ratio)
        current_num = count_by(selected_posts, 'sentiment', sentiment)
        remain = target_num - current_num
        if remain > 0:
            candidates = [p for p in posts if p['id'] not in used_post_ids and p.get('sentiment') == sentiment]
            if len(candidates) < remain:
                warning_msgs.append(f"情感{sentiment}目标{target_num}，实际{current_num+len(candidates)}，已全部选取。")
                remain = len(candidates)
            chosen = random.sample(candidates, remain)
            for post in chosen:
                selected_posts.append(post)
                used_post_ids.add(post['id'])
    # 5. 第三阶段：单独补足立场
    for stance, t_ratio in stance_distribution.items():
        target_num = int(quantity * t_ratio)
        current_num = count_by(selected_posts, 'stance', stance)
        remain = target_num - current_num
        if remain > 0:
            candidates = [p for p in posts if p['id'] not in used_post_ids and p.get('stance') == stance]
            if len(candidates) < remain:
                warning_msgs.append(f"立场{stance}目标{target_num}，实际{current_num+len(candidates)}，已全部选取。")
                remain = len(candidates)
            chosen = random.sample(candidates, remain)
            for post in chosen:
                selected_posts.append(post)
                used_post_ids.add(post['id'])
    # 6. 随机补足总量
    shortfall = quantity - len(selected_posts)
    if shortfall > 0:
        candidates = [p for p in posts if p['id'] not in used_post_ids]
        if len(candidates) < shortfall:
            warning_msgs.append(f"总量目标{quantity}，实际只能选到{len(selected_posts)+len(candidates)}。")
            shortfall = len(candidates)
        chosen = random.sample(candidates, shortfall)
        for post in chosen:
            selected_posts.append(post)
            used_post_ids.add(post['id'])
    random.shuffle(selected_posts)
    return selected_posts, warning_msgs

# 用于仿真初始化时筛选初始帖子池的函数示例
def build_initial_post_pool(all_posts, config):
    # 1. 时间筛选
    posts = [p for p in all_posts if config['start_time'] <= p['timestamp'] <= config['end_time']]
    stance_distribution = config.get('stance_distribution', {})
    sentiment_distribution = config.get('sentiment_distribution', {})
    quantity = config.get('quantity', None)
    # 只保留三项都存在时的采样逻辑
    if stance_distribution and sentiment_distribution and quantity:
        sampled, warnings = sample_posts_by_quota(posts, stance_distribution, sentiment_distribution, quantity)
        return {"posts": sampled, "warnings": warnings}
    # 如果三项不全，直接返回空列表或报错
    return {"error": "配置缺少必要的采样参数（立场、情感、数量）"}

# Agent决策时注入事件描述的示例
def build_agent_prompt(agent, posts, config):
    prompt = f"""
    # 事件背景
    {config['event_description']}
    # 你的角色...
    # 你看到的帖子...
    """
    return prompt 