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
        # 新增：记录本时间片已读帖子
        self.viewed_posts = []
        # 新增：记录本时间片每次读帖后的情绪和立场变化
        self.emotion_stance_history = []
        
        # LLM相关配置
        self.llm_api_key = os.getenv('LLM_API_KEY')
        self.llm_endpoint = os.getenv('LLM_ENDPOINT')
        self.llm_model = os.getenv('LLM_MODEL')
        
        # 发帖算法相关参数
        self.expression_threshold = 0.05  # 表达欲阈值
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

    def update_emotion_and_stance(self, post, event_description=None, time_slice_index=None, all_posts=None):
        """
        更新情绪状态和观点立场，使用LLM融合算法，并记录变化历史
        """
        prev_emotion = self.current_emotion
        prev_stance = self.current_stance
        prev_confidence = self.current_confidence
        emotion_suggested, stance_suggested = self._update_emotion_llm_fusion(post, event_description, all_posts)
        self._update_stance(post, llm_stance_suggested=stance_suggested)
        # 记录本次变化
        self.emotion_stance_history.append({
            'post_id': post.get('mid', post.get('id', post.get('post_id', None))),
            'emotion_before': prev_emotion,
            'stance_before': prev_stance,
            'confidence_before': prev_confidence,
            'emotion_after': self.current_emotion,
            'stance_after': self.current_stance,
            'confidence_after': self.current_confidence,
            'time_slice_index': time_slice_index
        })

    def _update_emotion_llm_fusion(self, post, event_description=None, all_posts=None):
        """
        LLM建议融合算法：
        1. 构造prompt，传递当前情绪、帖子内容、事件描述给LLM，获得建议情绪E_suggested（-1~1）
        2. 用公式融合：
           E_new = E_current * (1 - α * I_strength) + E_suggested * (α * I_strength)
        其中α为self.emotion_sensitivity，I_strength为post['information_strength']
        """
        # 1. 构造prompt并请求LLM
        if not self.llm_api_key or not self.llm_endpoint:
            print(f"[LLM Debug] Agent {self.agent_id}: api_key={bool(self.llm_api_key)}, endpoint={bool(self.llm_endpoint)}")
            print(f"[LLM] 未设置API KEY或endpoint，跳过LLM情绪推理，直接赋值。Agent: {self.agent_id}")
            E_suggested = post.get('emotion_score', post.get('emotion', 0.0))
            S_suggested = post.get('stance_score', 0.0)
        else:
            # 读取外部prompt模板
            template_path = 'data/agent_reading_prompt_template_enhanced.txt'
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
            except FileNotFoundError:
                print(f"[Warning] 找不到prompt模板文件: {template_path}，跳过LLM调用")
                E_suggested = post.get('emotion_score', post.get('emotion', 0.0))
                S_suggested = post.get('stance_score', 0.0)
                alpha = self.emotion_sensitivity
                I_strength = float(post.get('information_strength', 1.0))
                E_current = self.current_emotion
                lr = alpha * I_strength
                self.current_emotion = E_current * (1 - lr) + E_suggested * lr
                return E_suggested, S_suggested

            # 构建mid_index并提取对话链条
            if all_posts:
                # 动态导入避免循环依赖
                from .services import extract_chain, generate_context
                
                mid_index = {}
                def build_index(posts):
                    for p in posts:
                        mid_index[p.get('mid', p.get('id'))] = p
                        if 'children' in p:
                            build_index(p['children'])
                build_index(all_posts)
                
                # 提取对话链条
                target_mid = post.get('mid', post.get('id'))
                chain = extract_chain(mid_index, target_mid)
                context_text = generate_context(chain)
            else:
                # 没有all_posts，生成简单上下文
                context_text = "(这是一个独立帖子，没有回复关系)"

            # 获取帖子内容
            post_content = post.get('text', post.get('content', post.get('original_text', '')))
            
            # 替换模板中的占位符
            prompt = prompt_template.format(
                current_emotion=self.current_emotion,
                current_stance=self.current_stance,
                current_confidence=self.current_confidence,
                role_type=self.role_type.value,
                attitude_firmness=self.attitude_firmness,
                opinion_blocking=self.opinion_blocking,
                post_context=context_text,
                post_content=post_content,
                event_description=event_description or ""
            )
            
            print(f"[LLM] Agent {self.agent_id} 正在调用LLM分析情绪...")
            print(f"[LLM Prompt] {prompt}")
            print(f"[LLM Post] 帖子内容: '{post_content}'")
            print(f"[LLM Post] 帖子字段: {list(post.keys())}")
            try:
                response = requests.post(
                    self.llm_endpoint,
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.llm_api_key}'},
                    json={'model': self.llm_model, 'messages': [{'role': 'user', 'content': prompt}]}
                )
                response.raise_for_status()
                print(f"[LLM API Response] Status: {response.status_code}")
                print(f"[LLM API Response] Raw: {response.text[:500]}...")  # 只显示前500字符
                
                import json as _json
                api_response = response.json()
                print(f"[LLM API Response] JSON: {api_response}")
                
                llm_content = api_response['choices'][0]['message']['content']
                print(f"[LLM Content] {llm_content}")
                
                # 尝试解析LLM返回的JSON，处理markdown代码块格式
                content_to_parse = llm_content.strip()
                
                # 如果内容被markdown代码块包围，提取其中的JSON
                if content_to_parse.startswith('```json') and content_to_parse.endswith('```'):
                    # 移除开头的```json和结尾的```
                    content_to_parse = content_to_parse[7:-3].strip()
                elif content_to_parse.startswith('```') and content_to_parse.endswith('```'):
                    # 移除开头和结尾的```
                    content_to_parse = content_to_parse[3:-3].strip()
                
                print(f"[LLM JSON to parse] {content_to_parse}")
                
                result = _json.loads(content_to_parse.replace("'", '"'))
                E_suggested = float(result.get('emotion_suggested', self.current_emotion))
                S_suggested = float(result.get('stance_suggested', self.current_stance))
                print(f"[LLM] Agent {self.agent_id} LLM分析完成，建议情绪: {E_suggested}, 建议立场: {S_suggested}")
            except Exception as e:
                print(f"[LLM] API调用失败: {e}，使用默认值。Agent: {self.agent_id}")
                print(f"[LLM Debug] Exception type: {type(e).__name__}")
                E_suggested = self.current_emotion
                S_suggested = self.current_stance

        # 2. 融合更新
        alpha = self.emotion_sensitivity
        I_strength = float(post.get('information_strength', 1.0))  # 信息强度，0.0~1.0
        E_current = self.current_emotion
        lr = alpha * I_strength
        old_emotion = self.current_emotion
        self.current_emotion = E_current * (1 - lr) + E_suggested * lr
        
        print(f"[Emotion Debug] Agent {self.agent_id}: 情绪融合更新")
        print(f"[Emotion Debug] Agent {self.agent_id}: alpha={alpha}, I_strength={I_strength}, lr={lr:.3f}")
        print(f"[Emotion Debug] Agent {self.agent_id}: E_suggested={E_suggested}, E_current={E_current}")
        print(f"[Emotion Debug] Agent {self.agent_id}: 情绪更新: {old_emotion:.3f} -> {self.current_emotion:.3f}")
        
        return E_suggested, S_suggested

    def _update_stance(self, post, llm_stance_suggested=None):
        """
        立场更新算法：分为坚定型和不坚定型Agent
        """
        def clamp(val, minv, maxv):
            return max(minv, min(maxv, val))
        
        # 使用LLM建议的立场，如果没有则使用帖子的stance_score
        stance_score = llm_stance_suggested if llm_stance_suggested is not None else post.get('stance_score')
        information_strength = post.get('information_strength')
        
        print(f"[Stance Update] Agent {self.agent_id}: LLM建议立场={llm_stance_suggested}, 帖子立场={post.get('stance_score')}, 使用立场={stance_score}")
        print(f"[Stance Debug] Agent {self.agent_id}: information_strength={information_strength}, attitude_firmness={self.attitude_firmness}")
        
        if stance_score is None or information_strength is None:
            print(f"[Stance Debug] Agent {self.agent_id}: 跳过立场更新 - stance_score={stance_score}, information_strength={information_strength}")
            return
        
        # 判断类型
        is_firm = self.attitude_firmness >= 0.5
        print(f"[Stance Debug] Agent {self.agent_id}: 类型={'坚定型' if is_firm else '不坚定型'}, 当前立场={self.current_stance}, 当前置信度={self.current_confidence}")
        
        # 阈值常量
        THRESHOLD_PROCESS = 0.3
        THRESHOLD_CHANGE = 0.5
        DELTA_CONF_SMALL = 0.05
        DELTA_CONF_LARGE = 0.2
        
        if is_firm:
            # 坚定型Agent
            print(f"[Stance Debug] Agent {self.agent_id}: 坚定型Agent处理开始")
            if information_strength < THRESHOLD_PROCESS:
                # 信息强度太低，置信度随机扰动
                disturbance = random.uniform(-0.02, 0.02)
                old_conf = self.current_confidence
                self.current_confidence = clamp(self.current_confidence + disturbance, 0.0, 1.0)
                print(f"[Stance Debug] Agent {self.agent_id}: 信息强度太低({information_strength}<{THRESHOLD_PROCESS})，置信度扰动: {old_conf:.3f} -> {self.current_confidence:.3f}")
                return
            
            # 判断立场方向是否一致
            stance_match = (self.current_stance * stance_score >= 0)
            print(f"[Stance Debug] Agent {self.agent_id}: 立场匹配检查: current={self.current_stance}, target={stance_score}, match={stance_match}")
            if stance_match:
                # 立场一致，置信度小幅提升
                old_conf = self.current_confidence
                self.current_confidence = clamp(self.current_confidence + DELTA_CONF_SMALL, 0.0, 1.0)
                print(f"[Stance Debug] Agent {self.agent_id}: 立场一致，置信度提升: {old_conf:.3f} -> {self.current_confidence:.3f}")
            else:
                if information_strength >= THRESHOLD_CHANGE:
                    # 强度足够，立场反转，置信度大幅下降
                    old_stance = self.current_stance
                    old_conf = self.current_confidence
                    self.current_stance = stance_score
                    self.current_confidence = clamp(self.current_confidence - DELTA_CONF_LARGE, 0.0, 1.0)
                    print(f"[Stance Debug] Agent {self.agent_id}: 立场反转! 立场: {old_stance:.3f} -> {self.current_stance:.3f}, 置信度: {old_conf:.3f} -> {self.current_confidence:.3f}")
                else:
                    # 强度不足，置信度小幅下降
                    old_conf = self.current_confidence
                    self.current_confidence = clamp(self.current_confidence - DELTA_CONF_SMALL, 0.0, 1.0)
                    print(f"[Stance Debug] Agent {self.agent_id}: 立场不一致但强度不足，置信度下降: {old_conf:.3f} -> {self.current_confidence:.3f}")
        else:
            # 不坚定型Agent
            print(f"[Stance Debug] Agent {self.agent_id}: 不坚定型Agent处理开始")
            if information_strength < THRESHOLD_PROCESS:
                # 信息强度太低，立场随机扰动
                disturbance = random.uniform(-0.05, 0.05)
                old_stance = self.current_stance
                self.current_stance = clamp(self.current_stance + disturbance, -1.0, 1.0)
                print(f"[Stance Debug] Agent {self.agent_id}: 信息强度太低({information_strength}<{THRESHOLD_PROCESS})，立场扰动: {old_stance:.3f} -> {self.current_stance:.3f}")
                return
            
            # 立场更新
            lr = information_strength * 0.3  # 学习率
            old_stance = self.current_stance
            self.current_stance = clamp(self.current_stance * (1 - lr) + stance_score * lr, -1.0, 1.0)
            print(f"[Stance Debug] Agent {self.agent_id}: 立场融合更新: lr={lr:.3f}, {old_stance:.3f} -> {self.current_stance:.3f}")
            
            # 置信度更新
            stance_diff = abs(self.current_stance - stance_score)
            old_conf = self.current_confidence
            if stance_diff < 0.2:
                self.current_confidence = clamp(self.current_confidence + DELTA_CONF_SMALL, 0.0, 1.0)
                print(f"[Stance Debug] Agent {self.agent_id}: 立场差异小({stance_diff:.3f}<0.2)，置信度提升: {old_conf:.3f} -> {self.current_confidence:.3f}")
            else:
                self.current_confidence = clamp(self.current_confidence - DELTA_CONF_SMALL, 0.0, 1.0)
                print(f"[Stance Debug] Agent {self.agent_id}: 立场差异大({stance_diff:.3f}>=0.2)，置信度下降: {old_conf:.3f} -> {self.current_confidence:.3f}")

    def check_blocking(self, post):
        """检查是否需要屏蔽用户"""
        if self.opinion_blocking > 0.0:
            stance_diff = abs(self.current_stance - post.get('stance_score', 0.0))
            if stance_diff > 0.7:
                user_id = post.get('user_id', post.get('author_id'))
                if user_id and user_id not in self.blocked_user_ids:
                    self.blocked_user_ids.append(user_id)

    def generate_text(self, skip_llm=False, agent_controller=None):
        """调用LLM生成文本"""
        if skip_llm or not self.llm_api_key or not self.llm_endpoint:
            if skip_llm:
                print(f"[LLM] 跳过LLM文本生成，返回模板文本。Agent: {self.agent_id}")
            else:
                print(f"[LLM] 未设置API KEY或endpoint，跳过LLM调用，返回空字符串。Agent: {self.agent_id}")
            
            # 返回模板文本而不是空字符串
            if skip_llm:
                return f"[模拟发帖] {self.agent_id}表达{'正面' if self.current_emotion > 0 else '负面'}情绪，{'支持' if self.current_stance > 0 else '反对' if self.current_stance < 0 else '中性'}立场 (情绪:{self.current_emotion:.2f}, 立场:{self.current_stance:.2f})..."
            else:
                return ""
        
        print(f"[LLM] 调用 LLM 生成文本，Agent: {self.agent_id}, 情绪: {self.current_emotion}, 立场: {self.current_stance}")
        
        # 根据Agent类型选择不同的prompt
        if self.role_type.value == "opinion_leader":
            # 意见领袖使用专门的prompt模板
            if agent_controller and hasattr(agent_controller, 'last_env_summary'):
                from .opinion_leader_prompts import build_opinion_leader_post_prompt
                prompt = build_opinion_leader_post_prompt(self, agent_controller.last_env_summary)
            else:
                # 如果没有环境摘要，使用简化版本
                prompt = f"""你是一位在中国社交媒体上极具影响力的意见领袖。请基于你的当前状态撰写一篇社交媒体帖子。
当前状态：
- 立场：{self.current_stance:.2f}
- 情绪：{self.current_emotion:.2f}
- 置信度：{self.current_confidence:.2f}
请生成一段符合意见领袖身份的帖子内容。"""
        else:
            # 普通Agent使用agent_prompt_template.txt模板
            try:
                with open('data/agent_prompt_template.txt', 'r', encoding='utf-8') as f:
                    template = f.read()
                
                if agent_controller:
                    # 使用agent_controller的build_agent_prompt方法
                    prompt = agent_controller.build_agent_prompt(self, template)
                else:
                    # 简化版本
                    prompt = f"""你是一名普通社交媒体用户，请基于你的当前状态生成帖子内容。
当前状态：
- 角色类型：{self.role_type.value}
- 态度坚定性：{self.attitude_firmness}
- 观点屏蔽度：{self.opinion_blocking}
- 活跃度：{self.activity_level}
- 情绪：{self.current_emotion}
- 立场：{self.current_stance}
请生成一段符合以上特征的社交媒体帖子内容。"""
            except FileNotFoundError:
                print(f"[Warning] 找不到agent_prompt_template.txt，使用简化prompt")
                prompt = f"""作为社交媒体智能体，你的特征：
        - 角色类型：{self.role_type.value}
        - 态度坚定性：{self.attitude_firmness}
        - 观点屏蔽度：{self.opinion_blocking}
        - 活跃度：{self.activity_level}
        当前状态：
        - 情绪：{self.current_emotion}
        - 立场：{self.current_stance}
        请生成一段符合以上特征的社交媒体帖子内容。"""
        
        print(f"[LLM 发帖Prompt] Agent {self.agent_id}: 完整Prompt开始 ================")
        print(prompt)
        print(f"[LLM 发帖Prompt] Agent {self.agent_id}: 完整Prompt结束 ================")
        print(f"[LLM Debug] Prompt长度: {len(prompt)} 字符")
        
        # Debug: 检查模板是否被正确替换
        if "（请用实际内容替换）" in prompt:
            print(f"[LLM Warning] Agent {self.agent_id}: 模板未被正确替换，仍包含占位符")
        if "agent_id: 你的唯一标识符" in prompt:
            print(f"[LLM Warning] Agent {self.agent_id}: 属性模板未被正确替换")
        
        # Debug: 检查是否包含实际的agent信息
        if self.agent_id in prompt:
            print(f"[LLM Info] Agent {self.agent_id}: 模板包含agent_id信息")
        if f"current_emotion: {self.current_emotion:.3f}" in prompt:
            print(f"[LLM Info] Agent {self.agent_id}: 模板包含当前情绪信息")

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

    def apply_environmental_nudge(self, env_summary, kc=0.1, ke=0.05):
        """
        根据环境摘要微调意见领袖的置信度和情绪。
        公式：
        C' = C * (1 - kc * abs(S_agent - S_macro)/2)
        E' = E * (1 - ke) + E_macro * ke
        """
        if not env_summary:
            return
        S_macro = env_summary.get('average_stance_score', 0.0)
        E_macro = env_summary.get('average_emotion_score', 0.0)
        S_agent = getattr(self, 'current_stance', 0.0)
        C_agent = getattr(self, 'current_confidence', 0.5)
        E_agent = getattr(self, 'current_emotion', 0.0)
        # 立场置信度微调
        stance_diff = abs(S_agent - S_macro)
        self.current_confidence = C_agent * (1 - kc * stance_diff / 2)
        # 情绪感染微调
        self.current_emotion = E_agent * (1 - ke) + E_macro * ke

    def reset_viewed_posts(self):
        """清空本时间片已读帖子记录"""
        self.viewed_posts = []

    def reset_emotion_stance_history(self):
        """清空本时间片情绪立场变化历史"""
        self.emotion_stance_history = []

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