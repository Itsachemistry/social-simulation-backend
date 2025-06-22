import pytest
from datetime import datetime
from src.world_state import WorldState


class TestWorldState:
    """WorldState类的测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.world_state = WorldState()
        
        # 测试用的普通帖子
        self.test_post = {
            "content": "这是一条测试帖子",
            "author_id": "user_001",
            "timestamp": "2024-01-01T10:00:00Z",
            "heat": 50,
            "likes": 10,
            "shares": 5
        }
        
        # 测试用的事件帖子
        self.test_event_post = {
            "content": "突发新闻：重大事件发生！",
            "author_id": "system",
            "timestamp": "2024-01-01T12:00:00Z",
            "heat": 90,
            "likes": 100,
            "shares": 50
        }
    
    def test_init(self):
        """测试初始化"""
        assert self.world_state.posts_pool == []
        assert self.world_state.get_posts_count() == 0
    
    def test_add_post_with_all_fields(self):
        """测试添加包含所有字段的帖子"""
        post_id = self.world_state.add_post(self.test_post)
        
        assert isinstance(post_id, str)
        assert self.world_state.get_posts_count() == 1
        
        # 验证帖子被正确添加
        all_posts = self.world_state.get_all_posts()
        assert len(all_posts) == 1
        assert all_posts[0]["id"] == post_id
        assert all_posts[0]["content"] == "这是一条测试帖子"
        assert all_posts[0]["author_id"] == "user_001"
    
    def test_add_post_with_minimal_fields(self):
        """测试添加只包含必要字段的帖子"""
        minimal_post = {
            "content": "最小化帖子",
            "author_id": "user_002"
        }
        
        post_id = self.world_state.add_post(minimal_post)
        
        assert isinstance(post_id, str)
        assert self.world_state.get_posts_count() == 1
        
        # 验证默认值被正确设置
        all_posts = self.world_state.get_all_posts()
        post = all_posts[0]
        assert post["id"] == post_id
        assert post["content"] == "最小化帖子"
        assert post["author_id"] == "user_002"
        assert "timestamp" in post
        assert post["heat"] == 0
        assert post["likes"] == 0
        assert post["shares"] == 0
        assert post["is_event"] == False
        assert post["priority"] == 0
    
    def test_add_post_with_existing_id(self):
        """测试添加已包含ID的帖子"""
        post_with_id = self.test_post.copy()
        post_with_id["id"] = "existing_id_123"
        
        post_id = self.world_state.add_post(post_with_id)
        
        assert post_id == "existing_id_123"
        assert self.world_state.get_posts_count() == 1
    
    def test_add_post_missing_content(self):
        """测试添加缺少content字段的帖子"""
        invalid_post = {
            "author_id": "user_001"
        }
        
        with pytest.raises(ValueError) as exc_info:
            self.world_state.add_post(invalid_post)
        assert "帖子对象必须包含content和author_id字段" in str(exc_info.value)
    
    def test_add_post_missing_author_id(self):
        """测试添加缺少author_id字段的帖子"""
        invalid_post = {
            "content": "缺少作者ID的帖子"
        }
        
        with pytest.raises(ValueError) as exc_info:
            self.world_state.add_post(invalid_post)
        assert "帖子对象必须包含content和author_id字段" in str(exc_info.value)
    
    def test_inject_event(self):
        """测试注入事件帖子"""
        # 创建一个不包含heat字段的事件帖子
        event_post_without_heat = {
            "content": "突发新闻：重大事件发生！",
            "author_id": "system",
            "timestamp": "2024-01-01T12:00:00Z",
            "likes": 100,
            "shares": 50
        }
        
        event_id = self.world_state.inject_event(event_post_without_heat)
        
        assert isinstance(event_id, str)
        assert self.world_state.get_posts_count() == 1
        
        # 验证事件帖子被正确标记
        all_posts = self.world_state.get_all_posts()
        event_post = all_posts[0]
        assert event_post["id"] == event_id
        assert event_post["is_event"] == True
        assert event_post["priority"] == 100
        assert event_post["heat"] == 80  # 事件帖子的默认热度值
    
    def test_inject_event_with_custom_heat(self):
        """测试注入自定义热度的事件帖子"""
        custom_event = self.test_event_post.copy()
        custom_event["heat"] = 95
        
        event_id = self.world_state.inject_event(custom_event)
        
        all_posts = self.world_state.get_all_posts()
        event_post = all_posts[0]
        assert event_post["heat"] == 95  # 保持自定义热度值
        assert event_post["is_event"] == True
        assert event_post["priority"] == 100
    
    def test_get_all_posts_returns_copy(self):
        """测试get_all_posts返回副本而不是引用"""
        self.world_state.add_post(self.test_post)
        
        all_posts = self.world_state.get_all_posts()
        original_length = len(all_posts)
        
        # 修改返回的列表不应该影响原始数据
        all_posts.append({"id": "test_post"})
        
        assert self.world_state.get_posts_count() == 1
        assert len(all_posts) == original_length + 1
    
    def test_get_event_posts(self):
        """测试获取事件帖子"""
        # 添加普通帖子
        self.world_state.add_post(self.test_post)
        
        # 添加事件帖子
        self.world_state.inject_event(self.test_event_post)
        
        # 添加另一个普通帖子
        another_post = self.test_post.copy()
        another_post["content"] = "另一条普通帖子"
        self.world_state.add_post(another_post)
        
        # 验证只有事件帖子被返回
        event_posts = self.world_state.get_event_posts()
        assert len(event_posts) == 1
        assert event_posts[0]["is_event"] == True
        assert event_posts[0]["content"] == "突发新闻：重大事件发生！"
    
    def test_get_event_posts_empty(self):
        """测试获取事件帖子（无事件帖子时）"""
        self.world_state.add_post(self.test_post)
        
        event_posts = self.world_state.get_event_posts()
        assert event_posts == []
    
    def test_clear_posts(self):
        """测试清空帖子池"""
        # 添加一些帖子
        self.world_state.add_post(self.test_post)
        self.world_state.inject_event(self.test_event_post)
        
        assert self.world_state.get_posts_count() == 2
        
        # 清空帖子池
        self.world_state.clear_posts()
        
        assert self.world_state.get_posts_count() == 0
        assert self.world_state.get_all_posts() == []
        assert self.world_state.get_event_posts() == []
    
    def test_multiple_posts_management(self):
        """测试多个帖子的管理"""
        # 添加多个帖子
        post_ids = []
        for i in range(5):
            post = self.test_post.copy()
            post["content"] = f"帖子 {i+1}"
            post["author_id"] = f"user_{i+1:03d}"
            post_id = self.world_state.add_post(post)
            post_ids.append(post_id)
        
        # 添加一个事件帖子
        event_id = self.world_state.inject_event(self.test_event_post)
        
        # 验证总数
        assert self.world_state.get_posts_count() == 6
        
        # 验证事件帖子
        event_posts = self.world_state.get_event_posts()
        assert len(event_posts) == 1
        assert event_posts[0]["id"] == event_id
        
        # 验证所有帖子
        all_posts = self.world_state.get_all_posts()
        assert len(all_posts) == 6
        
        # 验证帖子ID都是唯一的
        post_ids_in_pool = [post["id"] for post in all_posts]
        assert len(set(post_ids_in_pool)) == 6