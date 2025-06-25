#!/usr/bin/env python3
"""
社交仿真引擎主程序
整合所有模块，实现完整的仿真流程
"""

import json
import time
from typing import Dict, List, Any, Optional
from src.time_manager import TimeSliceManager
from src.world_state import WorldState
from src.agent_controller import AgentController
from src.services import DataLoader
from src.llm_service import LLMServiceFactory


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
        
        # 初始化各个模块
        self.world_state = WorldState()
        
        # 创建LLM服务
        llm_config = config.get("llm", {})
        self.llm_service = LLMServiceFactory.create_service(llm_config)
        
        # 加载Agent配置
        agent_configs = self._load_agent_configs()
        self.agent_controller = AgentController(
            agent_configs=agent_configs,
            world_state=self.world_state,
            llm_service=self.llm_service
        )
        
        # 初始化时间管理器（稍后设置）
        self.time_manager: Optional[TimeSliceManager] = None
        self.posts_per_slice = config.get("posts_per_slice", 50)
        
        # 仿真状态
        self.current_slice = 0
        self.total_slices = 0
        self.simulation_results = []
        
        print("仿真引擎初始化完成")
    
    def _load_agent_configs(self) -> List[Dict[str, Any]]:
        """加载Agent配置"""
        agent_config_path = self.config.get("agent_config_path")
        if agent_config_path:
            try:
                agent_data = self.data_loader.load_agent_config(agent_config_path)
                return agent_data.get("agents", [])
            except Exception as e:
                print(f"加载Agent配置失败: {e}")
                return self._get_default_agent_configs()
        else:
            return self._get_default_agent_configs()
    
    def _get_default_agent_configs(self) -> List[Dict[str, Any]]:
        """获取默认Agent配置（调整了发帖概率和兴趣参数）"""
        return [
            {
                "agent_id": "leader_001",
                "type": "意见领袖",
                "stance": 0.8,
                "interests": ["政治", "经济"],
                "influence": 2.0,
                "post_probability": 0.6,  # 意见领袖发帖概率较高
                "max_posts_per_slice": 3
            },
            {
                "agent_id": "rule_001",
                "type": "规则Agent",
                "stance": 0.5,
                "interests": ["规则", "秩序"],
                "influence": 1.5,
                "post_probability": 0.4,  # 规则Agent中等发帖概率
                "max_posts_per_slice": 2
            },
            {
                "agent_id": "user_001",
                "type": "普通用户",
                "stance": 0.3,
                "interests": ["娱乐", "科技"],
                "influence": 1.0,
                "post_probability": 0.2,  # 普通用户发帖概率较低
                "max_posts_per_slice": 1
            },
            {
                "agent_id": "user_002",
                "type": "普通用户",
                "stance": 0.7,
                "interests": ["体育", "健康"],
                "influence": 1.0,
                "post_probability": 0.25,  # 普通用户发帖概率较低
                "max_posts_per_slice": 1
            }
        ]
    
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
        print(f"Agent数量: {self.agent_controller._get_total_agents_count()}")
        
        start_time = time.time()
        
        # 获取所有Agent对象池（含未激活）
        all_agents = []
        for agent_type, agent_list in self.agent_controller.agents.items():
            all_agents.extend(agent_list)
        
        while self.current_slice < self.total_slices:
            print(f"\n--- 时间片 {self.current_slice + 1}/{self.total_slices} ---")
            
            # 获取当前时间片的帖子
            current_slice_posts = self.time_manager.get_slice(self.current_slice)
            
            # 获取所有历史帖子
            all_posts = self.world_state.get_all_posts()
            
            # 1. 只筛选本轮已激活的Agent
            active_agents = [agent for agent in all_agents if getattr(agent, 'is_active', True)]
            
            # 2. 执行时间片调度（只对活跃Agent）
            slice_results = self.agent_controller.run_time_slice(
                active_agents, self.world_state, self.llm_service
            )
            
            # 3. 记录结果
            self.simulation_results.append({
                "slice_index": self.current_slice,
                "results": slice_results,
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
            "total_agents": self.agent_controller._get_total_agents_count(),
            "total_posts": self.world_state.get_posts_count(),
            "total_actions": total_actions,
            "event_posts": len(self.world_state.get_event_posts())
        }
    
    def save_results(self, output_file: str):
        """保存仿真结果"""
        results = {
            "summary": self.get_simulation_summary(),
            "simulation_results": self.simulation_results,
            "final_posts": self.world_state.get_all_posts()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_file}")


def main():
    """主函数"""
    # 仿真配置
    config = {
        "posts_per_slice": 10,  # 每个时间片的帖子数
        
        # LLM配置
        "llm": {
            "model_name": "qwen/Qwen2.5-0.5B-Instruct",  # 使用较小的模型
            "use_mock": True,  # 默认使用Mock模式
            "api_key": None
        },
        
        # Agent配置路径（None表示使用默认配置）
        "agent_config_path": None
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    
    # 加载初始数据（如果有数据文件的话）
    # engine.load_initial_data("data/posts.json")
    
    # 注入一个突发事件（可选）
    # engine.inject_event("重大新闻：某项政策即将出台", 90)
    
    # 运行仿真
    results = engine.run_simulation(max_slices=3)  # 限制为3个时间片用于测试
    
    # 显示摘要
    summary = engine.get_simulation_summary()
    print(f"\n仿真摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 保存结果（可选）
    # engine.save_results("simulation_results.json")


if __name__ == "__main__":
    main() 