from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from collections import defaultdict
import statistics
import jieba
import os

analysis_bp = Blueprint('analysis', __name__)

def normalize_post(post):
    """
    直接返回原始post对象，不做字段名映射。
    """
    return dict(post)

def load_original_posts():
    """加载原始帖子数据"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'postdata.json')
    if not os.path.exists(data_path):
        return []
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
        """
        all_posts = simulation_results.get('final_posts', [])
        if time_range:
            all_posts = self._filter_by_time_range(all_posts, time_range)
        group_func = self.granularity_functions.get(granularity, self._group_by_day)
        grouped_posts = group_func(all_posts)
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
        """分析一组帖子（只统计核心字段）"""
        if not posts:
            return {
                'post_count': 0,
                'emotion_distribution': {},
                'stance_distribution': {},
                'top_authors': [],
                'hot_topics': []
            }
        post_count = len(posts)
        emotion_counts = defaultdict(int)
        stance_counts = defaultdict(int)
        author_counts = defaultdict(int)
        for post in posts:
            post = normalize_post(post)
            # 情感分布
            emotion = post.get('emotion_score', post.get('emotion', 'neutral'))
            emotion_counts[emotion] += 1
            # 立场分布
            stance = post.get('stance_score', post.get('stance', 'neutral'))
            stance_counts[stance] += 1
            # 作者统计
            author = post.get('author_id', post.get('uid', 'unknown'))
            author_counts[author] += 1
        hot_topics = self._extract_hot_topics(posts)
        return {
            'post_count': post_count,
            'emotion_distribution': dict(emotion_counts),
            'stance_distribution': dict(stance_counts),
            'top_authors': sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'hot_topics': hot_topics
        }

    def _extract_hot_topics(self, posts, top_n=5):
        """提取热门话题（分词统计content字段）"""
        keyword_counts = defaultdict(int)
        stopwords = set(["的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        for post in posts:
            post = normalize_post(post)
            content = post.get('content', post.get('text', ''))
            words = jieba.lcut(content)
            for word in words:
                if len(word) > 1 and word not in stopwords:
                    keyword_counts[word] += 1
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
        
        # 从仿真管理器获取结果（这里需要导入simulation_manager
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        
        if not status:
            return jsonify({'error': '仿真不存在'}), 404
        
        if status['status'] != 'completed':
            return jsonify({'error': '仿真尚未完成'}), 400
        
        # 获取仿真结果
        agent_generated_posts = status['results'].get('agent_generated_posts', [])
        # 合并原始数据
        original_posts = load_original_posts()
        all_posts = original_posts + agent_generated_posts

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

@analysis_bp.route('/wordcloud', methods=['POST'])
def get_wordcloud():
    """
    统计所有帖子keywords字段，生成词云数据
    """
    try:
        data = request.json
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({'error': '缺少simulation_id参数'}), 400
        from .simulation_service import simulation_manager
        status = simulation_manager.get_simulation_status(simulation_id)
        if not status or status.get('status') != 'completed':
            return jsonify({'error': '仿真不存在或未完成'}), 404
        # 获取所有Agent生成的帖子
        agent_generated_posts = status['results'].get('agent_generated_posts', [])
        # 合并原始数据
        original_posts = load_original_posts()
        all_posts = original_posts + agent_generated_posts
        keyword_counts = defaultdict(int)
        for post in all_posts:
            for kw in post.get('keywords', []):
                keyword_counts[kw] += 1
        wordcloud = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify({'status': 'success', 'wordcloud': [{'word': w, 'count': c} for w, c in wordcloud]})
    except Exception as e:
        return jsonify({'error': f'词云统计失败: {str(e)}'}), 500 