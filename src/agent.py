from typing import Dict, List, Any, Optional
import random


class Agent:
    """
    真实的Agent类，用于模拟社交媒体用户的行为
    
    核心功能：
    1. 维护Agent的状态（情绪、立场、置信度等）
    2. 根据接收到的帖子更新状态
    3. 生成行动提示词
    4. 管理黑名单和兴趣偏好
    """
    
    def __init__(self, agent_config: dict):
        """
        初始化Agent
        
        Args:
            agent_config (dict): Agent配置字典
        """
        # 基本信息
        self.agent_id = agent_config.get("agent_id", "unknown")
        self.agent_type = agent_config.get("type", "普通用户")
        self.stance = agent_config.get("stance", 0.5)  # 立场值 (0-1)
        self.interests = agent_config.get("interests", [])  # 兴趣标签列表
        self.influence = agent_config.get("influence", 1.0)  # 影响力系数
        
        # 动态状态
        self.emotion = 0.5  # 情绪值 (0-1, 0=负面, 1=正面)
        self.confidence = 0.5  # 置信度 (0-1)
        self.energy = 1.0  # 精力值 (0-1)
        
        # 交互历史
        self.viewed_posts = []  # 已浏览的帖子ID列表
        self.blacklist = []  # 黑名单用户ID列表
        self.interaction_history = []  # 交互历史记录
        
        # 行为参数（可从配置中读取）
        self.post_probability = agent_config.get("post_probability", 0.3)  # 发帖概率
        self.max_posts_per_slice = agent_config.get("max_posts_per_slice", 2)  # 每个时间片最大发帖数
        self.current_posts_count = 0  # 当前时间片已发帖数
        
        # 重置当前时间片的发帖计数
        self._reset_slice_counters()
    
    def _reset_slice_counters(self):
        """重置时间片相关的计数器"""
        self.current_posts_count = 0
        self.viewed_posts = []
    
    def update_state(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据接收到的帖子更新Agent状态
        
        Args:
            post_data (Dict[str, Any]): 帖子数据
            
        Returns:
            Dict[str, Any]: 状态更新结果
        """
        post_id = post_data.get("id", "")
        
        # 避免重复处理同一帖子
        if post_id in self.viewed_posts:
            return {"status": "already_viewed", "post_id": post_id}
        
        # 记录已浏览的帖子
        self.viewed_posts.append(post_id)
        
        # 计算帖子对Agent的影响
        impact = self._calculate_post_impact(post_data)
        
        # 更新情绪
        self.emotion = max(0.0, min(1.0, self.emotion + impact["emotion_change"]))
        
        # 更新置信度
        self.confidence = max(0.0, min(1.0, self.confidence + impact["confidence_change"]))
        
        # 更新精力（浏览帖子消耗精力）
        self.energy = max(0.0, self.energy - 0.05)
        
        # 记录交互历史
        interaction_record = {
            "post_id": post_id,
            "timestamp": post_data.get("timestamp", ""),
            "impact": impact,
            "new_emotion": self.emotion,
            "new_confidence": self.confidence
        }
        self.interaction_history.append(interaction_record)
        
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
    
    def _calculate_post_impact(self, post_data: Dict[str, Any]) -> Dict[str, float]:
        """
        计算帖子对Agent的影响
        
        Args:
            post_data (Dict[str, Any]): 帖子数据
            
        Returns:
            Dict[str, float]: 影响值字典
        """
        # 获取帖子热度
        post_heat = post_data.get("heat", 0) / 100.0  # 归一化到0-1
        
        # 计算立场相似度（简化实现）
        post_stance = self._estimate_post_stance(post_data)
        stance_similarity = 1.0 - abs(self.stance - post_stance)
        
        # 计算兴趣匹配度
        interest_match = self._calculate_interest_match(post_data)
        
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
    
    def _estimate_post_stance(self, post_data: Dict[str, Any]) -> float:
        """
        估算帖子的立场值（简化实现）
        
        Args:
            post_data (Dict[str, Any]): 帖子数据
            
        Returns:
            float: 估算的立场值 (0-1)
        """
        # 这里应该使用更复杂的NLP分析
        # 暂时使用基于帖子ID的伪随机值
        random.seed(hash(post_data.get("id", "")))
        return random.uniform(0.0, 1.0)
    
    def _calculate_interest_match(self, post_data: Dict[str, Any]) -> float:
        """
        计算帖子与Agent兴趣的匹配度
        
        Args:
            post_data (Dict[str, Any]): 帖子数据
            
        Returns:
            float: 匹配度 (0-1)
        """
        if not self.interests:
            return 0.5  # 如果没有兴趣标签，返回中等匹配度
        
        # 获取帖子的兴趣标签（如果存在）
        post_interests = post_data.get("interests", [])
        
        if not post_interests:
            return 0.3  # 如果帖子没有兴趣标签，返回较低匹配度
        
        # 计算交集大小
        common_interests = set(self.interests) & set(post_interests)
        
        # 计算匹配度
        if len(self.interests) == 0:
            return 0.0
        
        return len(common_interests) / len(self.interests)
    
    def generate_action_prompt(self) -> Optional[str]:
        """
        生成行动提示词
        
        Returns:
            Optional[str]: 提示词文本，如果不需要行动则返回None
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
        base_prompt = f"""你是一个{self.agent_type}，ID为{self.agent_id}。

当前状态：
- 立场倾向：{self.stance:.2f} (0=反对，1=支持)
- 情绪状态：{self.emotion:.2f} (0=负面，1=正面)
- 置信度：{self.confidence:.2f} (0=不确定，1=确定)
- 精力值：{self.energy:.2f} (0=疲惫，1=充沛)
- 兴趣领域：{', '.join(self.interests) if self.interests else '无特定兴趣'}

最近浏览了{len(self.viewed_posts)}条帖子，请基于你的状态和浏览历史，生成一条社交媒体帖子。

要求：
1. 帖子内容要符合你的立场倾向和情绪状态
2. 内容要真实、自然，符合{self.agent_type}的身份特征
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
        if user_id not in self.blacklist:
            self.blacklist.append(user_id)
    
    def remove_from_blacklist(self, user_id: str) -> None:
        """
        从黑名单中移除用户
        
        Args:
            user_id (str): 要解除拉黑的用户ID
        """
        if user_id in self.blacklist:
            self.blacklist.remove(user_id)
    
    def is_blacklisted(self, user_id: str) -> bool:
        """
        检查用户是否在黑名单中
        
        Args:
            user_id (str): 用户ID
            
        Returns:
            bool: 是否在黑名单中
        """
        return user_id in self.blacklist
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        获取Agent状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "stance": self.stance,
            "emotion": self.emotion,
            "confidence": self.confidence,
            "energy": self.energy,
            "post_probability": self.post_probability,
            "max_posts_per_slice": self.max_posts_per_slice,
            "viewed_posts_count": len(self.viewed_posts),
            "blacklist_count": len(self.blacklist),
            "interaction_count": len(self.interaction_history)
        }
    
    def __str__(self):
        return f"Agent(id={self.agent_id}, type={self.agent_type}, stance={self.stance:.2f}, emotion={self.emotion:.2f})" 