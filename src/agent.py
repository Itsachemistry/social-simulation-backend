from typing import Dict, List, Any, Optional
import random
from datetime import datetime


class Agent:
    """
    Agent类（由Agent设计师负责实现）
    --------------------------
    该类模拟社交仿真中的"演员"，封装了个体决策、状态更新、行为生成等全部逻辑。
    
    设计契约：
    1. 你需要实现如下接口，供后端主流程调用：
        - __init__(agent_config): 初始化Agent，读取配置，塑造角色，包括性格（如is_firm_stance等）
        - update_state(post_object, llm_service=None): 状态更新，内部需调用LLM分析情绪，按性格规则更新立场，管理黑名单
        - generate_action_prompt(): 行动决策，决定是否发言，返回Prompt或None
        - agent_id/agent_type/stance/interests/blacklist等属性：供后端读取
        - join_timestamp: 加入仿真的时间戳（datetime对象），由后端用于激活判断
        - is_active: 是否已激活（bool），由后端主循环管理
        - firm_stance: 立场坚定度（接口属性，供队友实现）
        - filter_opposite: 是否过滤异见（接口属性，供队友实现）
        - activity_level: 活跃度（接口属性，供队友实现）
    2. 你只需保证接口契约，内部实现细节完全由你决定。
    3. 详细接口说明见下方各方法docstring。
    """
    
    def __init__(self, agent_config: dict):
        """
        初始化Agent
        - 读取agent_config，初始化ID、类型、立场、兴趣、性格（如is_firm_stance等）
        - 参数：agent_config (dict): 包含所有角色设定的配置字典
        - 你需要支持"态度坚定/不坚定"等性格特征
        """
        self._agent_id = agent_config.get("agent_id", "unknown")
        self._agent_type = agent_config.get("type", "普通用户")
        self._stance = agent_config.get("stance", 0.5)  # 立场值 (0-1)
        self._interests = agent_config.get("interests", [])  # 兴趣标签列表
        self.influence = agent_config.get("influence", 1.0)  # 影响力系数
        
        # 性格特征
        self._personality = agent_config.get("personality", {
            "activity_level": 0.5,      # 活跃度 (0-1)
            "emotion_sensitivity": 0.5,  # 情绪敏感度 (0-1)
            "stance_firmness": 0.5,      # 立场坚定度 (0-1)
            "information_thirst": 0.5,   # 信息渴求度 (0-1)
            "attention_span": 0.5        # 注意力持续时间 (0-1)
        })
        
        # 动态状态
        self.emotion = 0.5  # 情绪值 (0-1, 0=负面, 1=正面)
        self.confidence = 0.5  # 置信度 (0-1)
        self.energy = 1.0  # 精力值 (0-1)
        
        # 交互历史
        self.viewed_posts = []  # 已浏览的帖子ID列表
        self._blacklist = []  # 黑名单用户ID列表
        self.interaction_history = []  # 交互历史记录
        
        # 行为参数（可从配置中读取）
        self.post_probability = agent_config.get("post_probability", 0.3)  # 发帖概率
        self.max_posts_per_slice = agent_config.get("max_posts_per_slice", 2)  # 每个时间片最大发帖数
        self.current_posts_count = 0  # 当前时间片已发帖数
        
        # 重置当前时间片的发帖计数
        self._reset_slice_counters()
        
        # 加入仿真的时间戳（用于激活）
        join_ts = agent_config.get("join_time") or agent_config.get("join_timestamp")
        if join_ts is not None:
            if isinstance(join_ts, datetime):
                self.join_timestamp = join_ts
            else:
                # 支持字符串自动转datetime
                self.join_timestamp = datetime.fromisoformat(str(join_ts))
        else:
            self.join_timestamp = None
        # 是否已激活（由主循环管理）
        self.is_active = agent_config.get("is_active", True)
        # 立场坚定度、过滤异见、活跃度等为接口属性，供队友实现
        self._firm_stance = agent_config.get("is_firm_stance", None)  # 供队友实现
        self._filter_opposite = agent_config.get("filter_opposite", None)  # 供队友实现
        self._activity_level = agent_config.get("activity_level", None)  # 供队友实现
    
    def _reset_slice_counters(self):
        """重置时间片相关的计数器"""
        self.current_posts_count = 0
        self.viewed_posts = []
        self.max_impact_post_id = None  # 本时间片影响最大的帖子ID
        self.max_impact_score = float('-inf')  # 新增：最大影响分数
    
    def update_state(self, post_object: dict, llm_service=None) -> dict:
        """
        状态更新接口
        - 输入：单条post_object（dict）
        - 1. 调用LLM分析帖子内容，更新情绪
        - 2. 按"坚定/不坚定"性格，采用不同的立场更新算法（多重阈值/直接跟随）
        - 3. 判断是否需要将发帖人加入黑名单
        - 输出：状态变化详情（dict）
        - 你可以在内部自由设计Prompt和LLM调用方式
        """
        post_id = post_object.get("id", "")
        
        # 避免重复处理同一帖子
        if post_id in self.viewed_posts:
            return {"status": "already_viewed", "post_id": post_id}
        
        # 记录已浏览的帖子
        self.viewed_posts.append(post_id)
        
        # 计算帖子对Agent的影响
        impact = self._calculate_post_impact(post_object)
        
        # 更新情绪
        self.emotion = max(0.0, min(1.0, self.emotion + impact["emotion_change"]))
        
        # 更新置信度
        self.confidence = max(0.0, min(1.0, self.confidence + impact["confidence_change"]))
        
        # 更新精力（浏览帖子消耗精力）
        self.energy = max(0.0, self.energy - 0.05)
        
        # 记录交互历史
        interaction_record = {
            "post_id": post_id,
            "timestamp": post_object.get("timestamp", ""),
            "impact": impact,
            "new_emotion": self.emotion,
            "new_confidence": self.confidence
        }
        self.interaction_history.append(interaction_record)
        
        # 计算多因素加权分数
        score = (
            0.5 * abs(impact.get('emotion_change', 0)) +
            0.3 * abs(impact.get('confidence_change', 0)) +
            0.2 * impact.get('base_impact', 0)
        )
        if score > getattr(self, 'max_impact_score', float('-inf')):
            self.max_impact_score = score
            self.max_impact_post_id = post_object.get('id', None)
        
        return {
            "status": "updated",
            "post_id": post_id,
            "impact": impact,
            "new_state": {
                "emotion": self.emotion,
                "confidence": self.confidence,
                "energy": self.energy
            }
        }
    
    def _calculate_post_impact(self, post_object: dict) -> Dict[str, float]:
        """
        计算帖子对Agent的影响
        
        Args:
            post_object (dict): 帖子数据
            
        Returns:
            Dict[str, float]: 影响值字典
        """
        # 获取帖子热度
        post_heat = post_object.get("heat", 0) / 100.0  # 归一化到0-1
        
        # 计算立场相似度（简化实现）
        post_stance = self._estimate_post_stance(post_object)
        stance_similarity = 1.0 - abs(self._stance - post_stance)
        
        # 计算兴趣匹配度
        interest_match = self._calculate_interest_match(post_object)
        
        # 计算综合影响
        base_impact = post_heat * stance_similarity * interest_match
        
        # 情绪变化（基于立场相似度）
        emotion_change = (stance_similarity - 0.5) * 0.1 * post_heat
        
        # 置信度变化（基于兴趣匹配和热度）
        confidence_change = interest_match * post_heat * 0.05
        
        return {
            "emotion_change": emotion_change,
            "confidence_change": confidence_change,
            "base_impact": base_impact,
            "stance_similarity": stance_similarity,
            "interest_match": interest_match
        }
    
    def _estimate_post_stance(self, post_object: dict) -> float:
        """
        估算帖子的立场值（简化实现）
        
        Args:
            post_object (dict): 帖子数据
            
        Returns:
            float: 估算的立场值 (0-1)
        """
        # 这里应该使用更复杂的NLP分析
        # 暂时使用基于帖子ID的伪随机值
        random.seed(hash(post_object.get("id", "")))
        return random.uniform(0.0, 1.0)
    
    def _calculate_interest_match(self, post_object: dict) -> float:
        """
        计算帖子与Agent兴趣的匹配度
        
        Args:
            post_object (dict): 帖子数据
            
        Returns:
            float: 匹配度 (0-1)
        """
        if not self._interests:
            return 0.5  # 如果没有兴趣标签，返回中等匹配度
        
        # 获取帖子的兴趣标签（如果存在）
        post_interests = post_object.get("interests", [])
        
        if not post_interests:
            return 0.3  # 如果帖子没有兴趣标签，返回较低匹配度
        
        # 计算交集大小
        common_interests = set(self._interests) & set(post_interests)
        
        # 计算匹配度
        if len(self._interests) == 0:
            return 0.0
        
        return len(common_interests) / len(self._interests)
    
    def generate_action_prompt(self) -> str | None:
        """
        行动决策接口，决定是否发言，返回Prompt或None。
        发言概率逻辑（如状态波动、活跃度加成、随机决策等）应由Agent设计师在本方法内部实现。
        """
        # 检查是否还能发帖
        if self.current_posts_count >= self.max_posts_per_slice:
            return None
        
        # 检查精力是否足够
        if self.energy < 0.2:
            return None
        
        # 基于概率决定是否发帖
        if random.random() > self.post_probability:
            return None
        
        # 基于当前状态调整发帖概率
        adjusted_probability = self.post_probability
        
        # 情绪极端时更容易发帖
        if self.emotion < 0.2 or self.emotion > 0.8:
            adjusted_probability *= 1.5
        
        # 置信度高时更容易发帖
        if self.confidence > 0.7:
            adjusted_probability *= 1.3
        
        # 最终概率检查
        if random.random() > adjusted_probability:
            return None
        
        # 生成提示词
        prompt = self._create_action_prompt()
        
        # 增加发帖计数
        self.current_posts_count += 1
        
        return prompt
    
    def _create_action_prompt(self) -> str:
        """
        创建具体的行动提示词
        
        Returns:
            str: 提示词文本
        """
        # 基于Agent类型和状态生成不同的提示词
        base_prompt = f"""你是一个{self._agent_type}，ID为{self._agent_id}。

当前状态：
- 立场倾向：{self._stance:.2f} (0=反对，1=支持)
- 情绪状态：{self.emotion:.2f} (0=负面，1=正面)
- 置信度：{self.confidence:.2f} (0=不确定，1=确定)
- 精力值：{self.energy:.2f} (0=疲惫，1=充沛)
- 兴趣领域：{', '.join(self._interests) if self._interests else '无特定兴趣'}

最近浏览了{len(self.viewed_posts)}条帖子，请基于你的状态和浏览历史，生成一条社交媒体帖子。

要求：
1. 帖子内容要符合你的立场倾向和情绪状态
2. 内容要真实、自然，符合{self._agent_type}的身份特征
3. 长度控制在50-200字之间
4. 可以是对某条帖子的回应，也可以是原创内容
5. 避免过于极端或不当的言论

请直接输出帖子内容，不要包含任何解释或标记。"""

        return base_prompt
    
    def add_to_blacklist(self, user_id: str) -> None:
        """
        将用户添加到黑名单
        
        Args:
            user_id (str): 要拉黑的用户ID
        """
        if user_id not in self._blacklist:
            self._blacklist.append(user_id)
    
    def remove_from_blacklist(self, user_id: str) -> None:
        """
        从黑名单中移除用户
        
        Args:
            user_id (str): 要解除拉黑的用户ID
        """
        if user_id in self._blacklist:
            self._blacklist.remove(user_id)
    
    def is_blacklisted(self, user_id: str) -> bool:
        """
        检查用户是否在黑名单中
        
        Args:
            user_id (str): 用户ID
            
        Returns:
            bool: 是否在黑名单中
        """
        return user_id in self._blacklist
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        获取Agent状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要
        """
        return {
            "agent_id": self._agent_id,
            "agent_type": self._agent_type,
            "stance": self._stance,
            "emotion": self.emotion,
            "confidence": self.confidence,
            "energy": self.energy,
            "post_probability": self.post_probability,
            "max_posts_per_slice": self.max_posts_per_slice,
            "viewed_posts_count": len(self.viewed_posts),
            "blacklist_count": len(self._blacklist),
            "interaction_count": len(self.interaction_history)
        }
    
    def __str__(self):
        return f"Agent(id={self._agent_id}, type={self._agent_type}, stance={self._stance:.2f}, emotion={self.emotion:.2f})"

    @property
    def agent_id(self) -> str:
        """
        Agent唯一标识符，供后端调度和日志使用
        """
        return self._agent_id

    @property
    def agent_type(self) -> str:
        """
        Agent类型（如"意见领袖"、"规则Agent"、"普通用户"），用于行动顺序调度
        """
        return self._agent_type

    @property
    def stance(self) -> float:
        """
        Agent当前立场值（0-1），用于信息流筛选和立场相似度计算
        """
        return self._stance

    @property
    def interests(self) -> list:
        """
        Agent兴趣标签列表，用于兴趣匹配筛选
        """
        return self._interests

    @property
    def blacklist(self) -> list:
        """
        Agent黑名单，存储被屏蔽用户ID，用于信息流过滤
        """
        return self._blacklist

    @property
    def personality(self) -> dict:
        """
        Agent性格特征，包含活跃度、情绪敏感度、立场坚定度等
        """
        return self._personality.copy()

    @property
    def firm_stance(self):
        """
        Agent立场坚定度（接口属性，供队友实现）
        """
        if self._firm_stance is not None:
            return self._firm_stance
        return self._personality.get("stance_firmness", 0.5)

    @property
    def filter_opposite(self):
        """
        Agent是否过滤异见（接口属性，供队友实现）
        """
        if self._filter_opposite is not None:
            return self._filter_opposite
        return None

    @property
    def activity_level(self):
        """
        Agent活跃度 (0-1)
        """
        if self._activity_level is not None:
            return self._activity_level
        return self._personality.get("activity_level", 0.5)

    @property
    def emotion_sensitivity(self) -> float:
        """
        Agent情绪敏感度 (0-1)
        """
        return self._personality.get("emotion_sensitivity", 0.5)

    @property
    def stance_firmness(self) -> float:
        """
        Agent立场坚定度 (0-1)
        """
        return self._personality.get("stance_firmness", 0.5)

    @property
    def information_thirst(self) -> float:
        """
        Agent信息渴求度 (0-1)
        """
        return self._personality.get("information_thirst", 0.5)

    @property
    def attention_span(self) -> float:
        """
        Agent注意力持续时间 (0-1)
        """
        return self._personality.get("attention_span", 0.5)

    def update_state_with_summary(self, environmental_summary: Dict[str, Any], llm_service=None) -> None:
        """
        环境摘要更新接口（Agent设计师负责实现）
        - 参数：environmental_summary (Dict): 环境摘要数据，包含情感分布、立场分布、热点话题等
        - 参数：llm_service: LLM服务实例，用于分析摘要内容（可选）
        - 职责：
            * 处理宏观舆情信息，更新Agent对整体环境的认知
            * 可能影响Agent的决策策略和发言倾向
            * 这是意见领袖特有的接口，普通Agent不需要
        - 注意：这个接口在update_state之前调用，为后续具体帖子处理提供背景
        """
        # 由Agent设计师实现：处理环境摘要，更新宏观认知状态
        pass 