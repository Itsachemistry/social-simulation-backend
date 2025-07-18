# opinion_leader_prompts.py
"""
存储意见领袖专用的LLM prompt模板，字段名与环境摘要统计输出完全对齐，语义参考promptdataprocess.txt。
"""

OPINION_LEADER_POST_PROMPT_TEMPLATE = """
# 角色与目标 (Role & Goal)
你是一位在中国社交媒体上极具影响力的意见领袖，你的发言风格{agent_style}。你的核心任务是根据你自身的观点和一份舆情简报，撰写一篇具有高度策略性的帖子，以引导舆论走向。

# 你的当前状态 (Your Current State)
- 我的立场: {agent_stance_desc}
- 我的情绪: {agent_emotion_desc}

# 舆情简报 (Strategic Intelligence Briefing)
这是你收到的关于当前时间片内舆论场的最新报告：
- 帖子总数: {total_posts_in_slice}
- 立场分布:
  - 支持医院: {support_hospital_pct}%
  - 支持患者: {support_patient_pct}%
  - 中立/调解: {neutral_mediating_pct}%
- 整体情绪:
  - 积极情绪占比: {positive_pct}%
  - 消极情绪占比: {negative_pct}%
- 核心洞察: 当前舆论场整体对事件持{stance_summary} (平均立场分: {average_stance_score})，且民众情绪普遍{emotion_summary} (平均情绪分: {average_emotion_score})。

# 你的任务 (Your Task)
基于你的状态和上述舆情简报，撰写一篇不超过150字的中文社交媒体帖子。请展现出你的策略性：
- 如果舆论对你有利，思考如何巩固优势，并进一步扩大你的影响力。
- 如果舆论对你不利，思考是应该直接反驳，还是安抚情绪，或是从一个新的角度切入来转移焦点。
- 你的发言应该符合你的身份和一贯风格。

# 输出 (Output)
请只输出最终生成的帖子内容，不要包含任何其他解释。
"""

def build_opinion_leader_post_prompt(agent, env_summary, agent_style='理性'):
    """
    构建意见领袖发帖prompt，所有变量名与环境摘要统计输出字段完全一致。
    agent_style: 可选，风格描述字符串。
    """
    stance_dist = env_summary.get('stance_distribution', {})
    emotion_dist = env_summary.get('emotion_distribution', {})
    def pct(val):
        return round(val * 100, 1)
    # 立场/情绪中文描述可根据实际需要自定义
    agent_stance_desc = f"当前立场分值为{getattr(agent, 'current_stance', 0):.2f}"
    agent_emotion_desc = f"当前情绪分值为{getattr(agent, 'current_emotion', 0):.2f}"
    # 核心洞察描述
    avg_stance = env_summary.get('average_stance_score', 0)
    avg_emotion = env_summary.get('average_emotion_score', 0)
    stance_summary = '正面' if avg_stance > 0.1 else ('负面' if avg_stance < -0.1 else '中性')
    emotion_summary = '高涨' if avg_emotion > 0.1 else ('低落' if avg_emotion < -0.1 else '平稳')
    return OPINION_LEADER_POST_PROMPT_TEMPLATE.format(
        agent_style=agent_style,
        agent_stance_desc=agent_stance_desc,
        agent_emotion_desc=agent_emotion_desc,
        total_posts_in_slice=env_summary.get('total_posts_in_slice', 0),
        support_hospital_pct=pct(stance_dist.get('SUPPORT_HOSPITAL', 0)),
        support_patient_pct=pct(stance_dist.get('SUPPORT_PATIENT', 0)),
        neutral_mediating_pct=pct(stance_dist.get('NEUTRAL_MEDIATING', 0)),
        positive_pct=pct(emotion_dist.get('positive', 0)),
        negative_pct=pct(emotion_dist.get('negative', 0)),
        stance_summary=stance_summary,
        average_stance_score=round(avg_stance, 3),
        emotion_summary=emotion_summary,
        average_emotion_score=round(avg_emotion, 3)
    ) 