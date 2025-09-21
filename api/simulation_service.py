from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import threading
import time
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from src.agent_controller import AgentController
from src.main import SimulationEngine
from .environment_service import load_environment_config
from simulation_log_extractor import SimulationLogExtractor, create_frontend_api_adapter

# 创建前端API适配器实例
frontend_adapter = create_frontend_api_adapter()

simulation_bp = Blueprint('simulation', __name__)

class SimulationManager:
    """仿真管理器，负责启动、管理和存储仿真"""
    
    def __init__(self):
        self.simulations = {}
        self.stop_flags = {}  # 新增：用于控制仿真停止的标志
    
    def start_simulation(self, config, agent_configs):
        """启动仿真"""
        simulation_id = str(uuid.uuid4())
        
        # 合并环境配置
        env_config = load_environment_config()
        merged_config = {**env_config, **config}
        
        # 创建仿真配置
        simulation_config = {
            "id": simulation_id,
            "config": merged_config,
            "agent_configs": agent_configs,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "events": [],
            "results": None,
            "detailed_log": ""  # 新增：存储详细日志
        }
        
        self.simulations[simulation_id] = simulation_config
        
        # 初始化停止标志
        self.stop_flags[simulation_id] = False
        
        # 在后台线程中运行仿真
        thread = threading.Thread(
            target=self._run_simulation_background,
            args=(simulation_id, merged_config, agent_configs)
        )
        thread.start()
        
        return simulation_id
    
    def _run_simulation_background(self, simulation_id, config, agent_configs):
        """后台运行仿真"""
        try:
            simulation_config = self.simulations[simulation_id]
            simulation_config["status"] = "running"
            
            # 🔥 实时监控模式：不拦截输出，让实时日志文件正常工作
            print("=== 社交仿真引擎（Web版本 - 实时监控模式）===")
            print(f"仿真ID: {simulation_id}")
            print(f"使用主系统代码，LLM启用状态：{not config.get('skip_llm', False)}")
            print(f"\n[参数] w_pop={config.get('w_pop', 0.7)}, k={config.get('k', 2)}")
            print(f"[配置] posts_per_slice={config.get('posts_per_slice', 50)}")
            print(f"[模式] max_slices={config.get('max_slices', 'unlimited')}")
            print(f"[时间] 开始时间: {simulation_config['start_time']}")
            print(f"💡 实时日志将保存到: simulation_log_*.txt")
            
            # 创建仿真引擎，传入完整配置
            engine_config = {
                "posts_per_slice": config.get("posts_per_slice", 50),
                "llm": config.get("llm", {}),
                "w_pop": config.get("w_pop", 0.7),
                "k": config.get("k", 2),
                "skip_llm": config.get("skip_llm", False),  # 新增：跳过LLM调用的配置
                "llm_config": config.get("llm_config", {}),  # 新增：LLM测试配置
                "pre_injected_events": config.get("pre_injected_events", [])  # 🔥 修复：传入预置官方声明事件
            }
            
            # 🔍 调试信息：检查是否有预置官方声明
            pre_injected_events = config.get("pre_injected_events", [])
            if pre_injected_events:
                print(f"🔥 [官方声明] 检测到 {len(pre_injected_events)} 个预置官方声明事件：")
                for i, event in enumerate(pre_injected_events):
                    print(f"   事件 {i+1}: 时间片 {event.get('target_time_slice', '未知')}, 内容: {event.get('content', '未设置')[:50]}...")
                print(f"🚀 [重要] 这是一个完全重新运行的仿真，将从头开始执行所有时间片！")
            else:
                print("ℹ️  [官方声明] 无预置官方声明事件")
            
            # 🔍 显示仿真类型和配置
            max_slices = config.get("max_slices")
            if max_slices:
                print(f"⚠️  [限制模式] 最大时间片数: {max_slices}")
            else:
                print(f"✅ [完整模式] 将运行所有可用时间片，预计需要15-30分钟")
                
            engine = SimulationEngine(engine_config)
            
            # 如果有LLM配置，设置环境变量
            # 支持两种配置字段名：llm 和 llm_config（前端发送的是llm_config）
            llm_api_config = config.get("llm_config", {}) or config.get("llm", {})
            if llm_api_config.get("api_key"):
                import os
                os.environ['LLM_API_KEY'] = llm_api_config['api_key']
                os.environ['LLM_ENDPOINT'] = llm_api_config.get('base_url', llm_api_config.get('endpoint', ''))
                os.environ['LLM_MODEL'] = llm_api_config.get('model', '')
                print(f"✅ 已设置LLM环境变量：")
                print(f"   - API_KEY: {'*' * len(llm_api_config['api_key'][:8])}...{llm_api_config['api_key'][-4:]}")
                print(f"   - ENDPOINT: {llm_api_config.get('base_url', llm_api_config.get('endpoint', ''))}")
                print(f"   - MODEL: {llm_api_config.get('model', '')}")
        
            # 设置Agent控制器参数
            engine.agent_controller.w_pop = config.get("w_pop", 0.7)
            engine.agent_controller.k = config.get("k", 2)
            
            print(f"\n=== Agent配置 ===")
            print(f"总共选择了 {len(agent_configs)} 个Agent:")
            
            # 添加选中的Agents
            for agent_config in agent_configs:
                from src.agent import Agent, RoleType
                # 将字符串角色类型转换为枚举
                role_type = RoleType.ORDINARY_USER
                if agent_config.get("role_type") == "opinion_leader":
                    role_type = RoleType.OPINION_LEADER
                elif agent_config.get("role_type") == "bot":
                    role_type = RoleType.BOT
                
                agent = Agent(
                    agent_id=agent_config["agent_id"],
                    role_type=role_type,
                    attitude_firmness=agent_config.get("attitude_firmness", 0.5),
                    opinion_blocking=agent_config.get("opinion_blocking", 0.1),
                    activity_level=agent_config.get("activity_level", 0.5),
                    initial_emotion=agent_config.get("initial_emotion", 0.0),
                    initial_stance=agent_config.get("initial_stance", 0.0),
                    initial_confidence=agent_config.get("initial_confidence", 0.5)
                )
                engine.agent_controller.add_agent(agent)
                engine.agents.append(agent)  # 同时更新SimulationEngine的agents列表
                print(f"✅ 创建Agent: {agent}")
            
            print(f"\n=== 开始仿真流程 ===")
            # 加载数据并运行仿真
            print("正在加载初始数据...")
            import os
            data_file = 'data/postdata.json'
            if os.path.exists(data_file):
                engine.load_initial_data(data_file)
                print(f"从 {data_file} 加载数据完成，总时间片数: {engine.total_slices}")
            else:
                print(f"数据文件 {data_file} 不存在，使用示例数据")
                # 触发示例数据加载
                engine._load_sample_data()
                print(f"示例数据加载完成，总时间片数: {engine.total_slices}")
            
            # 确定最大时间片数
            max_slices = config.get("max_slices")
            if max_slices:
                print(f"限制最大时间片数为: {max_slices}")
                
            # 创建停止检查回调
            def should_stop():
                return self.stop_flags.get(simulation_id, False)
            
            print("开始执行仿真...")
            print("🚀 实时监控已启动，详细日志将实时写入文件！")
            if max_slices:
                results = engine.run_simulation(max_slices=max_slices, should_stop_callback=should_stop)
            else:
                results = engine.run_simulation(should_stop_callback=should_stop)
            print("仿真执行完成")
        
            # 查找生成的日志文件
            import glob
            log_files = glob.glob("simulation_log_*.txt")
            latest_log = ""
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                print(f"📁 实时日志已保存到: {latest_log}")
                
                # 读取日志文件内容（用于Web界面显示）
                try:
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        detailed_log = f.read()
                except Exception as e:
                    detailed_log = f"读取日志文件失败: {e}"
            else:
                detailed_log = "未找到实时日志文件"
        
            # 保存结果
            simulation_config["status"] = "completed"
            simulation_config["detailed_log"] = detailed_log  # 保存详细日志
            simulation_config["log_file"] = latest_log  # 新增：日志文件路径
            simulation_config["results"] = {
                "total_slices": engine.current_slice,
                "agent_count": len(agent_configs),
                "duration": 0,  # 简化处理，不依赖results的结构
                "simulation_data": results,
                "agent_states": self._get_agent_states(engine.agent_controller)
            }
            
            # 清理停止标志
            if simulation_id in self.stop_flags:
                del self.stop_flags[simulation_id]
            
        except Exception as e:
            simulation_config = self.simulations[simulation_id]
            simulation_config["status"] = "error"
            simulation_config["error"] = str(e)
            # 清理停止标志
            if simulation_id in self.stop_flags:
                del self.stop_flags[simulation_id]
            print(f"仿真运行错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_agent_states(self, agent_controller):
        """获取所有Agent的最终状态"""
        agent_states = []
        for agent in agent_controller.agents:
            agent_states.append({
                "agent_id": agent.agent_id,
                "role_type": agent.role_type.value,
                "current_emotion": agent.current_emotion,
                "current_stance": agent.current_stance,
                "current_confidence": agent.current_confidence,
                "activity_level": agent.activity_level
            })
        return agent_states
    
    def get_simulation_status(self, simulation_id):
        """获取仿真状态"""
        return self.simulations.get(simulation_id, None)
    
    def stop_simulation(self, simulation_id):
        """停止仿真"""
        if simulation_id not in self.simulations:
            return False
        
        simulation_config = self.simulations[simulation_id]
        if simulation_config["status"] == "running":
            # 设置停止标志
            self.stop_flags[simulation_id] = True
            simulation_config["status"] = "stopped"
            return True
        
        return False
    
    def inject_event(self, simulation_id, event_data):
        """注入突发事件"""
        if simulation_id not in self.simulations:
            return {"success": False, "error": "仿真不存在"}
        
        simulation_config = self.simulations[simulation_id]
        if simulation_config["status"] == "running":
            # 仿真运行中，添加到事件队列
            if "events" not in simulation_config:
                simulation_config["events"] = []
            simulation_config["events"].append(event_data)
            return {"success": True, "event_id": event_data.get("id", "unknown")}
        else:
            return {"success": False, "error": "仿真已完成，无法注入事件"}
    
    def _create_official_statement_data(self, statement_config):
        """创建官方声明数据结构，包含LLM数据标记"""
        import time
        timestamp = int(time.time())
        
        # 根据声明类型设置不同的权重
        statement_type = statement_config.get("statement_type", "clarification")
        authority_level = statement_config.get("authority_level", "high")
        content = statement_config.get("content", "")
        
        # 调用LLM进行数据标记
        llm_annotations = self._annotate_with_llm(content)
        
        # 权威性映射到数值参数
        authority_mapping = {
            "high": {"priority": 999, "popularity": 9999},
            "medium": {"priority": 500, "popularity": 5000}, 
            "low": {"priority": 100, "popularity": 1000}
        }
        
        authority_params = authority_mapping.get(authority_level, authority_mapping["high"])
        
        # 声明类型影响情绪立场（作为后备，如果LLM标记失败时使用）
        type_effects = {
            "clarification": {"emotion_impact": 0.1, "stance_impact": 0.0},  # 澄清：轻微正面
            "refutation": {"emotion_impact": -0.2, "stance_impact": 0.3},   # 辟谣：负面情绪，正面立场
            "official_notice": {"emotion_impact": 0.0, "stance_impact": 0.1}  # 通知：中性偏正
        }
        
        type_params = type_effects.get(statement_type, type_effects["clarification"])
        
        return {
            "id": f"official_statement_{timestamp}",
            "mid": f"OFFICIAL_STMT_{timestamp}",  # 特殊标识
            "pid": f"official_parent_{timestamp}",
            "author_id": "official_authority",
            "user_id": "official_authority", 
            "content": content,
            "t": timestamp,
            "timestamp": timestamp,
            
            # 官方声明的特殊属性
            "is_official_statement": True,
            "is_hurricane": True,  # 保持兼容性
            "is_event": True,
            "force_read": True,
            "statement_type": statement_type,
            "authority_level": authority_level,
            
            # 影响参数（优先使用LLM标记结果）
            "priority": authority_params["priority"],
            "information_strength": llm_annotations.get("information_strength", 0.8),
            "popularity": authority_params["popularity"],
            "emotion_score": llm_annotations.get("emotion_score", type_params["emotion_impact"]),
            "stance_score": llm_annotations.get("stance_score", type_params["stance_impact"]),
            "stance_category": llm_annotations.get("stance_category", "NEUTRAL_MEDIATING"),
            "stance_confidence": llm_annotations.get("stance_confidence", 0.7),
            "keywords": llm_annotations.get("keywords", [statement_type, "官方声明"]),
            
            # 帖子结构字段（保证能被正常feed给agents）
            "uid": "official_authority",
            "name": "官方权威机构",
            "original_text": content,
            "text": content,
            "children": [],  # 官方声明通常是顶级帖子
            
            # 目标时间片
            "target_time_slice": statement_config.get("target_time_slice", 0),
            
            # 生成信息
            "generation_info": {
                "agent_id": "official_authority",
                "agent_role": "official",
                "agent_emotion": 0.0,
                "agent_stance": 0.1,  # 轻微正面立场
                "agent_confidence": 1.0,
                "generation_time": datetime.now().isoformat(),
                "timestep": statement_config.get("target_time_slice", 0),
                "is_official_statement": True,
                "llm_annotated": llm_annotations.get("success", False)
            }
        }

    def _annotate_with_llm(self, content):
        """使用LLM对官方声明内容进行数据标记，重用现有的promptdataprocess.txt模板"""
        import os
        import requests
        import json
        
        # 检查LLM配置
        api_key = os.getenv('LLM_API_KEY')
        endpoint = os.getenv('LLM_ENDPOINT')
        model = os.getenv('LLM_MODEL', 'deepseek-v3')
        
        if not api_key or not endpoint:
            print(f"[LLM标记] 未配置LLM API，跳过自动标记")
            return {"success": False, "error": "LLM未配置"}
        
        # 读取现有的promptdataprocess模板
        try:
            with open('data/promptdataprocess.txt', 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"[LLM标记] 未找到 data/promptdataprocess.txt 文件")
            return {"success": False, "error": "Prompt模板文件未找到"}
        
        # 为官方声明构建prompt（省略对话上下文，直接标注官方声明内容）
        # 替换模板中的目标帖子为官方声明内容
        annotation_prompt = template.replace(
            '[目标帖子 (回复 4)]: 走正常途径不如闹来钱多又快',
            f'[目标帖子 (官方声明)]: {content}'
        ).replace(
            '[目标帖子]: "走正常途径不如闹来钱多又快"',
            f'[目标帖子]: "{content}"'
        )
        
        # 由于是官方声明，移除对话上下文部分，简化为直接分析
        # 找到对话上下文部分并替换为简化版本
        context_start = annotation_prompt.find('## 2. 对话上下文 (Conversational Context)')
        context_end = annotation_prompt.find('## 3. 你的任务 (Your Task)')
        
        if context_start != -1 and context_end != -1:
            simplified_context = """## 2. 对话上下文 (Conversational Context)
这是一个官方声明，无需考虑对话上下文，请直接分析官方声明的内容倾向。

"""
            annotation_prompt = (annotation_prompt[:context_start] + 
                                simplified_context + 
                                annotation_prompt[context_end:])
        
        try:
            print(f"[LLM标记] 开始标记官方声明内容...")
            print(f"[LLM标记] 内容长度: {len(content)} 字符")
            
            response = requests.post(
                endpoint,
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
                json={'model': model, 'messages': [{'role': 'user', 'content': annotation_prompt}]},
                timeout=30
            )
            response.raise_for_status()
            
            api_response = response.json()
            llm_content = api_response['choices'][0]['message']['content']
            
            print(f"[LLM标记] 原始响应: {llm_content}")
            
            # 使用与agent_controller相同的JSON解析逻辑
            try:
                # 尝试提取JSON部分
                if '{' in llm_content and '}' in llm_content:
                    json_start = llm_content.find('{')
                    json_end = llm_content.rfind('}') + 1
                    json_str = llm_content[json_start:json_end]
                    annotations = json.loads(json_str)
                    annotations["success"] = True
                    
                    print(f"[LLM标记] 解析成功: {annotations}")
                    return annotations
                else:
                    print(f"[LLM标记] 响应中未找到JSON格式")
                    return {"success": False, "error": "响应格式无效"}
                
            except json.JSONDecodeError as e:
                print(f"[LLM标记] JSON解析失败: {e}")
                print(f"[LLM标记] 响应内容: {llm_content}")
                return {"success": False, "error": f"JSON解析失败: {str(e)}"}
                
        except Exception as e:
            print(f"[LLM标记] API调用失败: {e}")
            return {"success": False, "error": f"API调用失败: {str(e)}"}
    
    def _get_current_llm_config(self):
        """获取当前有效的LLM配置（从环境变量或配置文件）"""
        import os
        
        # 尝试从环境变量获取
        llm_config = {}
        
        # 1. 从环境变量获取
        if os.getenv('LLM_API_KEY'):
            llm_config = {
                "api_key": os.getenv('LLM_API_KEY'),
                "base_url": os.getenv('LLM_ENDPOINT', ''),
                "model": os.getenv('LLM_MODEL', 'deepseek-v3')
            }
            print(f"[LLM配置] 从环境变量获取LLM配置")
            return llm_config
        
        # 2. 从配置文件获取
        try:
            from api.environment_service import load_environment_config
            env_config = load_environment_config()
            if env_config.get('llm_config', {}).get('api_key'):
                llm_config = env_config['llm_config']
                print(f"[LLM配置] 从配置文件获取LLM配置")
                return llm_config
        except Exception as e:
            print(f"[LLM配置] 从配置文件读取失败: {e}")
        
        # 3. 如果都没有，使用默认配置（从setup脚本中获取）
        print(f"⚠️ [LLM配置] 环境变量和配置文件均为空，使用默认LLM配置")
        default_llm_config = {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "base_url": "https://www.chataiapi.com/v1/chat/completions", 
            "model": "deepseek-v3-250324"
        }
        print(f"[LLM配置] 使用默认配置: {default_llm_config['base_url']}")
        return default_llm_config
    
    def inject_official_statement(self, original_simulation_id, statement_config, agent_configs=None):
        """
        注入官方声明/辟谣消息到新的仿真中
        这是飓风消息的核心功能：对比原仿真vs加入官方干预后的仿真
        
        Args:
            original_simulation_id: 原始仿真ID  
            statement_config: 官方声明配置
                {
                    "content": "官方声明内容",
                    "target_time_slice": 3,  # 在第几个时间片发布
                    "statement_type": "clarification|refutation|official_notice",
                    "authority_level": "high|medium|low"  # 权威性级别
                }
            agent_configs: Agent配置列表（可选），如果不提供则使用默认配置
        
        Returns:
            dict: 包含新仿真ID和注入结果
        """
        # 首先检查内存中的仿真
        if original_simulation_id in self.simulations:
            original_simulation = self.simulations[original_simulation_id]
            
            # 创建新仿真配置（复制原配置）
            new_config = original_simulation["config"].copy()
            new_config["simulation_name"] = f"官方干预对比_{int(time.time())}"
            new_config["comparison_type"] = "official_intervention"
            new_config["original_simulation_id"] = original_simulation_id
            
            # 准备官方声明数据
            statement_data = self._create_official_statement_data(statement_config)
            
            # 预置官方声明事件（在仿真开始前就设置好）
            new_config["pre_injected_events"] = [statement_data]
            
            # 使用传入的Agent配置或原始仿真的Agent配置
            final_agent_configs = agent_configs if agent_configs is not None else original_simulation["agent_configs"]
            print(f"[官方声明] 使用Agent配置: {'用户选择' if agent_configs is not None else '原始仿真'} ({len(final_agent_configs)} 个Agent)")
            
            # 启动新仿真
            new_simulation_id = self.start_simulation(new_config, final_agent_configs)
            
            return {
                "success": True, 
                "new_simulation_id": new_simulation_id,
                "original_simulation_id": original_simulation_id,
                "statement_data": statement_data,
                "agent_source": "user_selected" if agent_configs is not None else "original_simulation"
            }
        
        # 如果内存中找不到，检查日志文件中的仿真
        try:
            from simulation_log_extractor import create_frontend_api_adapter
            adapter = create_frontend_api_adapter()
            log_simulations = adapter["get_simulation_list"]()
            
            # 查找目标仿真
            target_simulation = None
            if log_simulations and log_simulations.get("simulations"):
                for sim in log_simulations["simulations"]:
                    if sim["id"] == original_simulation_id:
                        target_simulation = sim
                        break
            
            if not target_simulation:
                return {"success": False, "error": "原始仿真不存在"}
            
            # 🔥 修复：创建完全独立的新仿真配置，包含LLM配置
            default_config = {
                "simulation_name": f"官方声明对比仿真_{int(time.time())}",
                "comparison_type": "official_intervention_from_log",
                "original_simulation_id": original_simulation_id,
                # 🔥 关键：不传入original_log_file，避免引用原始日志数据
                "w_pop": 0.7,  # 默认参数
                "k": 2,
                "skip_llm": False,
                "posts_per_slice": 30,  # 统一使用30
                "max_slices": target_simulation.get("total_time_slices", 4),  # 🔄 恢复：保持时间片限制功能
                # 🔥 关键修复：添加LLM配置，确保新仿真能调用LLM
                "llm_config": self._get_current_llm_config()
            }
            
            # 准备官方声明数据
            statement_data = self._create_official_statement_data(statement_config)
            
            # 预置官方声明事件
            default_config["pre_injected_events"] = [statement_data]
            
            # 确定使用哪些Agent配置
            if agent_configs is not None:
                # 使用用户传入的Agent配置
                print(f"[官方声明] 使用用户选择的Agent配置: {len(agent_configs)} 个Agent")
                final_agent_configs = agent_configs
                agent_source = "user_selected"
            else:
                # 从agents.json加载Agent配置（与仿真配置面板保持一致）
                from api.agent_service import load_agents
                agents_from_config = load_agents()
                
                if not agents_from_config:
                    # 如果agents.json不存在或为空，使用硬编码的默认配置作为后备
                    print("⚠️ agents.json不存在或为空，使用默认Agent配置")
                    final_agent_configs = [
                        {"agent_id": "agent_001", "role_type": "ordinary_user", "initial_emotion": 0.4, "initial_stance": 0.1, "initial_confidence": 0.6},
                        {"agent_id": "agent_002", "role_type": "ordinary_user", "initial_emotion": -0.2, "initial_stance": -0.3, "initial_confidence": 0.7},
                        {"agent_id": "agent_003", "role_type": "opinion_leader", "initial_emotion": 0.1, "initial_stance": 0.4, "initial_confidence": 0.8},
                        {"agent_id": "agent_004", "role_type": "ordinary_user", "initial_emotion": 0.3, "initial_stance": -0.1, "initial_confidence": 0.5}
                    ]
                    agent_source = "hardcoded_default"
                else:
                    # 使用agents.json中的配置（与仿真配置面板保持一致）
                    print(f"✅ 从agents.json加载了 {len(agents_from_config)} 个Agent配置")
                    final_agent_configs = agents_from_config
                    agent_source = "agents_json"
            
            # 启动新仿真
            new_simulation_id = self.start_simulation(default_config, final_agent_configs)
            
            return {
                "success": True, 
                "new_simulation_id": new_simulation_id,
                "original_simulation_id": original_simulation_id,
                "statement_data": statement_data,
                "source": "log_file",
                "agent_source": agent_source,
                "agent_count": len(final_agent_configs)
            }
            
        except Exception as e:
            return {"success": False, "error": f"处理日志文件仿真失败: {str(e)}"}

    def inject_batch_official_statements(self, simulation_config, agent_configs, statements):
        """
        批量注入官方声明并启动新仿真
        
        Args:
            simulation_config: 仿真配置
            agent_configs: Agent配置列表
            statements: 官方声明列表，每个包含content、target_time_slice、statement_type、authority_level
        
        Returns:
            dict: 包含新仿真ID和所有处理后的声明数据
        """
        try:
            print(f"[批量官方声明] 开始处理 {len(statements)} 条声明...")
            
            # 处理所有官方声明
            processed_statements = []
            for i, statement_config in enumerate(statements):
                print(f"[批量官方声明] 处理第 {i+1} 条声明...")
                statement_data = self._create_official_statement_data(statement_config)
                processed_statements.append(statement_data)
                print(f"[批量官方声明] 第 {i+1} 条声明处理完成，LLM标注: {statement_data.get('generation_info', {}).get('llm_annotated', False)}")
            
            # 创建新仿真配置
            new_config = simulation_config.copy()
            new_config["simulation_name"] = f"批量官方声明仿真_{int(time.time())}"
            new_config["comparison_type"] = "batch_official_statements"
            new_config["statement_count"] = len(statements)
            
            # 预置所有官方声明事件
            new_config["pre_injected_events"] = processed_statements
            
            # 启动新仿真
            new_simulation_id = self.start_simulation(new_config, agent_configs)
            
            print(f"[批量官方声明] 新仿真已启动: {new_simulation_id}")
            print(f"[批量官方声明] 预置事件数量: {len(processed_statements)}")
            
            return {
                "success": True,
                "new_simulation_id": new_simulation_id,
                "processed_statements": processed_statements,
                "statement_count": len(statements),
                "simulation_config": new_config
            }
            
        except Exception as e:
            print(f"[批量官方声明] 处理失败: {e}")
            return {"success": False, "error": f"批量处理官方声明失败: {str(e)}"}

# 创建全局仿真管理器
simulation_manager = SimulationManager()

def filter_agent_fields(agent_info):
    """只保留agent初始化需要的字段"""
    allowed_fields = [
        "agent_id", "role_type", "attitude_firmness", "opinion_blocking",
        "activity_level", "initial_emotion", "initial_stance", "initial_confidence"
    ]
    return {k: v for k, v in agent_info.items() if k in allowed_fields}

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """启动仿真API"""
    try:
        print("🚀 收到仿真启动请求")
        data = request.json
        print(f"📋 请求数据: {data}")
        
        if not data:
            print("❌ 请求体为空")
            return jsonify({'error': '请求体不能为空'}), 400
            
        config = data.get("config", {})
        agent_configs = data.get("agent_configs", data.get("agents", []))  # 兼容两种字段名
        
        print(f"⚙️ 仿真配置: {config}")
        print(f"👥 Agent配置数量: {len(agent_configs)}")
        print(f"👤 Agent列表: {[a.get('agent_id', 'unknown') for a in agent_configs]}")
        
        # 过滤agent参数
        filtered_agents = [filter_agent_fields(a) for a in agent_configs]
        print(f"🔧 过滤后的Agent配置: {filtered_agents}")
        
        # 启动仿真时只用filtered_agents
        print("🎬 调用仿真管理器启动仿真...")
        simulation_id = simulation_manager.start_simulation(config, filtered_agents)
        print(f"✅ 仿真启动成功，ID: {simulation_id}")
        
        return jsonify({
            "status": "success",
            "simulation_id": simulation_id,
            "message": "仿真已启动，请稍后查询结果"
        })
        
    except Exception as e:
        print(f"💥 启动仿真失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"启动仿真失败: {str(e)}"}), 500

@simulation_bp.route('/status/<simulation_id>', methods=['GET'])
def get_simulation_status(simulation_id):
    """获取仿真状态"""
    status = simulation_manager.get_simulation_status(simulation_id)
    if not status:
        return jsonify({"error": "仿真不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": status
    })

@simulation_bp.route('/stop/<simulation_id>', methods=['POST'])
def stop_simulation(simulation_id):
    """停止仿真"""
    success = simulation_manager.stop_simulation(simulation_id)
    if success:
        return jsonify({
            "status": "success",
            "message": "仿真已停止"
        })
    else:
        return jsonify({"error": "仿真不存在或已完成"}), 404

@simulation_bp.route('/inject_event', methods=['POST'])
def inject_event():
    """注入突发事件"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get("simulation_id")
        event_content = data.get("content")
        event_heat = data.get("heat", 80)
        event_timestamp = data.get("timestamp")
        
        if not simulation_id or not event_content:
            return jsonify({"error": "缺少必要参数"}), 400
        
        event_data = {
            "id": str(uuid.uuid4()),
            "content": event_content,
            "heat": event_heat,
            "timestamp": event_timestamp or datetime.now().isoformat()
        }
        
        success = simulation_manager.inject_event(simulation_id, event_data)
        
        if success:
            return jsonify({
                "status": "success",
                "event_id": event_data["id"],
                "message": "事件注入成功"
            })
        else:
            return jsonify({"error": "仿真不存在"}), 404
            
    except Exception as e:
        return jsonify({"error": f"注入事件失败: {str(e)}"}), 500

@simulation_bp.route('/realtime_log/<simulation_id>', methods=['GET'])
def get_realtime_log(simulation_id):
    """获取实时仿真日志流"""
    from flask import Response
    import glob
    import os
    import time
    
    def generate_log_stream():
        simulation = simulation_manager.get_simulation_status(simulation_id)
        if not simulation:
            yield f"data: {{'error': '仿真不存在'}}\n\n"
            return
            
        # 等待日志文件生成
        log_file_path = None
        max_wait = 30  # 最多等待30秒
        wait_count = 0
        
        while wait_count < max_wait:
            # 查找最新的日志文件
            log_files = glob.glob("simulation_log_*.txt")
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                # 检查文件是否是当前仿真的（通过修改时间判断）
                file_time = os.path.getctime(latest_log)
                simulation_start_time = datetime.fromisoformat(simulation['start_time']).timestamp()
                if file_time >= simulation_start_time - 5:  # 5秒容差
                    log_file_path = latest_log
                    break
            
            time.sleep(1)
            wait_count += 1
        
        if not log_file_path:
            yield f"data: {{'error': '未找到日志文件'}}\n\n"
            return
            
        # 实时读取日志文件
        last_position = 0
        while True:
            try:
                simulation = simulation_manager.get_simulation_status(simulation_id)
                if not simulation or simulation['status'] in ['completed', 'error', 'stopped']:
                    # 仿真结束，发送最后的日志内容
                    if os.path.exists(log_file_path):
                        with open(log_file_path, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_content = f.read()
                            if new_content:
                                import json
                                yield f"data: {json.dumps({'content': new_content, 'status': simulation['status']})}\n\n"
                    yield f"data: {json.dumps({'status': simulation['status'], 'finished': True})}\n\n"
                    break
                
                # 读取新增的日志内容
                if os.path.exists(log_file_path):
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        f.seek(last_position)
                        new_content = f.read()
                        if new_content:
                            # 发送新增的日志内容，使用JSON格式发送
                            import json
                            yield f"data: {json.dumps({'content': new_content, 'status': 'running'})}\n\n"
                            last_position = f.tell()
                
                time.sleep(0.5)  # 每0.5秒检查一次
                
            except Exception as e:
                yield f"data: {{'error': '读取日志失败: {str(e)}'}}\n\n"
                break
    
    return Response(
        generate_log_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

@simulation_bp.route('/results/<simulation_id>', methods=['GET'])
def get_simulation_results(simulation_id):
    """获取仿真结果"""
    status = simulation_manager.get_simulation_status(simulation_id)
    if not status:
        return jsonify({"error": "仿真不存在"}), 404
    
    if status["status"] != "completed":
        return jsonify({
            "status": status["status"],
            "message": "仿真尚未完成"
        })
    
    return jsonify(status["results"])

@simulation_bp.route('/load', methods=['POST'])
def load_simulation():
    """加载历史仿真配置"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_id = data.get("simulation_id")
        
        status = simulation_manager.get_simulation_status(simulation_id)
        if not status:
            return jsonify({"error": "仿真不存在"}), 404
        
        # 返回配置信息，前端可以修改后重新启动
        return jsonify({
            "status": "success",
            "config": status["config"],
            "agent_configs": status["agent_configs"],
            "events": status.get("events", [])
        })
        
    except Exception as e:
        return jsonify({"error": f"加载仿真失败: {str(e)}"}), 500

@simulation_bp.route('/compare', methods=['POST'])
def compare_simulations():
    """对比多次仿真结果"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        simulation_ids = data.get("simulation_ids", [])
        
        if len(simulation_ids) < 2:
            return jsonify({"error": "至少需要两个仿真ID进行对比"}), 400
        
        comparison_results = {}
        for sim_id in simulation_ids:
            status = simulation_manager.get_simulation_status(sim_id)
            if status and status["status"] == "completed":
                comparison_results[sim_id] = {
                    "summary": status["results"]["summary"],
                    "agent_states": status["results"]["agent_states"]
                }
        
        return jsonify({
            "status": "success",
            "comparison": comparison_results
        })
        
    except Exception as e:
        return jsonify({"error": f"对比仿真失败: {str(e)}"}), 500

@simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """获取所有仿真列表"""
    simulations = []
    for sim_id, config in simulation_manager.simulations.items():
        simulations.append({
            "id": sim_id,
            "status": config["status"],
            "start_time": config["start_time"],
            "agent_count": len(config["agent_configs"])
        })
    
    return jsonify({
        "status": "success",
        "simulations": simulations
    })

@simulation_bp.route('/inject_official_statement', methods=['POST'])
def inject_official_statement_api():
    """注入官方声明API（替代飓风消息）"""
    try:
        data = request.get_json()
        simulation_id = data.get('simulation_id')
        content = data.get('content')
        target_time_slice = data.get('target_time_slice', 0)
        statement_type = data.get('statement_type', 'clarification')
        authority_level = data.get('authority_level', 'high')
        agent_configs = data.get('agent_configs')  # 新增：接收Agent配置
        
        # 验证必需参数
        if not simulation_id:
            return jsonify({"error": "缺少仿真ID"}), 400
        
        if not content:
            return jsonify({"error": "缺少官方声明内容"}), 400
        
        # 组装声明配置
        statement_config = {
            "content": content,
            "target_time_slice": target_time_slice,
            "statement_type": statement_type,
            "authority_level": authority_level,
            "custom_tags": data.get('custom_tags', []),
            "notes": data.get('notes', ''),
            "enable_tracking": data.get('enable_tracking', False)
        }
        
        # 如果有Agent配置，进行过滤处理（与仿真配置面板保持一致）
        filtered_agent_configs = None
        if agent_configs:
            filtered_agent_configs = [filter_agent_fields(a) for a in agent_configs]
            print(f"[官方声明API] 收到 {len(agent_configs)} 个Agent配置，过滤后: {len(filtered_agent_configs)} 个")
        else:
            print(f"[官方声明API] 未收到Agent配置，将使用默认配置")
        
        # 注入官方声明
        result = simulation_manager.inject_official_statement(simulation_id, statement_config, filtered_agent_configs)
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": "官方声明注入成功，已启动对比仿真",
                "new_simulation_id": result["new_simulation_id"],
                "original_simulation_id": result["original_simulation_id"],
                "statement_data": result["statement_data"],
                "agent_source": result.get("agent_source", "unknown"),
                "agent_count": result.get("agent_count", 0)
            })
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"注入官方声明失败: {str(e)}"}), 500

@simulation_bp.route('/inject_batch_official_statements', methods=['POST'])
def inject_batch_official_statements_api():
    """批量注入官方声明API"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        simulation_config = data.get('simulation_config')
        agent_configs = data.get('agent_configs')
        statements = data.get('statements')
        
        if not simulation_config:
            return jsonify({"error": "缺少仿真配置"}), 400
            
        if not agent_configs:
            return jsonify({"error": "缺少Agent配置"}), 400
            
        if not statements or not isinstance(statements, list):
            return jsonify({"error": "缺少官方声明列表"}), 400
        
        # 验证每个声明的必需字段
        for i, statement in enumerate(statements):
            if not statement.get('content'):
                return jsonify({"error": f"第{i+1}条声明缺少内容"}), 400
                
            if 'target_time_slice' not in statement:
                return jsonify({"error": f"第{i+1}条声明缺少目标时间片"}), 400
        
        print(f"[批量API] 收到批量官方声明请求: {len(statements)} 条声明")
        
        # 调用批量处理方法
        result = simulation_manager.inject_batch_official_statements(
            simulation_config, 
            agent_configs, 
            statements
        )
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": f"批量官方声明注入成功，共处理 {result['statement_count']} 条声明",
                "new_simulation_id": result["new_simulation_id"],
                "processed_statements": result["processed_statements"],
                "statement_count": result["statement_count"]
            })
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"批量注入官方声明失败: {str(e)}"}), 500

@simulation_bp.route('/inject_hurricane', methods=['POST'])
def inject_hurricane_message():
    """注入飓风消息（紧急广播）- 兼容性保留，建议使用官方声明API"""
    try:
        data = request.get_json()
        simulation_id = data.get('simulation_id')
        content = data.get('content')
        target_time_slice = data.get('target_time_slice')
        emotion_impact = data.get('emotion_impact', -0.5)
        stance_impact = data.get('stance_impact', 0.0)
        priority = data.get('priority', 999)
        
        if not simulation_id or not content:
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 创建飓风消息数据
        hurricane_data = {
            "content": f"🚨 紧急广播：{content}",
            "author_id": "emergency_system",
            "is_hurricane": True,
            "is_event": True,
            "force_read": True,
            "priority": priority,
            "information_strength": 1.0,
            "popularity": 9999,
            "emotion_score": emotion_impact,
            "stance_score": stance_impact,
            "target_time_slice": target_time_slice,
            "timestamp": time.time()
        }
        
        # 使用现有的事件注入功能
        result = simulation_manager.inject_event(simulation_id, hurricane_data)
        
        return jsonify({
            "status": "success",
            "message": "飓风消息注入成功",
            "event_id": result.get("event_id"),
            "hurricane_data": hurricane_data
        })
        
    except Exception as e:
        return jsonify({"error": f"注入飓风消息失败: {str(e)}"}), 500

@simulation_bp.route('/inject_hurricane_with_llm', methods=['POST'])
def inject_hurricane_message_with_llm():
    """注入飓风消息（使用LLM进行数据标注并保存到JSON文件）- 已废弃，请使用官方声明API"""
    return jsonify({
        "error": "此API已废弃，请使用 /inject_official_statement API",
        "migration_guide": {
            "old_api": "/inject_hurricane_with_llm",
            "new_api": "/inject_official_statement", 
            "description": "新API支持更准确的社交媒体仿真中的官方舆论干预功能"
        }
    }), 410  # Gone

@simulation_bp.route('/inject_multiple_hurricanes', methods=['POST'])
def inject_multiple_hurricanes():
    """批量注入多个飓风消息 - 已废弃，请使用官方声明API"""
    return jsonify({
        "error": "此API已废弃，请使用 /inject_official_statement API进行批量操作",
        "migration_guide": {
            "old_api": "/inject_multiple_hurricanes",
            "new_api": "/inject_official_statement",
            "description": "请循环调用新API或联系开发团队实现批量官方声明功能"
        }
    }), 410  # Gone

@simulation_bp.route('/official_statement/config_panel', methods=['GET'])
def get_official_statement_config_panel():
    """获取官方声明配置面板的数据"""
    try:
        # 优先获取基于日志文件的仿真（这些是完整的历史仿真）
        simulations = []
        try:
            log_based_simulations = frontend_adapter["get_simulation_list"]()
            if log_based_simulations.get("simulations"):
                print(f"[官方声明API] 从日志文件获取到 {len(log_based_simulations['simulations'])} 个仿真")
                for sim in log_based_simulations.get("simulations", []):
                    # 只添加已完成且有Agent数据的仿真
                    if (sim.get("status") == "completed" and 
                        sim.get("agent_count", 0) > 0 and 
                        sim.get("total_time_slices", 0) > 0):
                        simulations.append(sim)
                        print(f"[官方声明API] 添加仿真: {sim['id']} - {sim['name']}")
        except Exception as e:
            print(f"[官方声明API] 获取日志文件仿真失败: {e}")
        
        # 补充内存中的仿真（如果有的话）
        for sim_id, config in simulation_manager.simulations.items():
            if config["status"] == "completed":
                # 检查是否已经在日志文件仿真中
                if not any(s["id"] == sim_id for s in simulations):
                    simulations.append({
                        "id": sim_id,
                        "name": config.get("config", {}).get("simulation_name", f"仿真_{sim_id[:8]}"),
                        "start_time": config["start_time"],
                        "agent_count": len(config["agent_configs"]),
                        "status": config["status"],
                        "total_time_slices": config.get("results", {}).get("total_slices", 0)
                    })
        
        # 获取可用的Agent列表（与仿真配置面板保持一致）
        available_agents = []
        try:
            from api.agent_service import load_agents
            agents_from_config = load_agents()
            if agents_from_config:
                available_agents = agents_from_config
                print(f"[官方声明API] 从agents.json加载了 {len(available_agents)} 个可用Agent")
            else:
                print(f"[官方声明API] agents.json为空或不存在")
        except Exception as e:
            print(f"[官方声明API] 加载Agent配置失败: {e}")
        
        print(f"[官方声明API] 最终返回 {len(simulations)} 个可用仿真，{len(available_agents)} 个可用Agent")
        
        return jsonify({
            "status": "success",
            "simulations": simulations,
            "available_agents": available_agents,  # 新增：Agent列表
            "statement_types": [
                {
                    "id": "clarification",
                    "name": "澄清说明",
                    "description": "对事件进行官方澄清",
                    "emotion_effect": "轻微正面",
                    "stance_effect": "中性"
                },
                {
                    "id": "refutation", 
                    "name": "辟谣声明",
                    "description": "官方辟谣虚假信息",
                    "emotion_effect": "负面转正面",
                    "stance_effect": "正面引导"
                },
                {
                    "id": "official_notice",
                    "name": "官方通知",
                    "description": "发布官方政策或通知",
                    "emotion_effect": "中性",
                    "stance_effect": "轻微正面"
                }
            ],
            "authority_levels": [
                {
                    "id": "high",
                    "name": "高权威",
                    "description": "政府机构、官方媒体",
                    "influence_multiplier": 1.0
                },
                {
                    "id": "medium", 
                    "name": "中权威",
                    "description": "专业机构、知名专家",
                    "influence_multiplier": 0.7
                },
                {
                    "id": "low",
                    "name": "低权威", 
                    "description": "一般组织、普通账号",
                    "influence_multiplier": 0.4
                }
            ]
        })
        
    except Exception as e:
        return jsonify({"error": f"获取配置面板数据失败: {str(e)}"}), 500

@simulation_bp.route('/official_statement/simulation_details/<simulation_id>', methods=['GET'])
def get_simulation_details_for_statement(simulation_id):
    """获取指定仿真的详细信息（用于配置官方声明）"""
    try:
        # 首先检查内存中的仿真
        if simulation_id in simulation_manager.simulations:
            simulation = simulation_manager.simulations[simulation_id]
            
            # 从结果中提取时间片信息
            results = simulation.get("results", {})
            total_slices = results.get("total_slices", 0)
            
            time_slices = []
            for i in range(total_slices):
                time_slices.append({
                    "index": i,
                    "timeRange": f"T{i:02d}:00-T{i+1:02d}:00",
                    "description": f"时间片 {i+1}"
                })
            
            return jsonify({
                "status": "success",
                "simulation": {
                    "id": simulation_id,
                    "name": simulation.get("config", {}).get("simulation_name", f"仿真_{simulation_id[:8]}"),
                    "start_time": simulation["start_time"],
                    "status": simulation["status"],
                    "agent_count": len(simulation["agent_configs"]),
                    "total_time_slices": total_slices
                },
                "time_slices": time_slices
            })
        
        # 如果内存中没有，尝试从日志文件获取
        try:
            details = frontend_adapter["get_simulation_details"](simulation_id)
            return jsonify(details)
        except ValueError:
            return jsonify({"error": "仿真不存在"}), 404
        
    except Exception as e:
        return jsonify({"error": f"获取仿真详情失败: {str(e)}"}), 500

@simulation_bp.route('/<simulation_id>/timeslices', methods=['GET'])
def get_simulation_timeslices(simulation_id):
    """获取仿真的时间片信息"""
    try:
        if simulation_id not in simulation_manager.simulations:
            return jsonify({"error": "仿真不存在"}), 404
        
        simulation = simulation_manager.simulations[simulation_id]
        
        # 从仿真配置中获取时间片信息
        config = simulation.get("config", {})
        time_slices_count = config.get("time_slices", 10)
        slice_duration = config.get("slice_duration", 2)  # 每个时间片2小时
        
        # 生成时间片信息
        time_slices = []
        for i in range(time_slices_count):
            start_hour = i * slice_duration
            end_hour = start_hour + slice_duration
            time_slices.append({
                "index": i,
                "timeRange": f"{str(start_hour).zfill(2)}:00 - {str(end_hour).zfill(2)}:00",
                "postCount": None  # 实际实现中应该从仿真结果中获取
            })
        
        return jsonify({
            "status": "success",
            "time_slices": time_slices,
            "total_slices": time_slices_count
        })
        
    except Exception as e:
        return jsonify({"error": f"获取时间片信息失败: {str(e)}"}), 500

@simulation_bp.route('/create_comparison', methods=['POST'])
def create_comparison_simulation():
    """创建对比仿真（基于原仿真+飓风消息）"""
    try:
        data = request.get_json()
        original_simulation_id = data.get('original_simulation_id')
        hurricane_config = data.get('hurricane_config')
        comparison_name = data.get('comparison_name', f"对比仿真_{int(time.time())}")
        
        if not original_simulation_id or not hurricane_config:
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 检查原始仿真是否存在
        if original_simulation_id not in simulation_manager.simulations:
            return jsonify({"error": "原始仿真不存在"}), 404
        
        original_simulation = simulation_manager.simulations[original_simulation_id]
        
        # 复制原始仿真配置
        comparison_config = original_simulation["config"].copy()
        comparison_config["name"] = comparison_name
        comparison_config["comparison_type"] = "hurricane_intervention"
        comparison_config["original_simulation_id"] = original_simulation_id
        
        # 启动对比仿真
        comparison_simulation_id = simulation_manager.start_simulation(
            comparison_config,
            original_simulation["agent_configs"]
        )
        
        # 注入飓风消息
        hurricanes = hurricane_config.get('hurricanes', [])
        for hurricane in hurricanes:
            hurricane_data = {
                "content": hurricane.get('content', ''),
                "author_id": "emergency_system",
                "is_hurricane": True,
                "is_event": True,
                "force_read": True,
                "priority": hurricane.get('priority', 999),
                "information_strength": 1.0,
                "popularity": 9999,
                "emotion_score": hurricane.get('emotion_impact', -0.5),
                "stance_score": hurricane.get('stance_impact', 0.0),
                "target_time_slice": hurricane.get('target_time_slice'),
                "message_type": hurricane.get('message_type', 'custom'),
                "timestamp": time.time()
            }
            
            simulation_manager.inject_event(comparison_simulation_id, hurricane_data)
        
        return jsonify({
            "status": "success",
            "message": "对比仿真创建成功",
            "simulation_id": comparison_simulation_id,
            "original_simulation_id": original_simulation_id,
            "hurricane_count": len(hurricanes),
            "comparison_name": comparison_name
        })
        
    except Exception as e:
        return jsonify({"error": f"创建对比仿真失败: {str(e)}"}), 500

# ===== 新增：基于日志文件的仿真信息API =====

# 创建前端API适配器
frontend_adapter = create_frontend_api_adapter()

@simulation_bp.route('/log_based/list', methods=['GET'])
def get_log_based_simulation_list():
    """获取基于日志文件的仿真列表（用于飓风消息功能）"""
    try:
        return jsonify(frontend_adapter["get_simulation_list"]())
    except Exception as e:
        return jsonify({"error": f"获取仿真列表失败: {str(e)}"}), 500

@simulation_bp.route('/log_based/<simulation_id>/time_slices', methods=['GET'])
def get_log_based_time_slices(simulation_id):
    """获取基于日志文件的仿真时间片信息"""
    try:
        return jsonify(frontend_adapter["get_simulation_time_slices"](simulation_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"获取时间片信息失败: {str(e)}"}), 500

@simulation_bp.route('/log_based/<simulation_id>/details', methods=['GET'])
def get_log_based_simulation_details(simulation_id):
    """获取基于日志文件的仿真详细信息"""
    try:
        return jsonify(frontend_adapter["get_simulation_details"](simulation_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"获取仿真详情失败: {str(e)}"}), 500

@simulation_bp.route('/log_based/refresh_index', methods=['POST'])
def refresh_simulation_index():
    """刷新仿真索引（重新扫描日志文件）"""
    try:
        extractor = SimulationLogExtractor()
        output_file = extractor.save_simulations_index()
        simulations = extractor.extract_all_simulations()
        
        return jsonify({
            "status": "success",
            "message": "仿真索引已刷新",
            "index_file": output_file,
            "total_simulations": len(simulations),
            "completed_simulations": len([s for s in simulations if s.get("status") == "completed"])
        })
    except Exception as e:
        return jsonify({"error": f"刷新索引失败: {str(e)}"}), 500


# ===== 官方声明处理辅助函数 =====
# 注意：新的官方声明系统不再依赖LLM自动标注，而是使用预设的权威性和类型参数

# 保留旧的LLM函数以兼容性，但标记为已废弃
def _annotate_hurricane_with_llm(content):
    """使用LLM对飓风消息进行数据标注 - 已废弃"""
    print("[警告] _annotate_hurricane_with_llm 已废弃，官方声明系统使用预设参数")
    return _get_default_annotation()

def _get_default_annotation():
    """获取默认的标注数据 - 已废弃"""
    return {
        "emotion_score": 0.1,
        "stance_category": "NEUTRAL_MEDIATING",
        "stance_confidence": 0.8,
        "information_strength": 0.9,
        "keywords": ["官方声明"],
        "stance_score": 0.0
    }

def _get_default_value(field):
    """获取字段的默认值 - 已废弃"""
    defaults = {
        "emotion_score": 0.1,
        "stance_category": "NEUTRAL_MEDIATING", 
        "stance_confidence": 0.8,
        "information_strength": 0.9,
        "keywords": ["官方声明"],
        "stance_score": 0.0
    }
    return defaults.get(field, None)

def _create_hurricane_message_data(simulation_id, content, annotated_data, target_time_slice):
    """创建完整的飓风消息数据结构 - 已废弃，使用官方声明系统"""
    print("[警告] _create_hurricane_message_data 已废弃，请使用官方声明系统")
    timestamp = int(time.time())
    return {
        "id": f"legacy_hurricane_{timestamp}",
        "content": content,
        "author_id": "legacy_system",
        "is_hurricane": True,
        "is_event": True,
        "force_read": True,
        "priority": 999,
        "target_time_slice": target_time_slice,
        "timestamp": timestamp,
        "deprecated": True
    }

def _save_hurricane_to_json_file(simulation_id, hurricane_message):
    """保存飓风消息到对应仿真的JSON文件 - 已废弃"""
    print("[警告] _save_hurricane_to_json_file 已废弃，官方声明直接注入到仿真中")
    return f"deprecated_hurricane_{int(time.time())}.json" 