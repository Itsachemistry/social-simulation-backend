#!/usr/bin/env python3
"""
使用配置文件的仿真测试
"""

from main import SimulationEngine


def test_with_config():
    """使用配置文件测试仿真"""
    
    # 仿真配置
    config = {
        "posts_per_slice": 5,  # 每个时间片的帖子数
        
        # LLM配置
        "llm": {
            "model_name": "qwen/Qwen2.5-0.5B-Instruct",
            "use_mock": True,  # 使用Mock模式
            "api_key": None
        },
        
        # 使用配置文件
        "agent_config_path": "config/agents.json"
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    
    # 注入一个突发事件
    engine.inject_event("重大新闻：某项政策即将出台，引发广泛讨论", 90)
    
    # 运行仿真
    results = engine.run_simulation(max_slices=2)
    
    # 显示摘要
    summary = engine.get_simulation_summary()
    print(f"\n仿真摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 显示每个Agent的状态
    print(f"\nAgent状态:")
    for agent_type, agents in engine.agent_controller.agents.items():
        print(f"  {agent_type}:")
        for agent in agents:
            state = agent.get_state_summary()
            print(f"    {agent.agent_id}: 情绪={state['emotion']:.2f}, 置信度={state['confidence']:.2f}, 发帖概率={state['post_probability']:.2f}")
    
    # 保存结果
    engine.save_results("test_results.json")
    print(f"\n结果已保存到 test_results.json")


if __name__ == "__main__":
    test_with_config() 