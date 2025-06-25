from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import threading
import time
from src.agent_controller import AgentController

simulation_bp = Blueprint('simulation', __name__)

class SimulationManager:
    """仿真管理器，负责启动、管理和存储仿真"""
    
    def __init__(self):
        self.simulations = {}
    
    def start_simulation(self, config, agent_configs):
        """启动仿真"""
        simulation_id = str(uuid.uuid4())
        
        # 创建仿真配置
        simulation_config = {
            "id": simulation_id,
            "config": config,
            "agent_configs": agent_configs,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "events": [],
            "results": None
        }
        
        self.simulations[simulation_id] = simulation_config
        
        # 在后台线程中运行仿真
        thread = threading.Thread(
            target=self._run_simulation_background,
            args=(simulation_id, config, agent_configs)
        )
        thread.start()
        
        return simulation_id
    
    def _run_simulation_background(self, simulation_id, config, agent_configs):
        """后台运行仿真"""
        try:
            from main import SimulationEngine
            
            # 创建仿真引擎
            engine = SimulationEngine(config)
            
            # 加载Agent配置
            engine.agent_controller = AgentController(
                agent_configs=agent_configs,
                world_state=engine.world_state,
                llm_service=engine.llm_service
            )
            
            # 注入预设事件
            simulation_config = self.simulations[simulation_id]
            for event in simulation_config.get("events", []):
                engine.inject_event(event["content"], event["heat"])
            
            # 运行仿真
            results = engine.run_simulation()
            
            # 保存结果
            simulation_config["status"] = "completed"
            simulation_config["results"] = {
                "summary": engine.get_simulation_summary(),
                "simulation_results": results,
                "final_posts": engine.world_state.get_all_posts(),
                "agent_states": self._get_agent_states(engine.agent_controller)
            }
            
        except Exception as e:
            simulation_config = self.simulations[simulation_id]
            simulation_config["status"] = "failed"
            simulation_config["error"] = str(e)
    
    def _get_agent_states(self, agent_controller):
        """获取所有Agent的最终状态"""
        agent_states = {}
        for agent_type, agents in agent_controller.agents.items():
            agent_states[agent_type] = []
            for agent in agents:
                agent_states[agent_type].append(agent.get_state_summary())
        return agent_states
    
    def get_simulation_status(self, simulation_id):
        """获取仿真状态"""
        return self.simulations.get(simulation_id, None)
    
    def inject_event(self, simulation_id, event_data):
        """注入突发事件"""
        if simulation_id not in self.simulations:
            return False
        
        simulation_config = self.simulations[simulation_id]
        if simulation_config["status"] == "running":
            # 仿真运行中，添加到事件队列
            if "events" not in simulation_config:
                simulation_config["events"] = []
            simulation_config["events"].append(event_data)
        else:
            # 仿真已完成，创建新的仿真
            new_simulation_id = str(uuid.uuid4())
            new_config = simulation_config["config"].copy()
            new_agent_configs = simulation_config["agent_configs"].copy()
            
            # 添加新事件
            new_events = simulation_config.get("events", []) + [event_data]
            
            # 启动新仿真
            self.start_simulation(new_config, new_agent_configs)
            
        return True

# 创建全局仿真管理器
simulation_manager = SimulationManager()

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """启动仿真API"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        config = data.get("config", {})
        agent_configs = data.get("agents", [])
        
        # 启动仿真
        simulation_id = simulation_manager.start_simulation(config, agent_configs)
        
        return jsonify({
            "status": "success",
            "simulation_id": simulation_id,
            "message": "仿真已启动，请稍后查询结果"
        })
        
    except Exception as e:
        return jsonify({"error": f"启动仿真失败: {str(e)}"}), 500

@simulation_bp.route('/status/<simulation_id>', methods=['GET'])
def get_simulation_status(simulation_id):
    """获取仿真状态"""
    status = simulation_manager.get_simulation_status(simulation_id)
    if not status:
        return jsonify({"error": "仿真不存在"}), 404
    
    return jsonify(status)

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