#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的JSONL到JSON转换脚本
"""

import json

def convert_jsonl_to_json(input_file, output_file=None):
    """
    将JSONL文件转换为JSON文件
    
    Args:
        input_file (str): 输入的JSONL文件路径
        output_file (str, optional): 输出的JSON文件路径
    """
    # 如果没有指定输出文件，则自动生成
    if output_file is None:
        output_file = input_file.replace('.jsonl', '.json')
    
    # 读取JSONL文件并解析每一行
    data_list = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:  # 跳过空行
                try:
                    data = json.loads(line)
                    data_list.append(data)
                except json.JSONDecodeError as e:
                    print(f"警告：第 {line_num} 行JSON解析失败: {e}")
                    continue
    
    # 将数据写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    
    print(f"转换完成！")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"成功转换 {len(data_list)} 条记录")
    
    return data_list

# 使用示例
if __name__ == '__main__':
    # 转换您的文件
    input_file = 'data/data/extract_weibo_chain_output.jsonl'
    output_file = 'data/data/extract_weibo_chain_output.json'
    
    try:
        result = convert_jsonl_to_json(input_file, output_file)
        print(f"转换成功，共处理 {len(result)} 条数据")
    except Exception as e:
        print(f"转换失败: {e}") 