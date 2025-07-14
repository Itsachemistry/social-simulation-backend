import json
import yaml
from typing import Dict, List, Any
from pathlib import Path


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