#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数对比实验脚本
自动运行多组参数组合，并将结果保存到独立的txt文件中
"""

import os
import sys
import json
from datetime import datetime
from io import StringIO
from contextlib import redirect_stdout

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent_controller import AgentController
from world_state import WorldState
from time_manager import TimeSliceManager
from services import flatten_posts_recursive, filter_valid_posts

def run_single_experiment(w_pop, k, opinion_blocking, output_file):
    """
    运行单组参数实验并保存结果到文件
    
    Args:
        w_pop: 热度权重
        k: Sigmoid门控参数
        opinion_blocking: 立场容忍度
        output_file: 输出文件路径
    """
    # 计算相关性权重
    w_rel = 1.0 - w_pop
    
    # 创建输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"=== 参数对比实验 ===\n")
        f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参数配置:\n")
        f.write(f"  - 热度权重 (w_pop): {w_pop}\n")
        f.write(f"  - 相关性权重 (w_rel): {w_rel}\n")
        f.write(f"  - Sigmoid门控参数 (k): {k}\n")
        f.write(f"  - 立场容忍度 (opinion_blocking): {opinion_blocking}\n")
        f.write(f"\n{'='*50}\n\n")
        
        # 重定向stdout到StringIO，然后写入文件
        output_buffer = StringIO()
        
        try:
            with redirect_stdout(output_buffer):
                # 加载配置
                config_path = "config/simulation_config.json"
                with open(config_path, 'r', encoding='utf-8') as config_file:
                    config = json.load(config_file)
                
                # 创建世界状态
                world_state = WorldState()
                
                # 创建时间管理器
                time_manager = TimeSliceManager(config.get('time_config', {}))
                
                # 创建Agent控制器
                agent_controller = AgentController(
                    world_state=world_state,
                    time_manager=time_manager,
                    config=config
                )
                
                # 设置实验参数
                agent_controller.w_pop = w_pop
                agent_controller.w_rel = w_rel
                agent_controller.k = k
                agent_controller.opinion_blocking = opinion_blocking
                
                # 加载数据
                data_path = "data/real_data.json"
                with open(data_path, 'r', encoding='utf-8') as data_file:
                    data = json.load(data_file)
                
                # 扁平化帖子数据
                all_posts = flatten_posts_recursive(data)
                
                # 过滤有效帖子
                valid_posts = filter_valid_posts(all_posts)
                
                print(f"加载了 {len(valid_posts)} 个有效帖子")
                
                # 初始化Agents
                agent_controller.initialize_agents(config.get('agents', []))
                print(f"初始化了 {len(agent_controller.agents)} 个Agent")
                
                # 运行仿真
                max_time_slices = config.get('max_time_slices', 5)
                
                for time_slice in range(1, max_time_slices + 1):
                    print(f"\n=== 时间片 {time_slice} ===")
                    
                    # 更新Agent情绪
                    agent_controller.update_agent_emotions(valid_posts, time_slice)
                    
                    # 输出每个Agent的状态
                    for agent in agent_controller.agents:
                        print(f"Agent {agent.id}: 情绪={agent.emotion:.3f}, 立场={agent.stance:.3f}, 置信度={agent.confidence:.3f}")
                
                # 输出最终统计
                print(f"\n=== 实验完成 ===")
                print(f"参数组合: w_pop={w_pop}, w_rel={w_rel}, k={k}, opinion_blocking={opinion_blocking}")
                
        except Exception as e:
            print(f"实验运行出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 将输出写入文件
        output_content = output_buffer.getvalue()
        f.write(output_content)
        output_buffer.close()
        
        print(f"实验结果已保存到: {output_file}")

def run_all_experiments():
    """
    运行所有参数组合的实验
    """
    # 定义参数组合
    w_pop_values = [0.3, 0.5, 0.7, 0.8]
    k_values = [1, 2, 3]
    opinion_blocking_values = [0.2, 0.5]
    
    # 创建结果目录
    results_dir = "experiment_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    total_experiments = len(w_pop_values) * len(k_values) * len(opinion_blocking_values)
    current_experiment = 0
    
    print(f"开始运行 {total_experiments} 组参数对比实验...")
    print(f"结果将保存到 {results_dir} 目录")
    
    for w_pop in w_pop_values:
        for k in k_values:
            for opinion_blocking in opinion_blocking_values:
                current_experiment += 1
                
                # 生成文件名
                filename = f"result_wpop{w_pop}_k{k}_ob{opinion_blocking}.txt"
                output_path = os.path.join(results_dir, filename)
                
                print(f"\n[{current_experiment}/{total_experiments}] 运行实验: {filename}")
                print(f"参数: w_pop={w_pop}, k={k}, opinion_blocking={opinion_blocking}")
                
                # 运行实验
                run_single_experiment(w_pop, k, opinion_blocking, output_path)
                
                print(f"实验完成: {filename}")
    
    print(f"\n所有实验完成！共运行 {total_experiments} 组实验")
    print(f"结果文件保存在: {os.path.abspath(results_dir)}")
    
    # 生成实验总结
    summary_file = os.path.join(results_dir, "experiment_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"=== 参数对比实验总结 ===\n")
        f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总实验数: {total_experiments}\n\n")
        
        f.write("参数组合列表:\n")
        for w_pop in w_pop_values:
            for k in k_values:
                for opinion_blocking in opinion_blocking_values:
                    filename = f"result_wpop{w_pop}_k{k}_ob{opinion_blocking}.txt"
                    f.write(f"  - {filename}\n")
        
        f.write(f"\n实验参数范围:\n")
        f.write(f"  - 热度权重 (w_pop): {w_pop_values}\n")
        f.write(f"  - Sigmoid门控参数 (k): {k_values}\n")
        f.write(f"  - 立场容忍度 (opinion_blocking): {opinion_blocking_values}\n")
    
    print(f"实验总结已保存到: {summary_file}")

if __name__ == "__main__":
    run_all_experiments() 