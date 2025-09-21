#!/usr/bin/env python3
"""
社交仿真引擎主程序
整的仿真流程
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import time
import datetime
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
        
        # 检查是否跳过LLM
        self.skip_llm = config.get("skip_llm", False)
        if self.skip_llm:
            print("跳过LLM模式：不会调用大语言模型，仅生成prompt")
            self.llm_service = None
        else:
            llm_config = config.get("llm", {})
            self.llm_service = LLMServiceFactory.create_service(llm_config)
        
        # 创建Agent生成帖子的JSON文件 (在初始化Agent控制器之前)
        import datetime
        self.simulation_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # 保存时间戳供后续使用
        agent_posts_filename = f"agent_generated_posts_{self.simulation_timestamp}.json"
        self.agent_posts_file = agent_posts_filename
        
        # 初始化Agent帖子JSON文件
        import json
        with open(agent_posts_filename, 'w', encoding='utf-8') as f:
            json.dump({"simulation_info": {
                "timestamp": self.simulation_timestamp,
                "start_time": datetime.datetime.now().isoformat(),
                "log_file": f"simulation_log_{self.simulation_timestamp}.txt"
            }, "agent_posts": []}, f, ensure_ascii=False, indent=2)
        
        print(f"Agent帖子JSON文件: {agent_posts_filename}")
        
        # 初始化Agent控制器（不自动加载Agent）
        self.agents = []  # 空的Agent列表，等待外部添加
        self.agent_controller = AgentController(self.world_state, None, agent_posts_file=self.agent_posts_file)  # time_manager稍后设置
        
        # 配置Agent的LLM设置
        # 支持两种配置字段名：llm_config（前端发送）和 llm（传统字段）
        llm_config = config.get("llm_config", {}) or config.get("llm", {})
        if llm_config and llm_config.get("enabled", True):
            self.agent_controller.configure_llm_for_agents(llm_config)
            
        self.time_manager: Optional[TimeSliceManager] = None
        self.posts_per_slice = config.get("posts_per_slice", 30)
        self.current_slice = 0
        self.total_slices = 0
        self.simulation_results = []
        print("仿真引擎初始化完成")
        print("仿真引擎初始化完成")
    
    def _load_agent_configs(self) -> List[Dict[str, Any]]:
        """已废弃，直接返回空列表"""
        return []
    
    def load_initial_data(self, posts_file_path: str):
        """
        加载初始帖子数据（使用完整的数据处理流程）
        
        Args:
            posts_file_path: 帖子数据文件路径
        """
        try:
            # 1. 加载原始数据
            raw_posts = self.data_loader.load_post_data(posts_file_path)
            print(f"1. 原始数据加载: {len(raw_posts)} 个顶级帖子")
            
            # 2. 展开嵌套帖子结构
            all_posts = flatten_posts_recursive(raw_posts)
            print(f"2. 展开嵌套结构: {len(all_posts)} 条帖子")
            
            # 3. 过滤有效帖子
            valid_posts = filter_valid_posts(all_posts)
            print(f"3. 过滤有效帖子: {len(valid_posts)} 条帖子")
            
            if not valid_posts:
                print("没有有效的帖子数据，使用示例数据")
                self._load_sample_data()
                return
            
            # 4. 标准化帖子数据并添加到世界状态
            for post in valid_posts:
                normalized_post = self.world_state.normalize_post(post)
                self.world_state.add_post(normalized_post)
            
            # 5. 初始化时间管理器（使用处理后的数据）
            self.time_manager = TimeSliceManager(valid_posts, self.posts_per_slice)
            self.total_slices = self.time_manager.total_slices
            
            print(f"✅ 数据处理完成：{len(valid_posts)} 条有效帖子，{self.total_slices} 个时间片")
            
        except Exception as e:
            print(f"加载初始数据失败: {e}")
            # 使用示例数据
            self._load_sample_data()
    
    def _load_sample_data(self):
        """加载示例数据"""
        sample_posts = [
            {
                "id": "post_001",
                "content": "高热度政治话题讨论：最新政策变化引发热议",
                "author_id": "author_001",
                "heat": 80,
                "popularity": 80,
                "likes": 100,
                "shares": 50,
                "timestamp": "2024-01-01T10:00:00",
                "information_strength": 0.8,
                "emotion_score": 0.6,
                "stance_score": 0.7
            },
            {
                "id": "post_002",
                "content": "中等热度娱乐话题：新电影上映引关注",
                "author_id": "author_002",
                "heat": 60,
                "popularity": 60,
                "likes": 50,
                "shares": 20,
                "timestamp": "2024-01-01T10:30:00",
                "information_strength": 0.6,
                "emotion_score": 0.8,
                "stance_score": 0.5
            },
            {
                "id": "post_003",
                "content": "低热度科技话题：AI技术最新进展分享",
                "author_id": "author_003",
                "heat": 30,
                "popularity": 30,
                "likes": 10,
                "shares": 5,
                "timestamp": "2024-01-01T11:00:00",
                "information_strength": 0.5,
                "emotion_score": 0.4,
                "stance_score": 0.3
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
    
    def run_simulation(self, max_slices: Optional[int] = None, should_stop_callback=None):
        """
        运行仿真
        
        Args:
            max_slices: 最大时间片数（可选）
            should_stop_callback: 停止检查回调函数
        """
        if not self.time_manager:
            self._load_sample_data()
        
        if max_slices:
            self.total_slices = min(self.total_slices, max_slices)
        
        print(f"\n=== 开始仿真 ===")
        print(f"总时间片数: {self.total_slices}")
        print(f"Agent数量: {len(self.agent_controller.agents)}")
        
        # 创建详细日志文件
        import datetime
        # 使用初始化时保存的时间戳，确保与agent_posts文件时间戳一致
        log_filename = f"simulation_log_{self.simulation_timestamp}.txt"
        
        # 创建实时日志写入器
        class RealTimeLogger:
            def __init__(self, file_path, simulation_id=None):
                self.terminal = sys.stdout
                self.log_file = open(file_path, 'w', encoding='utf-8')
                self.simulation_id = simulation_id
                self.step_count = 0
                
            def write(self, message):
                self.terminal.write(message)
                self.log_file.write(message)
                self.log_file.flush()
                
                # 如果有仿真ID，同时更新仿真状态
                if self.simulation_id and hasattr(self, '_update_simulation_log'):
                    self._update_simulation_log(message)
                    
            def flush(self):
                self.terminal.flush()
                self.log_file.flush()
                
            def close(self):
                self.log_file.close()
                
            def log_step(self, step_type, details):
                """记录关键步骤"""
                self.step_count += 1
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                log_msg = f"\n[{timestamp}] 步骤 #{self.step_count} - {step_type}: {details}\n"
                self.write(log_msg)
        
        # 重定向输出到实时日志
        logger = RealTimeLogger(log_filename)
        sys.stdout = logger
        
        print(f"=== 详细日志记录开始 ===")
        print(f"日志文件: {log_filename}")
        print(f"包含: 所有LLM Prompt、响应、Agent状态变化")
        
        # === 前端元数据输出开始 ===
        print("\n=== SIMULATION_METADATA_START ===")
        
        # 输出仿真基本信息
        simulation_metadata = {
            "simulation_id": f"sim_{self.simulation_timestamp}",
            "name": self.config.get("simulation_name", f"仿真_{self.simulation_timestamp}"),
            "start_time": datetime.datetime.now().isoformat(),
            "status": "running",
            "total_time_slices": self.total_slices,
            "agent_count": len(self.agent_controller.agents),
            "posts_count": len(self.world_state.get_all_posts()),
            "config": {
                "w_pop": self.config.get("w_pop", 0.7),
                "k": self.config.get("k", 2),
                "skip_llm": self.config.get("skip_llm", False),
                "posts_per_slice": self.posts_per_slice
            },
            "agents": []
        }
        
        # 输出Agent信息
        for agent in self.agent_controller.agents:
            agent_info = {
                "id": agent.agent_id,
                "role_type": agent.role_type.value if hasattr(agent.role_type, 'value') else str(agent.role_type),
                "initial_emotion": getattr(agent, 'initial_emotion', 0.0),
                "initial_stance": getattr(agent, 'initial_stance', 0.0),
                "initial_confidence": getattr(agent, 'initial_confidence', 0.5),
                "attitude_firmness": getattr(agent, 'attitude_firmness', 0.5),
                "opinion_blocking": getattr(agent, 'opinion_blocking', 0.3),
                "activity_level": getattr(agent, 'activity_level', 0.7)
            }
            simulation_metadata["agents"].append(agent_info)
        
        # 输出时间片信息
        time_slices_info = []
        for i in range(self.total_slices):
            if self.time_manager:
                slice_posts = self.time_manager.get_slice(i)
                post_count = len(slice_posts)
                # 计算时间范围（简化版）
                time_range = f"T{i:02d}:00-T{i:02d}:59"
            else:
                post_count = 0
                time_range = f"T{i:02d}:00-T{i:02d}:59"
            
            time_slice_info = {
                "index": i,
                "time_range": time_range,
                "post_count": post_count,
                "description": f"时间片 {i+1}"
            }
            time_slices_info.append(time_slice_info)
        
        simulation_metadata["time_slices"] = time_slices_info
        
        # 输出JSON格式的元数据
        print(json.dumps(simulation_metadata, ensure_ascii=False, indent=2))
        print("=== SIMULATION_METADATA_END ===\n")
        
        start_time = time.time()
        
        # 获取所有Agent对象池（含未激活）
        all_agents = self.agent_controller.agents
        
        while self.current_slice < self.total_slices:
            # 检查是否应该停止仿真
            if should_stop_callback and should_stop_callback():
                print(f"\n仿真被用户停止，当前时间片: {self.current_slice + 1}")
                break
                
            print(f"\n--- 时间片 {self.current_slice + 1}/{self.total_slices} ---")
            
            # 获取当前时间片的原始帖子
            if self.time_manager:
                current_slice_posts = self.time_manager.get_slice(self.current_slice)
            else:
                current_slice_posts = []
            
            # 检查是否有预置的官方声明需要在此时间片发布
            pre_injected_events = self.config.get("pre_injected_events", [])
            official_statements = [
                event for event in pre_injected_events 
                if event.get("target_time_slice") == self.current_slice and 
                   event.get("is_official_statement", False)
            ]
            
            # 将官方声明注入到当前时间片
            if official_statements:
                print(f"🏛️ [官方声明] 在时间片 {self.current_slice} 发布 {len(official_statements)} 条官方声明")
                for statement in official_statements:
                    print(f"📢 官方声明: {statement.get('content', '')[:50]}...")
                    # 添加到当前时间片的帖子列表中
                    current_slice_posts.append(statement)
                    # 同时添加到世界状态中
                    self.world_state.add_post(statement)
                    # 保存官方声明到agent_posts文件
                    self._save_official_statement_to_posts_file(
                        statement.get('content', ''),
                        self.current_slice,
                        statement.get('annotation')  # 如果有LLM标注就传递
                    )
            
            print(f"本时间片帖子数量: {len(current_slice_posts)} (包含 {len(official_statements)} 条官方声明)")
            
            # 获取所有历史帖子
            all_posts = self.world_state.get_all_posts()
            
            # 1. 只筛选本轮已激活的Agent
            active_agents = [agent for agent in all_agents if getattr(agent, 'is_active', True)]
            print(f"活跃Agent数量: {len(active_agents)}")
            
            # 2. 执行时间片调度（只对活跃Agent）
            print(f"\n=== 开始Agent情绪更新和发帖判定 ===")
            
            # 检查是否有LLM配置
            llm_config = self.config.get("llm_config", {})
            
            # 为实时监控，启用所有Agent在所有时间片的LLM调用
            if llm_config.get("enabled", True):  # 如果LLM配置启用
                # 检查配置中是否指定了特定的启用模式
                if "enabled_agents" in llm_config or "enabled_timeslices" in llm_config:
                    # 使用配置文件中的设置（测试模式）
                    llm_config_for_agents = llm_config
                    enabled_agents_config = llm_config.get("enabled_agents", [])
                    enabled_timeslices_config = llm_config.get("enabled_timeslices", [])
                    print(f"[LLM Config] 测试模式 - 启用Agent: {enabled_agents_config}, 启用时间片: {enabled_timeslices_config}")
                else:
                    # 默认为所有Agent和所有时间片启用LLM（实时监控模式）
                    llm_config_for_agents = {
                        **llm_config,
                        "enabled_agents": [agent.agent_id for agent in active_agents],  # 所有活跃Agent
                        "enabled_timeslices": list(range(self.total_slices))  # 所有时间片
                    }
                    print(f"[LLM Config] 完整模式 - 为 {len(active_agents)} 个Agent在所有 {self.total_slices} 个时间片启用LLM调用")
            else:
                llm_config_for_agents = llm_config
                print(f"[LLM Config] LLM调用已禁用")
            
            # === 新增：意见领袖简报流程 ===
            # 生成宏观统计简报并让意见领袖优先阅读
            macro_summary = self.agent_controller.compute_macro_summary()
            print(f"[宏观简报] {macro_summary}")
            
            # 意见领袖读取简报并进行轻推情绪立场更新
            briefing_post, leader_statuses = self.agent_controller.leader_read_briefing(self.current_slice)
            for leader_id, leader_status in leader_statuses:
                print(f"[Leader] {leader_id} 读简报后状态: 情绪={leader_status.get('current_emotion', 0):.3f}, 立场={leader_status.get('current_stance', 0):.3f}")
            
            # 执行所有Agent的情绪更新和发帖判定
            self.agent_controller.update_agent_emotions(current_slice_posts, 
                                                      time_slice_index=self.current_slice,
                                                      llm_config=llm_config_for_agents)
            
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
                    # 处理Unix时间戳或ISO格式字符串
                    try:
                        if isinstance(anchor_ts, (int, float)):
                            # Unix时间戳
                            anchor_dt = datetime.datetime.fromtimestamp(anchor_ts)
                        else:
                            # ISO格式字符串
                            anchor_dt = datetime.datetime.fromisoformat(str(anchor_ts))
                    except (ValueError, TypeError):
                        # 如果时间戳处理失败，跳过激活检查
                        anchor_dt = None
                    
                    if anchor_dt:
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
        print(f"详细日志已保存到: {log_filename}")
        
        # === 前端完成状态元数据输出开始 ===
        print("\n=== SIMULATION_COMPLETION_METADATA_START ===")
        
        completion_metadata = {
            "simulation_id": f"sim_{self.simulation_timestamp}",
            "status": "completed",
            "end_time": datetime.datetime.now().isoformat(),
            "duration_seconds": elapsed_time,
            "completed_time_slices": self.current_slice,
            "total_time_slices": self.total_slices,
            "final_posts_count": self.world_state.get_posts_count(),
            "final_agent_states": []
        }
        
        # 输出最终Agent状态
        for agent in self.agent_controller.agents:
            final_agent_state = {
                "id": agent.agent_id,
                "final_emotion": getattr(agent, 'current_emotion', 0.0),
                "final_stance": getattr(agent, 'current_stance', 0.0),
                "final_confidence": getattr(agent, 'current_confidence', 0.5),
                "posts_generated": getattr(agent, 'posts_count', 0),
                "total_interactions": getattr(agent, 'interaction_count', 0)
            }
            completion_metadata["final_agent_states"].append(final_agent_state)
        
        # 输出JSON格式的完成元数据
        print(json.dumps(completion_metadata, ensure_ascii=False, indent=2))
        print("=== SIMULATION_COMPLETION_METADATA_END ===")
        
        # 恢复标准输出并关闭日志文件
        sys.stdout = logger.terminal
        logger.close()
        
        print(f"仿真完成！详细日志已保存到: {log_filename}")
        
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
    
    def _save_official_statement_to_posts_file(self, statement_content, target_slice, annotation=None):
        """将官方声明保存到agent_generated_posts文件中"""
        if not hasattr(self, 'agent_posts_file') or not self.agent_posts_file:
            print("   ⚠️ 没有找到agent_posts_file，跳过保存官方声明")
            return
            
        try:
            import json
            
            # 读取现有数据
            with open(self.agent_posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建官方声明对象
            official_statement = {
                "content": statement_content,
                "annotation": annotation or statement_content,  # 如果有LLM标注就使用，否则使用原内容
                "type": "official_statement",
                "target_slice": target_slice,
                "generation_info": {
                    "source": "official_government",
                    "statement_type": "batch_official_statement",
                    "generation_time": datetime.datetime.now().isoformat(),
                    "current_slice": getattr(self, 'current_slice', 'unknown'),
                    "injection_method": "pre_injected_events"
                }
            }
            
            # 添加到帖子列表
            data['agent_posts'].append(official_statement)
            
            # 写回文件
            with open(self.agent_posts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"   📝 官方声明已保存到JSON文件: {self.agent_posts_file}")
            
        except Exception as e:
            print(f"   ⚠️ 保存官方声明到JSON文件失败: {e}")


def main(w_pop=0.7, k=2, save_log=False):
    print("=== 社交模拟引擎主程序（新版）===")
    print(f"[参数] w_pop={w_pop}, k={k}")
    
    # 创建Agent生成帖子的JSON文件
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_posts_filename = f"agent_generated_posts_{timestamp}.json"
    
    # 初始化Agent帖子JSON文件
    import json
    with open(agent_posts_filename, 'w', encoding='utf-8') as f:
        json.dump({"simulation_info": {
            "timestamp": timestamp,
            "start_time": datetime.datetime.now().isoformat(),
            "mode": "main_function_test"
        }, "agent_posts": []}, f, ensure_ascii=False, indent=2)
    
    print(f"Agent帖子JSON文件: {agent_posts_filename}")
    
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
    agent_controller = AgentController(world_state, time_manager, w_pop=w_pop, k=k, agent_posts_file=agent_posts_filename)
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