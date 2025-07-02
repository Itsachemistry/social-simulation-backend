from typing import Dict, List, Any
from datetime import datetime
import uuid
import re


class WorldState:
    """
    世界状态管理器，负责维护动态帖子池和全局事件注入。
    
    帖子数据结构：
    {
        "id": str,              # 帖子唯一标识符
        "content": str,         # 帖子内容
        "author_id": str,       # 作者ID
        "timestamp": str,       # ISO格式时间戳
        "heat": int,           # 热度值 (0-100)
        "likes": int,          # 点赞数
        "shares": int,         # 分享数
        "is_event": bool,      # 是否为突发事件
        "priority": int,       # 优先级 (普通帖子=0, 事件帖子>0)
        "is_repost": bool,     # 是否为转发
        "parent_post_id": str|None,  # 转发自哪条帖子
        "tags": List[str]      # 新增：微博标签列表，如 ["#科技#", "#创新#"]
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
        统一标准化post对象的字段名，兼容不同来源的数据格式。
        主要兼容以下字段：
        - 'children'/'Children'：子节点列表，树结构用
        - 'author_id'/'uid'：作者ID
        - 'timestamp'/'t'：时间戳
        - 'parent_post_id'/'pid'：父帖ID
        - 'stance'/'group'：立场标签，group字段（0/1/2）直接映射为stance（2=支持医院，1=支持患者，0=中立）
        - 其他字段如'content'、'id'、'tags'等保持不变
        - 详细说明见每个字段注释
        - 'tags'：本系统当前不使用标签功能，tags字段始终为空列表
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
        # 兼容stance/group
        if 'stance' not in std and 'group' in std:
            std['stance'] = std['group']  # group字段直接作为stance
        # 兼容totalChildren/heat
        if 'heat' not in std and 'totalChildren' in std:
            std['heat'] = std['totalChildren']
        # 兼容tags为空的情况（本系统不使用标签功能，tags始终为空）
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
        if "id" not in post_object:
            post_object["id"] = str(uuid.uuid4())
        
        # 设置时间戳（如果未提供）
        if "timestamp" not in post_object:
            post_object["timestamp"] = datetime.now().isoformat()
        
        # 设置默认值
        post_object.setdefault("heat", 0)
        post_object.setdefault("likes", 0)
        post_object.setdefault("shares", 0)
        post_object.setdefault("is_event", False)
        post_object.setdefault("priority", 0)
        post_object.setdefault("is_repost", False)
        post_object.setdefault("parent_post_id", None)
        
        # 强制tags为空（本系统不使用标签功能）
        post_object['tags'] = []
        
        # 添加到帖子池
        self.posts_pool.append(post_object)
        
        return post_object["id"]
    
    def inject_event(self, event_post_object: Dict[str, Any]) -> str:
        """
        强制插入一个高权重的突发事件帖子
        
        Args
            event_post_object (Dict[str, Any]): 事件帖子对象
            
        Returns:
            str: 新添加事件帖子的ID
        """
        event_post_object = self.normalize_post(event_post_object)  # 字段标准化
        # 标记为事件帖子
        event_post_object["is_event"] = True
        event_post_object["priority"] = 100  # 事件帖子具有高优先级
        
        # 设置较高的热度值（如果未提供则使用默认值）
        event_post_object.setdefault("heat", 80)
        
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
        获取所有事件帖子
        
        Returns:
            List[Dict[str, Any]]: 事件帖子列表
        """
        return [post for post in self.posts_pool if post.get("is_event", False)]
    
    def clear_posts(self) -> None:
        """
        清空帖子池
        
        Returns:
            None
        """
        self.posts_pool.clear()
