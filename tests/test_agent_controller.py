import pytest
from src.agent_controller import AgentController, PlaceholderAgent


class TestAgentController:
    """AgentController类的测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 测试用的Agent配置
        self.test_agent_configs = [
            {
                "agent_id": "leader_001",
                "type": "意见领袖",
                "stance": 0.8,
                "interests": ["政治", "经济"],
                "influence": 2.0
            },
            {
                "agent_id": "rule_001", 
                "type": "规则Agent",
                "stance": 0.5,
                "interests": ["规则", "秩序"],
                "influence": 1.5
            },
            {
                "agent_id": "user_001",
                "type": "普通用户",
                "stance": 0.3,
                "interests": ["娱乐", "科技"],
                "influence": 1.0
            },
            {
                "agent_id": "user_002",
                "type": "普通用户", 
                "stance": 0.7,
                "interests": ["体育", "健康"],
                "influence": 1.0
            }
        ]
        
        # 测试用的帖子数据
        self.test_posts = [
            {
                "id": "post_001",
                "content": "高热度政治话题",
                "author_id": "author_001",
                "heat": 80,
                "likes": 100,
                "shares": 50
            },
            {
                "id": "post_002", 
                "content": "中等热度娱乐话题",
                "author_id": "author_002",
                "heat": 60,
                "likes": 50,
                "shares": 20
            },
            {
                "id": "post_003",
                "content": "低热度科技话题", 
                "author_id": "author_003",
                "heat": 30,
                "likes": 10,
                "shares": 5
            },
            {
                "id": "post_004",
                "content": "规则相关话题",
                "author_id": "author_004", 
                "heat": 40,
                "likes": 30,
                "shares": 15
            }
        ]
        
        # 创建AgentController实例
        self.agent_controller = AgentController(self.test_agent_configs)
    
    def test_init(self):
        """测试初始化"""
        assert len(self.agent_controller.agents) == 3
        assert "意见领袖" in self.agent_controller.agents
        assert "规则Agent" in self.agent_controller.agents
        assert "普通用户" in self.agent_controller.agents
        
        # 验证Agent分组
        assert len(self.agent_controller.agents["意见领袖"]) == 1
        assert len(self.agent_controller.agents["规则Agent"]) == 1
        assert len(self.agent_controller.agents["普通用户"]) == 2
    
    def test_action_priority_order(self):
        """测试行动优先级顺序"""
        expected_order = ["意见领袖", "规则Agent", "普通用户"]
        sorted_types = sorted(
            self.agent_controller.action_priority.keys(),
            key=lambda x: self.agent_controller.action_priority[x]
        )
        
        assert sorted_types == expected_order
    
    def test_get_total_agents_count(self):
        """测试获取Agent总数"""
        total_count = self.agent_controller._get_total_agents_count()
        assert total_count == 4
    
    def test_heat_threshold_for_different_agent_types(self):
        """测试不同Agent类型的热度阈值"""
        # 获取不同类型的Agent
        leader_agent = self.agent_controller.agents["意见领袖"][0]
        rule_agent = self.agent_controller.agents["规则Agent"][0]
        user_agent = self.agent_controller.agents["普通用户"][0]
        
        # 验证热度阈值
        assert self.agent_controller._get_heat_threshold_for_agent(leader_agent) == 30
        assert self.agent_controller._get_heat_threshold_for_agent(rule_agent) == 20
        assert self.agent_controller._get_heat_threshold_for_agent(user_agent) == 50
    
    def test_heat_filtering(self):
        """测试热度筛选逻辑"""
        user_agent = self.agent_controller.agents["普通用户"][0]
        
        # 生成个性化信息流
        personalized_posts = self.agent_controller._generate_personalized_feed(
            user_agent, self.test_posts
        )
        
        # 验证所有返回的帖子热度都达到阈值
        heat_threshold = self.agent_controller._get_heat_threshold_for_agent(user_agent)
        for post in personalized_posts:
            assert post.get("heat", 0) >= heat_threshold
    
    def test_stance_similarity_calculation(self):
        """测试立场相似度计算"""
        agent = self.agent_controller.agents["意见领袖"][0]
        post = self.test_posts[0]
        
        similarity = self.agent_controller._calculate_stance_similarity(agent, post)
        
        # 验证相似度在合理范围内
        assert 0.0 <= similarity <= 1.0
    
    def test_interest_match_check(self):
        """测试兴趣匹配检查"""
        agent = self.agent_controller.agents["意见领袖"][0]  # 兴趣：["政治", "经济"]
        
        # 测试匹配的帖子
        political_post = {"content": "政治话题", "interests": ["政治"]}
        assert self.agent_controller._check_interest_match(agent, political_post) == True
        
        # 测试不匹配的帖子
        sports_post = {"content": "体育话题", "interests": ["体育"]}
        assert self.agent_controller._check_interest_match(agent, sports_post) == False
    
    def test_personalized_feed_generation(self):
        """测试个性化信息流生成"""
        agent = self.agent_controller.agents["意见领袖"][0]
        
        personalized_posts = self.agent_controller._generate_personalized_feed(
            agent, self.test_posts
        )
        
        # 验证返回的帖子数量合理
        assert len(personalized_posts) <= len(self.test_posts)
        
        # 验证帖子按热度降序排序
        if len(personalized_posts) > 1:
            for i in range(len(personalized_posts) - 1):
                assert personalized_posts[i].get("heat", 0) >= personalized_posts[i+1].get("heat", 0)
    
    def test_run_time_slice_basic(self):
        """测试时间片执行的基本流程"""
        current_slice_posts = [self.test_posts[0]]
        
        results = self.agent_controller.run_time_slice(current_slice_posts, self.test_posts)
        
        # 验证返回结果结构
        assert "processed_agents" in results
        assert "generated_actions" in results
        assert "agent_actions" in results
        
        # 验证处理了所有Agent
        assert results["processed_agents"] == 4
        assert results["generated_actions"] == 4
        
        # 验证每个Agent都有行动记录
        assert len(results["agent_actions"]) == 4
        for agent_id in ["leader_001", "rule_001", "user_001", "user_002"]:
            assert agent_id in results["agent_actions"]
    
    def test_agent_actions_structure(self):
        """测试Agent行动记录的结构"""
        current_slice_posts = [self.test_posts[0]]
        
        results = self.agent_controller.run_time_slice(current_slice_posts, self.test_posts)
        
        # 验证每个Agent的行动记录结构
        for agent_id, action in results["agent_actions"].items():
            assert "action_type" in action
            assert "processed_posts" in action
            assert "generated_content" in action
    
    def test_unknown_agent_type_handling(self):
        """测试未知Agent类型的处理"""
        unknown_config = {
            "agent_id": "unknown_001",
            "type": "未知类型",
            "stance": 0.5,
            "interests": ["测试"],
            "influence": 1.0
        }
        
        controller = AgentController([unknown_config])
        
        # 验证未知类型被归类为普通用户
        assert len(controller.agents["普通用户"]) == 1
        assert controller.agents["普通用户"][0].agent_id == "unknown_001"
    
    def test_empty_agent_configs(self):
        """测试空Agent配置的处理"""
        controller = AgentController([])
        
        # 验证所有Agent类型列表都为空
        for agent_type in controller.agents.values():
            assert len(agent_type) == 0
        
        assert controller._get_total_agents_count() == 0
    
    def test_empty_posts_handling(self):
        """测试空帖子列表的处理"""
        agent = self.agent_controller.agents["意见领袖"][0]
        
        personalized_posts = self.agent_controller._generate_personalized_feed(agent, [])
        
        assert personalized_posts == []
    
    def test_placeholder_agent_creation(self):
        """测试PlaceholderAgent的创建"""
        config = {
            "agent_id": "test_agent",
            "type": "普通用户",
            "stance": 0.6,
            "interests": ["测试"],
            "influence": 1.2
        }
        
        agent = PlaceholderAgent(config)
        
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "普通用户"
        assert agent.stance == 0.6
        assert agent.interests == ["测试"]
        assert agent.influence == 1.2
    
    def test_placeholder_agent_default_values(self):
        """测试PlaceholderAgent的默认值"""
        minimal_config = {"agent_id": "minimal_agent"}
        
        agent = PlaceholderAgent(minimal_config)
        
        assert agent.agent_id == "minimal_agent"
        assert agent.agent_type == "普通用户"  # 默认值
        assert agent.stance == 0.5  # 默认值
        assert agent.interests == []  # 默认值
        assert agent.influence == 1.0  # 默认值