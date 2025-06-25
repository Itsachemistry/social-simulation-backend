from typing import Dict, List, Any
from datetime import datetime
import uuid


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
        "parent_post_id": str|None  # 新增：转发自哪条帖子
    }
    """
    
    def __init__(self):
        """初始化世界状态管理器"""
        self.posts_pool: List[Dict[str, Any]] = []
    
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
