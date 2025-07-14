from enum import Enum
import requests
import os
import random
from dotenv import load_dotenv
import csv

load_dotenv()  # 加载环境变量

class RoleType(Enum):
    ORDINARY_USER = "ordinary_user"
    OPINION_LEADER = "opinion_leader"

class Agent:
    """
    统一的Agent类，只保留标准字段和LLM功能
    """
    def __init__(self, agent_id, role_type, attitude_firmness, opinion_blocking, activity_level,
                 initial_emotion, initial_stance, initial_confidence,
                 current_emotion=None, current_stance=None, current_confidence=None,
                 blocked_user_ids=None):
        # 身份与角色属性
        self.agent_id = agent_id
        self.role_type = RoleType(role_type) if isinstance(role_type, str) else role_type
        
        # 个性特征 (静态)
        self.attitude_firmness = float(attitude_firmness)
        self.opinion_blocking = float(opinion_blocking)
        self.activity_level = float(activity_level)
        
        # 状态属性 (动态)
        self.initial_emotion = float(initial_emotion)
        self.initial_stance = float(initial_stance)
        self.initial_confidence = float(initial_confidence)
        
        # 当前状态（如果未指定则使用初始值）
        self.current_emotion = float(current_emotion) if current_emotion is not None else self.initial_emotion
        self.current_stance = float(current_stance) if current_stance is not None else self.initial_stance
        self.current_confidence = float(current_confidence) if current_confidence is not None else self.initial_confidence
        
        # 时间片开始时的状态（用于计算波动量）
        self.last_emotion = self.current_emotion
        self.last_stance = self.current_stance
        self.last_confidence = self.current_confidence
        
        # 交互属性
        self.blocked_user_ids = blocked_user_ids or []
        
        # LLM相关配置
        self.llm_api_key = os.getenv('LLM_API_KEY')
        self.llm_endpoint = os.getenv('LLM_ENDPOINT')
        self.llm_model = os.getenv('LLM_MODEL')
        
        # 发帖算法相关参数
        self.expression_threshold = 0.1  # 表达欲阈值
        self.scale_constant = 2.0  # 全局缩放常数
        self.emotion_sensitivity = 0.5  # 情绪敏感度

    def snapshot_state(self):
        """记录当前时间片开始时的状态"""
        self.last_emotion = self.current_emotion
        self.last_stance = self.current_stance
        self.last_confidence = self.current_confidence

    def should_post(self):
        """
        发帖判断算法：两阶段决策
        阶段一：资格审查 - 判断状态波动是否足够大
        阶段二：概率决策 - 基于波动量和活跃度计算最终概率
        """
        # 计算状态波动量（与时间片开始时的状态比较）
        delta_emotion = abs(self.current_emotion - self.last_emotion)
        delta_stance = abs(self.current_stance - self.last_stance)
        fluctuation = delta_emotion + delta_stance
        
        # 阈值判定
        if fluctuation < self.expression_threshold:
            return False  # 波动量不足，不满足表达欲阈值
        
        # 概率决策
        p_base = min(fluctuation / self.scale_constant, 1.0)
        p_reply = p_base * self.activity_level
        
        # 最终随机判定
        rand = random.random()
        return rand < p_reply

    def update_emotion_and_stance(self, post, event_description=None):
        """
        更新情绪状态和观点立场，使用LLM融合算法
        """
        self._update_emotion_llm_fusion(post, event_description)
        self._update_stance(post)

    def _update_emotion_llm_fusion(self, post, event_description=None):
        """
        LLM建议融合算法：
        1. 构造prompt，传递当前情绪、帖子内容、事件描述给LLM，获得建议情绪E_suggested（-1~1）
        2. 用公式融合：
           E_new = E_current * (1 - α * I_strength) + E_suggested * (α * I_strength)
        其中α为self.emotion_sensitivity，I_strength为post['information_strength']
        """
        # 1. 构造prompt并请求LLM
        if not self.llm_api_key or not self.llm_endpoint:
            print(f"[LLM] 未设置API KEY或endpoint，跳过LLM情绪推理，直接赋值。Agent: {self.agent_id}")
            E_suggested = post.get('emotion_score', post.get('emotion', 0.0))
        else:
            prompt = f"""你是一个社交媒体用户。你当前的情绪值为：{self.current_emotion}（范围-1到1）。\n你刚刚浏览了一条内容如下的帖子：{post.get('content', '')}。\n事件描述：{event_description or ''}\n请你根据当前情绪、帖子内容和事件描述，判断你现在的情绪值（-1到1之间的小数），并以如下JSON格式输出：{{'emotion': 0.xx}}。"""
            try:
                response = requests.post(
                    self.llm_endpoint,
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.llm_api_key}'},
                    json={'model': self.llm_model, 'messages': [{'role': 'user', 'content': prompt}]}
                )
                response.raise_for_status()
                import json as _json
                result = _json.loads(response.json()['choices'][0]['message']['content'].strip().replace("'", '"'))
                E_suggested = float(result.get('emotion', self.current_emotion))
            except Exception as e:
                print(f"[LLM] API调用失败: {e}，使用默认值。Agent: {self.agent_id}")
                E_suggested = self.current_emotion
        
        # 2. 融合更新
        alpha = self.emotion_sensitivity
        I_strength = float(post.get('information_strength', 1.0))  # 信息强度，0.0~1.0
        E_current = self.current_emotion
        lr = alpha * I_strength
        self.current_emotion = E_current * (1 - lr) + E_suggested * lr

    def _update_stance(self, post):
        """
        立场更新算法：分为坚定型和不坚定型Agent
        """
        def clamp(val, minv, maxv):
            return max(minv, min(maxv, val))
        
        stance_score = post.get('stance_score')
        information_strength = post.get('information_strength')
        if stance_score is None or information_strength is None:
            return
        
        # 判断类型
        is_firm = self.attitude_firmness >= 0.5
        
        # 阈值常量
        THRESHOLD_PROCESS = 0.3
        THRESHOLD_CHANGE = 0.5
        DELTA_CONF_SMALL = 0.05
        DELTA_CONF_LARGE = 0.2
        
        if is_firm:
            # 坚定型Agent
            if information_strength < THRESHOLD_PROCESS:
                # 信息强度太低，置信度随机扰动
                disturbance = random.uniform(-0.02, 0.02)
                self.current_confidence = clamp(self.current_confidence + disturbance, 0.0, 1.0)
                return
            
            # 判断立场方向是否一致
            stance_match = (self.current_stance * stance_score >= 0)
            if stance_match:
                # 立场一致，置信度小幅提升
                self.current_confidence = clamp(self.current_confidence + DELTA_CONF_SMALL, 0.0, 1.0)
            else:
                if information_strength >= THRESHOLD_CHANGE:
                    # 强度足够，立场反转，置信度大幅下降
                    self.current_stance = stance_score
                    self.current_confidence = clamp(self.current_confidence - DELTA_CONF_LARGE, 0.0, 1.0)
                else:
                    # 强度不足，置信度小幅下降
                    self.current_confidence = clamp(self.current_confidence - DELTA_CONF_SMALL, 0.0, 1.0)
        else:
            # 不坚定型Agent
            if information_strength < THRESHOLD_PROCESS:
                # 信息强度太低，立场随机扰动
                disturbance = random.uniform(-0.05, 0.05)
                self.current_stance = clamp(self.current_stance + disturbance, -1.0, 1.0)
                return
            
            # 立场更新
            lr = information_strength * 0.3  # 学习率
            self.current_stance = clamp(self.current_stance * (1 - lr) + stance_score * lr, -1.0, 1.0)
            
            # 置信度更新
            if abs(self.current_stance - stance_score) < 0.2:
                self.current_confidence = clamp(self.current_confidence + DELTA_CONF_SMALL, 0.0, 1.0)
            else:
                self.current_confidence = clamp(self.current_confidence - DELTA_CONF_SMALL, 0.0, 1.0)

    def check_blocking(self, post):
        """检查是否需要屏蔽用户"""
        if self.opinion_blocking > 0.0:
            stance_diff = abs(self.current_stance - post.get('stance_score', 0.0))
            if stance_diff > 0.7:
                user_id = post.get('user_id', post.get('author_id'))
                if user_id and user_id not in self.blocked_user_ids:
                    self.blocked_user_ids.append(user_id)

    def generate_text(self):
        """调用LLM生成文本"""
        if not self.llm_api_key or not self.llm_endpoint:
            print(f"[LLM] 未设置API KEY或endpoint，跳过LLM调用，返回空字符串。Agent: {self.agent_id}")
            return ""
        
        print(f"[LLM] 调用 LLM 生成文本，Agent: {self.agent_id}, 情绪: {self.current_emotion}, 立场: {self.current_stance}")
        prompt = f"""作为社交媒体智能体，你的特征：
        - 角色类型：{self.role_type.value}
        - 态度坚定性：{self.attitude_firmness}
        - 观点屏蔽度：{self.opinion_blocking}
        - 活跃度：{self.activity_level}
        当前状态：
        - 情绪：{self.current_emotion}
        - 立场：{self.current_stance}
        请生成一段符合以上特征的社交媒体帖子内容。"""

        try:
            response = requests.post(
                self.llm_endpoint,
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.llm_api_key}'},
                json={'model': self.llm_model, 'messages': [{'role': 'user', 'content': prompt}]}
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[LLM] 生成文本失败: {e}，返回空字符串。Agent: {self.agent_id}")
            return ""

    def get_status(self):
        """返回Agent的标准状态"""
        return {
            'agent_id': self.agent_id,
            'role_type': self.role_type.value,
            'attitude_firmness': self.attitude_firmness,
            'opinion_blocking': self.opinion_blocking,
            'activity_level': self.activity_level,
            'initial_emotion': self.initial_emotion,
            'initial_stance': self.initial_stance,
            'initial_confidence': self.initial_confidence,
            'current_emotion': self.current_emotion,
            'current_stance': self.current_stance,
            'current_confidence': self.current_confidence,
            'last_emotion': self.last_emotion,
            'last_stance': self.last_stance,
            'last_confidence': self.last_confidence,
            'blocked_user_ids': self.blocked_user_ids
        }

    @classmethod
    def from_dict(cls, config):
        """从配置字典创建Agent"""
        current_emotion = float(config.get('current_emotion', config.get('initial_emotion', 0.0)))
        current_stance = float(config.get('current_stance', config.get('initial_stance', 0.0)))
        current_confidence = float(config.get('current_confidence', config.get('initial_confidence', 0.5)))
        
        agent = cls(
            config['agent_id'],
            config['role_type'],
            float(config.get('attitude_firmness', 0.5)),
            float(config.get('opinion_blocking', 0.0)),
            float(config.get('activity_level', 0.5)),
            float(config.get('initial_emotion', 0.0)),
            float(config.get('initial_stance', 0.0)),
            float(config.get('initial_confidence', 0.5)),
            current_emotion,
            current_stance,
            current_confidence,
            config.get('blocked_user_ids', [])
        )
        
        # 设置last_*字段（如果配置中有，否则使用current_*）
        agent.last_emotion = float(config.get('last_emotion', current_emotion))
        agent.last_stance = float(config.get('last_stance', current_stance))
        agent.last_confidence = float(config.get('last_confidence', current_confidence))
        
        return agent

    def __str__(self):
        return f"Agent(id={self.agent_id}, role={self.role_type.value}, emotion={self.current_emotion:.2f}, stance={self.current_stance:.2f})"

def load_agents_from_csv(csv_path):
    """从CSV文件读取智能体状态并恢复为对象列表"""
    agents = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            agent = Agent(
                row['agent_id'],
                row['role_type'],
                float(row.get('attitude_firmness', 0.5)),
                float(row.get('opinion_blocking', 0.0)),
                float(row.get('activity_level', 0.5)),
                float(row.get('initial_emotion', 0.0)),
                float(row.get('initial_stance', 0.0)),
                float(row.get('initial_confidence', 0.5)),
                float(row.get('current_emotion', row.get('initial_emotion', 0.0))),
                float(row.get('current_stance', row.get('initial_stance', 0.0))),
                float(row.get('current_confidence', row.get('initial_confidence', 0.5))),
                row.get('blocked_user_ids', '').split(',') if row.get('blocked_user_ids') else []
            )
            agents.append(agent)
    return agents

def main():
    """测试函数"""
    import os
    csv_path = 'agent_status_output.csv'
    if os.path.exists(csv_path):
        agents = load_agents_from_csv(csv_path)
    else:
        agents = [
            Agent('pub_001', 'opinion_leader', 0.8, 0.2, 0.9, 0.3, 0.5, 0.7),
            Agent('rec_001', 'ordinary_user', 0.4, 0.1, 0.6, 0.0, 0.0, 0.5),
            Agent('rec_002', 'ordinary_user', 0.3, 0.3, 0.4, -0.2, -0.1, 0.3)
        ]

    # 让每个智能体执行一次行动
    for agent in agents:
        if agent.should_post():
            try:
                content = agent.generate_text()
                print(f"Agent {agent.agent_id} posted: {content}")
            except Exception as e:
                print(f"Agent {agent.agent_id} failed to post: {e}")

    # 保存所有智能体当前状态到CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['agent_id', 'role_type', 'attitude_firmness', 'opinion_blocking', 'activity_level', 
                     'initial_emotion', 'initial_stance', 'initial_confidence',
                     'current_emotion', 'current_stance', 'current_confidence',
                     'blocked_user_ids']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for agent in agents:
            status = agent.get_status()
            status['blocked_user_ids'] = ','.join(map(str, status['blocked_user_ids']))
            writer.writerow(status)

if __name__ == "__main__":
    main()