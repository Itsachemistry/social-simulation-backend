from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from collections import defaultdict
import statistics
import jieba

analysis_bp = Blueprint('analysis', __name__)

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

class TemporalAnalyzer:
    """时间粒度分析器"""
    
    def __init__(self):
        self.granularity_functions = {
            'hour': self._group_by_hour,
            'day': self._group_by_day,
            'week': self._group_by_week
        }
    
    def analyze_simulation_results(self, simulation_results, granularity='day', time_range=None):
        """
        按时间粒度分析仿真结果
        
        Args:
            simulation_results: 仿真结果数据
            granularity: 时间粒度 ('hour', 'day', 'week')
            time_range: 时间范围 {'start': '2024-01-01T00:00:00', 'end': '2024-01-31T23:59:59'}
        
        Returns:
            dict: 按时间粒度聚合的分析结果
        """
        # 提取所有帖子
        all_posts = simulation_results.get('final_posts', [])
        
        # 过滤时间范围
        if time_range:
            all_posts = self._filter_by_time_range(all_posts, time_range)
        
        # 按时间粒度分组
        group_func = self.granularity_functions.get(granularity, self._group_by_day)
        grouped_posts = group_func(all_posts)
        
        # 分析每个时间组
        analysis_results = {}
        for time_key, posts in grouped_posts.items():
            analysis_results[time_key] = self._analyze_posts_group(posts)
        
        return {
            'granularity': granularity,
            'time_range': time_range,
            'total_posts': len(all_posts),
            'time_groups': len(grouped_posts),
            'analysis': analysis_results
        }
    
    def _filter_by_time_range(self, posts, time_range):
        """按时间范围过滤帖子"""
        start_time = datetime.fromisoformat(time_range['start'])
        end_time = datetime.fromisoformat(time_range['end'])
        
        filtered_posts = []
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_time = datetime.fromisoformat(post.get('timestamp', ''))
            if start_time <= post_time <= end_time:
                filtered_posts.append(post)
        
        return filtered_posts
    
    def _group_by_hour(self, posts):
        """按小时分组"""
        grouped = defaultdict(list)
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_time = datetime.fromisoformat(post.get('timestamp', ''))
            hour_key = post_time.strftime('%Y-%m-%d %H:00')
            grouped[hour_key].append(post)
        return dict(grouped)
    
    def _group_by_day(self, posts):
        """按天分组"""
        grouped = defaultdict(list)
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_time = datetime.fromisoformat(post.get('timestamp', ''))
            day_key = post_time.strftime('%Y-%m-%d')
            grouped[day_key].append(post)
        return dict(grouped)
    
    def _group_by_week(self, posts):
        """按周分组"""
        grouped = defaultdict(list)
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            post_time = datetime.fromisoformat(post.get('timestamp', ''))
            # 获取该周的周一作为周标识
            week_start = post_time - timedelta(days=post_time.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            grouped[week_key].append(post)
        return dict(grouped)
    
    def _analyze_posts_group(self, posts):
        """分析一组帖子"""
        if not posts:
            return {
                'post_count': 0,
                'avg_heat': 0,
                'total_likes': 0,
                'total_shares': 0,
                'emotion_distribution': {},
                'stance_distribution': {},
                'top_authors': [],
                'hot_topics': []
            }
        
        # 基础统计
        post_count = len(posts)
        heats = [post.get('heat', 0) for post in posts]
        likes = [post.get('likes', 0) for post in posts]
        shares = [post.get('shares', 0) for post in posts]
        
        # 情感分布
        emotion_counts = defaultdict(int)
        stance_counts = defaultdict(int)
        author_counts = defaultdict(int)
        
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            # 情感分析（如果有）
            emotion = post.get('emotion', 'neutral')
            emotion_counts[emotion] += 1
            
            # 立场分析（如果有）
            stance = post.get('stance', 'neutral')
            stance_counts[stance] += 1
            
            # 作者统计
            author = post.get('author_id', 'unknown')
            author_counts[author] += 1
        
        # 热度话题（按内容关键词）
        hot_topics = self._extract_hot_topics(posts)
        
        return {
            'post_count': post_count,
            'avg_heat': statistics.mean(heats) if heats else 0,
            'max_heat': max(heats) if heats else 0,
            'total_likes': sum(likes),
            'total_shares': sum(shares),
            'emotion_distribution': dict(emotion_counts),
            'stance_distribution': dict(stance_counts),
            'top_authors': sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'hot_topics': hot_topics
        }
    
    def _extract_hot_topics(self, posts, top_n=5):
        """提取热门话题（适配中文微博文本，使用jieba分词）"""
        keyword_counts = defaultdict(int)
        stopwords = set(["的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        for post in posts:
            post = normalize_post(post)  # 字段标准化
            content = post.get('content', '')
            # 使用jieba分词
            words = jieba.lcut(content)
            for word in words:
                if len(word) > 1 and word not in stopwords:
                    keyword_counts[word] += 1
        # 返回前N个热门关键词
        return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

# 创建全局分析器
temporal_analyzer = TemporalAnalyzer()

@analysis_bp.route('/temporal', methods=['POST'])
def analyze_temporal():
    """按时间粒度分析仿真结果"""
    try:
        data = request.json
        if data is None:
            return jsonify({'error': '无效的JSON数据'}), 400
            
        simulation_id = data.get('simulation_id')
        granularity = data.get('granularity', 'day')  # hour, day, week 默认值是day
        time_range = data.get('time_range')  # 可选的时间范围
        
        if not simulation_id:
            return jsonify({'error': '缺少simulation_id参数'}), 400
        
        # 从仿真管理器获取结果（这里需要导入simulation_manager）
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        
        if not status:
            return jsonify({'error': '仿真不存在'}), 404
        
        if status['status'] != 'completed':
            return jsonify({'error': '仿真尚未完成'}), 400
        
        # 执行时间粒度分析
        analysis_result = temporal_analyzer.analyze_simulation_results(
            status['results'],
            granularity=granularity,
            time_range=time_range
        )
        
        return jsonify({
            'status': 'success',
            'simulation_id': simulation_id,
            'analysis': analysis_result
        })
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@analysis_bp.route('/comparison', methods=['POST'])
def compare_temporal():
    """对比多个仿真的时间粒度分析"""
    try:
        data = request.json
        if data is None:
            return jsonify({'error': '无效的JSON数据'}), 400
            
        simulation_ids = data.get('simulation_ids', [])
        granularity = data.get('granularity', 'day')
        time_range = data.get('time_range')
        
        if len(simulation_ids) < 2:
            return jsonify({'error': '至少需要两个仿真ID进行对比'}), 400
        
        from .simulation_service import simulation_manager
        
        comparison_results = {}
        for sim_id in simulation_ids:
            status = simulation_manager.get_simulation_status(sim_id)
            if status and status['status'] == 'completed':
                analysis_result = temporal_analyzer.analyze_simulation_results(
                    status['results'],
                    granularity=granularity,
                    time_range=time_range
                )
                comparison_results[sim_id] = analysis_result
        
        return jsonify({
            'status': 'success',
            'granularity': granularity,
            'time_range': time_range,
            'comparison': comparison_results
        })
        
    except Exception as e:
        return jsonify({'error': f'对比分析失败: {str(e)}'}), 500

@analysis_bp.route('/granularities', methods=['GET'])
def get_available_granularities():
    """获取支持的时间粒度"""
    return jsonify({
        'status': 'success',
        'granularities': [
            {'value': 'hour', 'label': '按小时'},
            {'value': 'day', 'label': '按天'},
            {'value': 'week', 'label': '按周'}
        ]
    }) 