from agent import Agent, RoleType
from world_state import WorldState
from time_manager import TimeSliceManager
import json
import random
import math

class AgentController:
    def __init__(self, world_state: WorldState, time_manager: TimeSliceManager, w_pop=0.7, k=2):
        self.world_state = world_state
        self.time_manager = time_manager
        self.agents = []
        self.w_pop = w_pop
        self.k = k

    def create_agent(self, agent_config):
        """创建Agent实例"""
        return Agent.from_dict(agent_config)

    def add_agent(self, agent: Agent):
        """添加Agent到控制器"""
        self.agents.append(agent)
    
    def load_agents_from_config(self, config_path):
        """从配置文件加载Agent"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        for agent_config in config.get('agents', []):
            agent = self.create_agent(agent_config)
            self.add_agent(agent)
        
        print(f"已加载 {len(self.agents)} 个Agent")
    
    def get_agent_by_id(self, agent_id):
        """根据ID获取Agent"""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    def _generate_personalized_feed(self, agent, all_posts, k=None, x0=None, w_pop=None, w_rel=None, opinion_blocking=None):
        """
        为指定Agent生成个性化信息流（完整加权融合+Sigmoid概率门控）
        移除T_stance硬性过滤，让立场差异通过相关性分数自然处理
        """
        # 优先使用传参，否则用控制器属性
        k = self.k if k is None else k
        w_pop = self.w_pop if w_pop is None else w_pop
        w_rel = 1.0 - w_pop if w_rel is None else w_rel
        # 移除opinion_blocking参数，不再用于T_stance计算

        candidate_posts = []
        final_scores = []
        score_rels = []
        score_pops = []
        post_ids = []

        # 计算热度归一化参数
        pops = [post.get('popularity', 0) for post in all_posts]
        pop_min = min(pops) if pops else 0
        pop_max = max(pops) if pops else 1
        pop_range = max(1e-6, pop_max - pop_min)

        for post in all_posts:
            # 硬性屏蔽：只保留有information_strength的帖子
            if post.get("information_strength") is None:
                continue
            if "author_id" in post and post["author_id"] in getattr(agent, "blocked_user_ids", []):
                continue
            
            # 相关性分数：基于立场差异，但不做硬性过滤
            agent_stance = getattr(agent, 'current_stance', 0.0)
            post_stance = post.get('stance_score', 0.0)
            stance_diff = abs(agent_stance - post_stance)
            score_rel = max(0.0, 1.0 - stance_diff)  # 立场差异越大，相关性越低
            
            # 热度归一化分数
            pop = post.get('popularity', 0)
            score_pop = (pop - pop_min) / pop_range if pop_range > 0 else 0.0
            
            # Final_Score加权融合
            final_score = w_pop * score_pop + w_rel * score_rel
            
            candidate_posts.append(post)
            final_scores.append(final_score)
            score_rels.append(score_rel)
            score_pops.append(score_pop)
            post_ids.append(post.get('id', post.get('post_id', 'unknown')))

        print(f"[Feed] Agent {agent.agent_id} 候选池大小: {len(candidate_posts)} (k={k}, x0={'auto' if x0 is None else x0})")

        if not candidate_posts:
            return [], []

        # Sigmoid概率转换
        if x0 is None:
            x0 = sum(final_scores) / len(final_scores)  # 均值为中心点
        viewing_probs = [
            1.0 / (1.0 + math.exp(-k * (score - x0)))
            for score in final_scores
        ]

        # 独立概率判定
        agent_feed = []
        for idx, (post, prob) in enumerate(zip(candidate_posts, viewing_probs)):
            selected = random.random() < prob
            print(f"    帖子{idx+1}: id={post_ids[idx]}, Score_Pop={score_pops[idx]:.3f}, Score_Rel={score_rels[idx]:.3f}, Final_Score={final_scores[idx]:.3f}, Sigmoid概率={prob:.3f}, {'✔选中' if selected else '✘未选中'}")
            if selected:
                agent_feed.append(post)
        # 返回详细分数信息，便于后续统计
        return agent_feed, list(zip(post_ids, score_pops, score_rels, final_scores, viewing_probs))

    # update_agent_emotions 也要适配返回值
    def update_agent_emotions(self, posts):
        """为每个Agent生成个性化Feed并逐条阅读，调用Agent自身的情绪更新算法，并统计分数"""
        all_agent_scores = {}
        for agent in self.agents:
            personalized_feed, post_scores = self._generate_personalized_feed(agent, posts)
            all_agent_scores[agent.agent_id] = post_scores
            for post in personalized_feed:
                agent.check_blocking(post)
                agent.update_emotion_and_stance(post)
                print(f"Agent {agent.agent_id} 阅读帖子 {post.get('id', post.get('post_id', 'unknown'))}: "
                      f"情绪 {agent.current_emotion:.3f}, 立场 {agent.current_stance:.3f}, "
                      f"置信度 {agent.current_confidence:.3f}")
        return all_agent_scores

    def get_agent_statuses(self):
        """获取所有Agent的状态"""
        return [agent.get_status() for agent in self.agents]

    def reset_agents(self):
        """重置所有Agent到初始状态"""
        for agent in self.agents:
            agent.current_emotion = agent.initial_emotion
            agent.current_stance = agent.initial_stance
            agent.current_confidence = agent.initial_confidence
            agent.blocked_user_ids = []

    def get_agents_by_role(self, role_type):
        """根据角色类型获取Agent列表"""
        return [agent for agent in self.agents if agent.role_type == role_type]

    def get_opinion_leaders(self):
        """获取意见领袖Agent"""
        return self.get_agents_by_role(RoleType.OPINION_LEADER)
    
    def get_ordinary_users(self):
        """获取普通用户Agent"""
        return self.get_agents_by_role(RoleType.ORDINARY_USER)

    def __str__(self):
        return f"AgentController(agents={len(self.agents)})"


