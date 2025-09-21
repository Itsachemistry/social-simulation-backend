"""
测试实时监控功能
"""
import json
import time
import os
from src.main import SimulationEngine

def test_realtime_monitoring():
    """测试实时监控功能"""
    print("=== 测试实时监控功能 ===")
    
    # 准备配置
    config = {
        "max_slices": 3,  # 只运行3个时间片进行测试
        "llm_config": {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "base_url": "https://www.chataiapi.com/v1/chat/completions",
            "model": "gpt-3.5-turbo"
        },
        "agents": [
            {
                "id": "user1",
                "personality": "积极乐观",
                "is_opinion_leader": False,
                "initial_emotion": 0.6,
                "initial_stance": 0.4
            },
            {
                "id": "leader1", 
                "personality": "理性分析",
                "is_opinion_leader": True,
                "initial_emotion": 0.5,
                "initial_stance": 0.3
            }
        ]
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    print(f"Agent数量: {len(engine.agent_controller.agents)}")
    
    # 开始仿真（这会创建实时日志文件）
    print("\n开始仿真，实时日志将保存到文件...")
    start_time = time.time()
    
    results = engine.run_simulation(max_slices=3)
    
    elapsed = time.time() - start_time
    print(f"\n测试完成，耗时: {elapsed:.2f}秒")
    
    # 检查是否生成了日志文件
    import glob
    log_files = glob.glob("simulation_log_*.txt")
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        print(f"最新日志文件: {latest_log}")
        
        # 显示日志文件的前几行
        print("\n=== 日志文件内容预览 ===")
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20]):  # 显示前20行
                print(f"{i+1:2d}: {line.rstrip()}")
            
            if len(lines) > 20:
                print(f"... (总共 {len(lines)} 行)")
    else:
        print("⚠️ 没有找到日志文件")
    
    return True

if __name__ == "__main__":
    test_realtime_monitoring()
