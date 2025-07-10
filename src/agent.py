from enum import Enum
import requests
import os
import random
from dotenv import load_dotenv
import csv

load_dotenv()  # 加载环境变量

class AttitudeStability(Enum):
    FIRM = "firm"
    UNCERTAIN = "uncertain"

class ResponseStyle(Enum):
    FILTERING = "filtering"  # 观点屏蔽
    OPEN = "open"            # 开放接受

class ActivityLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BaseAgent:
    def __init__(self, agent_id, attitude_stability, response_style, activity_level, emotion_update_mode="llm", emotion_sensitivity=0.5):
        self.agent_id = agent_id
        self.attitude_stability = AttitudeStability(attitude_stability)
        self.response_style = ResponseStyle(response_style)
        self.activity_level = ActivityLevel(activity_level)
        self.emotion = 0.0  # 情绪值：-1.0~1.0
        self.confidence = 0.5  # 信心度：0.0-1.0
        self.stance = 0.0  # 立场值：-1.0~1.0
        self.blocked_users = set()
        self.memory = []
        self.emotion_update_mode = emotion_update_mode  # "llm" or "rule"
        self.emotion_sensitivity = emotion_sensitivity  # α, 0.0~1.0
        self.llm_api_key = os.getenv('LLM_API_KEY')
        self.llm_endpoint = os.getenv('LLM_ENDPOINT')
        self.llm_model = os.getenv('LLM_MODEL') 
        # 立场更新相关系统参数
        self.THRESHOLD_PROCESS = 0.3
        self.THRESHOLD_CHANGE = 0.5
        self.DELTA_CONF_SMALL = 0.05
        self.DELTA_CONF_LARGE = 0.2

    def browse_posts(self, current_time_slice_posts):
        """浏览当前时间片的帖子，按热度和立场相似度排序，返回浏览列表"""
        def stance_similarity(post_stance):
            # 立场相似度，越接近越高
            if self.stance is None or post_stance is None:
                return 0.5
            return 1 - abs(self._stance_to_value(self.stance) - self._stance_to_value(post_stance))
        # 先按热度（假设有popularity字段），再按立场相似度排序
        sorted_posts = sorted(
            current_time_slice_posts,
            key=lambda p: (p.get('popularity', 0), stance_similarity(p.get('stance'))),
            reverse=True
        )
        browsed_posts = []
        for post in sorted_posts:
            if post['user_id'] in self.blocked_users:  # 如果用户被屏蔽，则跳过
                continue
            browsed_posts.append(post)
            self.memory.append(post['post_id'])
            if len(browsed_posts) >= self._get_browse_count(): # 按活跃度限制浏览数量
                break
        return browsed_posts

    def _get_browse_count(self):
        """根据活跃度返回浏览数量"""
        return 5 if self.activity_level == ActivityLevel.HIGH else 3 if self.activity_level == ActivityLevel.MEDIUM else 1

    def update_emotion_and_stance(self, post, event_description=None):
        """
        更新情绪状态和观点立场。根据self.emotion_update_mode选择算法：
        - "llm": LLM建议融合算法
        - "rule": 纯规则算法
        """
        if self.emotion_update_mode == "llm":
            self._update_emotion_llm_fusion(post, event_description)
        else:
            self._update_emotion_rule(post)

    def _update_emotion_llm_fusion(self, post, event_description=None):
        """
        LLM建议融合算法：
        1. 构造prompt，传递当前情绪、帖子内容、事件描述给LLM，获得建议情绪E_suggested（-1~1）
        2. 用公式融合：
           E_new = E_current * (1 - α * I_strength) + E_suggested * (α * I_strength)
        其中α为self.emotion_sensitivity，I_strength为post['strength']
        """
        # 1. 构造prompt并请求LLM
        if not hasattr(self, 'llm_api_key') or not self.llm_api_key or not self.llm_endpoint:
            print(f"[LLM] 未设置API KEY或endpoint，跳过LLM情绪推理，直接赋值。Agent: {self.agent_id}")
            E_suggested = post.get('emotion', 0.0)
        else:
            prompt = f"""你是一个社交媒体用户。你当前的情绪值为：{self.emotion}（范围-1到1）。\n你刚刚浏览了一条内容如下的帖子：{post.get('content', '')}。\n事件描述：{event_description or ''}\n请你根据当前情绪、帖子内容和事件描述，判断你现在的情绪值（-1到1之间的小数），并以如下JSON格式输出：{{'emotion': 0.xx}}。"""
            response = requests.post(
                self.llm_endpoint or '',
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.llm_api_key}'},
                json={'model': self.llm_model, 'messages': [{'role': 'user', 'content': prompt}]}
            )
            response.raise_for_status()
            import json as _json
            try:
                result = _json.loads(response.json()['choices'][0]['message']['content'].strip().replace("'", '"'))
                E_suggested = float(result.get('emotion', self.emotion))
            except Exception:
                E_suggested = self.emotion
        # 2. 融合更新
        alpha = self.emotion_sensitivity
        I_strength = float(post.get('strength', 1.0))
        E_current = self.emotion
        lr = alpha * I_strength
        self.emotion = E_current * (1 - lr) + E_suggested * lr

    def _update_emotion_rule(self, post):
        """
        纯规则算法：直接用post['emotion']作为建议情绪P_emotion，带入融合公式
        E_new = E_current * (1 - α * I_strength) + P_emotion * (α * I_strength)
        """
        P_emotion = float(post.get('emotion', 0.0))
        alpha = self.emotion_sensitivity
        I_strength = float(post.get('strength', 1.0))
        E_current = self.emotion
        lr = alpha * I_strength
        self.emotion = E_current * (1 - lr) + P_emotion * lr

    def check_blocking(self, post):
        """检查是否需要屏蔽用户"""
        if self.response_style == ResponseStyle.FILTERING:
            stance_diff = abs(self._stance_to_value(self.stance) - self._stance_to_value(post['stance']))
            if stance_diff > 0.7:
                self.blocked_users.add(post['user_id'])

    def _stance_to_value(self, stance):
        """立场数值化转换"""
        stance_map = {'support': 1.0, 'neutral': 0.5, 'oppose': 0.0}
        return stance_map.get(stance, 0.5)

    def get_status(self):
        return {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__,
            'attitude_stability': self.attitude_stability.value,
            'response_style': self.response_style.value,
            'activity_level': self.activity_level.value,
            'emotion': self.emotion,
            'stance': self.stance,
            'confidence': self.confidence,
            'blocked_users': list(self.blocked_users),
            'memory': self.memory,
            'attitude_firmness': getattr(self, 'attitude_firmness', 0.5),
            'opinion_blocking_degree': getattr(self, 'opinion_blocking_degree', 0.0),
            'emotion_update_mode': getattr(self, 'emotion_update_mode', 'llm'),
            'emotion_sensitivity': getattr(self, 'emotion_sensitivity', 0.5)
        }

    @classmethod
    def from_dict(cls, config):
        return cls(
            config['agent_id'],
            config['attitude_stability'],
            config['response_style'],
            config['activity_level'],
            config.get('emotion_update_mode', 'llm'),
            float(config.get('emotion_sensitivity', 0.5))
        )

    def update_stance(self, post):
        """
        立场更新算法：分为坚定型和不坚定型Agent
        - agent.attitude_stability: Enum (FIRM/UNCERTAIN)
        - agent.attitude_firmness: float (0-1), 0.5为分界
        - agent.stance: float (-1~1)
        - agent.confidence: float (0~1)
        - post['stance']: float (-1~1)
        - post['strength']: float (0~1)
        """
        def clamp(val, minv, maxv):
            return max(minv, min(maxv, val))
        stance_score = post.get('stance')
        information_strength = post.get('strength')
        if stance_score is None or information_strength is None:
            return
        # 判断类型
        is_firm = (self.attitude_stability == AttitudeStability.FIRM) or (getattr(self, 'attitude_firmness', 0.5) >= 0.5)
        if is_firm:
            # 坚定型Agent
            if information_strength < self.THRESHOLD_PROCESS:
                # 信息强度太低，置信度随机扰动
                disturbance = random.uniform(-0.02, 0.02)
                self.confidence = clamp(self.confidence + disturbance, 0.0, 1.0)
                return
            # 判断立场方向是否一致
            stance_match = (self.stance * stance_score >= 0)
            if stance_match:
                # 立场一致，置信度小幅提升
                self.confidence = clamp(self.confidence + self.DELTA_CONF_SMALL, 0.0, 1.0)
            else:
                if information_strength >= self.THRESHOLD_CHANGE:
                    # 强度足够，立场反转，置信度大幅下降
                    self.stance = stance_score
                    self.confidence = clamp(self.confidence - self.DELTA_CONF_LARGE, 0.0, 1.0)
                else:
                    # 强度不足，置信度小幅下降
                    self.confidence = clamp(self.confidence - self.DELTA_CONF_SMALL, 0.0, 1.0)
        else:
            # 不坚定型Agent
            if information_strength >= self.THRESHOLD_PROCESS:
                # 强度足够，直接采纳新立场，置信度=信息强度
                self.stance = stance_score
                self.confidence = information_strength
            else:
                # 强度不足，置信度小幅下降
                self.confidence = clamp(self.confidence - self.DELTA_CONF_SMALL, 0.0, 1.0)

class LLMDrivenAgent(BaseAgent):
    def __init__(self, agent_id, attitude_stability, response_style, activity_level, agent_type, attitude_firmness=0.5, opinion_blocking_degree=0.0, emotion_update_mode='llm', emotion_sensitivity=0.5):
        super().__init__(agent_id, attitude_stability, response_style, activity_level, emotion_update_mode, emotion_sensitivity)
        self.agent_type = agent_type
        self.attitude_firmness = attitude_firmness
        self.opinion_blocking_degree = opinion_blocking_degree
        self.emotion_update_mode = emotion_update_mode
        self.emotion_sensitivity = emotion_sensitivity
        self.llm_api_key = os.getenv('LLM_API_KEY')
        self.llm_endpoint = os.getenv('LLM_ENDPOINT')
        self.llm_model = os.getenv('LLM_MODEL') 

    def generate_text(self):
        """调用LLM生成文本"""
        if not self.llm_api_key:
            print(f"[LLM] 未设置API KEY，跳过LLM调用，返回空字符串。Agent: {self.agent_id}")
            return ""
        print(f"[LLM] 调用 LLM 生成文本，Agent: {self.agent_id}, 情绪: {self.emotion}, 立场: {self.stance}")
        prompt = f"""作为社交媒体智能体，你的特征：
        - 态度坚定性：{self.attitude_stability.value}
        - 回应方式：{self.response_style.value}
        - 活跃度：{self.activity_level.value}
        当前状态：
        - 情绪：{self.emotion}
        - 立场：{self.stance}
        请生成一段符合以上特征的社交媒体帖子内容。"""

        response = requests.post(
            self.llm_endpoint,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.llm_api_key}'},
            json={'model': {self.llm_model}, 'messages': [{'role': 'user', 'content': prompt}]}
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()

    def get_status(self):
        return {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__,
            'attitude_stability': self.attitude_stability.value,
            'response_style': self.response_style.value,
            'activity_level': self.activity_level.value,
            'emotion': self.emotion,
            'stance': self.stance,
            'confidence': self.confidence,
            'blocked_users': list(self.blocked_users),
            'memory': self.memory,
            'attitude_firmness': getattr(self, 'attitude_firmness', 0.5),
            'opinion_blocking_degree': getattr(self, 'opinion_blocking_degree', 0.0),
            'emotion_update_mode': getattr(self, 'emotion_update_mode', 'llm'),
            'emotion_sensitivity': getattr(self, 'emotion_sensitivity', 0.5)
        }

    @classmethod
    def from_dict(cls, config):
        return cls(
            config['agent_id'],
            config['attitude_stability'],
            config['response_style'],
            config['activity_level'],
            config.get('agent_type', 'llm'),
            float(config.get('attitude_firmness', 0.5)),
            float(config.get('opinion_blocking_degree', 0.0)),
            config.get('emotion_update_mode', 'llm'),
            float(config.get('emotion_sensitivity', 0.5))
        )

class OpinionPublisher(LLMDrivenAgent):
    def __init__(self, agent_id, attitude_stability, response_style, activity_level, attitude_firmness=0.5, opinion_blocking_degree=0.0, emotion_update_mode='llm', emotion_sensitivity=0.5):
        super().__init__(agent_id, attitude_stability, response_style, activity_level, 'publisher', attitude_firmness, opinion_blocking_degree, emotion_update_mode, emotion_sensitivity)

    def should_post(self):
        """判断是否需要发布帖子"""
        return self.activity_level == ActivityLevel.HIGH or abs(self.emotion) > 0.7

    @classmethod
    def from_dict(cls, config):
        return cls(
            config['agent_id'],
            config['attitude_stability'],
            config['response_style'],
            config['activity_level'],
            float(config.get('attitude_firmness', 0.5)),
            float(config.get('opinion_blocking_degree', 0.0)),
            config.get('emotion_update_mode', 'llm'),
            float(config.get('emotion_sensitivity', 0.5))
        )

class OpinionReceiver(LLMDrivenAgent):
    def __init__(self, agent_id, attitude_stability, response_style, activity_level, attitude_firmness=0.5, opinion_blocking_degree=0.0, emotion_update_mode='llm', emotion_sensitivity=0.5):
        super().__init__(agent_id, attitude_stability, response_style, activity_level, 'receiver', attitude_firmness, opinion_blocking_degree, emotion_update_mode, emotion_sensitivity)

    def should_post(self):
        """判断是否需要发布帖子"""
        # 接收者通常不会主动发布帖子，除非情绪非常强烈
        return self.activity_level == ActivityLevel.HIGH and abs(self.emotion) > 0.9

    @classmethod
    def from_dict(cls, config):
        return cls(
            config['agent_id'],
            config['attitude_stability'],
            config['response_style'],
            config['activity_level'],
            float(config.get('attitude_firmness', 0.5)),
            float(config.get('opinion_blocking_degree', 0.0)),
            config.get('emotion_update_mode', 'llm'),
            float(config.get('emotion_sensitivity', 0.5))
        )

class RuleBasedAgent(BaseAgent):
    def __init__(self, agent_id, attitude_stability, response_style, activity_level, attitude_firmness=0.5, opinion_blocking_degree=0.0, emotion_update_mode='llm', emotion_sensitivity=0.5):
        super().__init__(agent_id, attitude_stability, response_style, activity_level, emotion_update_mode, emotion_sensitivity)
        self.attitude_firmness = attitude_firmness
        self.opinion_blocking_degree = opinion_blocking_degree
        self.emotion_update_mode = emotion_update_mode
        self.emotion_sensitivity = emotion_sensitivity

    def generate_text(self):
        """基于规则生成文本"""
        if self.emotion == 'positive':
            return f"我支持{self.stance}！这是个好消息！"
        elif self.emotion == 'negative':
            return f"我反对{self.stance}。这让我很失望。"
        else:
            return f"关于这件事，我保持中立态度"

    def should_post(self):
        """判断是否需要发布帖子"""
        # 根据情绪和活跃度判断是否发布帖子
        activity_factor = {'high': 0.8, 'medium': 0.5, 'low': 0.2}[self.activity_level.value]
        return (abs(self.emotion) * activity_factor) > 0.5

    def get_status(self):
        """返回当前智能体状态，便于导出和查询"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__,
            'attitude_stability': self.attitude_stability.value,
            'response_style': self.response_style.value,
            'activity_level': self.activity_level.value,
            'emotion': self.emotion,
            'stance': self.stance,
            'confidence': self.confidence,
            'blocked_users': list(self.blocked_users),
            'memory': self.memory,
            'attitude_firmness': getattr(self, 'attitude_firmness', 0.5),
            'opinion_blocking_degree': getattr(self, 'opinion_blocking_degree', 0.0),
            'emotion_update_mode': getattr(self, 'emotion_update_mode', 'llm'),
            'emotion_sensitivity': getattr(self, 'emotion_sensitivity', 0.5)
        }

    @classmethod
    def from_dict(cls, config):
        return cls(
            config['agent_id'],
            config['attitude_stability'],
            config['response_style'],
            config['activity_level'],
            float(config.get('attitude_firmness', 0.5)),
            float(config.get('opinion_blocking_degree', 0.0)),
            config.get('emotion_update_mode', 'llm'),
            float(config.get('emotion_sensitivity', 0.5))
        )

def load_agents_from_csv(csv_path):
    """从CSV文件读取智能体状态并恢复为对象列表"""
    agents = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            agent_type = row['agent_type']
            attitude_firmness = float(row.get('attitude_firmness', 0.5))
            opinion_blocking_degree = float(row.get('opinion_blocking_degree', 0.0))
            emotion_update_mode = row.get('emotion_update_mode', 'llm')
            emotion_sensitivity = float(row.get('emotion_sensitivity', 0.5))
            if agent_type == 'OpinionPublisher':
                agent = OpinionPublisher(row['agent_id'], row['attitude_stability'], row['response_style'], row['activity_level'], attitude_firmness, opinion_blocking_degree, emotion_update_mode, emotion_sensitivity)
            elif agent_type == 'OpinionReceiver':
                agent = OpinionReceiver(row['agent_id'], row['attitude_stability'], row['response_style'], row['activity_level'], attitude_firmness, opinion_blocking_degree, emotion_update_mode, emotion_sensitivity)
            else:
                agent = RuleBasedAgent(row['agent_id'], row['attitude_stability'], row['response_style'], row['activity_level'], attitude_firmness, opinion_blocking_degree, emotion_update_mode, emotion_sensitivity)
            # 恢复状态
            agent.emotion = float(row['emotion']) if row['emotion'] else 0.0
            agent.stance = float(row['stance']) if row['stance'] else 0.0
            agent.confidence = float(row['confidence']) if row['confidence'] else 0.5
            agent.blocked_users = set(row['blocked_users'].split(',')) if row['blocked_users'] else set()
            agent.memory = row['memory'].split(',') if row['memory'] else []
            agents.append(agent)
    return agents

def main():
    # 先尝试从CSV读取智能体状态，否则新建
    import os
    csv_path = 'agent_status_output.csv'
    if os.path.exists(csv_path):
        agents = load_agents_from_csv(csv_path)
    else:
        agents = [
            OpinionPublisher('pub_001', 'firm', 'filtering', 'high'),
            OpinionReceiver('rec_001', 'uncertain', 'open', 'medium'),
            RuleBasedAgent('rule_001', 'uncertain', 'open', 'low')
        ]

    # 让每个智能体执行一次行动（如判断是否发帖并生成内容）
    for agent in agents:
        if hasattr(agent, 'should_post') and agent.should_post():
            try:
                content = agent.generate_text()
                print(f"Agent {agent.agent_id} posted: {content}")
            except Exception as e:
                print(f"Agent {agent.agent_id} failed to post: {e}")

    # 保存所有智能体当前状态到CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['agent_id', 'agent_type', 'attitude_stability', 'response_style', 'activity_level', 'emotion', 'stance', 'confidence', 'blocked_users', 'memory', 'attitude_firmness', 'opinion_blocking_degree', 'emotion_update_mode', 'emotion_sensitivity']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for agent in agents:
            status = agent.get_status()
            status['blocked_users'] = ','.join(map(str, status['blocked_users']))
            status['memory'] = ','.join(map(str, status['memory']))
            writer.writerow(status)

if __name__ == "__main__":
    main()