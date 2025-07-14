#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取指定MID的消息链并生成prompt
基于extract_weibo_chain.py的逻辑
"""

import json
import os
import re
from typing import List, Dict, Any, Optional


# 配置参数
DATA_PATH = 'data/extract_weibo_chain_output .json'
PROMPT_TEMPLATE_PATH = 'data/promptdataprocess.txt'
OUTPUT_PATH = 'data/specific_chain_prompt.txt'

# 目标MID
TARGET_MID = "4047076486025918"


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """
    加载JSON数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        数据列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功加载 {len(data)} 条记录")
        return data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return []


def load_prompt_template(file_path: str) -> str:
    """
    加载prompt模板
    
    Args:
        file_path: prompt模板文件路径
        
    Returns:
        prompt模板内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            template = f.read()
        print(f"成功加载prompt模板")
        return template
    except Exception as e:
        print(f"加载prompt模板失败: {e}")
        return ""


def build_mid_index(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    构建MID索引
    
    Args:
        data: 数据列表
        
    Returns:
        MID到对象的映射
    """
    mid_index = {}
    
    def add_post(post: Dict[str, Any]):
        mid_index[post['mid']] = post
        for child in post.get('children', []):
            add_post(child)
    
    for post in data:
        add_post(post)
    
    print(f"构建了 {len(mid_index)} 个MID索引")
    return mid_index


def extract_chain(mid_index: Dict[str, Dict[str, Any]], target_mid: str) -> List[Dict[str, Any]]:
    """
    提取消息链
    
    Args:
        mid_index: MID索引
        target_mid: 目标MID
        
    Returns:
        消息链列表
    """
    chain = []
    current_mid = target_mid
    
    print(f"开始提取MID {target_mid} 的消息链...")
    
    while current_mid and current_mid in mid_index:
        post = mid_index[current_mid]
        chain.append(post)
        print(f"  添加: MID {current_mid} -> PID {post.get('pid', 'None')}")
        
        pid = post.get('pid')
        if not pid or pid == '0' or pid == 0 or pid == '2':
            print(f"  到达根节点，停止提取")
            break
        current_mid = pid
    
    chain.reverse()
    print(f"提取完成，共 {len(chain)} 条消息")
    return chain


def generate_context(chain: List[Dict[str, Any]]) -> str:
    """
    生成对话上下文
    
    Args:
        chain: 消息链
        
    Returns:
        格式化的对话上下文
    """
    context_lines = []
    
    for idx, post in enumerate(chain[:-1]):
        text = post.get('text', '').strip()
        if text:
            context_lines.append(f"[父帖子 {idx+1}]: {text}")
    
    # 添加目标帖子
    target_text = chain[-1].get('text', '').strip()
    if target_text:
        context_lines.append(f"[目标帖子]: \"{target_text}\"")
    
    return '\n'.join(context_lines)


def make_prompt(context_text: str, target_post: str, template: str) -> str:
    """
    生成完整的prompt
    
    Args:
        context_text: 对话上下文
        target_post: 目标帖子内容
        template: prompt模板
        
    Returns:
        完整的prompt
    """
    # 分割模板
    before, after = template.split('## 2. 对话上下文 (Conversational Context)', 1)
    after_split = after.split('## 3. 你的任务 (Your Task)', 1)
    
    if len(after_split) == 2:
        context_block, after_rest = after_split
        prompt = (before + 
                 '## 2. 对话上下文 (Conversational Context)\n' + 
                 context_text + 
                 '\n\n## 3. 你的任务 (Your Task)' + 
                 after_rest)
    else:
        prompt = before + '## 2. 对话上下文 (Conversational Context)\n' + context_text
    
    # 替换目标帖子
    prompt = re.sub(r'\[目标帖子\]:\s*".*?"', f'[目标帖子]: "{target_post}"', prompt)
    
    return prompt


def save_prompt_to_file(prompt: str, output_path: str) -> bool:
    """
    保存prompt到文件
    
    Args:
        prompt: prompt内容
        output_path: 输出文件路径
        
    Returns:
        是否成功保存
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"Prompt已保存到: {output_path}")
        return True
    except Exception as e:
        print(f"保存prompt失败: {e}")
        return False


def print_chain_info(chain: List[Dict[str, Any]]) -> None:
    """
    打印消息链信息
    
    Args:
        chain: 消息链
    """
    print(f"\n📋 消息链详细信息:")
    print(f"=" * 60)
    
    for i, post in enumerate(chain):
        print(f"\n{i+1}. MID: {post.get('mid', 'N/A')}")
        print(f"   PID: {post.get('pid', 'N/A')}")
        print(f"   用户: {post.get('name', 'N/A')} (UID: {post.get('uid', 'N/A')})")
        print(f"   时间: {post.get('t', 'N/A')}")
        print(f"   内容: {post.get('text', 'N/A')[:100]}...")
        
        if i == len(chain) - 1:
            print(f"   🎯 这是目标帖子")
        
        print(f"   " + "-" * 40)


def main():
    """主函数"""
    print(f"🎯 开始提取MID {TARGET_MID} 的消息链")
    print("=" * 60)
    
    # 1. 加载数据
    data = load_data(DATA_PATH)
    if not data:
        return
    
    # 2. 加载prompt模板
    template = load_prompt_template(PROMPT_TEMPLATE_PATH)
    if not template:
        return
    
    # 3. 构建MID索引
    mid_index = build_mid_index(data)
    
    # 4. 检查目标MID是否存在
    if TARGET_MID not in mid_index:
        print(f"❌ 错误: 找不到MID {TARGET_MID}")
        print(f"可用的MID数量: {len(mid_index)}")
        return
    
    # 5. 提取消息链
    chain = extract_chain(mid_index, TARGET_MID)
    if not chain:
        print(f"❌ 错误: 无法提取MID {TARGET_MID} 的消息链")
        return
    
    # 6. 打印消息链信息
    print_chain_info(chain)
    
    # 7. 生成对话上下文
    context_text = generate_context(chain)
    print(f"\n📝 生成的对话上下文:")
    print("-" * 40)
    print(context_text)
    print("-" * 40)
    
    # 8. 生成完整prompt
    target_post = chain[-1].get('text', '').strip()
    prompt = make_prompt(context_text, target_post, template)
    
    # 9. 保存prompt到文件
    success = save_prompt_to_file(prompt, OUTPUT_PATH)
    
    if success:
        print(f"\n✅ 处理完成!")
        print(f"📁 输出文件: {OUTPUT_PATH}")
        print(f"📊 消息链长度: {len(chain)}")
        print(f"🎯 目标MID: {TARGET_MID}")
    else:
        print(f"\n❌ 处理失败!")


if __name__ == "__main__":
    main() 