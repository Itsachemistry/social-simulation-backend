from src.agent import Agent
from typing import Optional

class PlaceholderAgent:
    """
    临时的Agent占位符类，用于在AgentController中模拟Agent对象
    当真实的Agent类实现后，这个类将被替换
    """
    
    def __init__(self, agent_config: dict):
        """
        初始化占位符Agent
        
        Args:
            agent_config (dict): Agent配置字典，包含类型、立场等信息
        """
        self.agent_id = agent_config.get("agent_id", "unknown")
        self.agent_type = agent_config.get("type", "普通用户")  # 意见领袖、规则Agent、普通用户
        self.stance = agent_config.get("stance", 0.5)  # 立场值 (0-1)
        self.interests = agent_config.get("interests", [])  # 兴趣标签列表
        self.influence = agent_config.get("influence", 1.0)  # 影响力系数
        
    def __str__(self):
        return f"PlaceholderAgent(id={self.agent_id}, type={self.agent_type}, stance={self.stance})"


class AgentController:
    """
    Agent控制器，负责管理和调度所有Agent的行为
    
    核心功能：
    1. 管理不同类型的Agent（意见领袖、规则Agent、普通用户）
    2. 实现行动顺序调度器
    3. 为每个Agent生成个性化信息流
    4. 协调Agent之间的交互
    """
    
    def __init__(self, agent_configs: list, world_state=None, llm_service=None):
        """
        初始化Agent控制器
        
        Args:
            agent_configs (list): Agent配置列表
            world_state: 世界状态管理器实例
            llm_service: LLM服务实例
        """
        self.agents = {
            "意见领袖": [],
            "规则Agent": [],
            "普通用户": []
        }
        self.action_priority = {
            "意见领袖": 1,
            "规则Agent": 2,
            "普通用户": 3
        }
        self.world_state = world_state
        self.llm_service = llm_service
        self._create_and_group_agents(agent_configs)
        print(f"AgentController初始化完成，共创建 {self._get_total_agents_count()} 个Agent")
        for agent_type, agents in self.agents.items():
            print(f"  - {agent_type}: {len(agents)} 个")
    
    def _create_and_group_agents(self, agent_configs: list) -> None:
        """
        根据配置创建Agent对象并按类型分组
        
        Args:
            agent_configs (list): Agent配置列表
        """
        for config in agent_configs:
            try:
                agent = Agent(config)
                if agent.agent_type in self.agents:
                    self.agents[agent.agent_type].append(agent)
                else:
                    print(f"警告：未知的Agent类型 '{agent.agent_type}'，归类为普通用户")
                    self.agents["普通用户"].append(agent)
            except Exception as e:
                print(f"创建Agent失败，配置：{config}，错误：{e}")
    
    def _get_total_agents_count(self) -> int:
        """
        获取所有Agent的总数
        
        Returns:
            int: Agent总数
        """
        return sum(len(agents) for agents in self.agents.values())
    
    def run_time_slice(self, current_slice_posts: list, all_posts: list) -> dict:
        """
        执行一个时间片的核心调度逻辑
        
        Args:
            current_slice_posts (list): 当前时间片的新帖子列表
            all_posts (list): 所有历史帖子的列表
            
        Returns:
            dict: 本轮调度的结果统计
        """
        print(f"\n=== 开始执行时间片调度 ===")
        print(f"当前时间片新帖子数: {len(current_slice_posts)}")
        print(f"历史帖子总数: {len(all_posts)}")
        
        # 存储本轮调度的结果
        round_results = {
            "processed_agents": 0,
            "generated_actions": 0,
            "agent_actions": {}  # 每个Agent的行动记录
        }
        
        # === 行动顺序调度器 ===
        # 按照预定义的优先级顺序处理不同类型的Agent
        sorted_agent_types = sorted(
            self.action_priority.keys(), 
            key=lambda x: self.action_priority[x]
        )
        
        for agent_type in sorted_agent_types:
            print(f"\n--- 处理 {agent_type} 类型Agent ---")
            
            # 获取当前类型的所有Agent
            type_agents = self.agents[agent_type]
            print(f"该类型共有 {len(type_agents)} 个Agent")
            
            # 逐个处理该类型的每个Agent
            for agent in type_agents:
                print(f"  处理Agent: {agent.agent_id}")
                
                # === 个性化信息流生成器 ===
                # 为当前Agent生成个性化的帖子列表
                personalized_posts = self._generate_personalized_feed(agent, all_posts)
                
                print(f"    为Agent生成了 {len(personalized_posts)} 条个性化帖子")
                
                # === 真实交互逻辑 ===
                processed_posts = []
                for post in personalized_posts:
                    update_result = agent.update_state(post)
                    processed_posts.append({
                        "post_id": post.get("id", ""),
                        "update_result": update_result
                    })
                prompt = agent.generate_action_prompt()
                generated_content = None
                if prompt:
                    # 调用LLM服务（如果未注入则用mock）
                    if self.llm_service:
                        generated_content = self.llm_service.generate_post(prompt)
                    else:
                        generated_content = self._mock_llm_service(prompt)
                    # 新帖子加入世界状态
                    if self.world_state and generated_content:
                        self.world_state.add_post({
                            "content": generated_content,
                            "author_id": agent.agent_id
                        })
                agent_action = {
                    "action_type": "发帖" if generated_content else "浏览",
                    "processed_posts": processed_posts,
                    "generated_content": generated_content
                }
                round_results["agent_actions"][agent.agent_id] = agent_action
                round_results["processed_agents"] += 1
                if generated_content:
                    round_results["generated_actions"] += 1
                print(f"    Agent行动: {agent_action['action_type']}")
        
        print(f"\n=== 时间片调度完成 ===")
        print(f"处理Agent数: {round_results['processed_agents']}")
        print(f"生成行动数: {round_results['generated_actions']}")
        
        return round_results
    
    def _generate_personalized_feed(self, agent: PlaceholderAgent, all_posts: list) -> list:
        """
        为指定Agent生成个性化信息流
        
        Args:
            agent (PlaceholderAgent): 目标Agent对象
            all_posts (list): 所有可用的帖子列表
            
        Returns:
            list: 筛选后的个性化帖子列表
        """
        personalized_posts = []
        
        for post in all_posts:
            # === 帖子筛选逻辑 ===
            
            # 1. 热度筛选：只选择热度值达到阈值的帖子
            post_heat = post.get("heat", 0)
            heat_threshold = self._get_heat_threshold_for_agent(agent)
            
            if post_heat < heat_threshold:
                continue
            
            # 2. 立场相似度筛选：计算帖子与Agent立场的相似度
            similarity_score = self._calculate_stance_similarity(agent, post)
            similarity_threshold = self._get_similarity_threshold_for_agent(agent)
            
            if similarity_score < similarity_threshold:
                continue
            
            # 3. 兴趣匹配筛选：检查帖子是否匹配Agent的兴趣
            if not self._check_interest_match(agent, post):
                continue
            
            # 通过所有筛选条件的帖子被添加到个性化信息流
            personalized_posts.append(post)
        
        # 按热度降序排序，确保高热度帖子优先显示
        personalized_posts.sort(key=lambda x: x.get("heat", 0), reverse=True)
        
        return personalized_posts
    
    def _get_heat_threshold_for_agent(self, agent: PlaceholderAgent) -> int:
        """
        根据Agent类型获取热度阈值
        
        Args:
            agent (PlaceholderAgent): Agent对象
            
        Returns:
            int: 热度阈值
        """
        # 不同类型的Agent对热度敏感度不同
        heat_thresholds = {
            "意见领袖": 30,    # 意见领袖关注度较高，能看到更多帖子
            "规则Agent": 20,   # 规则Agent需要监控更多内容
            "普通用户": 50     # 普通用户只关注高热度内容
        }
        
        return heat_thresholds.get(agent.agent_type, 50)
    
    def _calculate_stance_similarity(self, agent: PlaceholderAgent, post: dict) -> float:
        """
        计算Agent立场与帖子立场的相似度
        
        Args:
            agent (PlaceholderAgent): Agent对象
            post (dict): 帖子对象
            
        Returns:
            float: 相似度分数 (0-1)
        """
        # 临时实现：使用随机数模拟相似度计算
        # 在实际实现中，这里应该分析帖子内容的情感倾向和立场
        import random
        random.seed(hash(agent.agent_id + str(post.get("id", ""))))
        
        # 基础相似度（基于Agent立场）
        base_similarity = 0.5
        
        # 添加随机波动
        random_factor = random.uniform(-0.3, 0.3)
        
        return base_similarity + random_factor
    
    def _get_similarity_threshold_for_agent(self, agent: PlaceholderAgent) -> float:
        """
        根据Agent类型获取相似度阈值
        
        Args:
            agent (PlaceholderAgent): Agent对象
            
        Returns:
            float: 相似度阈值
        """
        # 不同类型的Agent对相似度敏感度不同
        similarity_thresholds = {
            "意见领袖": 0.7,    # 意见领袖关注度较高，对相似度要求也较高
            "规则Agent": 0.5,   # 规则Agent需要监控更多内容，对相似度要求较低
            "普通用户": 0.3     # 普通用户只关注高热度内容，对相似度要求最低
        }
        
        return similarity_thresholds.get(agent.agent_type, 0.3)
    
    def _check_interest_match(self, agent: PlaceholderAgent, post: dict) -> bool:
        """
        检查帖子是否匹配Agent的兴趣
        
        Args:
            agent (PlaceholderAgent): Agent对象
            post (dict): 帖子对象
            
        Returns:
            bool: 是否匹配
        """
        # 临时实现：使用随机数模拟兴趣匹配
        # 在实际实现中，这里应该分析帖子内容的主题和关键词
        import random
        random.seed(hash(agent.agent_id + str(post.get("id", ""))))
        
        # 兴趣匹配阈值
        interest_threshold = 0.5
        
        # 计算兴趣匹配度
        interest_score = 0.0
        for interest in agent.interests:
            if interest in post.get("content", ""):
                interest_score += 1.0
        
        return interest_score >= interest_threshold
    
    def _mock_llm_service(self, prompt: str) -> str:
        """模拟LLM回复"""
        return f"【模拟LLM生成内容】基于提示：{prompt[:30]}..."


