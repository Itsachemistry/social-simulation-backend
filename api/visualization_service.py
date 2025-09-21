from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from collections import defaultdict
import re
from flask import current_app
import os

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
        agent_generated_posts = status['results'].get('agent_generated_posts', [])
        # TODO: 后续在此处合并原始数据
        filtered_posts = agent_generated_posts
        
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
        agent_generated_posts = status['results'].get('agent_generated_posts', [])
        # TODO: 后续在此处合并原始数据
        if time_range:
            agent_generated_posts = interactive_visualizer.filter_posts_by_time_range(
                agent_generated_posts, time_range
            )
        agent_generated_posts = interactive_visualizer.filter_posts_by_type(
            agent_generated_posts, filter_type, include_reposts
        )
        # 生成摘要
        summary = interactive_visualizer.get_posts_summary(agent_generated_posts)
        
        return jsonify({
            'status': 'success',
            'simulation_id': simulation_id,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': f'获取摘要失败: {str(e)}'}), 500

@visualization_bp.route('/options', methods=['GET'])
def get_visualization_options():
    print('[get_visualization_options] called')
    
    # 扫描Agent生成的帖子文件
    agent_posts_files = []
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    for filename in os.listdir(base_dir):
        if filename.startswith('agent_generated_posts_') and filename.endswith('.json'):
            # 提取时间戳（例如从 agent_generated_posts_20250729_112026.json 提取 20250729_112026）
            timestamp = filename[len('agent_generated_posts_'):-5]  # 去掉前缀和.json后缀
            agent_posts_files.append({
                'value': filename,
                'label': f'Agent仿真 {timestamp[:8]}-{timestamp[9:]}',
                'timestamp': timestamp,
                'filepath': os.path.join(base_dir, filename)
            })
    
    # 按时间戳倒序排列（最新的在前）
    agent_posts_files.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'status': 'success',
        'data_source_options': [
            {'value': 'original', 'label': '仅原始微博数据'},
            {'value': 'merged', 'label': '融合Agent生成帖子'}
        ],
        'agent_posts_files': agent_posts_files,
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

# 工具函数：递归平铺所有children，去掉children字段

def flatten_posts(posts):
    flat = []
    def _flatten(post):
        post_copy = dict(post)
        children = post_copy.pop('children', [])
        flat.append(post_copy)
        for child in children:
            _flatten(child)
    for p in posts:
        _flatten(p)
    return flat

def merge_agent_posts_with_original(original_posts, agent_posts_file):
    """
    将Agent生成的帖子融合到原始帖子数据中
    Agent帖子的pid指向原始帖子的mid，需要将Agent帖子作为对应原始帖子的子节点
    """
    print(f"[数据融合] 开始融合Agent帖子文件: {agent_posts_file}")
    
    # 读取Agent生成的帖子
    if not os.path.exists(agent_posts_file):
        print(f"[数据融合] Agent帖子文件不存在: {agent_posts_file}")
        return original_posts
    
    try:
        with open(agent_posts_file, 'r', encoding='utf-8') as f:
            agent_data = json.load(f)
        
        agent_posts = agent_data.get('agent_posts', [])
        print(f"[数据融合] 读取到 {len(agent_posts)} 个Agent帖子")
        
        if not agent_posts:
            return original_posts
        
        # 创建原始帖子的mid索引
        mid_to_post = {}
        
        def build_index(posts):
            for post in posts:
                mid = post.get('mid') or post.get('id')
                if mid:
                    mid_to_post[mid] = post
                # 递归处理子帖子
                children = post.get('children', [])
                if children:
                    build_index(children)
        
        build_index(original_posts)
        print(f"[数据融合] 构建了 {len(mid_to_post)} 个原始帖子的索引")
        
        # 将Agent帖子插入到对应的父帖子中
        successful_merges = 0
        orphaned_agents = []
        
        for agent_post in agent_posts:
            pid = agent_post.get('pid')
            
            if not pid:
                print(f"[数据融合] Agent帖子 {agent_post.get('id')} 没有pid，跳过")
                orphaned_agents.append(agent_post)
                continue
            
            # 查找对应的父帖子
            parent_post = mid_to_post.get(pid)
            if not parent_post:
                print(f"[数据融合] 找不到pid={pid}对应的父帖子，Agent帖子 {agent_post.get('id')} 成为孤儿")
                orphaned_agents.append(agent_post)
                continue
            
            # 转换Agent帖子格式以兼容转发树结构
            agent_post_converted = {
                'id': agent_post.get('id'),
                'mid': agent_post.get('mid'),
                'pid': agent_post.get('pid'),
                'uid': agent_post.get('author_id'),
                'author_id': agent_post.get('author_id'),
                'content': agent_post.get('content'),
                'text': agent_post.get('content'),  # 兼容字段
                't': agent_post.get('t'),
                'timestamp': agent_post.get('timestamp'),
                'reposts_count': 0,
                'attitudes_count': 0,
                'comments_count': 0,
                'children': [],
                # 保留Agent特有的字段
                'emotion_score': agent_post.get('emotion_score'),
                'stance_score': agent_post.get('stance_score'),
                'information_strength': agent_post.get('information_strength'),
                'keywords': agent_post.get('keywords', []),
                'stance_category': agent_post.get('stance_category'),
                'stance_confidence': agent_post.get('stance_confidence'),
                'generation_info': agent_post.get('generation_info'),
                'is_agent_generated': True  # 标记为Agent生成
            }
            
            # 将Agent帖子添加到父帖子的children中
            if 'children' not in parent_post:
                parent_post['children'] = []
            parent_post['children'].append(agent_post_converted)
            successful_merges += 1
            
            print(f"[数据融合] 成功将Agent帖子 {agent_post.get('id')} 添加到父帖子 {pid} 的children中")
        
        print(f"[数据融合] 融合完成: 成功融合 {successful_merges} 个Agent帖子，{len(orphaned_agents)} 个孤儿帖子")
        
        # 如果有孤儿Agent帖子，可以选择添加到根级别或者创建一个特殊的根节点
        if orphaned_agents:
            print(f"[数据融合] 处理 {len(orphaned_agents)} 个孤儿Agent帖子")
            # 这里可以根据需要决定如何处理孤儿帖子
            # 暂时添加到原始帖子列表的末尾
            for orphan in orphaned_agents:
                orphan_converted = {
                    'id': orphan.get('id'),
                    'mid': orphan.get('mid'),
                    'pid': '2',  # 设置为根节点
                    'uid': orphan.get('author_id'),
                    'author_id': orphan.get('author_id'),
                    'content': orphan.get('content'),
                    'text': orphan.get('content'),
                    't': orphan.get('t'),
                    'timestamp': orphan.get('timestamp'),
                    'reposts_count': 0,
                    'attitudes_count': 0,
                    'comments_count': 0,
                    'children': [],
                    'emotion_score': orphan.get('emotion_score'),
                    'stance_score': orphan.get('stance_score'),
                    'information_strength': orphan.get('information_strength'),
                    'keywords': orphan.get('keywords', []),
                    'stance_category': orphan.get('stance_category'),
                    'stance_confidence': orphan.get('stance_confidence'),
                    'generation_info': orphan.get('generation_info'),
                    'is_agent_generated': True,
                    'is_orphaned': True
                }
                original_posts.append(orphan_converted)
        
        return original_posts
        
    except Exception as e:
        print(f"[数据融合] 融合过程中出错: {e}")
        return original_posts

@visualization_bp.route('/tree', methods=['GET'])
def get_repost_tree():
    """返回完整的转播树结构，展示所有微博的转发关系链（支持时间范围筛选和Agent帖子融合）"""
    try:
        # 获取参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        data_source = request.args.get('data_source', 'original')  # 'original' 或 'merged'
        agent_posts_file = request.args.get('agent_posts_file')  # Agent帖子文件名
        
        print(f"[转播树] 请求参数: data_source={data_source}, agent_posts_file={agent_posts_file}")
        
        # 读取原始数据
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        
        with open(data_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 根据数据源选择进行数据处理
        if data_source == 'merged' and agent_posts_file:
            # 融合模式：将Agent帖子与原始数据融合
            agent_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), agent_posts_file)
            merged_data = merge_agent_posts_with_original(original_data, agent_file_path)
            all_posts = flatten_posts(merged_data)
            print(f"[转播树] 使用融合数据，总帖子数: {len(all_posts)}")
        else:
            # 原始模式：只使用原始数据
            all_posts = flatten_posts(original_data)
            print(f"[转播树] 使用原始数据，总帖子数: {len(all_posts)}")
        
        # 应用时间筛选
        posts = all_posts
        if start_time and end_time:
            try:
                start_timestamp = int(datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp())
                end_timestamp = int(datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp())
                posts = [p for p in all_posts if start_timestamp <= p.get('t', 0) <= end_timestamp]
                print(f"[转播树] 时间筛选: {start_time} - {end_time}, 原始帖子数: {len(all_posts)}, 筛选后: {len(posts)}")
            except Exception as e:
                print(f"[转播树] 时间解析失败: {e}, 使用全部数据")
                posts = all_posts
        
        # 构建完整的转播关系映射
        post_details = {}    # 所有帖子详情
        parent_child_map = {}  # parent_id -> [child_ids]
        all_root_nodes = []   # 所有根节点（包括pid="2"的补充节点）
        
        for post in posts:
            post_id = post.get('mid') or post.get('id')
            if not post_id:
                continue
                
        for post in posts:
            post_id = post.get('mid') or post.get('id')
            if not post_id:
                continue
                
            # 构建基础帖子详情
            content = (post.get('text', '') or post.get('content', ''))
            truncated_content = content[:100] + '...' if len(content) > 100 else content
            
            post_detail = {
                'id': post_id,
                'content': truncated_content,
                'author_id': post.get('uid') or post.get('author_id', ''),
                'reposts_count': post.get('reposts_count', 0),
                'attitudes_count': post.get('attitudes_count', 0),
                'comments_count': post.get('comments_count', 0),
                'timestamp': post.get('t', 0),
                'children': []
            }
            
            # 如果是Agent生成的帖子，添加额外信息
            if post.get('is_agent_generated'):
                post_detail.update({
                    'is_agent_generated': True,
                    'emotion_score': post.get('emotion_score'),
                    'stance_score': post.get('stance_score'),
                    'information_strength': post.get('information_strength'),
                    'keywords': post.get('keywords', []),
                    'stance_category': post.get('stance_category'),
                    'stance_confidence': post.get('stance_confidence'),
                    'generation_info': post.get('generation_info'),
                    'is_orphaned': post.get('is_orphaned', False)
                })
            
            post_details[post_id] = post_detail
            
            # 构建父子关系 - 包括所有关系
            pid = post.get('pid')
            if pid:
                if pid == '2':
                    # pid="2"是根节点，直接添加到根节点列表
                    all_root_nodes.append(post_id)
                elif pid != post_id:  # 排除自引用
                    if pid not in parent_child_map:
                        parent_child_map[pid] = []
                    parent_child_map[pid].append(post_id)
        
        # 构建完整转播树 - 无任何限制
        def build_complete_repost_tree(root_id, visited=None):
            if visited is None:
                visited = set()
            
            if root_id in visited or root_id not in post_details:
                return None
            
            visited.add(root_id)
            root_node = dict(post_details[root_id])
            
            # 获取所有转发这个微博的子微博
            child_ids = parent_child_map.get(root_id, [])
            root_node['direct_reposts'] = len(child_ids)  # 记录直接转发数
            
            # 递归构建所有子节点 - 无数量限制
            children = []
            for child_id in child_ids:
                child_node = build_complete_repost_tree(child_id, visited.copy())
                if child_node:
                    children.append(child_node)
            
            # 按转发数和时间排序
            children.sort(key=lambda x: (x.get('direct_reposts', 0), x.get('timestamp', 0)), reverse=True)
            root_node['children'] = children
            
            return root_node
        
        # 构建所有转播树 - 显示所有根节点
        tree_roots = []
        
        # 1. 处理pid="2"的根节点（补充节点）
        for root_id in all_root_nodes:
            root_tree = build_complete_repost_tree(root_id)
            if root_tree:
                # 标记为补充根节点
                root_tree['is_supplementary_root'] = True
                tree_roots.append(root_tree)
        
        # 2. 处理有转发但没有pid="2"的孤立节点
        for post_id in post_details.keys():
            if post_id not in all_root_nodes and post_id not in set().union(*parent_child_map.values()):
                # 这是一个孤立的节点（既不是根节点，也不是别人的子节点）
                if parent_child_map.get(post_id):  # 但它有子节点
                    root_tree = build_complete_repost_tree(post_id)
                    if root_tree:
                        root_tree['is_isolated_root'] = True
                        tree_roots.append(root_tree)
        
        # 按转发数排序所有根节点
        tree_roots.sort(key=lambda x: x.get('direct_reposts', 0), reverse=True)
        
        # 计算统计信息
        total_nodes = sum(len(json.dumps(root).split('"id":')) - 1 for root in tree_roots)
        max_depth = 0
        agent_posts_count = 0
        
        def calculate_depth_and_stats(node, depth=0):
            nonlocal max_depth, agent_posts_count
            max_depth = max(max_depth, depth)
            if node.get('is_agent_generated'):
                agent_posts_count += 1
            for child in node.get('children', []):
                calculate_depth_and_stats(child, depth + 1)
        
        for root in tree_roots:
            calculate_depth_and_stats(root)
        
        # 构建元数据
        meta_info = {
            'total_posts': len(posts),
            'total_nodes': total_nodes,
            'max_depth': max_depth,
            'parent_child_relations': sum(len(children) for children in parent_child_map.values()),
            'supplementary_roots': len([r for r in tree_roots if r.get('is_supplementary_root')]),
            'isolated_roots': len([r for r in tree_roots if r.get('is_isolated_root')]),
            'displayed_trees': len(tree_roots),
            'data_source': data_source,
            'description': '完整转播树：显示所有节点和关系，包括补充根节点(pid=2)和孤立节点，支持缩放观察细节'
        }
        
        # 如果是融合模式，添加Agent帖子的统计信息
        if data_source == 'merged':
            meta_info.update({
                'agent_posts_count': agent_posts_count,
                'agent_posts_file': agent_posts_file,
                'original_posts_count': len(posts) - agent_posts_count
            })
        
        tree = {
            'id': 'complete_repost_tree_root',
            'children': tree_roots,
            'meta': meta_info
        }
        
        return jsonify({'tree': tree})
        
    except Exception as e:
        return jsonify({'error': f'生成完整转播树失败: {str(e)}'}), 500

@visualization_bp.route('/posts', methods=['GET'])
def get_all_posts():
    """返回所有原始帖子数据（已平铺children）"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        with open(data_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        flat_posts = flatten_posts(posts)
        return jsonify({'posts': flat_posts})
    except Exception as e:
        return jsonify({'error': f'读取帖子数据失败: {str(e)}'}), 500

@visualization_bp.route('/histogram', methods=['GET'])
def get_histogram():
    """返回指定时间范围内的所有帖子，供前端直方图使用（已平铺children）"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        with open(data_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        flat_posts = flatten_posts(posts)
        def parse_ts(ts):
            if isinstance(ts, (int, float)):
                return int(ts)
            try:
                return int(datetime.fromisoformat(ts).timestamp())
            except Exception:
                return int(ts) if str(ts).isdigit() else None
        if start_time:
            start_ts = parse_ts(start_time)
        else:
            start_ts = min(p.get('t', 0) for p in flat_posts)
        if end_time:
            end_ts = parse_ts(end_time)
        else:
            end_ts = max(p.get('t', 0) for p in flat_posts)
        filtered = [p for p in flat_posts if start_ts <= p.get('t', 0) <= end_ts]
        return jsonify({'posts': filtered})
    except Exception as e:
        return jsonify({'error': f'生成直方图数据失败: {str(e)}'}), 500

@visualization_bp.route('/timeline', methods=['GET'])
def get_timeline():
    """返回分时间点聚合的帖子列表，支持hour/day粒度（已平铺children）"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        interval = request.args.get('interval', 'hour')
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        with open(data_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        flat_posts = flatten_posts(posts)
        def parse_ts(ts):
            if isinstance(ts, (int, float)):
                return int(ts)
            try:
                return int(datetime.fromisoformat(ts).timestamp())
            except Exception:
                return int(ts) if str(ts).isdigit() else None
        if start_time:
            start_ts = parse_ts(start_time)
        else:
            start_ts = min(p.get('t', 0) for p in flat_posts)
        if end_time:
            end_ts = parse_ts(end_time)
        else:
            end_ts = max(p.get('t', 0) for p in flat_posts)
        filtered = [p for p in flat_posts if start_ts <= p.get('t', 0) <= end_ts]
        timeline_dict = {}
        for p in filtered:
            t = p.get('t', 0)
            dt = datetime.fromtimestamp(t)
            if interval == 'day':
                group_key = datetime(dt.year, dt.month, dt.day).timestamp()
            else:
                group_key = datetime(dt.year, dt.month, dt.day, dt.hour).timestamp()
            group_key = int(group_key)
            if group_key not in timeline_dict:
                timeline_dict[group_key] = []
            timeline_dict[group_key].append(p)
        timeline = []
        for t_key in sorted(timeline_dict.keys()):
            timeline.append({
                't': t_key,
                'hotness': None,
                'posts': timeline_dict[t_key]
            })
        return jsonify({'timeline': timeline})
    except Exception as e:
        return jsonify({'error': f'生成时间轴数据失败: {str(e)}'}), 500 

@visualization_bp.route('/attitude', methods=['GET'])
def get_attitude():
    """返回指定时间范围内的情绪/立场分析，支持hour/day"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        unit = request.args.get('unit', 'hour')
        # range参数暂不处理
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        with open(data_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        flat_posts = flatten_posts(posts)
        def parse_ts(ts):
            if isinstance(ts, (int, float)):
                return int(ts)
            try:
                return int(datetime.fromisoformat(ts).timestamp())
            except Exception:
                return int(ts) if str(ts).isdigit() else None
        if start_time:
            start_ts = parse_ts(start_time)
        else:
            start_ts = min(p.get('t', 0) for p in flat_posts)
        if end_time:
            end_ts = parse_ts(end_time)
        else:
            end_ts = max(p.get('t', 0) for p in flat_posts)
        filtered = [p for p in flat_posts if start_ts <= p.get('t', 0) <= end_ts]
        # 按小时分组
        hourly = {}
        for p in filtered:
            t = p.get('t', 0)
            dt = datetime.fromtimestamp(t)
            hour_key = datetime(dt.year, dt.month, dt.day, dt.hour)
            if hour_key not in hourly:
                hourly[hour_key] = []
            hourly[hour_key].append(p)
        hourly_data = []
        for k in sorted(hourly.keys()):
            group = hourly[k]
            if group:
                # 过滤掉None值并计算平均值
                emotion_scores = [p.get('emotion_score', 0) or 0 for p in group]
                stance_scores = [p.get('stance_score', 0) or 0 for p in group]
                avg_emotion = sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0
                avg_stance = sum(stance_scores) / len(stance_scores) if stance_scores else 0
            else:
                avg_emotion = 0
                avg_stance = 0
            hourly_data.append({
                'timestamp': k.isoformat(),
                'emotion': avg_emotion,
                'stance': avg_stance
            })
        # 按天分组
        daily = {}
        for p in filtered:
            t = p.get('t', 0)
            dt = datetime.fromtimestamp(t)
            day_key = datetime(dt.year, dt.month, dt.day)
            if day_key not in daily:
                daily[day_key] = []
            daily[day_key].append(p)
        daily_data = []
        for k in sorted(daily.keys()):
            group = daily[k]
            if group:
                # 过滤掉None值并计算平均值
                emotion_scores = [p.get('emotion_score', 0) or 0 for p in group]
                stance_scores = [p.get('stance_score', 0) or 0 for p in group]
                avg_emotion = sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0
                avg_stance = sum(stance_scores) / len(stance_scores) if stance_scores else 0
            else:
                avg_emotion = 0
                avg_stance = 0
            daily_data.append({
                'date': k.strftime('%Y-%m-%d'),
                'emotion': avg_emotion,
                'stance': avg_stance
            })
        return jsonify({'hourly_data': hourly_data, 'daily_data': daily_data})
    except Exception as e:
        return jsonify({'error': f'生成情绪/立场分析数据失败: {str(e)}'}), 500 

@visualization_bp.route('/wordcloud', methods=['GET'])
def get_wordcloud():
    """统计所有帖子keywords字段，生成词云数据"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
        if not os.path.exists(data_path):
            return jsonify({'error': '未找到帖子数据文件'}), 404
        with open(data_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        flat_posts = flatten_posts(posts)
        word_count = {}
        for p in flat_posts:
            keywords = p.get('keywords', []) or []  # 处理None值
            for kw in keywords:
                if not kw:
                    continue
                word_count[kw] = word_count.get(kw, 0) + 1
        words = [{"text": k, "frequency": v} for k, v in sorted(word_count.items(), key=lambda x: -x[1])]
        return jsonify({"words": words})
    except Exception as e:
        return jsonify({'error': f'生成词云数据失败: {str(e)}'}), 500 