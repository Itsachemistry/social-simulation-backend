from typing import Dict, List, Any
from datetime import datetime
import uuid
import re


class WorldState:
    """
    世界状态管理器，负责维护动态帖子池和全局事件注入。
    
    帖子数据结构（符合标准定义）：
    {
        "post_id": str,                    # 帖子唯一标识符
        "author_id": str,                  # 作者ID
        "content": str,                    # 帖子内容
        "timestamp": str,                  # ISO格式时间戳
        "emotion_category": str,           # 情绪类别 (positive/neutral/negative)
        "emotion_score": float,            # 情绪分值 (-1.0~1.0)
        "stance_category": str,            # 立场类别 (support/neutral/oppose)
        "stance_score": float,             # 立场分值 (-1.0~1.0)
        "information_strength": float,     # 信息强度 (0.0~1.0)
        "keywords": List[str],             # 关键词列表
        "is_repost": bool,                 # 是否为转发
        "parent_post_id": str|None         # 转发自哪条帖子
    }
    """
    
    def __init__(self):
        """初始化世界状态管理器"""
        self.posts_pool: List[Dict[str, Any]] = []
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """
        从帖子内容中提取微博标签（#XXXX#格式）
        
        Args:
            content (str): 帖子内容
            
        Returns:
            List[str]: 提取到的标签列表
        """
        # 匹配 #XXXX# 格式的标签
        hashtag_pattern = r'#([^#]+)#'
        hashtags = re.findall(hashtag_pattern, content)
        return hashtags
    
    def normalize_post(self, post):
        """
        统一标准化post对象的字段名，转换为标准属性定义。
        主要兼容以下字段：
        - 'id'/'mid' → 'post_id'：帖子ID
        - 'author_id'/'uid'：作者ID
        - 'content'/'text'：帖子内容
        - 'timestamp'/'t'：时间戳
        - 'emotion_score'：情绪分值
        - 'stance_score'：立场分值
        - 'information_strength'：信息强度
        - 'parent_post_id'/'pid'：父帖ID
        - 'keywords'：关键词列表
        """
        std = dict(post)  # 拷贝，避免原数据被修改
        
        # 兼容post_id字段
        if 'post_id' not in std:
            if 'id' in std:
                std['post_id'] = std['id']
            elif 'mid' in std:
                std['post_id'] = std['mid']
            else:
                std['post_id'] = str(std.get('uid', '')) + '_' + str(std.get('t', ''))
        
        # 兼容author_id/uid
        if 'author_id' not in std and 'uid' in std:
            std['author_id'] = std['uid']
        
        # 兼容content/text
        if 'content' not in std and 'text' in std:
            std['content'] = std['text']
        elif 'content' not in std:
            std['content'] = ''
        
        # 兼容timestamp/t
        if 'timestamp' not in std and 't' in std:
            std['timestamp'] = std['t']
        
        # 兼容parent_post_id/pid
        if 'parent_post_id' not in std and 'pid' in std:
            std['parent_post_id'] = std['pid']
        
        # 设置默认值
        std.setdefault('emotion_score', 0.0)
        std.setdefault('stance_score', 0.0)
        std.setdefault('information_strength', 0.5)
        std.setdefault('keywords', [])
        std.setdefault('is_repost', False)
        
        # 设置情绪和立场类别（处理None值）
        emotion_score = std.get('emotion_score', 0.0)
        if emotion_score is None:
            emotion_score = 0.0
        if emotion_score > 0.3:
            std['emotion_category'] = 'positive'
        elif emotion_score < -0.3:
            std['emotion_category'] = 'negative'
        else:
            std['emotion_category'] = 'neutral'
        
        stance_score = std.get('stance_score', 0.0)
        if stance_score is None:
            stance_score = 0.0
        if stance_score > 0.3:
            std['stance_category'] = 'support'
        elif stance_score < -0.3:
            std['stance_category'] = 'oppose'
        else:
            std['stance_category'] = 'neutral'
        
        return std
    
    def add_post(self, post_object: Dict[str, Any]) -> str:
        """
        向帖子池中添加新的帖子（由Agent生成）
        
        Args:
            post_object (Dict[str, Any]): 帖子对象，必须包含content和author_id字段
            
        Returns:
            str: 新添加帖子的ID
            
        Raises:
            ValueError: 当帖子对象缺少必要字段时
        """
        post_object = self.normalize_post(post_object)  # 字段标准化
        # 验证必要字段
        if "content" not in post_object or "author_id" not in post_object:
            raise ValueError("帖子对象必须包含content和author_id字段")
        
        # 生成帖子ID（如果未提供）
        if "post_id" not in post_object:
            post_object["post_id"] = str(uuid.uuid4())
        
        # 设置时间戳（如果未提供）
        if "timestamp" not in post_object:
            post_object["timestamp"] = datetime.now().isoformat()
        
        # 设置默认值
        post_object.setdefault("emotion_score", 0.0)
        post_object.setdefault("stance_score", 0.0)
        post_object.setdefault("information_strength", 0.5)
        post_object.setdefault("keywords", [])
        post_object.setdefault("is_repost", False)
        post_object.setdefault("parent_post_id", None)
        
        # 添加到帖子池
        self.posts_pool.append(post_object)
        
        return post_object["post_id"]
    
    def inject_event(self, event_post_object: Dict[str, Any]) -> str:
        """
        强制插入一个高权重的突发事件帖子
        
        Args:
            event_post_object (Dict[str, Any]): 事件帖子对象
            
        Returns:
            str: 新添加事件帖子的ID
        """
        event_post_object = self.normalize_post(event_post_object)  # 字段标准化
        
        # 设置事件帖子的特殊属性
        event_post_object["information_strength"] = 1.0  # 事件帖子具有最高信息强度
        
        # 使用add_post方法添加帖子
        return self.add_post(event_post_object)
    
    def get_all_posts(self) -> List[Dict[str, Any]]:
        """
        返回当前池中所有的帖子
        
        Returns:
            List[Dict[str, Any]]: 帖子列表的副本
        """
        return self.posts_pool.copy()
    
    def get_posts_count(self) -> int:
        """
        获取当前帖子池中的帖子数量
        
        Returns:
            int: 帖子数量
        """
        return len(self.posts_pool)
    
    def get_event_posts(self) -> List[Dict[str, Any]]:
        """
        获取所有事件帖子（信息强度为1.0的帖子）
        
        Returns:
            List[Dict[str, Any]]: 事件帖子列表
        """
        return [post for post in self.posts_pool if post.get("information_strength", 0.0) >= 1.0]
    
    def clear_posts(self) -> None:
        """
        清空帖子池
        
        Returns:
            None
        """
        self.posts_pool.clear()
