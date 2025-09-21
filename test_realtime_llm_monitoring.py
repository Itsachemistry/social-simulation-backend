"""
测试带真实LLM调用的实时监控功能
"""
import json
import time
import os
from src.main import SimulationEngine

def test_realtime_monitoring_with_llm():
    """测试带真实LLM调用的实时监控功能"""
    print("=== 测试带真实LLM调用的实时监控功能 ===")
    
    # 准备配置，使用真实的DeepSeek API
    config = {
        "max_slices": 2,  # 只运行2个时间片进行测试
        "llm_config": {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "base_url": "https://www.chataiapi.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "enabled": True  # 启用真实LLM
        },
        "agents": [
            {
                "id": "user1",
                "personality": "积极乐观的年轻人",
                "is_opinion_leader": False,
                "initial_emotion": 0.7,
                "initial_stance": 0.6
            },
            {
                "id": "leader1", 
                "personality": "理性分析的意见领袖",
                "is_opinion_leader": True,
                "initial_emotion": 0.5,
                "initial_stance": 0.3
            }
        ]
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    print(f"Agent数量: {len(engine.agent_controller.agents)}")
    
    # 注入一个热门事件来触发LLM调用
    print("注入测试事件...")
    event_id = engine.inject_event("最新科技新闻：AI技术取得重大突破", event_heat=90)
    
    # 开始仿真（这会创建实时日志文件并包含LLM调用）
    print("\n开始仿真，实时监控将捕获所有LLM Prompt和响应...")
    start_time = time.time()
    
    results = engine.run_simulation(max_slices=2)
    
    elapsed = time.time() - start_time
    print(f"\n测试完成，耗时: {elapsed:.2f}秒")
    
    # 检查生成的日志文件
    import glob
    log_files = glob.glob("simulation_log_*.txt")
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        print(f"最新日志文件: {latest_log}")
        
        # 分析日志内容
        print("\n=== 日志内容分析 ===")
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 统计关键信息
        llm_calls = content.count("[LLM Request]")
        llm_responses = content.count("[LLM Response]")
        agent_updates = content.count("Agent")
        leader_updates = content.count("[Leader]")
        
        print(f"📊 监控统计:")
        print(f"  - LLM请求次数: {llm_calls}")
        print(f"  - LLM响应次数: {llm_responses}")
        print(f"  - Agent状态更新: {agent_updates}")
        print(f"  - 意见领袖更新: {leader_updates}")
        print(f"  - 总日志行数: {len(content.splitlines())}")
        
        # 显示包含LLM调用的关键行
        lines = content.splitlines()
        print(f"\n=== LLM调用监控样例 ===")
        for i, line in enumerate(lines):
            if "[LLM" in line:
                print(f"第{i+1}行: {line}")
                # 显示下一行的内容（通常是prompt或response内容）
                if i+1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line:
                        print(f"内容: {next_line[:100]}...")
                print()
        
        # 提供查看完整日志的提示
        print(f"\n💡 查看完整实时日志请打开: {latest_log}")
        print("   该文件包含了仿真过程中的所有LLM Prompt、响应和Agent状态变化")
        
    else:
        print("⚠️ 没有找到日志文件")
    
    return True

if __name__ == "__main__":
    test_realtime_monitoring_with_llm()
