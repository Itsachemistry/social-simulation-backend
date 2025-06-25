#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化API测试脚本
演示交互式数据筛选和分析功能
"""

import requests
import json
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:5000/api"

def test_visualization_options():
    """测试获取可视化选项"""
    print("=== 测试获取可视化选项 ===")
    
    response = requests.get(f"{BASE_URL}/visualization/options")
    if response.status_code == 200:
        options = response.json()
        print("✅ 可视化选项获取成功")
        print(f"排序选项: {options['sort_options']}")
        print(f"筛选选项: {options['filter_options']}")
        print(f"搜索字段: {options['search_fields']}")
    else:
        print(f"❌ 获取选项失败: {response.text}")

def test_posts_filter():
    """测试综合帖子筛选"""
    print("\n=== 测试综合帖子筛选 ===")
    
    # 首先启动一个仿真
    simulation_config = {
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-02T00:00:00",
        "stance_distribution": {"支持": 0.6, "反对": 0.3, "中立": 0.1},
        "sentiment_distribution": {"正面": 0.5, "负面": 0.3, "中性": 0.2},
        "event_description": "测试事件：新产品发布",
        "quantity": 50
    }
    
    # 设置仿真配置
    response = requests.post(f"{BASE_URL}/simulation/config", json=simulation_config)
    if response.status_code != 200:
        print("❌ 设置仿真配置失败")
        return None
    
    # 启动仿真
    response = requests.post(f"{BASE_URL}/simulation/start")
    if response.status_code != 200:
        print("❌ 启动仿真失败")
        return None
    
    simulation_id = response.json().get('simulation_id')
    print(f"✅ 仿真启动成功，ID: {simulation_id}")
    
    # 等待仿真完成
    import time
    while True:
        response = requests.get(f"{BASE_URL}/simulation/status/{simulation_id}")
        if response.status_code == 200:
            status = response.json()
            if status['status'] == 'completed':
                print("✅ 仿真完成")
                break
            elif status['status'] == 'failed':
                print("❌ 仿真失败")
                return None
        time.sleep(2)
    
    # 测试时间范围筛选
    print("\n--- 测试时间范围筛选 ---")
    time_range = {
        "start": "2024-01-01T06:00:00",
        "end": "2024-01-01T18:00:00"
    }
    
    filter_params = {
        "simulation_id": simulation_id,
        "time_range": time_range,
        "limit": 20
    }
    
    response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=filter_params)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 时间筛选成功，找到 {result['total_filtered']} 条帖子")
        print(f"时间范围: {time_range['start']} 到 {time_range['end']}")
    else:
        print(f"❌ 时间筛选失败: {response.text}")
    
    # 测试关键词搜索
    print("\n--- 测试关键词搜索 ---")
    search_params = {
        "simulation_id": simulation_id,
        "keywords": "产品 发布",
        "search_fields": ["content"],
        "limit": 10
    }
    
    response = requests.post(f"{BASE_URL}/visualization/posts/search", json=search_params)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 关键词搜索成功，找到 {result['total_found']} 条帖子")
        print(f"搜索关键词: {search_params['keywords']}")
    else:
        print(f"❌ 关键词搜索失败: {response.text}")
    
    # 测试综合筛选
    print("\n--- 测试综合筛选 ---")
    complex_filter = {
        "simulation_id": simulation_id,
        "time_range": time_range,
        "keywords": "产品",
        "sort_by": "popularity",
        "sort_reverse": True,
        "min_popularity": 10,
        "filter_type": "original",
        "include_reposts": False,
        "limit": 15
    }
    
    response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=complex_filter)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 综合筛选成功，找到 {result['total_filtered']} 条帖子")
        print(f"筛选参数: {result['filter_params']}")
        
        # 显示摘要统计
        summary = result['summary']
        print(f"总帖子数: {summary['total_posts']}")
        print(f"类型分布: {summary['type_distribution']}")
        print(f"热度统计: {summary['popularity_stats']}")
    else:
        print(f"❌ 综合筛选失败: {response.text}")
    
    return simulation_id

def test_posts_summary():
    """测试帖子摘要统计"""
    print("\n=== 测试帖子摘要统计 ===")
    
    # 使用之前的仿真ID
    simulation_id = test_posts_filter()
    if not simulation_id:
        return
    
    # 测试不同时间范围的摘要
    time_ranges = [
        {"start": "2024-01-01T00:00:00", "end": "2024-01-01T12:00:00"},
        {"start": "2024-01-01T12:00:00", "end": "2024-01-02T00:00:00"}
    ]
    
    for i, time_range in enumerate(time_ranges, 1):
        print(f"\n--- 时间段 {i} 摘要 ---")
        summary_params = {
            "simulation_id": simulation_id,
            "time_range": time_range,
            "filter_type": "all",
            "include_reposts": True
        }
        
        response = requests.post(f"{BASE_URL}/visualization/posts/summary", json=summary_params)
        if response.status_code == 200:
            result = response.json()
            summary = result['summary']
            print(f"✅ 摘要生成成功")
            print(f"时间段: {time_range['start']} 到 {time_range['end']}")
            print(f"总帖子数: {summary['total_posts']}")
            print(f"类型分布: {summary['type_distribution']}")
            print(f"平均热度: {summary['popularity_stats']['avg_heat']:.2f}")
            print(f"热门话题: {summary['hot_topics'][:5]}")
        else:
            print(f"❌ 摘要生成失败: {response.text}")

def test_interactive_features():
    """测试交互式功能"""
    print("\n=== 测试交互式功能 ===")
    
    # 模拟前端交互场景
    simulation_id = test_posts_filter()
    if not simulation_id:
        return
    
    # 场景1: 用户调整时间刷选
    print("\n--- 场景1: 时间刷选调整 ---")
    time_brush_scenarios = [
        {"start": "2024-01-01T00:00:00", "end": "2024-01-01T06:00:00"},
        {"start": "2024-01-01T06:00:00", "end": "2024-01-01T12:00:00"},
        {"start": "2024-01-01T12:00:00", "end": "2024-01-01T18:00:00"},
        {"start": "2024-01-01T18:00:00", "end": "2024-01-02T00:00:00"}
    ]
    
    for i, time_range in enumerate(time_brush_scenarios, 1):
        print(f"时间刷选 {i}: {time_range['start']} - {time_range['end']}")
        
        filter_params = {
            "simulation_id": simulation_id,
            "time_range": time_range,
            "sort_by": "time",
            "limit": 10
        }
        
        response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=filter_params)
        if response.status_code == 200:
            result = response.json()
            print(f"  找到 {result['total_filtered']} 条帖子")
        else:
            print(f"  筛选失败")
    
    # 场景2: 用户切换排序方式
    print("\n--- 场景2: 排序方式切换 ---")
    sort_scenarios = [
        {"sort_by": "time", "label": "按时间"},
        {"sort_by": "popularity", "label": "按热度"},
        {"sort_by": "heat", "label": "按热度值"},
        {"sort_by": "likes", "label": "按点赞数"}
    ]
    
    for sort_config in sort_scenarios:
        print(f"排序方式: {sort_config['label']}")
        
        filter_params = {
            "simulation_id": simulation_id,
            "sort_by": sort_config['sort_by'],
            "sort_reverse": True,
            "limit": 5
        }
        
        response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=filter_params)
        if response.status_code == 200:
            result = response.json()
            posts = result['posts']
            if posts:
                top_post = posts[0]
                print(f"  热门帖子: {top_post.get('content', '')[:50]}...")
                print(f"  热度值: {top_post.get('heat', 0)}, 点赞: {top_post.get('likes', 0)}")
        else:
            print(f"  排序失败")
    
    # 场景3: 用户调整热度阈值
    print("\n--- 场景3: 热度阈值调整 ---")
    popularity_thresholds = [0, 5, 10, 20, 50]
    
    for threshold in popularity_thresholds:
        print(f"热度阈值: {threshold}")
        
        filter_params = {
            "simulation_id": simulation_id,
            "min_popularity": threshold,
            "sort_by": "popularity",
            "sort_reverse": True,
            "limit": 10
        }
        
        response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=filter_params)
        if response.status_code == 200:
            result = response.json()
            print(f"  符合条件的帖子: {result['total_filtered']} 条")
        else:
            print(f"  筛选失败")
    
    # 场景4: 用户控制转发显示
    print("\n--- 场景4: 转发内容控制 ---")
    repost_scenarios = [
        {"include_reposts": True, "label": "包含转发"},
        {"include_reposts": False, "label": "仅原创"}
    ]
    
    for repost_config in repost_scenarios:
        print(f"转发设置: {repost_config['label']}")
        
        filter_params = {
            "simulation_id": simulation_id,
            "include_reposts": repost_config['include_reposts'],
            "limit": 20
        }
        
        response = requests.post(f"{BASE_URL}/visualization/posts/filter", json=filter_params)
        if response.status_code == 200:
            result = response.json()
            summary = result['summary']
            print(f"  总帖子数: {summary['total_posts']}")
            print(f"  类型分布: {summary['type_distribution']}")
        else:
            print(f"  筛选失败")

def main():
    """主测试函数"""
    print("🚀 开始测试可视化API功能")
    print("=" * 50)
    
    try:
        # 测试基础功能
        test_visualization_options()
        test_posts_filter()
        test_posts_summary()
        
        # 测试交互式功能
        test_interactive_features()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main() 