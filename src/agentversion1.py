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
        agent_id = agent_config.get("agent_id", "unknown")
        if not agent_id.startswith("agent_"):
            agent_id = f"agent_{agent_id}"
        self._agent_id = agent_id
        self._agent_type = agent_config.get("type", "普通用户")
        self._stance = agent_config.get("stance", 0.5)  # 立场值 (0-1)
        self._interests = agent_config.get("interests", [])  # 兴趣标签列表
        self.influence = agent_config.get("influence", 1.0)  # 影响力系数
        
        # 性格特征
        self._personality = agent_config.get("personality", {
            "activity_level": 0.5,      # 活跃度 (0-1)
            "emotion_sensitivity": 0.5,  # 情绪敏感度 (0-1)
            "stance_firmness": 0.5,      # 立场坚定度 (0-1)
            "attention_span": 0.5        # 注意力持续时间 (0-1)
        })
        
        # 动态状态
        self.emotion = 0.5  # 情绪值 (0-1, 0=负面, 1=正面)
        self.confidence = 0.5  # 置信度 (0-1)
        
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
        self.state_history = []  # 新增：记录时序变化
    
    def _reset_slice_counters(self):
        """重置时间片相关的计数器"""
        self.current_posts_count = 0
        self.viewed_posts = []
        self.max_impact_post_id = None  # 本时间片影响最大的帖子ID
        self.max_impact_score = float('-inf')  # 新增：最大影响分数
    
    def update_state(self, post_object: dict, llm_service=None) -> dict:
        """
        状态更新接口（改进版：支持信息强度过滤）
        - 输入：单条post_object（dict）
        - 1. 检查信息强度：strength为null的帖子被完全过滤
        - 2. 调用LLM分析帖子内容，更新情绪
        - 3. 按"坚定/不坚定"性格，采用不同的立场更新算法（多重阈值/直接跟随）
        - 4. 判断是否需要将发帖人加入黑名单
        - 输出：状态变化详情（dict）
        - 你可以在内部自由设计Prompt和LLM调用方式
        """
        post_id = post_object.get("id", "")
        
        # 避免重复处理同一帖子
        if post_id in self.viewed_posts:
            return {"status": "already_viewed", "post_id": post_id}
        
        # 计算帖子对Agent的影响（包含信息强度过滤逻辑）
        impact = self._calculate_post_impact(post_object)
        
        # 检查是否被信息强度过滤
        if impact.get("filtered", False):
            return {
                "status": "filtered_by_strength", 
                "post_id": post_id,
                "reason": "strength为null，信息强度不足"
            }
        
        # 记录已浏览的帖子
        self.viewed_posts.append(post_id)
        
        # 记录旧状态
        old_emotion = self.emotion
        old_confidence = self.confidence
        
        # 更新情绪
        self.emotion = max(0.0, min(1.0, self.emotion + impact["emotion_change"]))
        
        # 更新置信度
        self.confidence = max(0.0, min(1.0, self.confidence + impact["confidence_change"]))
        
        # 记录交互历史
        interaction_record = {
            "post_id": post_id,
            "timestamp": post_object.get("timestamp", ""),
            "impact": impact,
            "new_emotion": self.emotion,
            "new_confidence": self.confidence
        }
        self.interaction_history.append(interaction_record)
        
        # 计算本次状态变化量
        delta_emotion = self.emotion - old_emotion
        delta_confidence = self.confidence - old_confidence
        
        # 计算影响分数
        influence_score = abs(delta_emotion) + abs(delta_confidence)
        if influence_score > getattr(self, 'max_impact_score', float('-inf')):
            self.max_impact_score = influence_score
            self.max_impact_post_id = post_id
        
        # 状态变化后，记录一条历史
        self.state_history.append({
            "timestamp": post_object.get("timestamp", datetime.now().isoformat()),
            "emotion": self.emotion,
            "stance": self._stance
        })
        
        # 记录每个帖子对Agent的影响分数
        if not hasattr(self, 'impact_records') or self.impact_records is None:
            self.impact_records = []
        self.impact_records.append({
            'post_id': post_id,
            'impact_score': impact.get('base_impact', 0.0)
        })
        
        return {
            "status": "updated",
            "post_id": post_id,
            "impact": impact,
            "delta_emotion": delta_emotion,
            "delta_confidence": delta_confidence,
            "new_state": {
                "emotion": self.emotion,
                "confidence": self.confidence,
            }
        }
    
    def _calculate_post_impact(self, post_object: dict) -> Dict[str, float]:
        """
        计算帖子对Agent的影响（改进版：使用信息强度权重和完善的置信度逻辑）
        
        【重要改进】
        1. 信息强度权重：使用帖子的strength字段作为影响权重，而不是过滤门槛
        2. 完善置信度逻辑：区分立场一致/不一致对置信度的不同影响
        3. null值处理：strength为null的帖子被完全过滤，不产生任何影响
        
        Args:
            post_object (dict): 帖子数据
            
        Returns:
            Dict[str, float]: 影响值字典
        """
        # === 信息强度权重处理 ===
        # 获取帖子信息强度（strength字段）
        post_strength = post_object.get("strength")
        
        # 处理null值：strength为null的帖子被完全过滤
        if post_strength is None:
            return {
                "emotion_change": 0.0,
                "confidence_change": 0.0,
                "base_impact": 0.0,
                "stance_similarity": 0.0,
                "interest_match": 0.0,
                "strength_weight": 0.0,
                "filtered": True
            }
        
        # 将strength转换为影响权重（1.0, 2.0, 3.0 → 权重）
        strength_weight = float(post_strength)  # 1.0, 2.0, 3.0 直接作为权重
        
        # === 基础影响因子计算 ===
        # 获取帖子热度（归一化到0-1）
        post_heat = post_object.get("heat", 0) / 100.0  # 归一化到0-1
        
        # 计算立场相似度（使用真实的group字段映射的立场值）
        post_stance = self._estimate_post_stance(post_object)
        stance_similarity = 1.0 - abs(self._stance - post_stance)
        
        # 计算兴趣匹配度
        interest_match = self._calculate_interest_match(post_object)
        
        # === 情绪变化计算（应用强度权重）===
        # 情绪变化：基于立场相似度，应用强度权重
        base_emotion_change = (stance_similarity - 0.5) * 0.1 * post_heat
        emotion_change = base_emotion_change * strength_weight
        
        # === 置信度变化计算（完善逻辑，应用强度权重）===
        # 完善置信度更新逻辑：区分立场一致/不一致
        if stance_similarity > 0.5:  # 立场一致
            # 立场一致时，帖子强度越高，置信度提升越多
            base_confidence_change = interest_match * post_heat * 0.05
            confidence_change = base_confidence_change * strength_weight
        else:  # 立场不一致
            # 立场不一致时，帖子强度越高，对置信度的削弱也越厉害
            # 但削弱幅度稍小，避免过度影响
            base_confidence_change = -interest_match * post_heat * 0.03
            confidence_change = base_confidence_change * strength_weight
        
        # === 综合影响计算 ===
        base_impact = post_heat * stance_similarity * interest_match * strength_weight
        
        return {
            "emotion_change": emotion_change,
            "confidence_change": confidence_change,
            "base_impact": base_impact,
            "stance_similarity": stance_similarity,
            "interest_match": interest_match,
            "strength_weight": strength_weight,
            "filtered": False
        }
    
    def _estimate_post_stance(self, post_object: dict) -> float:
        """
        估算帖子的立场值（修复版：使用真实的group字段映射）
        
        【重要说明】本方法与AgentController._calculate_stance_similarity保持一致：
        - 从帖子的'stance'字段读取数据（该字段在WorldState.normalize_post中由'group'字段映射而来）
        - 使用相同的映射逻辑：group=1→0.0（支持患者），0→0.5（中立），2→1.0（支持医院）
        - 确保筛选阶段和状态更新阶段使用相同的立场值，避免数据不一致
        
        Args:
            post_object (dict): 帖子数据
            
        Returns:
            float: 估算的立场值 (0-1)
        """
        # 从帖子数据中读取已有的立场信息
        # 注意：这里的'stance'字段实际上是原始数据中的'group'字段映射而来
        stance = post_object.get('stance', 0)
        
        # 根据group字段映射（与AgentController._calculate_stance_similarity保持一致）
        # 映射规则：
        # - group=1 (支持患者) → 0.0
        # - group=0 (中立) → 0.5  
        # - group=2 (支持医院) → 1.0
        if stance == 1:
            return 0.0  # 支持患者
        elif stance == 0:
            return 0.5  # 中立
        elif stance == 2:
            return 1.0  # 支持医院
        else:
            return 0.5  # 默认中立（处理异常情况）
    
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
    
    def generate_action_prompt(self, debug_reason=False) -> tuple[str | None, str | None, str | None]:
        """
        行动决策接口，决定是否发言，返回Prompt或None。
        debug_reason: 若为True，则返回(发言内容, 原因)元组
        """
        if self.current_posts_count >= self.max_posts_per_slice:
            if debug_reason:
                return None, None, "已达本时间片发帖上限"
            return None, None, None
        delta_emotion = abs(self.emotion - getattr(self, '_last_emotion', self.emotion))
        delta_stance = abs(self._stance - getattr(self, '_last_stance', self._stance))
        fluctuation = delta_emotion + delta_stance
        base_threshold = 0.05
        if fluctuation < base_threshold:
            if debug_reason:
                return None, None, f"波动量{fluctuation:.3f}低于阈值{base_threshold}"
            return None, None, None
        base_prob = min(fluctuation / 2.0, 1.0)
        activity_multiplier = self.activity_level if self.activity_level is not None else 1.0
        final_prob = base_prob * activity_multiplier
        rand_val = random.random()
        if rand_val > final_prob:
            if debug_reason:
                return None, None, f"最终概率{final_prob:.3f}，随机值{rand_val:.3f}，未通过"
            return None, None, None
        parent_post_id = None
        if hasattr(self, 'impact_records') and self.impact_records:
            max_impact = max(self.impact_records, key=lambda x: x['impact_score'])
            parent_post_id = max_impact['post_id']
        prompt = self._create_action_prompt()
        self.current_posts_count += 1
        self._last_emotion = self.emotion
        self._last_stance = self._stance
        self.reset_impact_records()
        if debug_reason:
            return prompt, parent_post_id, "发言"
        return prompt, parent_post_id, None
    
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
        Agent类型（如"意见领袖"、"普通用户"），用于行动顺序调度
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

    def reset_impact_records(self):
        self.impact_records = [] 