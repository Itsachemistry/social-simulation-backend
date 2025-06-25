from src.agent import Agent
from src.world_state import WorldState
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

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
        self._debug_threshold = False  # 调试开关
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
    
    def _generate_environmental_summary(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成环境摘要（为意见领袖提供宏观舆情信息）
        - 参数：posts (List[Dict]): 当前时间片的所有帖子
        - 返回：Dict: 包含情感分布、立场分布、热点话题等宏观信息
        """
        if not posts:
            return {
                "emotion_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "stance_distribution": {"pro": 0, "neutral": 0, "anti": 0},
                "hot_topics": [],
                "overall_sentiment": "neutral",
                "total_posts": 0
            }
        
        # 统计情感分布
        emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
        stance_counts = {"pro": 0, "neutral": 0, "anti": 0}
        
        for post in posts:
            # 根据帖子情感值分类（假设情感值在0-1之间，0.5为中性）
            emotion = post.get("emotion", 0.5)
            if emotion > 0.6:
                emotion_counts["positive"] += 1
            elif emotion < 0.4:
                emotion_counts["negative"] += 1
            else:
                emotion_counts["neutral"] += 1
            
            # 根据帖子立场值分类（假设立场值在0-1之间，0.5为中性）
            stance = post.get("stance", 0.5)
            if stance > 0.6:
                stance_counts["pro"] += 1
            elif stance < 0.4:
                stance_counts["anti"] += 1
            else:
                stance_counts["neutral"] += 1
        
        # 计算整体情感倾向
        total_posts = len(posts)
        positive_ratio = emotion_counts["positive"] / total_posts
        negative_ratio = emotion_counts["negative"] / total_posts
        
        if positive_ratio > negative_ratio and positive_ratio > 0.4:
            overall_sentiment = "positive"
        elif negative_ratio > positive_ratio and negative_ratio > 0.4:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # 识别热点话题（按热度排序）
        hot_topics = sorted(posts, key=lambda x: x.get("heat", 0), reverse=True)[:5]
        
        return {
            "emotion_distribution": emotion_counts,
            "stance_distribution": stance_counts,
            "hot_topics": [post.get("content", "")[:50] + "..." for post in hot_topics],
            "overall_sentiment": overall_sentiment,
            "total_posts": total_posts
        }

    def run_time_slice(self, agents: List[Agent], world_state: WorldState, llm_service=None) -> List[Dict[str, Any]]:
        """
        运行一个时间片
        """
        # 获取当前时间片的所有帖子
        all_posts = world_state.get_all_posts()
        
        # 计算全局环境强度因子
        global_intensity_factor = self.calculate_global_intensity_factor(all_posts)
        
        # 生成环境摘要（为意见领袖准备）
        environmental_summary = self._generate_environmental_summary(all_posts)
        
        # 按类型分组Agent
        agents_by_type = {}
        for agent in agents:
            agent_type = agent.agent_type
            if agent_type not in agents_by_type:
                agents_by_type[agent_type] = []
            agents_by_type[agent_type].append(agent)
        
        # 按优先级排序Agent类型
        sorted_agent_types = sorted(
            agents_by_type.keys(),
            key=lambda x: self.action_priority.get(x, 999)
        )
        
        generated_posts = []
        
        # 按优先级处理每种类型的Agent
        for agent_type in sorted_agent_types:
            type_agents = agents_by_type[agent_type]
            
            for agent in type_agents:
                # 为意见领袖提供环境摘要
                if agent_type == "意见领袖":
                    agent.update_state_with_summary(environmental_summary, llm_service)
                
                # 为每个Agent生成个性化信息流（使用动态阈值）
                personalized_posts = self._generate_personalized_feed(
                    agent, all_posts, global_intensity_factor
                )
                
                # 处理每个帖子
                for post in personalized_posts:
                    agent.update_state(post, llm_service)
                
                # 生成行动
                action_prompt = agent.generate_action_prompt()
                if action_prompt:
                    # 调用LLM生成帖子内容
                    if llm_service:
                        generated_content = llm_service.generate_content(action_prompt)
                    else:
                        # Mock实现
                        generated_content = f"Agent {agent.agent_id} 的回复: {action_prompt[:50]}..."
                    
                    # 创建新帖子
                    new_post = {
                        "id": str(uuid.uuid4()),
                        "content": generated_content,
                        "author_id": agent.agent_id,
                        "timestamp": datetime.now().isoformat(),
                        "heat": 30,  # 默认热度
                        "likes": 0,
                        "shares": 0,
                        "is_event": False,
                        "priority": 0,
                        "is_repost": True if hasattr(agent, 'repost_source_id') and agent.repost_source_id else False,
                        "parent_post_id": getattr(agent, 'repost_source_id', None)
                    }
                    
                    # 添加到世界状态
                    if world_state:
                        world_state.add_post(new_post)
                    
                    generated_posts.append(new_post)
        
        return generated_posts
    
    def _generate_personalized_feed(self, agent: Agent, all_posts: list, global_intensity_factor: float = 1.0) -> list:
        """
        为指定Agent生成个性化信息流
        
        Args:
            agent (Agent): 目标Agent对象
            all_posts (list): 所有可用的帖子列表
            global_intensity_factor (float): 全局环境强度因子
            
        Returns:
            list: 筛选后的个性化帖子列表
        """
        personalized_posts = []
        
        for post in all_posts:
            # === 帖子筛选逻辑 ===
            
            # 1. 热度筛选：只选择热度值达到阈值的帖子
            post_heat = post.get("heat", 0)
            heat_threshold = self._get_heat_threshold_for_agent(agent, global_intensity_factor)
            
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
            
            # 4. 黑名单过滤
            if "author_id" in post and post["author_id"] in getattr(agent, "blacklist", []):
                continue
            
            # 通过所有筛选条件的帖子被添加到个性化信息流
            personalized_posts.append(post)
        
        # 按热度降序排序，确保高热度帖子优先显示
        personalized_posts.sort(key=lambda x: x.get("heat", 0), reverse=True)
        
        return personalized_posts
    
    def _get_heat_threshold_for_agent(self, agent: Agent, global_intensity_factor: float = 1.0) -> int:
        """
        根据Agent状态和全局环境动态计算热度阈值
        
        Args:
            agent (Agent): Agent对象
            global_intensity_factor (float): 全局环境强度因子 (0-2, 1.0为正常)
            
        Returns:
            int: 动态计算的热度阈值
        """
        # 获取基础配置
        config = self._get_dynamic_threshold_config()
        
        # 1. 基础阈值（基于Agent类型）
        base_threshold = self._get_base_heat_threshold(agent.agent_type)
        
        # 2. 性格调整系数
        personality_adjustment = self._calculate_personality_adjustment(agent)
        
        # 3. 情绪状态调整
        emotion_adjustment = self._calculate_emotion_adjustment(agent)
        
        # 4. 置信度调整
        confidence_adjustment = self._calculate_confidence_adjustment(agent)
        
        # 5. 全局环境调整
        global_adjustment = self._calculate_global_adjustment(global_intensity_factor)
        
        # 6. 综合计算动态阈值
        dynamic_threshold = (
            base_threshold * personality_adjustment +
            emotion_adjustment * config["emotion_weight"] * 100 +
            confidence_adjustment * config["confidence_weight"] * 100 +
            global_adjustment * config["global_intensity_weight"] * 100
        )
        
        # 7. 应用限制范围
        max_adjustment = config["max_threshold_adjustment"]
        min_threshold = config["min_threshold"]
        
        dynamic_threshold = max(
            min_threshold,
            min(base_threshold + max_adjustment, dynamic_threshold)
        )
        
        # 8. 记录调试信息
        if hasattr(self, '_debug_threshold') and self._debug_threshold:
            print(f"Agent {agent.agent_id} 动态阈值计算:")
            print(f"  基础阈值: {base_threshold}")
            print(f"  性格调整: {personality_adjustment:.2f}")
            print(f"  情绪调整: {emotion_adjustment:.2f}")
            print(f"  置信度调整: {confidence_adjustment:.2f}")
            print(f"  全局调整: {global_adjustment:.2f}")
            print(f"  最终阈值: {dynamic_threshold:.1f}")
        
        return int(dynamic_threshold)
    
    def _get_dynamic_threshold_config(self) -> dict:
        """
        获取动态阈值配置
        
        Returns:
            dict: 配置字典
        """
        # 这里可以从配置文件读取，暂时使用默认值
        return {
            "emotion_weight": 0.3,
            "confidence_weight": 0.2,
            "global_intensity_weight": 0.25,
            "personality_weight": 0.25,
            "max_threshold_adjustment": 30,
            "min_threshold": 10
        }
    
    def _get_base_heat_threshold(self, agent_type: str) -> int:
        """
        获取基于Agent类型的基础热度阈值
        
        Args:
            agent_type (str): Agent类型
            
        Returns:
            int: 基础热度阈值
        """
        base_thresholds = {
            "意见领袖": 30,
            "规则Agent": 20,
            "普通用户": 50
        }
        return base_thresholds.get(agent_type, 50)
    
    def _calculate_personality_adjustment(self, agent: Agent) -> float:
        """
        计算性格特征对阈值的影响
        
        Args:
            agent (Agent): Agent对象
            
        Returns:
            float: 性格调整系数 (0.5-1.5)
        """
        # 活跃度影响：高活跃度Agent对信息更敏感，阈值降低
        activity_factor = 1.0 - (agent.activity_level - 0.5) * 0.4
        
        # 信息渴求度影响：高信息渴求度Agent阈值降低
        thirst_factor = 1.0 - (agent.information_thirst - 0.5) * 0.3
        
        # 注意力持续时间影响：注意力短的Agent阈值降低
        attention_factor = 1.0 - (0.5 - agent.attention_span) * 0.2
        
        # 综合调整系数
        personality_adjustment = (activity_factor + thirst_factor + attention_factor) / 3
        
        return max(0.5, min(1.5, personality_adjustment))
    
    def _calculate_emotion_adjustment(self, agent: Agent) -> float:
        """
        计算情绪状态对阈值的影响
        
        Args:
            agent (Agent): Agent对象
            
        Returns:
            float: 情绪调整值 (-1.0 到 1.0)
        """
        # 情绪强度计算（距离中性情绪0.5的距离）
        emotion_intensity = abs(agent.emotion - 0.5) * 2  # 0-1
        
        # 情绪敏感度影响
        sensitivity_factor = agent.emotion_sensitivity
        
        # 情绪调整逻辑：
        # - 情绪极端时（愤怒/兴奋），阈值降低（更容易关注信息）
        # - 情绪平静时，阈值相对较高
        if agent.emotion < 0.3:  # 负面情绪
            adjustment = -emotion_intensity * sensitivity_factor
        elif agent.emotion > 0.7:  # 正面情绪
            adjustment = -emotion_intensity * sensitivity_factor * 0.8  # 正面情绪影响稍小
        else:  # 中性情绪
            adjustment = 0.0
        
        return max(-1.0, min(1.0, adjustment))
    
    def _calculate_confidence_adjustment(self, agent: Agent) -> float:
        """
        计算置信度对阈值的影响
        
        Args:
            agent (Agent): Agent对象
            
        Returns:
            float: 置信度调整值 (-1.0 到 1.0)
        """
        # 立场坚定度影响
        firmness_factor = agent.stance_firmness
        
        # 置信度调整逻辑：
        # - 高置信度 + 高坚定度：阈值升高（不太关心新信息）
        # - 低置信度：阈值降低（更渴求信息）
        if agent.confidence > 0.7 and firmness_factor > 0.7:
            # 高置信度且立场坚定，阈值升高
            adjustment = (agent.confidence - 0.7) * firmness_factor * 0.5
        elif agent.confidence < 0.3:
            # 低置信度，阈值降低
            adjustment = -(0.3 - agent.confidence) * 2.0
        else:
            # 中等置信度，影响较小
            adjustment = 0.0
        
        return max(-1.0, min(1.0, adjustment))
    
    def _calculate_global_adjustment(self, global_intensity_factor: float) -> float:
        """
        计算全局环境对阈值的影响
        
        Args:
            global_intensity_factor (float): 全局环境强度因子
            
        Returns:
            float: 全局调整值 (-1.0 到 1.0)
        """
        # 全局环境调整逻辑：
        # - 当全局事件强度高时（global_intensity_factor > 1.0），阈值降低
        # - 当全局环境平静时（global_intensity_factor < 1.0），阈值相对较高
        
        if global_intensity_factor > 1.0:
            # 高强度环境，阈值降低
            adjustment = -(global_intensity_factor - 1.0) * 0.8
        elif global_intensity_factor < 0.5:
            # 低强度环境，阈值升高
            adjustment = (0.5 - global_intensity_factor) * 0.5
        else:
            # 正常环境，影响较小
            adjustment = 0.0
        
        return max(-1.0, min(1.0, adjustment))
    
    def calculate_global_intensity_factor(self, all_posts: List[Dict[str, Any]]) -> float:
        """
        计算全局环境强度因子
        
        Args:
            all_posts (List[Dict]): 所有帖子列表
            
        Returns:
            float: 全局强度因子 (0-2, 1.0为正常)
        """
        if not all_posts:
            return 1.0
        
        # 1. 帖子数量因子
        post_count_factor = min(len(all_posts) / 100.0, 2.0)  # 100个帖子为基准
        
        # 2. 平均热度因子
        avg_heat = sum(post.get("heat", 0) for post in all_posts) / len(all_posts)
        heat_factor = min(avg_heat / 50.0, 2.0)  # 50热度为基准
        
        # 3. 情绪激烈程度因子
        emotion_intensities = []
        for post in all_posts:
            emotion = post.get("emotion", 0.5)
            intensity = abs(emotion - 0.5) * 2  # 0-1
            emotion_intensities.append(intensity)
        
        avg_emotion_intensity = sum(emotion_intensities) / len(emotion_intensities)
        emotion_factor = 1.0 + avg_emotion_intensity  # 1.0-2.0
        
        # 4. 综合计算
        global_intensity = (post_count_factor + heat_factor + emotion_factor) / 3
        
        return max(0.1, min(2.0, global_intensity))
    
    def _calculate_stance_similarity(self, agent: Agent, post: dict) -> float:
        """
        计算Agent立场与帖子立场的相似度
        
        Args:
            agent (Agent): Agent对象
            post (dict): 帖子对象
            
        Returns:
            float: 相似度分数 (0-1)
        """
        # 改进的相似度计算
        # 1. 基于帖子内容的简单情感分析
        content = post.get("content", "").lower()
        
        # 正面词汇
        positive_words = ["好", "棒", "赞", "喜欢", "支持", "同意", "正确", "优秀", "成功", "开心", "愉快"]
        # 负面词汇  
        negative_words = ["坏", "差", "讨厌", "反对", "错误", "失败", "愤怒", "失望", "糟糕", "问题"]
        
        # 计算情感倾向
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        # 估算帖子立场
        if positive_count > negative_count:
            post_stance = 0.7 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            post_stance = 0.3 - (negative_count - positive_count) * 0.1
        else:
            post_stance = 0.5
        
        # 计算相似度（使用高斯函数）
        stance_diff = abs(agent.stance - post_stance)
        similarity = max(0.0, 1.0 - stance_diff * 2.0)  # 更宽松的相似度计算
        
        return similarity
    
    def _get_similarity_threshold_for_agent(self, agent: Agent) -> float:
        """
        根据Agent类型获取相似度阈值
        
        Args:
            agent (Agent): Agent对象
            
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
    
    def _check_interest_match(self, agent: Agent, post: dict) -> bool:
        """
        检查帖子是否匹配Agent的兴趣
        
        Args:
            agent (Agent): Agent对象
            post (dict): 帖子对象
            
        Returns:
            bool: 是否匹配
        """
        # 改进的兴趣匹配逻辑
        if not agent.interests:
            return True  # 如果没有兴趣标签，接受所有帖子
        
        content = post.get("content", "").lower()
        
        # 兴趣关键词映射
        interest_keywords = {
            "政治": ["政策", "政府", "选举", "政治", "国家", "领导人", "法律"],
            "经济": ["经济", "股市", "投资", "金融", "商业", "贸易", "GDP"],
            "社会": ["社会", "民生", "教育", "医疗", "住房", "就业"],
            "文化": ["文化", "艺术", "文学", "历史", "传统", "习俗"],
            "科技": ["科技", "技术", "创新", "互联网", "AI", "数字化"],
            "娱乐": ["娱乐", "电影", "音乐", "明星", "综艺", "游戏"],
            "体育": ["体育", "足球", "篮球", "运动", "比赛", "健身"],
            "健康": ["健康", "医疗", "养生", "运动", "饮食", "疾病"],
            "美食": ["美食", "餐厅", "烹饪", "食材", "菜谱", "味道"],
            "旅游": ["旅游", "旅行", "景点", "酒店", "机票", "度假"],
            "教育": ["教育", "学校", "学习", "考试", "培训", "知识"],
            "职场": ["职场", "工作", "公司", "职业", "面试", "升职"],
            "规则": ["规则", "秩序", "制度", "规范", "管理", "监督"]
        }
        
        # 计算兴趣匹配度
        match_score = 0
        for interest in agent.interests:
            if interest in interest_keywords:
                keywords = interest_keywords[interest]
                for keyword in keywords:
                    if keyword in content:
                        match_score += 1
                        break  # 每个兴趣只匹配一次
        
        # 匹配阈值：至少匹配一个兴趣，或者没有明确兴趣标签
        return match_score > 0 or len(agent.interests) == 0
    
    def _mock_llm_service(self, prompt: str) -> str:
        """模拟LLM回复"""
        return f"【模拟LLM生成内容】基于提示：{prompt[:30]}..."


