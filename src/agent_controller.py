from .agent import Agent, RoleType
from .world_state import WorldState
from .time_manager import TimeSliceManager
import json
import random
import math
from typing import Optional
from src.services import generate_context, make_prompt
from datetime import datetime, timedelta

class AgentController:
    def __init__(self, world_state: WorldState, time_manager: Optional[TimeSliceManager], w_pop=0.7, k=2, agent_posts_file=None):
        self.world_state = world_state
        self.time_manager = time_manager
        self.agents = []
        self.w_pop = w_pop
        self.k = k
        self.agent_posts_file = agent_posts_file  # 用于存储Agent生成帖子的JSON文件路径
        self.current_time_slice = 0  # 用于飓风消息处理

    def configure_llm_for_agents(self, llm_config):
        """为所有Agent配置LLM设置"""
        if not llm_config:
            return
            
        api_key = llm_config.get("api_key")
        # 支持两种字段名：base_url（前端发送）和 endpoint（传统字段）
        base_url = llm_config.get("base_url") or llm_config.get("endpoint")
        model = llm_config.get("model", "deepseek-v3-250324")
        
        print(f"[LLM Config] 为 {len(self.agents)} 个Agent配置LLM: {model}")
        print(f"[LLM Config] API Key: {'已设置' if api_key else '未设置'}")
        print(f"[LLM Config] Endpoint: {base_url}")
        
        for agent in self.agents:
            agent.llm_api_key = api_key
            agent.llm_endpoint = base_url
            agent.llm_model = model
            print(f"  - Agent {agent.agent_id}: LLM已配置 (key={bool(api_key)}, endpoint={bool(base_url)})")

    def process_hurricane_messages(self, posts, agent):
        """
        处理官方声明和紧急广播消息
        官方声明会绕过正常的个性化筛选，强制被所有Agent阅读
        
        Args:
            posts: 当前时间片的所有帖子
            agent: 当前处理的Agent
        
        Returns:
            list: 官方消息列表
        """
        official_posts = [
            post for post in posts 
            if post.get('is_official_statement', False) or
               post.get('is_hurricane', False) or 
               post.get('force_read', False) or
               (post.get('is_event', False) and post.get('priority', 0) >= 999)
        ]
        
        if official_posts:
            print(f"🏛️ [官方消息] Agent {agent.agent_id} 收到 {len(official_posts)} 条官方消息")
            
            for official_post in official_posts:
                # 确定消息类型和处理方式
                if official_post.get('is_official_statement', False):
                    statement_type = official_post.get('statement_type', 'clarification')
                    authority_level = official_post.get('authority_level', 'high')
                    print(f"📢 官方声明({statement_type}|{authority_level}): {official_post.get('content', '')[:50]}...")
                else:
                    print(f"� 紧急广播: {official_post.get('content', '')[:50]}...")
                
                # 强制阅读，不受屏蔽影响
                if not hasattr(agent, 'viewed_posts'):
                    agent.viewed_posts = []
                agent.viewed_posts.append(official_post)
                
                # 官方声明的影响更稳定和可控
                if official_post.get('is_official_statement', False):
                    # 官方声明具有更高的可信度，影响更温和但持久
                    emotion_impact = official_post.get('emotion_score', 0.1) * 0.8  # 降低情绪波动
                    stance_impact = official_post.get('stance_score', 0.0) * 1.2   # 增强立场影响
                    
                    # 根据权威级别调整影响力
                    authority_multiplier = {
                        "high": 1.0,
                        "medium": 0.7, 
                        "low": 0.4
                    }.get(official_post.get('authority_level', 'high'), 1.0)
                    
                    emotion_impact *= authority_multiplier
                    stance_impact *= authority_multiplier
                    
                    # 应用影响
                    agent.current_emotion += emotion_impact
                    agent.current_stance += stance_impact
                    
                    # 限制范围
                    agent.current_emotion = max(-1.0, min(1.0, agent.current_emotion))
                    agent.current_stance = max(-1.0, min(1.0, agent.current_stance))
                    
                    print(f"   └─ Agent {agent.agent_id} 状态更新: 情绪{emotion_impact:+.3f}→{agent.current_emotion:.3f}, 立场{stance_impact:+.3f}→{agent.current_stance:.3f}")
                else:
                    # 传统的强制情绪立场更新
                    agent.update_emotion_and_stance(
                        official_post, 
                        time_slice_index=self.current_time_slice
                    )
                
                # 官方消息通常不触发屏蔽（来源可信）
                if not official_post.get('author_id', '').startswith('official'):
                    agent.check_blocking(official_post)
        
        return official_posts

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
            # 移除硬性屏蔽过滤，改为在阅读时进行单次屏蔽处理
            # if "author_id" in post and post["author_id"] in getattr(agent, "blocked_user_ids", []):
            #     continue
            
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
            post_ids.append(post.get('mid', post.get('id', post.get('post_id', 'unknown'))))

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
    def update_agent_emotions(self, posts, time_slice_index=None, llm_config=None):
        """为每个Agent生成个性化Feed并逐条阅读，调用Agent自身的情绪更新算法，并统计分数
        支持飓风消息（强制广播）功能
        
        Args:
            posts: 帖子列表
            time_slice_index: 时间片索引
            llm_config: LLM配置 {"enabled_agents": ["agent1"], "enabled_timeslices": [0]}
        """
        # 保存当前时间片索引
        self.current_time_slice = time_slice_index or 0
        
        # 分离飓风消息和普通消息
        hurricane_posts = [
            post for post in posts 
            if post.get('is_hurricane', False) or 
               post.get('force_read', False) or
               (post.get('is_event', False) and post.get('priority', 0) >= 999)
        ]
        
        normal_posts = [
            post for post in posts 
            if not (post.get('is_hurricane', False) or 
                    post.get('force_read', False) or
                    (post.get('is_event', False) and post.get('priority', 0) >= 999))
        ]
        
        if hurricane_posts:
            print(f"🌪️ [时间片 {time_slice_index}] 检测到 {len(hurricane_posts)} 条飓风消息")
            print(f"📊 普通帖子: {len(normal_posts)} 条")
        
        all_agent_scores = {}
        posting_agents = []  # 记录本时间片发帖的Agent
        llm_config = llm_config or {}
        enabled_agents = llm_config.get("enabled_agents", [])
        enabled_timeslices = llm_config.get("enabled_timeslices", [])
        
        # 判断当前时间片是否启用LLM
        llm_enabled_for_timeslice = time_slice_index in enabled_timeslices
        
        for agent in self.agents:
            # 每个时间片开始时记录状态快照（用于发帖判定）
            agent.snapshot_state()
            
            # 清空已读帖子和情绪立场历史
            agent.reset_viewed_posts()
            agent.reset_emotion_stance_history()
            
            # 判断当前Agent是否启用LLM
            agent_llm_enabled = agent.agent_id in enabled_agents and llm_enabled_for_timeslice
            
            if agent_llm_enabled:
                print(f"🤖 Agent {agent.agent_id} 在时间片 {time_slice_index} 使用LLM")
            
            # 1. 首先强制处理飓风消息
            if hurricane_posts:
                self.process_hurricane_messages(hurricane_posts, agent)
            
            # 2. 然后正常处理普通帖子
            personalized_feed, post_scores = self._generate_personalized_feed(agent, normal_posts)
            all_agent_scores[agent.agent_id] = post_scores
            
            # 注意：不要重新初始化viewed_posts，保留飓风消息记录
            # 如果viewed_posts不存在，才初始化
            if not hasattr(agent, 'viewed_posts'):
                agent.viewed_posts = []
            
            for idx, post in enumerate(personalized_feed):
                # 检查是否需要执行单次屏蔽跳过
                post_author = post.get('author_id') or post.get('user_id')
                if post_author and post_author in agent.blocked_user_ids:
                    # 单次屏蔽：跳过此帖子并从屏蔽列表中移除该用户
                    agent.blocked_user_ids.remove(post_author)
                    print(f"[单次屏蔽] Agent {agent.agent_id} 跳过已屏蔽用户 {post_author} 的帖子，并将其从屏蔽列表移除")
                    continue  # 跳过这个帖子，不做任何处理
                
                # 正常处理帖子
                agent.viewed_posts.append(post)  # 只有实际处理的帖子才计入viewed_posts
                
                # 根据配置决定是否跳过LLM
                skip_llm = not agent_llm_enabled
                # 只在第一个帖子时显示prompt示例，避免输出过长
                show_prompt_example = (idx == 0)
                # 传递帖子列表用于提取链条上下文
                agent.update_emotion_and_stance(
                    post, 
                    time_slice_index=time_slice_index,
                    all_posts=posts
                )
                
                # 处理完帖子后检查是否需要新增屏蔽
                agent.check_blocking(post)
                
                print(f"Agent {agent.agent_id} 阅读帖子 {post.get('mid', post.get('id', post.get('post_id', 'unknown')))}: "
                      f"情绪 {agent.current_emotion:.3f}, 立场 {agent.current_stance:.3f}, "
                      f"置信度 {agent.current_confidence:.3f} {'[LLM]' if agent_llm_enabled else '[非LLM]'}")
            
            # 发帖判定
            # =============================================================================
            # 🚨 临时作弊逻辑：强制所有Agent发帖（测试用）
            # TODO: 测试完成后删除此作弊逻辑，恢复正常的 agent.should_post() 判定
            # =============================================================================
            FORCE_ALL_AGENTS_POST = True  # 🚨 作弊开关：设为False恢复正常判定
            
            # 原始判定逻辑（保留但暂时注释）
            # original_should_post = agent.should_post()
            
            # 使用作弊逻辑或原始逻辑
            should_post_decision = FORCE_ALL_AGENTS_POST  # or original_should_post
            
            if should_post_decision:
                posting_agents.append(agent.agent_id)
                
                # 显示是否为强制发帖
                if FORCE_ALL_AGENTS_POST:
                    print(f"🚨 Agent {agent.agent_id} 强制发帖（作弊模式）！")
                else:
                    print(f"✍️ Agent {agent.agent_id} 决定发帖！")
                    
                print(f"   情绪波动: {abs(agent.current_emotion - agent.last_emotion):.3f}")
                print(f"   立场波动: {abs(agent.current_stance - agent.last_stance):.3f}")
                print(f"   活跃度: {agent.activity_level:.3f}")
                
                # 生成发帖内容（根据配置决定是否使用LLM）
                skip_llm_for_posting = not agent_llm_enabled
                post_content = agent.generate_text(skip_llm=skip_llm_for_posting, agent_controller=self)
                print(f"   发帖内容: {post_content[:100]}...")
                
                # === 新增：分析影响最大的帖子 ===
                self._analyze_most_influential_post(agent)
                
                # === 新增：构建帖子JSON并添加到世界状态 ===
                try:
                    # 构建帖子JSON对象（启用LLM标注）
                    post_json = self.build_post_json(
                        agent, 
                        post_content, 
                        posts, 
                        use_llm_annotation=agent_llm_enabled
                    )
                    
                    # 添加到世界状态，供下一轮阅读
                    if self.world_state:
                        self.world_state.add_post(post_json)
                        print(f"   ✅ 新帖子已添加到帖子池: ID={post_json.get('id', 'unknown')}")
                    
                    # 同时保存到Agent生成帖子的JSON文件
                    self._save_agent_post_to_file(post_json, agent)
                    
                except Exception as e:
                    print(f"   ❌ 发帖流程失败: {e}")
                
            else:
                delta_emotion = abs(agent.current_emotion - agent.last_emotion)
                delta_stance = abs(agent.current_stance - agent.last_stance)
                fluctuation = delta_emotion + delta_stance
                print(f"Agent {agent.agent_id} 不发帖 (波动量: {fluctuation:.3f}, 阈值: {agent.expression_threshold:.3f})")
        
        # 输出本时间片发帖统计
        if posting_agents:
            print(f"\n📊 本时间片发帖统计: {len(posting_agents)} 个Agent发帖")
            print(f"发帖Agent: {', '.join(posting_agents)}")
        else:
            print(f"\n📊 本时间片发帖统计: 无Agent发帖")
            
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

    def compute_macro_summary(self):
        """
        统计当前所有agent的平均情绪、平均立场、agent数量等。
        """
        emotion_sum = 0
        stance_sum = 0
        count = 0
        for agent in self.agents:
            status = agent.get_status()
            emotion_sum += status['current_emotion']
            stance_sum += status['current_stance']
            count += 1
        return {
            'average_emotion': emotion_sum / count if count else 0,
            'average_stance': stance_sum / count if count else 0,
            'agent_count': count
        }

    def leader_read_briefing(self, time_slice_index):
        """
        生成宏观简报并让所有leader agent用轻推算法读取。
        返回简报内容和每个leader的状态。
        """
        macro = self.compute_macro_summary()
        briefing_post = {
            'id': f'briefing_{time_slice_index}',
            'content': f"简报：本时间片全体平均情绪={macro['average_emotion']:.2f}，平均立场={macro['average_stance']:.2f}",
            'emotion_score': macro['average_emotion'],
            'stance_score': macro['average_stance'],
            'information_strength': 1.0
        }
        results = []
        for agent in self.get_opinion_leaders():
            if hasattr(agent, 'apply_environmental_nudge'):
                agent.apply_environmental_nudge({
                    'average_stance_score': macro['average_stance'],
                    'average_emotion_score': macro['average_emotion']
                })
            else:
                agent.update_emotion_and_stance(briefing_post, time_slice_index=time_slice_index)
            results.append((agent.agent_id, agent.get_status()))
        return briefing_post, results

    def build_agent_prompt(self, agent, prompt_template):
        """
        根据agent的已读帖子和prompt模板，自动组装发言prompt。
        专门为agent发言设计，不是分析帖子的prompt。
        """
        print(f"[Debug] build_agent_prompt 被调用，Agent: {agent.agent_id}")
        posts_read = getattr(agent, 'viewed_posts', [])
        print(f"[Debug] Agent {agent.agent_id} 本时间片读到 {len(posts_read)} 个帖子")
        
        # 构造已读帖子列表
        posts_content = []
        for i, post in enumerate(posts_read):
            post_content = post.get('content', post.get('text', ''))
            posts_content.append(f"- [帖子{i+1}] {post_content}")
        posts_text = '\n'.join(posts_content) if posts_content else "（本时间片未读到任何帖子）"
        
        # 构造agent属性信息
        agent_attributes = f"""- agent_id: {agent.agent_id}
- role_type: {agent.role_type.value}
- attitude_firmness: {agent.attitude_firmness:.3f} (态度坚定性，越高越不容易改变立场)
- opinion_blocking: {agent.opinion_blocking:.3f} (观点屏蔽度，越高越容易屏蔽不同观点)
- activity_level: {agent.activity_level:.3f} (活跃度，影响发帖频率)
- current_emotion: {agent.current_emotion:.3f} (范围[-1,1]，-1为极度负面，1为极度正面)
- current_stance: {agent.current_stance:.3f} (范围[-1,1]，-1为极度支持患者，1为极度支持医院，0为中立)
- current_confidence: {agent.current_confidence:.3f} (范围[0,1]，0为完全不确定，1为完全确定)"""
        
        print(f"[Debug] Agent属性信息长度: {len(agent_attributes)} 字符")
        
        # 替换模板中的占位符
        prompt = prompt_template
        original_prompt_length = len(prompt)
        print(f"[Debug] 原始模板长度: {original_prompt_length} 字符")
        
        # 替换帖子部分 - 查找更精确的文本
        posts_placeholder = "- [帖子1] 内容……\n- [帖子2] 内容……\n- [帖子3] 内容……\n（请用实际内容替换）"
        if posts_placeholder in prompt:
            prompt = prompt.replace(posts_placeholder, posts_text)
            print(f"[Debug] 成功替换帖子占位符")
        else:
            print(f"[Debug] 未找到帖子占位符，使用备用方案")
            # 备用方案：查找section并替换内容
            posts_section_start = "## 2. 当前时间片内你读到的所有帖子 (Posts Read in Current Timestep)"
            posts_section_end = "## 3. 你的属性与当前状态"
            
            start_idx = prompt.find(posts_section_start)
            end_idx = prompt.find(posts_section_end)
            print(f"[Debug] Posts section 位置: {start_idx} 到 {end_idx}")
            
            if start_idx != -1 and end_idx != -1:
                # 找到section边界，替换内容
                before_section = prompt[:start_idx]
                after_section = prompt[end_idx:]
                new_posts_section = f"{posts_section_start}\n{posts_text}\n\n"
                prompt = before_section + new_posts_section + after_section
                print(f"[Debug] 使用备用方案替换帖子section")
        
        # 替换属性部分 - 查找更精确的文本  
        attributes_placeholder = """- agent_id: 你的唯一标识符
- opinion_tendency: 你的立场倾向，范围[-1,1]，-1为极度支持患者，1为极度支持医院，0为中立
- emotion_state: 当前情绪状态，范围[-1,1]，-1为极度负面，1为极度正面
- information_preference: 信息偏好，范围[0,1]，0为偏好情绪化内容，1为偏好事实/数据
- influence_level: 影响力等级，范围[0,1]，0为普通用户，1为极具影响力
- memory: 你对事件的记忆片段或印象（如有）
（请用实际参数和含义替换/补充）"""
        
        if attributes_placeholder in prompt:
            prompt = prompt.replace(attributes_placeholder, agent_attributes)
            print(f"[Debug] 成功替换属性占位符")
        else:
            print(f"[Debug] 未找到属性占位符，使用备用方案")
            # 备用方案：查找section并替换内容
            attributes_section_start = "## 3. 你的属性与当前状态 (Your Attributes and State)"
            attributes_section_end = "## 4. 你的任务"
            
            start_idx = prompt.find(attributes_section_start)
            end_idx = prompt.find(attributes_section_end)
            print(f"[Debug] Attributes section 位置: {start_idx} 到 {end_idx}")
            
            if start_idx != -1 and end_idx != -1:
                # 找到section边界，替换内容
                before_section = prompt[:start_idx]
                after_section = prompt[end_idx:]
                new_attributes_section = f"{attributes_section_start}\n{agent_attributes}\n\n"
                prompt = before_section + new_attributes_section + after_section
                print(f"[Debug] 使用备用方案替换属性section")
        
        final_prompt_length = len(prompt)
        print(f"[Debug] 最终prompt长度: {final_prompt_length} 字符 (变化: {final_prompt_length - original_prompt_length})")
        
        return prompt

    def _save_agent_post_to_file(self, post_json, agent):
        """将Agent生成的帖子保存到JSON文件中"""
        if not self.agent_posts_file:
            return
            
        try:
            # 读取现有数据
            with open(self.agent_posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 添加时间戳和Agent信息到帖子
            enhanced_post = post_json.copy()
            enhanced_post['generation_info'] = {
                'agent_id': agent.agent_id,
                'agent_role': agent.role_type.value,
                'agent_emotion': agent.current_emotion,
                'agent_stance': agent.current_stance,
                'agent_confidence': agent.current_confidence,
                'generation_time': datetime.now().isoformat(),
                'timestep': getattr(self.time_manager, 'current_timestep', 'unknown') if self.time_manager else 'unknown'
            }
            
            # 添加到帖子列表
            data['agent_posts'].append(enhanced_post)
            
            # 写回文件
            with open(self.agent_posts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"   📝 帖子已保存到JSON文件: {self.agent_posts_file}")
            
        except Exception as e:
            print(f"   ⚠️ 保存帖子到JSON文件失败: {e}")

    def build_post_json(self, agent, content, all_posts_in_slice, use_llm_annotation=True):
        """
        根据agent的影响最大帖子、当前时间片帖子，自动拼接发帖json对象。
        时间戳使用全数字格式，pid为影响最大的帖子的mid。
        
        Args:
            agent: 发帖的Agent
            content: 帖子内容
            all_posts_in_slice: 当前时间片所有帖子
            use_llm_annotation: 是否使用LLM进行帖子标注（与原始帖子保持一致）
        """
        # 获取影响最大的帖子ID
        record = getattr(agent, 'most_influential_post_record', None)
        parent_mid = record['post_id'] if record else None
        
        # 生成时间戳（全数字格式）
        latest_ts = max([p.get('timestamp') for p in all_posts_in_slice if p.get('timestamp')], default=None)
        if latest_ts:
            from datetime import datetime, timedelta
            try:
                # 先尝试数字时间戳
                ts_val = float(latest_ts)
                # 判断是否为合理的时间戳（10位或13位）
                if ts_val > 1e12:
                    ts_val = ts_val / 1000  # 13位毫秒转秒
                dt = datetime.fromtimestamp(ts_val)
            except Exception:
                # 回退到ISO格式
                dt = datetime.fromisoformat(str(latest_ts))
            new_dt = dt + timedelta(seconds=1)
            new_timestamp = int(new_dt.timestamp())  # 转换为全数字时间戳
        else:
            from datetime import datetime
            new_timestamp = int(datetime.now().timestamp())
        
        # 初始化标注字段（默认值）
        emotion_score = agent.current_emotion
        stance_score = agent.current_stance  
        information_strength = 0.8
        keywords = []
        stance_category = "NEUTRAL_MEDIATING"
        stance_confidence = 0.5
        
        # 如果启用LLM标注，使用promptdataprocess模板进行标注
        if use_llm_annotation and hasattr(agent, 'llm_api_key') and agent.llm_api_key and agent.llm_endpoint:
            try:
                print(f"[标注] 使用LLM对Agent {agent.agent_id}的帖子进行标注...")
                
                # 读取promptdataprocess模板
                with open('data/promptdataprocess.txt', 'r', encoding='utf-8') as f:
                    template = f.read()
                
                # 构建对话上下文（如果有父帖子）
                conversation_context = ""
                if parent_mid and all_posts_in_slice:
                    # 找到父帖子
                    parent_post = None
                    for p in all_posts_in_slice:
                        if str(p.get('id', p.get('mid', ''))) == str(parent_mid):
                            parent_post = p
                            break
                    
                    if parent_post:
                        conversation_context = f"\n[父帖子]: {parent_post.get('content', '')}"
                
                # 构建标注prompt（替换模板中的目标帖子）
                target_post_section = f'[目标帖子]: {content}'
                
                # 如果有对话上下文，构建完整的目标帖子部分
                if conversation_context:
                    target_post_section = f'{conversation_context}\n\n[目标帖子]: {content}'
                
                # 替换模板中的示例目标帖子（两个地方都需要替换）
                annotation_prompt = template.replace(
                    '[目标帖子 (回复 4)]: 走正常途径不如闹来钱多又快',
                    target_post_section
                ).replace(
                    '[目标帖子]: "走正常途径不如闹来钱多又快"',
                    f'[目标帖子]: "{content}"'
                )
                
                print(f"    [标注Prompt完整版] Agent {agent.agent_id} 帖子标注prompt开始 ================")
                print(annotation_prompt)
                print(f"    [标注Prompt完整版] Agent {agent.agent_id} 帖子标注prompt结束 ================")
                print(f"    [标注Debug] 标注Prompt长度: {len(annotation_prompt)} 字符")
                
                # 调用LLM进行标注
                import requests
                response = requests.post(
                    agent.llm_endpoint,
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {agent.llm_api_key}'},
                    json={'model': agent.llm_model, 'messages': [{'role': 'user', 'content': annotation_prompt}]}
                )
                response.raise_for_status()
                
                # 解析LLM返回的标注结果
                import json
                result_text = response.json()['choices'][0]['message']['content'].strip()
                # 尝试提取JSON部分
                if '{' in result_text and '}' in result_text:
                    json_start = result_text.find('{')
                    json_end = result_text.rfind('}') + 1
                    json_str = result_text[json_start:json_end]
                    annotation_result = json.loads(json_str)
                    
                    # 使用LLM标注的结果
                    emotion_score = float(annotation_result.get('emotion_score', emotion_score))
                    stance_score = float(annotation_result.get('stance_score', stance_score))
                    information_strength = float(annotation_result.get('information_strength', information_strength))
                    keywords = annotation_result.get('keywords', keywords)
                    stance_category = annotation_result.get('stance_category', stance_category)
                    stance_confidence = float(annotation_result.get('stance_confidence', stance_confidence))
                    
                    print(f"[标注] LLM标注成功: emotion={emotion_score:.3f}, stance={stance_score:.3f}, info_strength={information_strength:.3f}")
                    print(f"[标注] LLM标注扩展: keywords={keywords}, stance_category={stance_category}, stance_confidence={stance_confidence:.3f}")
                else:
                    print(f"[标注] LLM返回格式无效，使用默认值")
                    
            except Exception as e:
                print(f"[标注] LLM标注失败: {e}，使用Agent状态值")
        else:
            print(f"[标注] 跳过LLM标注，使用Agent状态值")
        
        return {
            'id': f"{agent.agent_id}_{new_timestamp}",
            'mid': f"{agent.agent_id}_{new_timestamp}",  # 新帖子的message id
            'pid': parent_mid,  # 父帖子的message id（影响最大的帖子）
            'author_id': agent.agent_id,
            'content': content,
            't': new_timestamp,  # 时间戳
            # 添加标注字段（经过LLM标注或使用Agent状态）
            'emotion_score': emotion_score,
            'stance_score': stance_score,
            'information_strength': information_strength,
            'keywords': keywords,
            'stance_category': stance_category,
            'stance_confidence': stance_confidence,
            # 其他可能有用的字段
            'user_id': agent.agent_id,  # 兼容性字段
            'timestamp': new_timestamp  # 兼容性字段
        }

    def _analyze_most_influential_post(self, agent):
        """
        分析Agent在当前时间片中受影响最大的帖子，并设置most_influential_post_record
        """
        if not hasattr(agent, 'emotion_stance_history') or not agent.emotion_stance_history:
            print(f"[影响分析] Agent {agent.agent_id}: 无情绪立场变化历史，跳过影响分析")
            return
            
        max_influence_score = 0.0
        most_influential_record = None
        
        print(f"[影响分析] Agent {agent.agent_id}: 分析 {len(agent.emotion_stance_history)} 条历史记录")
        
        for i, record in enumerate(agent.emotion_stance_history):
            # 计算情绪变化幅度
            emotion_change = abs(record['emotion_after'] - record['emotion_before'])
            # 计算立场变化幅度
            stance_change = abs(record['stance_after'] - record['stance_before'])
            # 计算置信度变化幅度
            confidence_change = abs(record['confidence_after'] - record['confidence_before'])
            
            # 计算综合影响分数（可以调整权重）
            influence_score = emotion_change * 0.4 + stance_change * 0.4 + confidence_change * 0.2
            
            print(f"  帖子 {record['post_id']}: 情绪变化={emotion_change:.3f}, 立场变化={stance_change:.3f}, 置信度变化={confidence_change:.3f}, 影响分数={influence_score:.3f}")
            
            if influence_score > max_influence_score:
                max_influence_score = influence_score
                most_influential_record = {
                    'post_id': record['post_id'],
                    'influence_score': influence_score,
                    'emotion_change': emotion_change,
                    'stance_change': stance_change,
                    'confidence_change': confidence_change
                }
        
        if most_influential_record:
            agent.most_influential_post_record = most_influential_record
            print(f"[影响分析] Agent {agent.agent_id}: 影响最大的帖子是 {most_influential_record['post_id']}, 影响分数={most_influential_record['influence_score']:.3f}")
        else:
            print(f"[影响分析] Agent {agent.agent_id}: 未找到有影响的帖子")

    def __str__(self):
        return f"AgentController(agents={len(self.agents)})"


