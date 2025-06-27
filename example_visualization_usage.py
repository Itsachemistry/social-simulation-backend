#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化API使用示例
演示如何在实际应用中使用交互式数据筛选和分析功能
"""

import requests
import json
from datetime import datetime, timedelta

class VisualizationClient:
    """可视化API客户端"""
    
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.visualization_url = f"{base_url}/visualization"
        self.simulation_url = f"{base_url}/simulation"
    
    def get_options(self):
        """获取可视化选项"""
        response = requests.get(f"{self.visualization_url}/options")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"获取选项失败: {response.text}")
    
    def filter_posts(self, simulation_id, **kwargs):
        """综合筛选帖子"""
        params = {"simulation_id": simulation_id, **kwargs}
        response = requests.post(f"{self.visualization_url}/posts/filter", json=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"筛选失败: {response.text}")
    
    def search_posts(self, simulation_id, keywords, **kwargs):
        """搜索帖子"""
        params = {"simulation_id": simulation_id, "keywords": keywords, **kwargs}
        response = requests.post(f"{self.visualization_url}/posts/search", json=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"搜索失败: {response.text}")
    
    def get_summary(self, simulation_id, **kwargs):
        """获取摘要统计"""
        params = {"simulation_id": simulation_id, **kwargs}
        response = requests.post(f"{self.visualization_url}/posts/summary", json=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"获取摘要失败: {response.text}")

def demo_time_brush_interaction():
    """演示时间刷选交互"""
    print("=== 时间刷选交互演示 ===")
    
    client = VisualizationClient()
    
    # 假设我们有一个仿真ID
    simulation_id = "demo_sim_001"
    
    # 定义不同的时间范围
    time_ranges = [
        {"start": "2024-01-01T00:00:00", "end": "2024-01-01T06:00:00"},
        {"start": "2024-01-01T06:00:00", "end": "2024-01-01T12:00:00"},
        {"start": "2024-01-01T12:00:00", "end": "2024-01-01T18:00:00"},
        {"start": "2024-01-01T18:00:00", "end": "2024-01-02T00:00:00"}
    ]
    
    for i, time_range in enumerate(time_ranges, 1):
        print(f"\n时间段 {i}: {time_range['start']} - {time_range['end']}")
        
        try:
            result = client.filter_posts(
                simulation_id=simulation_id,
                time_range=time_range,
                sort_by="time",
                limit=20
            )
            
            print(f"  找到 {result['total_filtered']} 条帖子")
            
            # 显示时间分布
            if result['posts']:
                first_post = result['posts'][0]
                last_post = result['posts'][-1]
                print(f"  时间范围: {first_post['timestamp']} 到 {last_post['timestamp']}")
                
                # 显示热度统计
                summary = result['summary']
                print(f"  平均热度: {summary['popularity_stats']['avg_heat']:.1f}")
                print(f"  总点赞: {summary['popularity_stats']['total_likes']}")
                
        except Exception as e:
            print(f"  错误: {str(e)}")

def demo_keyword_search():
    """演示关键词搜索（含分页）"""
    print("\n=== 关键词搜索演示（含分页） ===")
    
    client = VisualizationClient()
    simulation_id = "demo_sim_001"
    
    # 测试不同的搜索关键词
    keywords_list = [
        "产品",
        "发布",
        "创新",
        "技术",
        "用户 体验"
    ]
    
    for keywords in keywords_list:
        print(f"\n搜索关键词: '{keywords}'（第一页）")
        try:
            # 请求第一页
            result = client.search_posts(
                simulation_id=simulation_id,
                keywords=keywords,
                search_fields=["content"],
                page=1,
                page_size=5
            )
            print(f"  找到 {result['total_found']} 条相关帖子，共 {result['total_pages']} 页")
            # 显示前5条结果
            for i, post in enumerate(result['results'], 1):
                print(f"  {i}. {post['content'][:50]}... (匹配度: {post.get('_search_score', 0)})")
            # 如果有多页，演示第二页
            if result['total_pages'] > 1:
                print(f"\n  —— 第二页 ——")
                result2 = client.search_posts(
                    simulation_id=simulation_id,
                    keywords=keywords,
                    search_fields=["content"],
                    page=2,
                    page_size=5
                )
                for i, post in enumerate(result2['results'], 1):
                    print(f"  {i}. {post['content'][:50]}... (匹配度: {post.get('_search_score', 0)})")
        except Exception as e:
            print(f"  错误: {str(e)}")

def demo_sorting_and_filtering():
    """演示排序和筛选"""
    print("\n=== 排序和筛选演示 ===")
    
    client = VisualizationClient()
    simulation_id = "demo_sim_001"
    
    # 测试不同的排序方式
    sort_configs = [
        {"sort_by": "time", "label": "按时间"},
        {"sort_by": "popularity", "label": "按热度"},
        {"sort_by": "heat", "label": "按热度值"},
        {"sort_by": "likes", "label": "按点赞数"}
    ]
    
    for config in sort_configs:
        print(f"\n排序方式: {config['label']}")
        
        try:
            result = client.filter_posts(
                simulation_id=simulation_id,
                sort_by=config['sort_by'],
                sort_reverse=True,
                limit=5
            )
            
            if result['posts']:
                top_post = result['posts'][0]
                print(f"  热门帖子: {top_post['content'][:50]}...")
                print(f"  热度值: {top_post.get('heat', 0)}, 点赞: {top_post.get('likes', 0)}")
                
        except Exception as e:
            print(f"  错误: {str(e)}")
    
    # 测试热度阈值筛选
    print("\n--- 热度阈值筛选 ---")
    thresholds = [0, 10, 20, 50, 100]
    
    for threshold in thresholds:
        print(f"热度阈值: {threshold}")
        
        try:
            result = client.filter_posts(
                simulation_id=simulation_id,
                min_popularity=threshold,
                sort_by="popularity",
                sort_reverse=True,
                limit=10
            )
            
            print(f"  符合条件的帖子: {result['total_filtered']} 条")
            
        except Exception as e:
            print(f"  错误: {str(e)}")

def demo_content_type_filtering():
    """演示内容类型筛选"""
    print("\n=== 内容类型筛选演示 ===")
    
    client = VisualizationClient()
    simulation_id = "demo_sim_001"
    
    # 测试不同的内容类型筛选
    filter_configs = [
        {"filter_type": "all", "include_reposts": True, "label": "全部内容"},
        {"filter_type": "original", "include_reposts": False, "label": "仅原创"},
        {"filter_type": "reposted", "include_reposts": True, "label": "仅转发"},
        {"filter_type": "events", "include_reposts": True, "label": "仅事件"}
    ]
    
    for config in filter_configs:
        print(f"\n筛选类型: {config['label']}")
        
        try:
            result = client.filter_posts(
                simulation_id=simulation_id,
                filter_type=config['filter_type'],
                include_reposts=config['include_reposts'],
                limit=20
            )
            
            summary = result['summary']
            print(f"  总帖子数: {summary['total_posts']}")
            print(f"  类型分布: {summary['type_distribution']}")
            
        except Exception as e:
            print(f"  错误: {str(e)}")

def demo_comprehensive_analysis():
    """演示综合分析"""
    print("\n=== 综合分析演示 ===")
    
    client = VisualizationClient()
    simulation_id = "demo_sim_001"
    
    # 综合分析：特定时间范围 + 关键词搜索 + 热度筛选 + 排序
    print("综合分析: 上午时段 + 产品相关 + 高热度 + 按热度排序")
    
    try:
        result = client.filter_posts(
            simulation_id=simulation_id,
            time_range={"start": "2024-01-01T06:00:00", "end": "2024-01-01T12:00:00"},
            keywords="产品",
            search_fields=["content"],
            min_popularity=20,
            sort_by="heat",
            sort_reverse=True,
            filter_type="original",
            include_reposts=False,
            limit=15
        )
        
        print(f"找到 {result['total_filtered']} 条符合条件的帖子")
        
        # 显示筛选参数
        print(f"筛选参数: {result['filter_params']}")
        
        # 显示摘要统计
        summary = result['summary']
        print(f"\n摘要统计:")
        print(f"  时间范围: {summary['time_range']}")
        print(f"  热度统计: {summary['popularity_stats']}")
        print(f"  类型分布: {summary['type_distribution']}")
        print(f"  热门话题: {summary['hot_topics'][:5]}")
        
        # 显示前5条帖子
        print(f"\n前5条热门帖子:")
        for i, post in enumerate(result['posts'][:5], 1):
            print(f"  {i}. {post['content'][:60]}...")
            print(f"     热度: {post['heat']}, 点赞: {post['likes']}, 分享: {post['shares']}")
            
    except Exception as e:
        print(f"错误: {str(e)}")

def demo_summary_statistics():
    """演示摘要统计"""
    print("\n=== 摘要统计演示 ===")
    
    client = VisualizationClient()
    simulation_id = "demo_sim_001"
    
    # 获取整体摘要
    print("整体摘要统计:")
    try:
        result = client.get_summary(simulation_id=simulation_id)
        summary = result['summary']
        
        print(f"  总帖子数: {summary['total_posts']}")
        print(f"  时间范围: {summary['time_range']}")
        print(f"  热度统计: {summary['popularity_stats']}")
        print(f"  类型分布: {summary['type_distribution']}")
        print(f"  热门话题: {summary['hot_topics'][:10]}")
        print(f"  活跃作者: {summary['top_authors'][:5]}")
        
    except Exception as e:
        print(f"  错误: {str(e)}")
    
    # 获取不同时间段的摘要对比
    print("\n时间段对比:")
    time_periods = [
        {"start": "2024-01-01T00:00:00", "end": "2024-01-01T12:00:00", "label": "上午"},
        {"start": "2024-01-01T12:00:00", "end": "2024-01-02T00:00:00", "label": "下午"}
    ]
    
    for period in time_periods:
        print(f"\n{period['label']}时段:")
        try:
            result = client.get_summary(
                simulation_id=simulation_id,
                time_range={"start": period['start'], "end": period['end']}
            )
            summary = result['summary']
            
            print(f"  帖子数: {summary['total_posts']}")
            print(f"  平均热度: {summary['popularity_stats']['avg_heat']:.1f}")
            print(f"  总点赞: {summary['popularity_stats']['total_likes']}")
            
        except Exception as e:
            print(f"  错误: {str(e)}")

def main():
    """主演示函数"""
    print("🚀 可视化API使用演示")
    print("=" * 60)
    
    try:
        # 演示各种功能
        demo_time_brush_interaction()
        demo_keyword_search()
        demo_sorting_and_filtering()
        demo_content_type_filtering()
        demo_comprehensive_analysis()
        demo_summary_statistics()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
        print("   运行命令: python api/app.py")
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main() 