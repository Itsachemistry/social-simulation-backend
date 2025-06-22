import pytest
import sys
import os
from datetime import datetime

# 确保可以导入src模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.insert(0, os.getcwd())
from src.time_manager import TimeSliceManager
print("导入成功！")


class TestTimeSliceManager:
    """TimeSliceManager类的测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.test_posts = [
            {
                "id": "post_001",
                "content": "第一条帖子",
                "author": "user_001",
                "timestamp": "2024-01-01T10:00:00Z",
                "likes": 10,
                "shares": 5
            },
            {
                "id": "post_002",
                "content": "第二条帖子",
                "author": "user_002", 
                "timestamp": "2024-01-01T11:00:00Z",
                "likes": 20,
                "shares": 8
            },
            {
                "id": "post_003",
                "content": "第三条帖子",
                "author": "user_003",
                "timestamp": "2024-01-01T09:00:00Z",
                "likes": 15,
                "shares": 3
            },
            {
                "id": "post_004",
                "content": "第四条帖子",
                "author": "user_004",
                "timestamp": "2024-01-01T12:00:00Z",
                "likes": 25,
                "shares": 10
            }
        ]
    
    def test_init_with_valid_posts(self):
        """测试使用有效帖子数据初始化"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        
        assert time_manager.total_posts == 4
        assert time_manager.total_slices == 2
        assert len(time_manager.get_all_posts()) == 4
    
    def test_init_with_empty_posts(self):
        """测试使用空帖子列表初始化"""
        time_manager = TimeSliceManager([], slice_size=5)
        
        assert time_manager.total_posts == 0
        assert time_manager.total_slices == 0
        assert time_manager.get_all_posts() == []
    
    def test_posts_sorted_by_timestamp(self):
        """测试帖子按时间戳排序"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        sorted_posts = time_manager.get_all_posts()
        
        # 验证帖子按时间戳升序排列
        timestamps = [post["timestamp"] for post in sorted_posts]
        expected_timestamps = [
            "2024-01-01T09:00:00Z",  # post_003
            "2024-01-01T10:00:00Z",  # post_001
            "2024-01-01T11:00:00Z",  # post_002
            "2024-01-01T12:00:00Z"   # post_004
        ]
        
        assert timestamps == expected_timestamps
    
    def test_get_slice_valid_index(self):
        """测试获取有效索引的时间片"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        
        # 获取第一个时间片
        slice_0 = time_manager.get_slice(0)
        assert len(slice_0) == 2
        assert slice_0[0]["id"] == "post_003"  # 最早的时间戳
        assert slice_0[1]["id"] == "post_001"
        
        # 获取第二个时间片
        slice_1 = time_manager.get_slice(1)
        assert len(slice_1) == 2
        assert slice_1[0]["id"] == "post_002"
        assert slice_1[1]["id"] == "post_004"
    
    def test_get_slice_invalid_index(self):
        """测试获取无效索引的时间片"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        
        # 测试负数索引
        with pytest.raises(IndexError) as exc_info:
            time_manager.get_slice(-1)
        assert "时间片索引 -1 超出范围" in str(exc_info.value)
        
        # 测试超出范围的索引
        with pytest.raises(IndexError) as exc_info:
            time_manager.get_slice(2)
        assert "时间片索引 2 超出范围" in str(exc_info.value)
    
    def test_get_slice_with_remainder(self):
        """测试处理不能整除的时间片"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=3)
        
        # 应该有2个时间片：第一个3个帖子，第二个1个帖子
        assert time_manager.total_slices == 2
        
        slice_0 = time_manager.get_slice(0)
        assert len(slice_0) == 3
        
        slice_1 = time_manager.get_slice(1)
        assert len(slice_1) == 1
    
    def test_properties(self):
        """测试属性方法"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        
        assert time_manager.total_posts == 4
        assert time_manager.total_slices == 2
    
    def test_get_all_posts_returns_copy(self):
        """测试get_all_posts返回副本而不是引用"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=2)
        
        all_posts = time_manager.get_all_posts()
        original_length = len(all_posts)
        
        # 修改返回的列表不应该影响原始数据
        all_posts.append({"id": "test_post"})
        
        assert len(time_manager.get_all_posts()) == original_length
        assert len(all_posts) == original_length + 1
    
    def test_slice_size_one(self):
        """测试时间片大小为1的情况"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=1)
        
        assert time_manager.total_slices == 4
        
        for i in range(4):
            slice_data = time_manager.get_slice(i)
            assert len(slice_data) == 1
    
    def test_slice_size_larger_than_posts(self):
        """测试时间片大小大于帖子总数的情况"""
        time_manager = TimeSliceManager(self.test_posts, slice_size=10)
        
        assert time_manager.total_slices == 1
        slice_data = time_manager.get_slice(0)
        assert len(slice_data) == 4
