#!/usr/bin/env python3
"""
测试跳过LLM模式是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.main import SimulationEngine

def test_skip_llm_mode():
    """测试跳过LLM模式"""
    print("=== 测试跳过LLM模式 ===")
    
    # 配置跳过LLM模式
    config = {
        "posts_per_slice": 30,
        "skip_llm": True,  # 关键：跳过LLM调用
        "w_pop": 0.7,
        "k": 2,
        "llm_config": {}
    }
    
    try:
        # 创建仿真引擎
        print("1. 创建仿真引擎...")
        engine = SimulationEngine(config)
        print(f"   ✅ 引擎创建成功，skip_llm={engine.skip_llm}")
        
        # 加载数据
        print("2. 加载数据...")
        engine.load_initial_data('data/postdata.json')
        print(f"   ✅ 数据加载成功，总时间片: {engine.total_slices}")
        
        # 检查Agent是否加载
        print("3. 检查Agent加载...")
        agent_count = len(engine.agent_controller.agents)
        print(f"   ✅ 加载了 {agent_count} 个Agent")
        
        if agent_count == 0:
            print("   ⚠️ 没有加载任何Agent，这可能是问题所在")
            return False
            
        # 测试运行一个时间片
        print("4. 测试运行一个时间片...")
        engine.total_slices = 1  # 只运行一个时间片
        
        try:
            results = engine.run_simulation(max_slices=1)
            print("   ✅ 时间片运行成功")
            return True
        except Exception as e:
            print(f"   ❌ 时间片运行失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_skip_llm_mode()
    if success:
        print("\n🎉 跳过LLM模式测试通过！")
    else:
        print("\n💥 跳过LLM模式测试失败！")
    
    sys.exit(0 if success else 1)
