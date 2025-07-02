from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from collections import defaultdict
import re

visualization_bp = Blueprint('visualization', __name__)

def normalize_post(post):
    """
    统一标准化post对象的字段名，兼容不同来源的数据格式。
    主要兼容以下字段：
    - 'children'/'Children'：子节点列表，树结构用
    - 'author_id'/'uid'：作者ID
    - 'timestamp'/'t'：时间戳
    - 'parent_post_id'/'pid'：父帖ID
    - 其他字段如'content'、'id'、'tags'等保持不变
    - 详细说明见每个字段注释
    """
    std = dict(post)  # 拷贝，避免原数据被修改
    # 兼容children/Children
    if 'children' not in std and 'Children' in std:
        std['children'] = std['Children']
    # 兼容author_id/uid
    if 'author_id' not in std and 'uid' in std:
        std['author_id'] = std['uid']
    # 兼容timestamp/t
    if 'timestamp' not in std and 't' in std:
        std['timestamp'] = std['t']
    # 兼容parent_post_id/pid
    if 'parent_post_id' not in std and 'pid' in std:
        std['parent_post_id'] = std['pid']
    # 兼容tags为空的情况
    if 'tags' not in std:
        std['tags'] = []
    # 兼容content为空的情况
    if 'content' not in std:
        std['content'] = ''
    # 兼容id为空的情况
    if 'id' not in std:
        std['id'] = ''
    # 兼容name字段（如有）
    if 'name' not in std and 'user' in std and isinstance(std['user'], dict):
        std['name'] = std['user'].get('name', '')
    # 其他字段可按需扩展
    return std

class InteractiveVisualizer:
    """交互式可视化数据处理器"""
    
    def __init__(self):
        self.sort_options = ['time', 'popularity', 'heat', 'likes', 'shares']
        self.filter_options = ['all', 'original', 'reposted', 'events']
    
    def filter_posts_by_time_range(self, posts, time_range):
        """按时间范围筛选帖子"""
        if not time_range:
            return posts
        
        start_time = datetime.fromisoformat(time_range['start'])
        end_time = datetime.fromisoformat(time_range['end'])
        
        filtered_posts = []
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_time = datetime.fromisoformat(post.get('timestamp', ''))
            if start_time <= post_time <= end_time:
                filtered_posts.append(post)
        
        return filtered_posts
    
    def search_posts_by_keywords(self, posts, keywords, search_fields=None):
        """按关键词搜索帖子"""
        if not keywords:
            return posts
        
        if search_fields is None:
            search_fields = ['content', 'author_id']
        
        keywords = keywords.lower().split()
        matched_posts = []
        
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            match_score = 0
            for field in search_fields:
                if field == 'tags':
                    # 特殊处理标签字段
                    post_tags = post.get('tags', [])
                    for keyword in keywords:
                        if any(keyword in tag.lower() for tag in post_tags):
                            match_score += 1
                else:
                    field_value = str(post.get(field, '')).lower()
                    for keyword in keywords:
                        if keyword in field_value:
                            match_score += 1
            
            if match_score > 0:
                post['_search_score'] = match_score
                matched_posts.append(post)
        
        # 按搜索匹配度排序
        matched_posts.sort(key=lambda x: x.get('_search_score', 0), reverse=True)
        return matched_posts
    
    def sort_posts(self, posts, sort_by='time', reverse=False):
        """排序帖子"""
        if sort_by == 'time':
            return sorted(posts, key=lambda x: x.get('timestamp', ''), reverse=reverse)
        elif sort_by == 'popularity':
            return sorted(posts, key=lambda x: x.get('likes', 0) + x.get('shares', 0), reverse=reverse)
        elif sort_by == 'heat':
            return sorted(posts, key=lambda x: x.get('heat', 0), reverse=reverse)
        elif sort_by == 'likes':
            return sorted(posts, key=lambda x: x.get('likes', 0), reverse=reverse)
        elif sort_by == 'shares':
            return sorted(posts, key=lambda x: x.get('shares', 0), reverse=reverse)
        else:
            return posts
    
    def filter_posts_by_popularity(self, posts, min_popularity=0):
        """按热度阈值筛选帖子"""
        if min_popularity <= 0:
            return posts
        
        filtered_posts = []
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            popularity = post.get('likes', 0) + post.get('shares', 0) + post.get('heat', 0)
            if popularity >= min_popularity:
                filtered_posts.append(post)
        
        return filtered_posts
    
    def filter_posts_by_tags(self, posts, tags=None, match_all=False):
        """
        按标签筛选帖子
        
        Args:
            posts: 帖子列表
            tags: 标签列表，如 ["科技", "创新"] 或 None（不过滤）
            match_all: True表示必须匹配所有标签，False表示匹配任一标签
            
        Returns:
            筛选后的帖子列表
        """
        if not tags:
            return posts
        
        filtered_posts = []
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_tags = post.get('tags', [])
            
            if match_all:
                # 必须匹配所有标签
                if all(tag in post_tags for tag in tags):
                    filtered_posts.append(post)
            else:
                # 匹配任一标签
                if any(tag in post_tags for tag in tags):
                    filtered_posts.append(post)
        
        return filtered_posts
    
    def filter_posts_by_type(self, posts, filter_type='all', include_reposts=True):
        """按类型筛选帖子"""
        if filter_type == 'all':
            if include_reposts:
                return posts
            else:
                # 过滤掉转发内容
                return [post for post in posts if not post.get('is_repost', False)]
        
        elif filter_type == 'original':
            return [post for post in posts if not post.get('is_repost', False)]
        
        elif filter_type == 'reposted':
            return [post for post in posts if post.get('is_repost', False)]
        
        elif filter_type == 'events':
            return [post for post in posts if post.get('is_event', False)]
        
        else:
            return posts
    
    def get_posts_summary(self, posts):
        """获取帖子摘要统计"""
        if not posts:
            return {
                'total_posts': 0,
                'time_range': None,
                'popularity_stats': {},
                'type_distribution': {},
                'top_authors': [],
                'top_tags': [],
                'hot_topics': []
            }
        
        # 时间范围
        timestamps = [post.get('timestamp') for post in posts if post.get('timestamp')]
        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
            time_range = {'start': start_time, 'end': end_time}
        else:
            time_range = None
        
        # 热度统计
        likes = [post.get('likes', 0) for post in posts]
        shares = [post.get('shares', 0) for post in posts]
        heats = [post.get('heat', 0) for post in posts]
        
        popularity_stats = {
            'total_likes': sum(likes),
            'total_shares': sum(shares),
            'avg_heat': sum(heats) / len(heats) if heats else 0,
            'max_heat': max(heats) if heats else 0,
            'avg_likes': sum(likes) / len(likes) if likes else 0,
            'avg_shares': sum(shares) / len(shares) if shares else 0
        }
        
        # 类型分布
        type_counts = defaultdict(int)
        author_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            if post.get('is_event'):
                type_counts['events'] += 1
            elif post.get('is_repost'):
                type_counts['reposts'] += 1
            else:
                type_counts['original'] += 1
            
            author = post.get('author_id', 'unknown')
            author_counts[author] += 1
            
            # 统计标签
            for tag in post.get('tags', []):
                tag_counts[tag] += 1
        
        type_distribution = dict(type_counts)
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 热门话题
        hot_topics = self._extract_hot_topics(posts)
        
        return {
            'total_posts': len(posts),
            'time_range': time_range,
            'popularity_stats': popularity_stats,
            'type_distribution': type_distribution,
            'top_authors': top_authors,
            'top_tags': top_tags,
            'hot_topics': hot_topics
        }
    
    def _extract_hot_topics(self, posts, top_n=10):
        """提取热门话题"""
        keyword_counts = defaultdict(int)
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            content = post.get('content', '').lower()
            # 简单的分词和过滤
            words = re.findall(r'\b\w{3,}\b', content)
            for word in words:
                keyword_counts[word] += 1
        
        return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

# 创建全局可视化器
interactive_visualizer = InteractiveVisualizer()


#getposts接口，用于获取帖子

@visualization_bp.route('/posts/filter', methods=['POST'])
def filter_posts():
    """综合帖子筛选接口"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get('simulation_id')
        
        # 筛选参数
        time_range = data.get('time_range')
        keywords = data.get('keywords')
        search_fields = data.get('search_fields', ['content', 'author_id'])
        sort_by = data.get('sort_by', 'time')
        sort_reverse = data.get('sort_reverse', False)
        min_popularity = data.get('min_popularity', 0)
        filter_type = data.get('filter_type', 'all')
        include_reposts = data.get('include_reposts', True)
        limit = data.get('limit', 100)  # 限制返回数量
        # 新增：标签筛选参数
        tags = data.get('tags')  # 标签列表，如 ["科技", "创新"]
        match_all_tags = data.get('match_all_tags', False)  # 是否必须匹配所有标签
        
        if not simulation_id:
            return jsonify({'error': '缺少simulation_id参数'}), 400
        
        # 获取仿真结果
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        
        if not status:
            return jsonify({'error': '仿真不存在'}), 404
        
        if status['status'] != 'completed':
            return jsonify({'error': '仿真尚未完成'}), 400
        
        # 获取所有帖子
        all_posts = status['results'].get('final_posts', [])
        
        # 应用筛选
        filtered_posts = all_posts
        
        # 1. 时间范围筛选
        if time_range:
            filtered_posts = interactive_visualizer.filter_posts_by_time_range(
                filtered_posts, time_range
            )
        
        # 2. 关键词搜索
        if keywords:
            filtered_posts = interactive_visualizer.search_posts_by_keywords(
                filtered_posts, keywords, search_fields
            )
        
        # 3. 类型筛选
        filtered_posts = interactive_visualizer.filter_posts_by_type(
            filtered_posts, filter_type, include_reposts
        )
        
        # 4. 热度阈值筛选
        filtered_posts = interactive_visualizer.filter_posts_by_popularity(
            filtered_posts, min_popularity
        )
        
        # 5. 标签筛选
        if tags:
            filtered_posts = interactive_visualizer.filter_posts_by_tags(
                filtered_posts, tags, match_all_tags
            )
        
        # 6. 排序
        filtered_posts = interactive_visualizer.sort_posts(
            filtered_posts, sort_by, sort_reverse
        )
        
        # 7. 限制数量
        if limit and limit > 0:
            filtered_posts = filtered_posts[:limit]
        
        # 8. 获取摘要统计
        summary = interactive_visualizer.get_posts_summary(filtered_posts)
        
        return jsonify({
            'status': 'success',
            'simulation_id': simulation_id,
            'filter_params': {
                'time_range': time_range,
                'keywords': keywords,
                'sort_by': sort_by,
                'sort_reverse': sort_reverse,
                'min_popularity': min_popularity,
                'filter_type': filter_type,
                'include_reposts': include_reposts,
                'limit': limit,
                'tags': tags,
                'match_all_tags': match_all_tags
            },
            'summary': summary,
            'posts': filtered_posts,
            'total_filtered': len(filtered_posts)
        })
        
    except Exception as e:
        return jsonify({'error': f'筛选失败: {str(e)}'}), 500

@visualization_bp.route('/posts/search', methods=['POST'])
def search_posts():
    """关键词搜索帖子，支持分页"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get('simulation_id')
        keywords = data.get('keywords')
        search_fields = data.get('search_fields', ['content', 'author_id'])
        # 新增分页参数
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 20))
        
        if not simulation_id or not keywords:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 获取仿真结果
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        
        if not status or status['status'] != 'completed':
            return jsonify({'error': '仿真不存在或未完成'}), 404
        
        # 搜索帖子
        all_posts = status['results'].get('final_posts', [])
        search_results = interactive_visualizer.search_posts_by_keywords(
            all_posts, keywords, search_fields
        )
        
        total_found = len(search_results)
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paged_results = search_results[start:end]
        
        return jsonify({
            'status': 'success',
            'keywords': keywords,
            'search_fields': search_fields,
            'results': paged_results,
            'total_found': total_found,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_found + page_size - 1) // page_size
        })
        
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@visualization_bp.route('/posts/summary', methods=['POST'])
def get_posts_summary():
    """获取帖子摘要统计"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get('simulation_id')
        time_range = data.get('time_range')
        filter_type = data.get('filter_type', 'all')
        include_reposts = data.get('include_reposts', True)
        
        if not simulation_id:
            return jsonify({'error': '缺少simulation_id参数'}), 400
        
        # 获取仿真结果
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        
        if not status or status['status'] != 'completed':
            return jsonify({'error': '仿真不存在或未完成'}), 404
        
        # 获取并筛选帖子
        all_posts = status['results'].get('final_posts', [])
        
        if time_range:
            all_posts = interactive_visualizer.filter_posts_by_time_range(
                all_posts, time_range
            )
        
        all_posts = interactive_visualizer.filter_posts_by_type(
            all_posts, filter_type, include_reposts
        )
        
        # 生成摘要
        summary = interactive_visualizer.get_posts_summary(all_posts)
        
        return jsonify({
            'status': 'success',
            'simulation_id': simulation_id,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': f'获取摘要失败: {str(e)}'}), 500

@visualization_bp.route('/options', methods=['GET'])
def get_visualization_options():
    """获取可视化选项"""
    return jsonify({
        'status': 'success',
        'sort_options': [
            {'value': 'time', 'label': '按时间'},
            {'value': 'popularity', 'label': '按热度'},
            {'value': 'heat', 'label': '按热度值'},
            {'value': 'likes', 'label': '按点赞数'},
            {'value': 'shares', 'label': '按分享数'}
        ],
        'filter_options': [
            {'value': 'all', 'label': '全部帖子'},
            {'value': 'original', 'label': '原创内容'},
            {'value': 'reposted', 'label': '转发内容'},
            {'value': 'events', 'label': '事件帖子'}
        ],
        'search_fields': [
            {'value': 'content', 'label': '帖子内容'},
            {'value': 'author_id', 'label': '作者ID'},
            {'value': 'id', 'label': '帖子ID'},
            {'value': 'tags', 'label': '标签'}
        ],
        'tag_options': {
            'description': '支持微博标签筛选，标签格式为 #XXXX#',
            'match_modes': [
                {'value': False, 'label': '匹配任一标签'},
                {'value': True, 'label': '匹配所有标签'}
            ],
            'example': ['科技', '创新', '产品']
        }
    })

@visualization_bp.route('/posts/repost_tree', methods=['POST'])
def get_repost_tree():
    """获取转播树结构"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({'error': '缺少simulation_id参数'}), 400
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        if not status or status['status'] != 'completed':
            return jsonify({'error': '仿真不存在或未完成'}), 404
        all_posts = status['results'].get('final_posts', [])
        agent_states = status['results'].get('agent_states', {})

        # 收集所有Agent的浏览过的post_id
        viewed_map = {}  # post_id -> [agent_id, ...]
        for agent_type, agents in agent_states.items():
            for agent in agents:
                for pid in agent.get("viewed_posts", []):
                    if isinstance(pid, str):
                        if pid not in viewed_map:
                            viewed_map[pid] = []
                        if isinstance(agent["agent_id"], str):
                            viewed_map[pid].append(agent["agent_id"])
        # 构建节点，增加is_agent_post和viewed_by_agents
        nodes = {}
        for p in all_posts:
            node = dict(p)
            node["children"] = []
            node["is_agent_post"] = str(p.get("author_id", "")).startswith("agent_")
            node["viewed_by_agents"] = viewed_map.get(p["id"], [])
            nodes[p['id']] = node
        root_nodes = []
        for post in all_posts:
            parent_id = post.get('parent_post_id')
            if parent_id and parent_id in nodes:
                nodes[parent_id]['children'].append(nodes[post['id']])
            else:
                root_nodes.append(nodes[post['id']])
        tree = {'id': 'virtual_root', 'children': root_nodes}
        return jsonify(tree)
    except Exception as e:
        return jsonify({'error': f'生成转播树失败: {str(e)}'}), 500 