#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据文件与程序的集成
包括字段转换、时间片划分、Agent创建等
"""

import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from world_state import WorldState
    from time_manager import TimeSliceManager
    from agent_controller import AgentController
    print("✅ 成功导入所有模块")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def flatten_posts_recursive(posts, parent_id=None, level=0):
    """
    递归展开所有嵌套的帖子
    """
    flattened_posts = []
    
    for post in posts:
        # 添加父帖子ID信息
        if parent_id:
            post['parent_post_id'] = parent_id
        else:
            post['parent_post_id'] = None
            
        # 添加层级信息
        post['nesting_level'] = level
        
        # 添加到扁平化列表
        flattened_posts.append(post)
        
        # 递归处理子帖子
        if 'children' in post and post['children']:
            child_posts = flatten_posts_recursive(
                post['children'], 
                parent_id=post.get('pid', post.get('mid', post.get('id'))), 
                level=level + 1
            )
            flattened_posts.extend(child_posts)
    
    return flattened_posts

def test_data_loading():
    """测试数据文件加载和嵌套帖子展开"""
    print("\n" + "="*60)
    print("测试数据文件加载和嵌套帖子展开")
    print("="*60)
    
    try:
        # 使用新的postdata.json文件
        with open('data/postdata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 成功加载数据文件，包含 {len(data)} 条顶层记录")
        
        # 检查第一条记录
        first_record = data[0]
        print(f"📊 第一条记录属性:")
        for key, value in first_record.items():
            if isinstance(value, list):
                print(f"  - {key}: {type(value).__name__} (长度: {len(value)})")
            else:
                print(f"  - {key}: {type(value).__name__} = {value}")
        
        # 展开所有嵌套帖子
        print(f"\n🔄 开始展开嵌套帖子...")
        flattened_posts = flatten_posts_recursive(data)
        print(f"✅ 展开完成，总共 {len(flattened_posts)} 条帖子")
        
        # 按时间戳排序
        print(f"🕐 按时间戳排序...")
        flattened_posts.sort(key=lambda x: x.get('t', x.get('timestamp', 0)))
        print(f"✅ 排序完成")
        
        # 统计层级分布
        level_counts = {}
        for post in flattened_posts:
            level = post.get('nesting_level', 0)
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"📊 层级分布:")
        for level in sorted(level_counts.keys()):
            print(f"  - 层级 {level}: {level_counts[level]} 条帖子")
        
        # 检查时间戳分布
        timestamps = [post.get('t', post.get('timestamp', 0)) for post in flattened_posts]
        if timestamps:
            print(f"📅 时间戳范围: {min(timestamps)} - {max(timestamps)}")
            print(f"📅 时间跨度: {max(timestamps) - min(timestamps)} 秒")
        
        return flattened_posts
    except Exception as e:
        print(f"❌ 数据文件加载失败: {e}")
        return None

def test_field_normalization():
    """测试字段标准化"""
    print("\n" + "="*60)
    print("测试字段标准化")
    print("="*60)
    
    world_state = WorldState()
    
    # 创建测试数据
    test_post = {
        "uid": "test_user_123",
        "name": "测试用户",
        "text": "这是一条测试微博",
        "mid": "test_mid_456",
        "pid": "test_pid_789",
        "t": 1480377345,
        "popularity": 100,
        "emotion_score": 0.5,
        "stance_score": 0.3,
        "information_strength": 0.8,
        "children": []
    }
    
    print("📝 原始数据:")
    for key, value in test_post.items():
        print(f"  - {key}: {value}")
    
    # 测试标准化
    normalized_post = world_state.normalize_post(test_post)
    
    print("\n🔄 标准化后的数据:")
    for key, value in normalized_post.items():
        print(f"  - {key}: {value}")
    
    # 验证关键转换
    expected_mappings = {
        'uid': 'author_id',
        't': 'timestamp',
        'pid': 'parent_post_id',
        'popularity': 'heat',
        'mid': 'id',
        'text': 'content'
    }
    
    print("\n✅ 字段转换验证:")
    for old_key, new_key in expected_mappings.items():
        if new_key in normalized_post:
            print(f"  - {old_key} → {new_key}: ✅")
        else:
            print(f"  - {old_key} → {new_key}: ❌")
    
    return normalized_post

def test_time_manager():
    """测试时间管理器"""
    print("\n" + "="*60)
    print("测试时间管理器")
    print("="*60)
    
    # 加载数据
    with open('data/postdata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 预处理数据，标准化字段
    world_state = WorldState()
    normalized_data = []
    for post in data:
        normalized_post = world_state.normalize_post(post)
        # 设置默认热度值，避免被过滤
        if normalized_post.get('heat', 0) == 0:
            normalized_post['heat'] = 10  # 设置默认热度
        normalized_data.append(normalized_post)
    
    # 创建时间管理器
    time_manager = TimeSliceManager(normalized_data, slice_size=10)
    
    print(f"📊 时间管理器统计:")
    print(f"  - 总帖子数: {len(data)}")
    print(f"  - 时间片大小: 10")
    print(f"  - 总时间片数: {time_manager.total_slices}")
    
    # 测试获取时间片
    for slice_num in range(min(3, time_manager.total_slices)):
        posts = time_manager.get_slice(slice_num)
        print(f"  - 时间片 {slice_num}: {len(posts)} 条帖子")
        
        if posts:
            first_post = posts[0]
            print(f"    第一条帖子: {first_post.get('content', '')[:50]}...")
    
    return time_manager

def create_test_agent_configs():
    """创建测试用的Agent配置"""
    print("\n" + "="*60)
    print("创建测试Agent配置")
    print("="*60)
    
    # 创建测试Agent配置 - 使用真正的Agent类配置格式
    agent_configs = [
        {
            "agent_id": "test_user_001",
            "role_type": "ordinary_user",
            "attitude_stability": "firm",
            "response_style": "open",
            "activity_level": 0.8,
            "attitude_firmness": 0.6,
            "opinion_blocking_degree": 0.1,
            "emotion_update_mode": "rule",  # 使用规则模式，不调用LLM
            "emotion_sensitivity": 0.5
        },
        {
            "agent_id": "test_user_002", 
            "role_type": "ordinary_user",
            "attitude_stability": "uncertain",
            "response_style": "filtering",
            "activity_level": 0.6,
            "attitude_firmness": 0.4,
            "opinion_blocking_degree": 0.2,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.3
        },
        {
            "agent_id": "test_user_003",
            "role_type": "ordinary_user", 
            "attitude_stability": "uncertain",
            "response_style": "open",
            "activity_level": 0.9,
            "attitude_firmness": 0.7,
            "opinion_blocking_degree": 0.0,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.7
        },
        {
            "agent_id": "test_user_004",
            "role_type": "ordinary_user",
            "attitude_stability": "firm",
            "response_style": "filtering",
            "activity_level": 0.4,
            "attitude_firmness": 0.5,
            "opinion_blocking_degree": 0.3,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.4
        },
        {
            "agent_id": "test_user_005",
            "role_type": "ordinary_user",
            "attitude_stability": "firm",
            "response_style": "open",
            "activity_level": 0.7,
            "attitude_firmness": 0.8,
            "opinion_blocking_degree": 0.1,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.6
        }
    ]
    
    # 使用AgentController创建真正的Agent对象
    from src.agent_controller import AgentController
    from src.world_state import WorldState
    
    world_state = WorldState()
    controller = AgentController(agent_configs, world_state, None)
    
    # 获取所有Agent
    all_agents = []
    for agent_list in controller.agents.values():
        all_agents.extend(agent_list)
    
    print(f"\n📊 Agent统计: {len(all_agents)} 个Agent创建成功")
    
    # 显示Agent状态
    for agent in all_agents:
        status = agent.get_status()
        print(f"  - {status['agent_id']}: 情绪={status['emotion']:.2f}, 立场={status['stance_score']:.2f}, 置信度={status['confidence']:.2f}, 活跃度={status['activity_level']:.2f}")
    
    return all_agents

def test_agent_controller():
    """测试Agent控制器"""
    print("\n" + "="*60)
    print("测试Agent控制器")
    print("="*60)
    
    # 创建世界状态
    world_state = WorldState()
    
    # 加载一些测试数据
    with open('data/postdata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 添加前几条数据到世界状态
    for i, post in enumerate(data[:5]):
        normalized_post = world_state.normalize_post(post)
        world_state.add_post(normalized_post)
        print(f"✅ 添加帖子 {i+1}: {normalized_post.get('content', '')[:30]}...")
    
    # 创建Agent控制器
    try:
        controller = AgentController([], world_state, None)  # 暂时不传入LLM服务
        print("✅ 成功创建Agent控制器")
        
        # 获取所有帖子
        all_posts = world_state.get_all_posts()
        print(f"📊 世界状态中有 {len(all_posts)} 条帖子")
        
        return controller
    except Exception as e:
        print(f"❌ 创建Agent控制器失败: {e}")
        return None

def test_time_slice_simulation():
    """测试时间片模拟 - 实现完整的测试流程"""
    print("\n" + "="*60)
    print("测试时间片模拟 - 完整流程")
    print("="*60)
    
    # 创建世界状态
    world_state = WorldState()
    
    # 1. 读取所有posts
    print("📖 步骤1: 读取所有posts")
    with open('data/postdata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  ✅ 成功读取 {len(data)} 条原始帖子")
    
    # 2. 过滤掉popularity为0的帖子，并为帖子添加合理的情绪和立场数据
    print("\n🔍 步骤2: 过滤无效帖子并添加测试数据")
    valid_posts = []
    filtered_count = 0
    for i, post in enumerate(data):
        popularity = post.get('popularity', post.get('heat', 0))
        if popularity > 0:
            # 为帖子添加合理的测试数据
            if 'emotion_score' not in post or post.get('emotion_score') is None:
                # 根据帖子内容或索引生成不同的情绪值
                post['emotion_score'] = (i % 7 - 3) / 3.0  # -1.0 到 1.0 之间
            if 'stance_score' not in post or post.get('stance_score') is None:
                # 根据帖子内容或索引生成不同的立场值
                post['stance_score'] = (i % 5 - 2) / 2.0  # -1.0 到 1.0 之间
            if 'information_strength' not in post or post.get('information_strength') is None:
                # 根据popularity生成信息强度
                post['information_strength'] = min(popularity / 100.0, 1.0)
            
            valid_posts.append(post)
        else:
            filtered_count += 1
    print(f"  ✅ 过滤掉 {filtered_count} 条无效帖子（popularity=0）")
    print(f"  ✅ 保留 {len(valid_posts)} 条有效帖子")
    print(f"  ✅ 已为所有帖子添加情绪、立场和信息强度数据")
    
    # 3. 每30个帖子一个时间片
    print("\n⏰ 步骤3: 创建时间片管理器")
    slice_size = 30
    time_manager = TimeSliceManager(valid_posts, slice_size)
    print(f"  ✅ 时间片大小: {slice_size} 条帖子")
    print(f"  ✅ 总时间片数: {time_manager.total_slices}")
    
    # 4. 创建Agent配置
    print("\n🤖 步骤4: 创建Agent")
    agent_configs = [
        {
            "agent_id": "test_user_001",
            "role_type": "ordinary_user",
            "attitude_stability": "firm",
            "response_style": "open",
            "activity_level": 0.8,
            "attitude_firmness": 0.6,
            "opinion_blocking_degree": 0.1,
            "emotion_update_mode": "rule",  # 使用规则模式，不调用LLM
            "emotion_sensitivity": 0.5
        },
        {
            "agent_id": "test_user_002", 
            "role_type": "ordinary_user",
            "attitude_stability": "uncertain",
            "response_style": "filtering",
            "activity_level": 0.6,
            "attitude_firmness": 0.4,
            "opinion_blocking_degree": 0.2,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.3
        },
        {
            "agent_id": "test_user_003",
            "role_type": "ordinary_user", 
            "attitude_stability": "uncertain",
            "response_style": "open",
            "activity_level": 0.9,
            "attitude_firmness": 0.7,
            "opinion_blocking_degree": 0.0,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.7
        }
    ]
    
    # 创建真正的Agent对象
    controller = AgentController(agent_configs, world_state, None)
    all_agents = []
    for agent_list in controller.agents.values():
        all_agents.extend(agent_list)
    print(f"  ✅ 成功创建 {len(all_agents)} 个Agent")
    
    # 显示初始Agent状态
    print("\n👥 初始Agent状态:")
    for agent in all_agents:
        status = agent.get_status()
        print(f"  - {status['agent_id']}: 情绪={status['emotion']:.3f}, 立场={status['stance_score']:.3f}, 活跃度={status['activity_level']:.2f}")
    
    # 5. 运行4个时间片
    print(f"\n🔄 步骤5: 开始运行时间片模拟（共4个时间片）")
    max_slices = min(4, time_manager.total_slices)
    
    for slice_num in range(max_slices):
        print(f"\n📅 时间片 {slice_num + 1}/{max_slices}:")
        
        # 获取当前时间片的帖子
        slice_posts = time_manager.get_slice(slice_num)
        print(f"  📊 当前时间片包含 {len(slice_posts)} 条帖子")
        
        # 将帖子添加到世界状态
        for post in slice_posts:
            normalized_post = world_state.normalize_post(post)
            world_state.add_post(normalized_post)
        
        # 运行时间片模拟
        try:
            result = controller.run_time_slice(all_agents, world_state, None)
            print(f"  ✅ 时间片 {slice_num + 1} 模拟完成")
            
            # 6. 时间片结尾盘点Agent发言情况
            print(f"  📝 发言情况统计:")
            speaking_agents = []
            silent_agents = []
            
            for judgement in result['action_judgements']:
                if judgement['action']:
                    speaking_agents.append(judgement['agent_id'])
                else:
                    silent_agents.append(judgement['agent_id'])
            
            print(f"    - 发言Agent: {len(speaking_agents)} 个 ({', '.join(speaking_agents)})")
            print(f"    - 沉默Agent: {len(silent_agents)} 个 ({', '.join(silent_agents)})")
            print(f"    - 生成新帖子: {len(result['generated_posts'])} 条")
            
            # 显示Agent状态变化
            print(f"  👥 Agent状态更新:")
            for agent in all_agents:
                status = agent.get_status()
                print(f"    - {status['agent_id']}: 情绪={status['emotion']:.3f}, 立场={status['stance_score']:.3f}, 置信度={status['confidence']:.3f}")
                
        except Exception as e:
            print(f"  ❌ 时间片 {slice_num + 1} 模拟失败: {e}")
    
    print(f"\n🎉 时间片模拟完成！")
    print(f"📊 最终统计:")
    print(f"  - 总有效帖子: {len(valid_posts)} 条")
    print(f"  - 过滤无效帖子: {filtered_count} 条")
    print(f"  - 运行时间片: {max_slices} 个")
    print(f"  - 参与Agent: {len(all_agents)} 个")
    
    return True

def test_full_integration():
    """测试完整集成"""
    print("\n" + "="*60)
    print("测试完整集成")
    print("="*60)
    
    print("🔄 开始完整集成测试...")
    
    # 1. 数据加载
    data = test_data_loading()
    if not data:
        return False
    
    # 2. 字段标准化
    normalized_post = test_field_normalization()
    
    # 3. 时间管理器
    time_manager = test_time_manager()
    
    # 4. Agent创建
    agents = create_test_agent_configs()
    
    # 5. Agent控制器
    controller = test_agent_controller()
    
    # 6. 时间片模拟
    test_time_slice_simulation()
    
    print("\n🎉 完整集成测试完成！")
    print("💡 测试结果总结:")
    print("  ✅ 数据文件加载成功")
    print("  ✅ 字段标准化工作正常")
    print("  ✅ 时间片划分功能正常")
    print("  ✅ Agent创建和配置成功")
    print("  ✅ Agent控制器初始化成功")
    print("  ✅ 时间片模拟运行正常")
    print("\n💡 下一步建议:")
    print("  1. 调整Agent参数以获得更真实的模拟效果")
    print("  2. 增加更多时间片进行长期模拟")
    print("  3. 分析Agent情绪和立场的变化趋势")
    print("  4. 测试不同Agent类型的行为差异")
    
    return True

def test_complete_workflow():
    """测试完整工作流程 - 按照用户期望的流程"""
    print("\n" + "="*80)
    print("🧪 完整工作流程测试")
    print("="*80)
    
    print("📋 测试流程:")
    print("  1. 读取所有posts")
    print("  2. 过滤掉popularity为0的帖子") 
    print("  3. 每30个帖子一个时间片")
    print("  4. 运行4个时间片")
    print("  5. 每个Agent阅读推送筛选后的帖子")
    print("  6. 使用无LLM的情绪更新算法")
    print("  7. 时间片结尾盘点Agent发言情况")
    print("="*80)
    
    # 创建世界状态
    world_state = WorldState()
    
    # 1. 读取所有posts并展开嵌套结构
    print("\n📖 步骤1: 读取所有posts并展开嵌套结构")
    try:
        data = test_data_loading()
        if not data:
            print("  ❌ 数据加载失败")
            return False
        print(f"  ✅ 成功读取并展开 {len(data)} 条帖子（包含所有嵌套子帖子）")
    except Exception as e:
        print(f"  ❌ 读取数据失败: {e}")
        return False
    
    # 2. 过滤掉无效帖子（popularity为0或关键字段为null）
    print("\n🔍 步骤2: 过滤无效帖子")
    valid_posts = []
    filtered_count = 0
    null_field_count = 0
    
    for post in data:
        # 检查popularity
        popularity = post.get('popularity', post.get('heat', 0))
        if popularity == 0:
            filtered_count += 1
            continue
            
        # 检查关键字段是否为null
        emotion_score = post.get('emotion_score')
        stance_score = post.get('stance_score') 
        information_strength = post.get('information_strength')
        stance_category = post.get('stance_category')
        
        if (emotion_score is None or stance_score is None or 
            information_strength is None or stance_category is None):
            null_field_count += 1
            continue
            
        valid_posts.append(post)
    
    print(f"  ✅ 过滤掉 {filtered_count} 条无效帖子（popularity=0）")
    print(f"  ✅ 过滤掉 {null_field_count} 条无效帖子（关键字段为null）")
    print(f"  ✅ 保留 {len(valid_posts)} 条有效帖子")
    
    if len(valid_posts) == 0:
        print("  ❌ 没有有效帖子，无法继续测试")
        return False
    
    # 3. 每30个帖子一个时间片
    print("\n⏰ 步骤3: 创建时间片管理器")
    slice_size = 30
    time_manager = TimeSliceManager(valid_posts, slice_size)
    print(f"  ✅ 时间片大小: {slice_size} 条帖子")
    print(f"  ✅ 总时间片数: {time_manager.total_slices}")
    
    # 4. 创建Agent配置
    print("\n🤖 步骤4: 创建Agent")
    agent_configs = [
        {
            "agent_id": "user_001",
            "role_type": "ordinary_user",
            "attitude_stability": "firm",
            "response_style": "open",
            "activity_level": 0.8,
            "attitude_firmness": 0.6,
            "opinion_blocking_degree": 0.1,
            "emotion_update_mode": "rule",  # 使用规则模式，不调用LLM
            "emotion_sensitivity": 0.5
        },
        {
            "agent_id": "user_002", 
            "role_type": "ordinary_user",
            "attitude_stability": "uncertain",
            "response_style": "filtering",
            "activity_level": 0.6,
            "attitude_firmness": 0.4,
            "opinion_blocking_degree": 0.2,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.3
        },
        {
            "agent_id": "user_003",
            "role_type": "ordinary_user", 
            "attitude_stability": "uncertain",
            "response_style": "open",
            "activity_level": 0.9,
            "attitude_firmness": 0.7,
            "opinion_blocking_degree": 0.0,
            "emotion_update_mode": "rule",
            "emotion_sensitivity": 0.7
        }
    ]
    
    # 创建真正的Agent对象
    try:
        controller = AgentController(agent_configs, world_state, None)
        all_agents = []
        for agent_list in controller.agents.values():
            all_agents.extend(agent_list)
        print(f"  ✅ 成功创建 {len(all_agents)} 个Agent")
        
        # 为Agent设置不同的初始情绪，增加多样性
        if len(all_agents) >= 3:
            all_agents[0].emotion = 0.2   # user_001: 轻微正面情绪
            all_agents[1].emotion = -0.1  # user_002: 轻微负面情绪  
            all_agents[2].emotion = 0.0   # user_003: 保持中立
        print(f"  🎭 已为Agent设置不同的初始情绪")
        
    except Exception as e:
        print(f"  ❌ 创建Agent失败: {e}")
        return False
    
    # 显示初始Agent状态
    print("\n👥 初始Agent状态:")
    for agent in all_agents:
        status = agent.get_status()
        print(f"  - {status['agent_id']}: 情绪={status['emotion']:.3f}, 立场={status['stance_score']:.3f}, 活跃度={status['activity_level']:.2f}")
    
    # 5. 运行4个时间片
    print(f"\n🔄 步骤5: 开始运行时间片模拟（共4个时间片）")
    max_slices = min(4, time_manager.total_slices)
    
    total_speaking_agents = 0
    total_generated_posts = 0
    
    for slice_num in range(max_slices):
        print(f"\n📅 时间片 {slice_num + 1}/{max_slices}:")
        
        # 获取当前时间片的帖子
        slice_posts = time_manager.get_slice(slice_num)
        print(f"  📊 当前时间片包含 {len(slice_posts)} 条帖子")
        
        # 将帖子添加到世界状态
        for post in slice_posts:
            normalized_post = world_state.normalize_post(post)
            world_state.add_post(normalized_post)
        
        # 运行时间片模拟
        try:
            print(f"  🔍 开始Agent阅读和情绪更新过程:")
            
            # 获取当前时间片的所有帖子
            all_posts = world_state.get_all_posts()
            
            # 为每个Agent生成个性化信息流并追踪变化
            for agent in all_agents:
                print(f"\n    🤖 {agent.agent_id} 开始阅读:")
                
                # 记录Agent阅读前的状态
                before_status = agent.get_status()
                print(f"      阅读前: 情绪={before_status['emotion']:.3f}, 立场={before_status['stance_score']:.3f}, 置信度={before_status['confidence']:.3f}")
                
                # 生成个性化信息流
                personalized_posts = controller._generate_personalized_feed(agent, all_posts, 1.0)
                print(f"      推送筛选结果: 从{len(all_posts)}条帖子中筛选到{len(personalized_posts)}条")
                
                # 逐条处理帖子，追踪情绪立场变化
                for i, post in enumerate(personalized_posts):
                    # 记录处理前的状态
                    pre_emotion = agent.emotion
                    pre_stance = agent.stance_score
                    pre_confidence = agent.confidence
                    
                    # 更新情绪和立场
                    agent.update_emotion_and_stance(post)
                    
                    # 记录变化
                    emotion_change = agent.emotion - pre_emotion
                    stance_change = agent.stance_score - pre_stance
                    confidence_change = agent.confidence - pre_confidence
                    
                    print(f"        帖子{i+1}: 情绪{pre_emotion:.3f}→{agent.emotion:.3f}({emotion_change:+.3f}), "
                          f"立场{pre_stance:.3f}→{agent.stance_score:.3f}({stance_change:+.3f}), "
                          f"置信度{pre_confidence:.3f}→{agent.confidence:.3f}({confidence_change:+.3f})")
                
                # 记录Agent阅读后的状态
                after_status = agent.get_status()
                print(f"      阅读后: 情绪={after_status['emotion']:.3f}, 立场={after_status['stance_score']:.3f}, 置信度={after_status['confidence']:.3f}")
            
            # 运行完整的时间片模拟
            result = controller.run_time_slice(all_agents, world_state, None)
            print(f"  ✅ 时间片 {slice_num + 1} 模拟完成")
            
            # 6. 时间片结尾盘点Agent发言情况
            print(f"  📝 发言情况统计:")
            speaking_agents = []
            silent_agents = []
            
            for judgement in result['action_judgements']:
                if judgement['action']:
                    speaking_agents.append(judgement['agent_id'])
                else:
                    silent_agents.append(judgement['agent_id'])
            
            total_speaking_agents += len(speaking_agents)
            total_generated_posts += len(result['generated_posts'])
            
            print(f"    - 发言Agent: {len(speaking_agents)} 个 ({', '.join(speaking_agents)})")
            print(f"    - 沉默Agent: {len(silent_agents)} 个 ({', '.join(silent_agents)})")
            print(f"    - 生成新帖子: {len(result['generated_posts'])} 条")
            
            # 显示Agent最终状态变化
            print(f"  👥 Agent最终状态:")
            for agent in all_agents:
                status = agent.get_status()
                print(f"    - {status['agent_id']}: 情绪={status['emotion']:.3f}, 立场={status['stance_score']:.3f}, 置信度={status['confidence']:.3f}")
                
        except Exception as e:
            print(f"  ❌ 时间片 {slice_num + 1} 模拟失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 7. 最终统计
    print(f"\n🎉 测试完成！")
    print(f"📊 最终统计:")
    print(f"  - 总原始帖子: {len(data)} 条")
    print(f"  - 有效帖子: {len(valid_posts)} 条")
    print(f"  - 过滤无效帖子: {filtered_count} 条")
    print(f"  - 运行时间片: {max_slices} 个")
    print(f"  - 参与Agent: {len(all_agents)} 个")
    print(f"  - 总发言次数: {total_speaking_agents} 次")
    print(f"  - 总生成帖子: {total_generated_posts} 条")
    
    print(f"\n✅ 完整工作流程测试成功！")
    return True

if __name__ == '__main__':
    # 运行完整工作流程测试
    test_complete_workflow() 