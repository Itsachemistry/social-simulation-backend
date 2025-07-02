#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微博标签功能使用示例

展示如何使用新增的标签筛选功能：
1. 按标签筛选帖子
2. 标签搜索
3. 标签统计
"""

import json
import requests

# API基础URL
BASE_URL = "http://localhost:5000/api/visualization"

def example_filter_by_tags():
    """示例：按标签筛选帖子"""
    print("=== 按标签筛选帖子示例 ===")
    
    # 请求数据
    filter_data = {
        "simulation_id": "your_simulation_id",  # 替换为实际的仿真ID
        "tags": ["科技", "创新"],  # 筛选包含这些标签的帖子
        "match_all_tags": False,  # False: 匹配任一标签, True: 匹配所有标签
        "sort_by": "time",
        "limit": 20
    }
    
    print("请求参数:")
    print(json.dumps(filter_data, indent=2, ensure_ascii=False))
    print()
    
    # 发送请求
    try:
        response = requests.post(f"{BASE_URL}/posts/filter", json=filter_data)
        if response.status_code == 200:
            result = response.json()
            print("筛选结果:")
            print(f"  找到 {result['total_filtered']} 条帖子")
            print(f"  热门标签: {result['summary']['top_tags'][:5]}")
            print()
            
            # 显示前几条帖子
            for i, post in enumerate(result['posts'][:3]):
                print(f"帖子 {i+1}:")
                print(f"  内容: {post['content']}")
                print(f"  标签: {post.get('tags', [])}")
                print(f"  作者: {post['author_id']}")
                print()
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"请求异常: {e}")
    
    print("-" * 50)

def example_search_by_tags():
    """示例：搜索标签"""
    print("=== 搜索标签示例 ===")
    
    # 请求数据
    search_data = {
        "simulation_id": "your_simulation_id",  # 替换为实际的仿真ID
        "keywords": "科技",  # 搜索关键词
        "search_fields": ["tags", "content"],  # 在标签和内容中搜索
        "page": 1,
        "page_size": 10
    }
    
    print("请求参数:")
    print(json.dumps(search_data, indent=2, ensure_ascii=False))
    print()
    
    # 发送请求
    try:
        response = requests.post(f"{BASE_URL}/posts/search", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print("搜索结果:")
            print(f"  找到 {result['total_found']} 条帖子")
            print(f"  当前页: {result['page']}/{result['total_pages']}")
            print()
            
            # 显示搜索结果
            for i, post in enumerate(result['results'][:3]):
                print(f"结果 {i+1}:")
                print(f"  内容: {post['content']}")
                print(f"  标签: {post.get('tags', [])}")
                print(f"  搜索匹配度: {post.get('_search_score', 0)}")
                print()
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"请求异常: {e}")
    
    print("-" * 50)

def example_get_tag_summary():
    """示例：获取标签统计"""
    print("=== 获取标签统计示例 ===")
    
    # 请求数据
    summary_data = {
        "simulation_id": "your_simulation_id",  # 替换为实际的仿真ID
        "time_range": {  # 可选：时间范围
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59"
        }
    }
    
    print("请求参数:")
    print(json.dumps(summary_data, indent=2, ensure_ascii=False))
    print()
    
    # 发送请求
    try:
        response = requests.post(f"{BASE_URL}/posts/summary", json=summary_data)
        if response.status_code == 200:
            result = response.json()
            print("统计结果:")
            print(f"  总帖子数: {result['summary']['total_posts']}")
            print("  热门标签:")
            for tag, count in result['summary']['top_tags'][:10]:
                print(f"    - {tag}: {count}次")
            print()
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"请求异常: {e}")
    
    print("-" * 50)

def example_get_options():
    """示例：获取标签选项"""
    print("=== 获取标签选项示例 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/options")
        if response.status_code == 200:
            result = response.json()
            print("标签选项:")
            print(f"  描述: {result['tag_options']['description']}")
            print("  匹配模式:")
            for mode in result['tag_options']['match_modes']:
                print(f"    - {mode['label']} (值: {mode['value']})")
            print(f"  示例: {result['tag_options']['example']}")
            print()
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"请求异常: {e}")
    
    print("-" * 50)

def example_advanced_filtering():
    """示例：高级筛选（组合多种条件）"""
    print("=== 高级筛选示例 ===")
    
    # 请求数据
    filter_data = {
        "simulation_id": "your_simulation_id",  # 替换为实际的仿真ID
        "time_range": {  # 时间范围
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-31T23:59:59"
        },
        "tags": ["科技", "创新"],  # 标签筛选
        "match_all_tags": False,  # 匹配任一标签
        "keywords": "产品",  # 关键词搜索
        "search_fields": ["content", "tags"],  # 在内容和标签中搜索
        "min_popularity": 10,  # 最低热度
        "filter_type": "original",  # 只要原创内容
        "sort_by": "popularity",  # 按热度排序
        "sort_reverse": True,  # 降序
        "limit": 50
    }
    
    print("高级筛选请求参数:")
    print(json.dumps(filter_data, indent=2, ensure_ascii=False))
    print()
    
    print("这个请求会:")
    print("1. 筛选指定时间范围内的帖子")
    print("2. 只保留包含'科技'或'创新'标签的帖子")
    print("3. 在内容和标签中搜索'产品'关键词")
    print("4. 只保留热度>=10的帖子")
    print("5. 只保留原创内容（排除转发）")
    print("6. 按热度降序排序")
    print("7. 最多返回50条结果")
    print()
    
    print("-" * 50)

def main():
    """主函数"""
    print("微博标签功能使用示例")
    print("=" * 50)
    print()
    
    example_filter_by_tags()
    example_search_by_tags()
    example_get_tag_summary()
    example_get_options()
    example_advanced_filtering()
    
    print("使用说明:")
    print("1. 将 'your_simulation_id' 替换为实际的仿真ID")
    print("2. 确保API服务器正在运行")
    print("3. 根据需要调整筛选参数")
    print("4. 标签格式为 #XXXX#，在筛选时使用 XXXX 部分")
    print()
    print("标签功能特点:")
    print("- 自动从帖子内容中提取 #XXXX# 格式的标签")
    print("- 支持按单个或多个标签筛选")
    print("- 支持'匹配任一标签'和'匹配所有标签'两种模式")
    print("- 支持在标签中进行关键词搜索")
    print("- 提供标签使用频率统计")

if __name__ == "__main__":
    main() 