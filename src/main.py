#!/usr/bin/env python3
"""
社交仿真引擎主程序
整合所有模块，实现完整的仿真流程
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import time
from typing import Dict, List, Any, Optional
from src.time_manager import TimeSliceManager
from src.world_state import WorldState
from src.agent_controller import AgentController
from src.services import DataLoader, flatten_posts_recursive, filter_valid_posts, load_agents_from_file
from src.llm_service import LLMServiceFactory
from src.agent import Agent, RoleType


class SimulationEngine:
    """仿真引擎主类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化仿真引擎
        
        Args:
            config: 仿真配置
        """
        self.config = config
        self.data_loader = DataLoader()
        self.world_state = WorldState()
        llm_config = config.get("llm", {})
        self.llm_service = LLMServiceFactory.create_service(llm_config)
        # 从文件加载agent
        self.agents = load_agents_from_file('config/agents.json')
        self.agent_controller = AgentController(self.world_state, None)  # time_manager稍后设置
        for agent in self.agents:
            self.agent_controller.add_agent(agent)
        self.time_manager: Optional[TimeSliceManager] = None
        self.posts_per_slice = config.get("posts_per_slice", 50)
        self.current_slice = 0
        self.total_slices = 0
        self.simulation_results = []
        print("仿真引擎初始化完成")
    
    def _load_agent_configs(self) -> List[Dict[str, Any]]:
        """已废弃，直接返回空列表"""
        return []
    
    def load_initial_data(self, posts_file_path: str):
        """
        加载初始帖子数据
        
        Args:
            posts_file_path: 帖子数据文件路径
        """
        try:
            posts_data = self.data_loader.load_post_data(posts_file_path)
            
            # 将初始帖子添加到世界状态
            for post in posts_data:
                self.world_state.add_post(post)
            
            # 初始化时间管理器
            self.time_manager = TimeSliceManager(posts_data, self.posts_per_slice)
            self.total_slices = self.time_manager.total_slices
            
            print(f"加载初始数据完成：{len(posts_data)} 条帖子，{self.total_slices} 个时间片")
            
        except Exception as e:
            print(f"加载初始数据失败: {e}")
            # 使用示例数据
            self._load_sample_data()
    
    def _load_sample_data(self):
        """加载示例数据"""
        sample_posts = [
            {
                "id": "post_001",
                "content": "高热度政治话题讨论",
                "author_id": "author_001",
                "heat": 80,
                "likes": 100,
                "shares": 50,
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "id": "post_002",
                "content": "中等热度娱乐话题",
                "author_id": "author_002",
                "heat": 60,
                "likes": 50,
                "shares": 20,
                "timestamp": "2024-01-01T10:30:00"
            },
            {
                "id": "post_003",
                "content": "低热度科技话题",
                "author_id": "author_003",
                "heat": 30,
                "likes": 10,
                "shares": 5,
                "timestamp": "2024-01-01T11:00:00"
            }
        ]
        
        for post in sample_posts:
            self.world_state.add_post(post)
        
        self.time_manager = TimeSliceManager(sample_posts, self.posts_per_slice)
        self.total_slices = self.time_manager.total_slices
        print(f"使用示例数据：{len(sample_posts)} 条帖子，{self.total_slices} 个时间片")
    
    def inject_event(self, event_content: str, event_heat: int = 80):
        """
        注入突发事件
        
        Args:
            event_content: 事件内容
            event_heat: 事件热度
        """
        event_post = {
            "content": event_content,
            "author_id": "system_event",
            "heat": event_heat,
            "likes": 0,
            "shares": 0,
            "is_event": True,
            "priority": 100
        }
        
        event_id = self.world_state.inject_event(event_post)
        print(f"注入突发事件: {event_id}")
        return event_id
    
    def run_simulation(self, max_slices: Optional[int] = None):
        """
        运行仿真
        
        Args:
            max_slices: 最大时间片数（可选）
        """
        if not self.time_manager:
            self._load_sample_data()
        
        if max_slices:
            self.total_slices = min(self.total_slices, max_slices)
        
        print(f"\n=== 开始仿真 ===")
        print(f"总时间片数: {self.total_slices}")
        print(f"Agent数量: {len(self.agent_controller.agents)}")
        
        start_time = time.time()
        
        # 获取所有Agent对象池（含未激活）
        all_agents = self.agent_controller.agents
        
        while self.current_slice < self.total_slices:
            print(f"\n--- 时间片 {self.current_slice + 1}/{self.total_slices} ---")
            
            # 获取当前时间片的帖子
            if self.time_manager:
                current_slice_posts = self.time_manager.get_slice(self.current_slice)
            else:
                current_slice_posts = []
            
            # 获取所有历史帖子
            all_posts = self.world_state.get_all_posts()
            
            # 1. 只筛选本轮已激活的Agent
            active_agents = [agent for agent in all_agents if getattr(agent, 'is_active', True)]
            
            # 2. 执行时间片调度（只对活跃Agent）
            # 这里假设run_time_slice已被移除，直接用update_agent_emotions
            self.agent_controller.update_agent_emotions(current_slice_posts, time_slice_index=self.current_slice)
            
            # 3. 记录结果
            self.simulation_results.append({
                "slice_index": self.current_slice,
                "results": {}, # No specific results to record here as update_agent_emotions doesn't return them
                "total_posts": len(all_posts),
                "new_posts_count": len(current_slice_posts)
            })
            
            # 4. 时间片结束后，检查是否有Agent需要激活（下轮生效）
            if current_slice_posts:
                last_post = current_slice_posts[-1]
                anchor_ts = last_post.get("timestamp")
                if anchor_ts:
                    from datetime import datetime
                    anchor_dt = datetime.fromisoformat(str(anchor_ts))
                    for agent in all_agents:
                        if not getattr(agent, 'is_active', True) and getattr(agent, 'join_timestamp', None):
                            if agent.join_timestamp <= anchor_dt:
                                agent.is_active = True  # 下轮生效
            
            # 5. 移动到下一个时间片
            self.current_slice += 1
            
            # 简单的进度显示
            if self.current_slice % 5 == 0:
                elapsed = time.time() - start_time
                print(f"进度: {self.current_slice}/{self.total_slices} ({elapsed:.1f}s)")
        
        elapsed_time = time.time() - start_time
        print(f"\n=== 仿真完成 ===")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"最终帖子数: {self.world_state.get_posts_count()}")
        
        return self.simulation_results
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """获取仿真摘要"""
        total_actions = sum(
            result["results"]["generated_actions"] 
            for result in self.simulation_results
        )
        
        return {
            "total_slices": self.total_slices,
            "total_agents": len(self.agent_controller.agents),
            "total_posts": self.world_state.get_posts_count(),
            "total_actions": total_actions,
            "event_posts": len(self.world_state.get_event_posts())
        }
    
    def save_results(self, output_file: str):
        """保存仿真结果"""
        results = {
            "summary": self.get_simulation_summary(),
            "simulation_results": self.simulation_results,
            "agent_generated_posts": self.world_state.get_all_posts()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_file}")


def main(w_pop=0.7, k=2, save_log=False):
    print("=== 社交模拟引擎主程序（新版）===")
    print(f"[参数] w_pop={w_pop}, k={k}")
    # 1. 加载原始帖子数据
    print("\n1. 加载原始帖子数据...")
    data_loader = DataLoader()
    try:
        raw_posts = data_loader.load_post_data('../data/postdata.json')
        print(f"✅ 成功加载 {len(raw_posts)} 条原始帖子")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    # 2. 展开嵌套帖子
    print("\n2. 展开嵌套帖子...")
    all_posts = flatten_posts_recursive(raw_posts)
    print(f"✅ 展开后共 {len(all_posts)} 条帖子")
    # 3. 过滤有效帖子
    print("\n3. 过滤有效帖子...")
    valid_posts = filter_valid_posts(all_posts)
    print(f"✅ 过滤后剩余 {len(valid_posts)} 条有效帖子")
    if not valid_posts:
        print("没有有效的帖子数据，退出主程序")
        return
    # 4. 字段标准化
    print("\n4. 字段标准化...")
    world_state = WorldState()
    normalized_posts = [world_state.normalize_post(post) for post in valid_posts]
    print(f"✅ 完成 {len(normalized_posts)} 条帖子的标准化")
    # 5. 时间片划分
    print("\n5. 时间片划分...")
    posts_per_timeslice = 30
    num_timeslices = 4
    time_manager = TimeSliceManager(normalized_posts, posts_per_timeslice)
    print(f"✅ 时间片大小: {posts_per_timeslice}")
    print(f"✅ 总时间片数: {time_manager.total_slices}")
    # 6. 创建Agent控制器
    print("\n6. 创建Agent控制器...")
    agent_controller = AgentController(world_state, time_manager, w_pop=w_pop, k=k)
    # 7. 创建测试Agent
    print("\n7. 创建测试Agent...")
    test_agents = load_agents_from_file('config/agents.json')
    for agent in test_agents:
        agent_controller.add_agent(agent)
        print(f"✅ 创建Agent: {agent}")
    # 8. 运行模拟
    print("\n8. 开始模拟...")
    for timeslice in range(min(num_timeslices, time_manager.total_slices)):
        print(f"\n--- 时间片 {timeslice + 1} ---")
        for agent in agent_controller.agents:
            agent.snapshot_state()
        current_posts = time_manager.get_slice(timeslice)
        print(f"处理 {len(current_posts)} 条帖子")
        # 新增：统计每个Agent阅读的帖子数量
        agent_read_counts = {}
        agent_post_scores = {}
        # 统计每个帖子被哪些agent选中
        post_read_by_agents = {}
        # 用新流程更新情绪，并收集分数
        all_agent_scores = agent_controller.update_agent_emotions(current_posts)
        for agent in agent_controller.agents:
            # 重新统计阅读数
            personalized_feed, post_scores = agent_controller._generate_personalized_feed(agent, current_posts)
            agent_read_counts[agent.agent_id] = len(personalized_feed)
            agent_post_scores[agent.agent_id] = post_scores
            for idx, (pid, score_pop, score_rel, final_score, prob) in enumerate(post_scores):
                if pid not in post_read_by_agents:
                    post_read_by_agents[pid] = []
                if personalized_feed and any(p.get('id', p.get('post_id', 'unknown')) == pid for p in personalized_feed):
                    post_read_by_agents[pid].append((agent.agent_id, final_score, prob))
        print(f"\n时间片 {timeslice + 1} 结束，Agent状态:")
        for agent in agent_controller.agents:
            emotion_fluctuation = abs(agent.current_emotion - agent.last_emotion)
            stance_fluctuation = abs(agent.current_stance - agent.last_stance)
            total_fluctuation = emotion_fluctuation + stance_fluctuation
            print(f"  {agent.agent_id}: 情绪={agent.current_emotion:.3f}(波动{emotion_fluctuation:.3f}), "
                  f"立场={agent.current_stance:.3f}(波动{stance_fluctuation:.3f}), "
                  f"置信度={agent.current_confidence:.3f}, 总波动={total_fluctuation:.3f}, "
                  f"本时间片阅读{agent_read_counts[agent.agent_id]}条帖子")
            if agent.should_post():
                print(f"    -> 决定发帖！")
            else:
                print(f"    -> 不发帖")
        # 输出每个帖子被哪些agent选中及分数
        print(f"\n[分析] 本时间片每个帖子被选中的情况：")
        for pid, agent_list in post_read_by_agents.items():
            if agent_list:
                agent_str = ", ".join([f"{aid}(Final={fs:.3f},P={prob:.2f})" for aid, fs, prob in agent_list])
                print(f"  帖子{pid}: 被 {len(agent_list)} 个Agent选中 -> {agent_str}")
    print("\n=== 模拟完成 ===")


if __name__ == "__main__":
    main() 