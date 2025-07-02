from typing import List, Dict, Any
from datetime import datetime


class TimeSliceManager:
    """
    时间片管理器类，负责将帖子按时间戳排序并划分为时间片。
    
    该类接收一个帖子列表和每个时间片的帖子数量，将帖子按时间戳排序后
    划分为多个时间片，提供获取指定时间片的功能。
    """
    
    def __init__(self, posts: List[Dict[str, Any]], slice_size: int):
        """
        初始化时间片管理器。
        
        Args:
            posts (List[Dict[str, Any]]): 帖子列表，每个帖子应包含timestamp字段
            slice_size (int): 每个时间片包含的帖子数量
            
        Raises:
            ValueError: 当slice_size小于等于0时
            KeyError: 当帖子缺少timestamp字段时
        """
        if slice_size <= 0:
            raise ValueError("时间片大小必须大于0")
        
        # 验证所有帖子都有timestamp字段
        for i, post in enumerate(posts):
            if 'timestamp' not in post:
                raise KeyError(f"帖子 {i} 缺少timestamp字段")
        
        # 过滤掉热度为0的帖子
        filtered_posts = [p for p in posts if p.get('heat', 0) > 0]
        self._posts = sorted(filtered_posts, key=lambda x: x['timestamp'])
        self._slice_size = slice_size
        
        # 计算总时间片数
        self._total_slices = (len(self._posts) + slice_size - 1) // slice_size
    
    def get_slice(self, slice_index: int) -> List[Dict[str, Any]]:
        """
        获取指定索引的时间片。
        
        Args:
            slice_index (int): 时间片索引，从0开始
            
        Returns:
            List[Dict[str, Any]]: 指定时间片的帖子列表
            
        Raises:
            IndexError: 当slice_index超出范围时
        """
        if slice_index < 0 or slice_index >= self._total_slices:
            raise IndexError(f"时间片索引 {slice_index} 超出范围 (0-{self._total_slices - 1})")
        
        start_index = slice_index * self._slice_size
        end_index = min(start_index + self._slice_size, len(self._posts))
        
        return self._posts[start_index:end_index]
    
    @property
    def total_slices(self) -> int:
        """
        获取总时间片数量。
        
        Returns:
            int: 总时间片数量
        """
        return self._total_slices
    
    @property
    def total_posts(self) -> int:
        """
        获取总帖子数量。
        
        Returns:
            int: 总帖子数量
        """
        return len(self._posts)
    
    def get_all_posts(self) -> List[Dict[str, Any]]:
        """
        获取所有已排序的帖子。
        
        Returns:
            List[Dict[str, Any]]: 按时间戳排序的所有帖子
        """
        return self._posts.copy()