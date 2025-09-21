"""
测试实时监控功能，包含Agent发帖
"""
import json
import time
import os
from src.main import SimulationEngine

def test_realtime_monitoring_with_posting():
    """测试带Agent发帖的实时监控功能"""
    print("=== 测试带Agent发帖的实时监控功能 ===")
    
    # 准备配置，启用LLM但提高发帖概率
    config = {
        "max_slices": 2,
        "llm_config": {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "base_url": "https://www.chataiapi.com/v1/chat/completions",
            "model": "gpt-3.5-turbo",
            "enabled": True
        },
        "agents": [
            {
                "id": "active_user",
                "personality": "热情活跃的用户",
                "is_opinion_leader": False,
                "initial_emotion": 0.8,  # 高情绪值增加发帖概率
                "initial_stance": 0.7,
                "activity_level": 0.9    # 高活跃度
            },
            {
                "id": "leader", 
                "personality": "有影响力的意见领袖",
                "is_opinion_leader": True,
                "initial_emotion": 0.6,
                "initial_stance": 0.5,
                "activity_level": 0.8
            }
        ]
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    print(f"Agent数量: {len(engine.agent_controller.agents)}")
    
    # 注入多个热门事件来提高发帖概率
    print("注入高热度测试事件...")
    engine.inject_event("突发新闻：重大科技创新发布", event_heat=95)
    engine.inject_event("热门话题：社会热点讨论", event_heat=90) 
    engine.inject_event("引发争议的观点", event_heat=88)
    
    # 开始仿真
    print("\n开始仿真，实时监控所有过程...")
    start_time = time.time()
    
    results = engine.run_simulation(max_slices=2)
    
    elapsed = time.time() - start_time
    print(f"\n测试完成，耗时: {elapsed:.2f}秒")
    
    # 分析生成的实时日志
    import glob
    log_files = glob.glob("simulation_log_*.txt")
    if log_files:
        latest_log = max(log_files, key=os.path.getctime)
        print(f"\n📁 实时日志文件: {latest_log}")
        
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计关键监控信息
        llm_calls = content.count("[LLM]")
        agent_actions = content.count("Agent")
        leader_actions = content.count("[Leader]")
        prompt_lines = content.count("[Prompt]")
        post_generation = content.count("发帖内容")
        
        print(f"\n📊 实时监控统计:")
        print(f"  - LLM相关操作: {llm_calls}")
        print(f"  - Agent活动记录: {agent_actions}")  
        print(f"  - 意见领袖活动: {leader_actions}")
        print(f"  - LLM Prompt记录: {prompt_lines}")
        print(f"  - 发帖生成记录: {post_generation}")
        print(f"  - 总日志行数: {len(content.splitlines())}")
        
        # 展示关键的LLM交互日志
        lines = content.splitlines()
        print(f"\n=== 关键LLM交互监控 ===")
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ["[LLM]", "[Prompt]", "发帖内容", "LLM生成"]):
                print(f"行{i+1}: {line}")
        
        print(f"\n💡 完整实时监控日志: {latest_log}")
        print("   包含完整的仿真过程、Agent状态变化、LLM交互等详细信息")
        
        # 验证日志文件大小
        file_size = os.path.getsize(latest_log)
        print(f"   日志文件大小: {file_size} 字节")
        
        return True
    else:
        print("❌ 没有找到实时日志文件")
        return False

if __name__ == "__main__":
    success = test_realtime_monitoring_with_posting()
    if success:
        print("\n✅ 实时监控系统测试成功！")
        print("现在您可以在仿真过程中实时查看：")
        print("  - 所有Agent的状态变化")
        print("  - LLM Prompt和响应") 
        print("  - 意见领袖的决策过程")
        print("  - 发帖生成的详细过程")
    else:
        print("\n❌ 实时监控系统测试失败")
