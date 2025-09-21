import json
import yaml
from typing import Dict, List, Any
from pathlib import Path
import re
from src.agent import Agent, RoleType


class DataLoader:
    """
    数据加载器类，负责从文件中加载帖子数据和Agent配置。
    
    提供健壮的文件读取和解析功能，支持JSON和YAML格式，
    包含完整的错误处理机制。
    """
    
    def load_post_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        读取并解析JSON格式的帖子数据文件。
        
        Args:
            file_path (str): 帖子数据文件的路径
            
        Returns:
            List[Dict[str, Any]]: 解析后的帖子数据列表
            
        Raises:
            FileNotFoundError: 当指定的文件不存在时
            json.JSONDecodeError: 当JSON格式不正确时
            Exception: 其他读取或解析错误
        """
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"帖子数据文件未找到: {file_path}")
            
            # 读取并解析JSON文件
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # 确保返回的是列表格式
            if not isinstance(data, list):
                raise ValueError("帖子数据必须是列表格式")
                
            return data
            
        except FileNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON格式错误: {e}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"读取帖子数据时发生错误: {str(e)}")
    
    def load_agent_config(self, file_path: str) -> Dict[str, Any]:
        """
        读取并解析JSON或YAML格式的Agent配置文件。
        
        根据文件扩展名自动判断格式：
        - .json: JSON格式
        - .yaml/.yml: YAML格式
        
        Args:
            file_path (str): Agent配置文件的路径
            
        Returns:
            Dict[str, Any]: 解析后的Agent配置字典
            
        Raises:
            FileNotFoundError: 当指定的文件不存在时
            json.JSONDecodeError: 当JSON格式不正确时
            yaml.YAMLError: 当YAML格式不正确时
            ValueError: 当文件格式不支持时
            Exception: 其他读取或解析错误
        """
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Agent配置文件未找到: {file_path}")
            
            # 根据文件扩展名判断格式
            file_extension = Path(file_path).suffix.lower()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_extension == '.json':
                    data = json.load(file)
                elif file_extension in ['.yaml', '.yml']:
                    data = yaml.safe_load(file)
                else:
                    raise ValueError(f"不支持的文件格式: {file_extension}。支持格式: .json, .yaml, .yml")
            
            # 确保返回的是字典格式
            if not isinstance(data, dict):
                raise ValueError("Agent配置必须是字典格式")
                
            return data
            
        except FileNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON格式错误: {e}", e.doc, e.pos)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML格式错误: {e}")
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"读取Agent配置时发生错误: {str(e)}") 


def flatten_posts_recursive(posts, parent_id=None, level=0):
    """
    递归展开所有嵌套的帖子，返回扁平化列表
    """
    flattened_posts = []
    for post in posts:
        post = dict(post)  # 避免修改原始数据
        post['parent_post_id'] = parent_id
        post['nesting_level'] = level
        flattened_posts.append(post)
        if 'children' in post and post['children']:
            flattened_posts.extend(flatten_posts_recursive(
                post['children'],
                parent_id=post.get('pid', post.get('mid', post.get('id'))),
                level=level + 1
            ))
    return flattened_posts

def filter_valid_posts(posts):
    """
    过滤有效的帖子（popularity>0且关键字段不为None）
    """
    valid_posts = []
    for post in posts:
        if post.get('popularity', 0) <= 0:
            continue
        if (post.get('emotion_score') is None or
            post.get('stance_score') is None or
            post.get('information_strength') is None):
            continue
        valid_posts.append(post)
    return valid_posts 


def calculate_environmental_summary(posts_in_slice: list) -> dict:
    """
    统计时间片内所有帖子，输出结构化环境摘要，字段和语义严格遵循promptdataprocess.txt定义。
    """
    if not posts_in_slice:
        return {}

    total_posts = len(posts_in_slice)
    stance_category_counts = {}
    emotion_category_counts = {}
    stance_score_sum = 0.0
    emotion_score_sum = 0.0
    stance_confidence_sum = 0.0
    information_strength_sum = 0.0

    valid_stance_score_count = 0
    valid_emotion_score_count = 0
    valid_stance_confidence_count = 0
    valid_information_strength_count = 0

    for post in posts_in_slice:
        # 立场类别统计
        sc = post.get("stance_category")
        if sc:
            stance_category_counts[sc] = stance_category_counts.get(sc, 0) + 1

        # 情绪类别统计
        ec = post.get("emotion_category")
        if ec:
            emotion_category_counts[ec] = emotion_category_counts.get(ec, 0) + 1

        # 均值统计
        ss = post.get("stance_score")
        if ss is not None:
            stance_score_sum += ss
            valid_stance_score_count += 1

        es = post.get("emotion_score")
        if es is not None:
            emotion_score_sum += es
            valid_emotion_score_count += 1

        scf = post.get("stance_confidence")
        if scf is not None:
            stance_confidence_sum += scf
            valid_stance_confidence_count += 1

        isf = post.get("information_strength")
        if isf is not None:
            information_strength_sum += isf
            valid_information_strength_count += 1

    # 归一化分布
    stance_distribution = {k: v / total_posts for k, v in stance_category_counts.items()}
    emotion_distribution = {k: v / total_posts for k, v in emotion_category_counts.items()}

    summary = {
        "total_posts_in_slice": total_posts,
        "stance_distribution": stance_distribution,
        "average_stance_score": stance_score_sum / valid_stance_score_count if valid_stance_score_count else 0.0,
        "average_stance_confidence": stance_confidence_sum / valid_stance_confidence_count if valid_stance_confidence_count else 0.0,
        "emotion_distribution": emotion_distribution,
        "average_emotion_score": emotion_score_sum / valid_emotion_score_count if valid_emotion_score_count else 0.0,
        "average_information_strength": information_strength_sum / valid_information_strength_count if valid_information_strength_count else 0.0,
    }
    return summary 


def extract_chain(mid_index, target_mid):
    """
    从mid_index中递归抽取以target_mid为终点的帖子链（父->子顺序）。
    """
    chain = []
    current_mid = target_mid
    while current_mid and current_mid in mid_index:
        post = mid_index[current_mid]
        chain.append(post)
        pid = post.get('pid')
        if not pid or pid == '0' or pid == 0:
            break
        current_mid = pid
    chain.reverse()
    return chain

def generate_context(chain):
    """
    根据帖子链生成对话上下文文本。
    """
    context_lines = []
    if len(chain) > 1:
        # 有父帖子的情况
        for idx, post in enumerate(chain[:-1]):
            context_lines.append(f"[父帖子 {idx+1}]: {post.get('text', post.get('content', ''))}")
        context_lines.append(f"[当前帖子]: \"{chain[-1].get('text', chain[-1].get('content', ''))}\"")
    else:
        # 只有一个帖子，没有上下文的情况
        context_lines.append(f"[当前帖子]: \"{chain[0].get('text', chain[0].get('content', ''))}\"")
        context_lines.append("(这是一个独立帖子，没有回复关系)")
    return '\n'.join(context_lines)

def make_prompt(context_text, target_post, prompt_template):
    """
    用prompt模板、上下文和目标帖内容生成最终prompt。
    """
    before, after = prompt_template.split('## 2. 对话上下文 (Conversational Context)', 1)
    after_split = after.split('## 3. 你的任务 (Your Task)', 1)
    if len(after_split) == 2:
        context_block, after_rest = after_split
        prompt = before + '## 2. 对话上下文 (Conversational Context)\n' + context_text + '\n\n## 3. 你的任务 (Your Task)' + after_rest
    else:
        prompt = before + '## 2. 对话上下文 (Conversational Context)\n' + context_text
    # 替换所有 [目标帖子]: "..." 为当前目标帖
    prompt = re.sub(r'\[目标帖子\]:\s*".*?"', f'[目标帖子]: "{target_post}"', prompt)
    return prompt 


def load_agents_from_file(filepath):
    """
    从json文件加载agent配置并实例化Agent对象列表。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        agent_configs = json.load(f)
    agents = []
    for cfg in agent_configs:
        agent = Agent(
            cfg['agent_id'],
            RoleType(cfg['role_type']),
            cfg['attitude_firmness'],
            cfg['opinion_blocking'],
            cfg['activity_level'],
            cfg['initial_emotion'],
            cfg['initial_stance'],
            cfg['initial_confidence']
        )
        agents.append(agent)
    return agents 