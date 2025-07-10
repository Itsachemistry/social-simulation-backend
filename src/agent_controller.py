from src.agent import OpinionPublisher, OpinionReceiver, RuleBasedAgent
from src.world_state import WorldState
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import random
import math

SYSTEM_OPINION_LEADER_POP_BONUS = 0.7

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
        self.agent_type = agent_config.get("type", "普通用户")  # 意见领袖、普通用户
        self.stance = agent_config.get("stance", 0.5)  # 立场值 (0-1)
        self.interests = agent_config.get("interests", [])  # 兴趣标签列表
        self.influence = agent_config.get("influence", 1.0)  # 影响力系数
        
    def __str__(self):
        return f"PlaceholderAgent(id={self.agent_id}, type={self.agent_type}, stance={self.stance})"


class AgentController:
    """
    Agent控制器，负责管理和调度所有Agent的行为
    
    核心功能：
            1. 管理不同类型的Agent（意见领袖、普通用户）
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
            "普通用户": []
        }
        self.action_priority = {
            "意见领袖": 1,
            "普通用户": 2
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
                agent_type = config.get('agent_type', 'RuleBasedAgent')
                if agent_type == 'OpinionPublisher':
                    agent = OpinionPublisher.from_dict(config)
                elif agent_type == 'OpinionReceiver':
                    agent = OpinionReceiver.from_dict(config)
                else:
                    agent = RuleBasedAgent.from_dict(config)
                status = agent.get_status()
                if status['agent_type'] in self.agents:
                    self.agents[status['agent_type']].append(agent)
                else:
                    print(f"警告：未知的Agent类型 '{status['agent_type']}'，归类为普通用户")
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
            if isinstance(emotion, str):
                emo_map = {'positive': 1.0, 'neutral': 0.5, 'negative': 0.0}
                emotion = emo_map.get(emotion, 0.5)
            if emotion > 0.6:
                emotion_counts["positive"] += 1
            elif emotion < 0.4:
                emotion_counts["negative"] += 1
            else:
                emotion_counts["neutral"] += 1
            
            # 根据帖子立场值分类（假设立场值在0-1之间，0.5为中性）
            stance = post.get("stance", 0.5)
            if isinstance(stance, str):
                stance_map = {'support': 1.0, 'neutral': 0.5, 'oppose': 0.0}
                stance = stance_map.get(stance, 0.5)
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

    def run_time_slice(self, agents, world_state, llm_service=None):
        """
        运行一个时间片
        """
        # 获取当前时间片的所有帖子
        all_posts = world_state.get_all_posts()
        
        # 计算全局环境强度因子
        global_intensity_factor = self.calculate_global_intensity_factor(all_posts)
        
        # 生成环境摘要（为意见领袖准备）
        environmental_summary = self._generate_environmental_summary(all_posts)
        
        # 按类型分组
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
        action_judgements = []  # 新增：记录每个agent的发言判定
        
        # 按优先级处理每种类型
        for agent_type in sorted_agent_types:
            type_agents = agents_by_type[agent_type]
            
            for agent in type_agents:
                # 为意见领袖提供环境摘要
                if agent_type == "意见领袖":
                    if hasattr(agent, 'update_state_with_summary'):
                        agent.update_state_with_summary(environmental_summary, llm_service)
                
                # 为每个Agent生成个性化信息流（使用动态阈值）
                personalized_posts = self._generate_personalized_feed(
                    agent, all_posts, global_intensity_factor
                )
                
                # 处理每个帖子
                for post in personalized_posts:
                    agent.update_emotion_and_stance(post)
                
                # 生成行动
                action_prompt, parent_post_id, reason = None, None, None
                if hasattr(agent, 'should_post') and agent.should_post():
                    action_prompt = agent.generate_text()
                action_judgements.append({
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "action": action_prompt is not None,
                    "reason": reason,
                    "parent_post_id": parent_post_id
                })
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
                        "parent_post_id": parent_post_id
                    }
                    
                    # 添加到世界状态
                    if world_state:
                        world_state.add_post(new_post)
                    
                    generated_posts.append(new_post)
                # 时间片结束后重置影响记录
                agent.max_impact_post_id = None
                agent.max_impact_value = float('-inf')
        
        # 新增：同步所有Agent的_last_emotion和_last_stance为当前值
        for agent in agents:
            agent._last_emotion = agent.emotion
            agent._last_stance = agent.stance
        
        return {"generated_posts": generated_posts, "action_judgements": action_judgements}
    
    def _generate_personalized_feed(self, agent, all_posts: list, global_intensity_factor: float = 1.0, w_pop: float = 0.7, w_rel: float = 0.3, k: float = 5.0, x0: float = None) -> list:
        """
        为指定Agent生成个性化信息流（逐帖概率门控模型，Sigmoid概率采样）
        """
        import math
        # === 广播信息强制注入 ===
        agent_feed = []
        broadcast_posts = [p for p in all_posts if p.get('is_broadcast') or p.get('is_event')]
        if broadcast_posts:
            # 只要有广播，全部强制注入（可多条）
            for bp in broadcast_posts:
                agent_feed.append(bp)
        # === 1. 过滤掉无效帖子 ===
        valid_posts = [p for p in all_posts if p.get('emotion') is not None and p.get('stance') is not None and p.get('strength') is not None]
        # 排除已注入的广播信息
        valid_posts = [p for p in valid_posts if p not in broadcast_posts]
        if not valid_posts:
            return agent_feed
        # === 2. 黑名单过滤 ===
        blocked_users = getattr(agent, 'blocked_users', set())
        posts = [p for p in valid_posts if p.get('author_id') not in blocked_users]
        if not posts:
            return agent_feed
        # === 3. 观点屏蔽过滤 ===
        opinion_blocking_degree = getattr(agent, 'opinion_blocking_degree', 0.0)
        T_stance = 2.0 * (1.0 - opinion_blocking_degree)
        agent_stance = agent.stance
        filtered_posts = []
        for post in posts:
            stance_score = post.get('stance')
            stance_diff = abs(agent_stance - stance_score)
            if stance_diff <= T_stance:
                filtered_posts.append(post)
        if not filtered_posts:
            return agent_feed
        # === 4. 计算分数 ===
        max_totalChildren = max([p.get('totalChildren', 0) for p in filtered_posts] or [1])
        scored_posts = []
        for post in filtered_posts:
            Score_Rel = max(0.0, 1.0 - abs(agent_stance - post.get('stance')))
            Score_Pop = 0.0
            tc = post.get('totalChildren', 0)
            if max_totalChildren > 0:
                Score_Pop = math.log(1 + tc) / math.log(1 + max_totalChildren)
            Final_Score = w_pop * Score_Pop + w_rel * Score_Rel
            scored_posts.append((Final_Score, post))
        if not scored_posts:
            return agent_feed
        # === 5. 逐帖概率门控 ===
        scores = [fs for fs, _ in scored_posts]
        if x0 is None:
            x0_val = float(sum(scores) / len(scores))
        else:
            x0_val = float(x0)
        for Final_Score, post in scored_posts:
            p_view = 1.0 / (1.0 + math.exp(-k * (Final_Score - x0_val)))
            R = random.random()
            if R < p_view:
                agent_feed.append(post)
        return agent_feed
    
    def _get_browse_count_for_agent(self, agent, global_intensity_factor: float = 1.0) -> int:
        """
        根据Agent类型和状态确定每个时间片的浏览帖子数量
        
        Args:
            agent: Agent对象
            global_intensity_factor (float): 全局环境强度因子
            
        Returns:
            int: 浏览帖子数量
        """
        # 基础浏览数量（基于Agent类型）
        base_counts = {
            "意见领袖": 5,    # 意见领袖关注更多信息
            "普通用户": 3     # 普通用户浏览较少
        }
        
        base_count = base_counts.get(agent.agent_type, 3)
        
        # 计算最终浏览数量
        final_count = base_count
        
        # 确保至少浏览1个帖子，最多浏览10个帖子
        return max(1, min(10, final_count))
    
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
            if isinstance(emotion, str):
                emo_map = {'positive': 1.0, 'neutral': 0.5, 'negative': 0.0}
                emotion = emo_map.get(emotion, 0.5)
            intensity = abs(emotion - 0.5) * 2  # 0-1
            emotion_intensities.append(intensity)
        
        avg_emotion_intensity = sum(emotion_intensities) / len(emotion_intensities)
        emotion_factor = 1.0 + avg_emotion_intensity  # 1.0-2.0
        
        # 4. 综合计算
        global_intensity = (post_count_factor + heat_factor + emotion_factor) / 3
        
        return max(0.1, min(2.0, global_intensity))
    
    def _calculate_stance_similarity(self, agent, post: dict) -> float:
        """
        计算Agent立场与帖子立场的相似度（新版：group=1→0.0，0→0.5，2→1.0）
        """
        group = post.get('stance', 0)
        if group == 1:
            post_stance_val = 0.0  # 支持患者
        elif group == 0:
            post_stance_val = 0.5  # 中立
        elif group == 2:
            post_stance_val = 1.0  # 支持医院
        else:
            post_stance_val = 0.5  # 默认中立
        # 兼容 agent.stance 为字符串的情况
        if isinstance(agent.stance, str):
            stance_map = {'support': 1.0, 'neutral': 0.5, 'oppose': 0.0}
            agent_stance_val = stance_map.get(agent.stance, 0.5)
        else:
            agent_stance_val = agent.stance
        similarity = 1.0 - abs(agent_stance_val - post_stance_val)
        return max(0.0, similarity)
    
    def _get_similarity_threshold_for_agent(self, agent) -> float:
        """
        根据Agent类型获取相似度阈值
        
        Args:
            agent: Agent对象
            
        Returns:
            float: 相似度阈值
        """
        # 不同类型的Agent对相似度敏感度不同
        similarity_thresholds = {
            "意见领袖": 0.7,    # 意见领袖关注度较高，对相似度要求也较高
            "普通用户": 0.3     # 普通用户只关注高热度内容，对相似度要求最低
        }
        
        return similarity_thresholds.get(agent.agent_type, 0.3)
    
    def _check_interest_match(self, agent, post: dict) -> bool:
        """
        当前系统不启用兴趣匹配，所有帖子均通过。
        """
        return True
    
    def _mock_llm_service(self, prompt: str) -> str:
        """模拟LLM回复"""
        return f"【模拟LLM生成内容】基于提示：{prompt[:30]}..."

    def create_post_from_agent(self, agent, content, timestamp=None):
        """
        由Agent生成新帖，自动赋予完整属性
        """
        import uuid
        post = {
            'id': str(uuid.uuid4()),
            'content': content,
            'author_id': agent.agent_id,
            'timestamp': timestamp or '',
            'emotion_score': agent.emotion,
            'stance_score': agent.stance,
            'information_strength': (abs(agent.emotion) + agent.confidence) / 2,
            'is_event': False,
        }
        # 角色区分热度
        if getattr(agent, 'agent_type', None) == 'OpinionPublisher':
            post['popularity_score'] = SYSTEM_OPINION_LEADER_POP_BONUS
        else:
            post['popularity_score'] = 0.0
        return post

    def create_broadcast_post(self, user_input_emotion, user_input_stance, content, timestamp=None):
        """
        创建广播信息/大新闻，属性全部顶格
        """
        import uuid
        post = {
            'id': str(uuid.uuid4()),
            'content': content,
            'author_id': 'system_broadcast',
            'timestamp': timestamp or '',
            'emotion_score': user_input_emotion,
            'stance_score': user_input_stance,
            'information_strength': 1.0,
            'popularity_score': 1.0,
            'is_event': True,
            'is_broadcast': True
        }
        return post


