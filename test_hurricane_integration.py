#!/usr/bin/env python3
"""
飓风消息集成测试脚本
测试从仿真运行→日志生成→元数据提取→前端API的完整流程
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import SimulationEngine
from simulation_log_extractor import SimulationLogExtractor, create_frontend_api_adapter


def run_test_simulation():
    """运行一个测试仿真"""
    print("🚀 开始运行测试仿真...")
    
    # 创建测试配置
    config = {
        "simulation_name": "飓风消息功能测试仿真",
        "posts_file": "data/sample_posts.json",
        "slice_size": 5,
        "total_slices": 3,
        "w_pop": 0.7,
        "k": 2,
        "skip_llm": True,  # 跳过LLM以加快测试
        "llm_config": {
            "enabled": False
        }
    }
    
    # 创建仿真引擎
    engine = SimulationEngine(config)
    
    # 运行仿真
    try:
        engine.load_initial_data("data/sample_posts.json")
        
        # 手动创建Agent并添加到控制器
        from src.agent import Agent, RoleType
        
        agent1 = Agent(
            agent_id="test_agent_1",
            role_type=RoleType.ORDINARY_USER,
            attitude_firmness=0.5,
            opinion_blocking=0.3,
            activity_level=0.7,
            initial_emotion=0.0,
            initial_stance=0.0,
            initial_confidence=0.5
        )
        
        agent2 = Agent(
            agent_id="test_agent_2", 
            role_type=RoleType.OPINION_LEADER,
            attitude_firmness=0.7,
            opinion_blocking=0.2,
            activity_level=0.9,
            initial_emotion=0.2,
            initial_stance=-0.1,
            initial_confidence=0.8
        )
        
        engine.agent_controller.agents = [agent1, agent2]
        
        results = engine.run_simulation()
        print("✅ 测试仿真运行完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试仿真运行失败: {e}")
        return False


def test_log_extraction():
    """测试日志提取功能"""
    print("\n📋 测试日志元数据提取...")
    
    extractor = SimulationLogExtractor()
    
    # 提取所有仿真
    simulations = extractor.extract_all_simulations()
    print(f"✅ 找到 {len(simulations)} 个仿真")
    
    if simulations:
        # 显示最新的仿真信息
        latest_sim = simulations[0]
        print(f"📊 最新仿真:")
        print(f"  ID: {latest_sim.get('simulation_id', 'unknown')}")
        print(f"  名称: {latest_sim.get('name', '未命名')}")
        print(f"  状态: {latest_sim.get('status', 'unknown')}")
        print(f"  Agent数量: {latest_sim.get('agent_count', 0)}")
        print(f"  时间片数量: {latest_sim.get('total_time_slices', 0)}")
        
        # 测试时间片提取
        if latest_sim.get('time_slices'):
            print(f"  时间片信息: {len(latest_sim['time_slices'])} 个时间片")
            for i, ts in enumerate(latest_sim['time_slices'][:3]):  # 只显示前3个
                print(f"    时间片 {i}: {ts.get('time_range', 'unknown')} ({ts.get('post_count', 0)} 帖子)")
        
        return latest_sim
    else:
        print("❌ 没有找到仿真记录")
        return None


def test_frontend_api_adapter():
    """测试前端API适配器"""
    print("\n🔌 测试前端API适配器...")
    
    adapter = create_frontend_api_adapter()
    
    try:
        # 测试获取仿真列表
        sim_list = adapter["get_simulation_list"]()
        print(f"✅ 获取仿真列表: {len(sim_list['simulations'])} 个仿真")
        
        if sim_list['simulations']:
            # 测试获取时间片信息
            first_sim = sim_list['simulations'][0]
            sim_id = first_sim['id']
            
            time_slices = adapter["get_simulation_time_slices"](sim_id)
            print(f"✅ 获取时间片信息: {time_slices['total_time_slices']} 个时间片")
            
            # 测试获取详细信息
            details = adapter["get_simulation_details"](sim_id)
            print(f"✅ 获取仿真详情: {details.get('name', '未命名')}")
            
            return True
        else:
            print("⚠️  没有可用的仿真数据")
            return False
            
    except Exception as e:
        print(f"❌ 前端API适配器测试失败: {e}")
        return False


def test_save_index():
    """测试保存索引功能"""
    print("\n💾 测试索引保存...")
    
    extractor = SimulationLogExtractor()
    
    try:
        output_file = extractor.save_simulations_index("test_simulations_index.json")
        print(f"✅ 索引已保存到: {output_file}")
        
        # 验证文件内容
        with open(output_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            
        print(f"📊 索引统计:")
        print(f"  总仿真数: {index_data.get('total_simulations', 0)}")
        print(f"  已完成数: {index_data.get('completed_simulations', 0)}")
        print(f"  更新时间: {index_data.get('last_updated', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 索引保存测试失败: {e}")
        return False


def simulate_frontend_workflow():
    """模拟前端工作流程"""
    print("\n🎨 模拟前端工作流程...")
    
    adapter = create_frontend_api_adapter()
    
    try:
        # 步骤1: 获取仿真列表
        print("步骤1: 获取已完成的仿真列表")
        sim_list = adapter["get_simulation_list"]()
        completed_sims = [s for s in sim_list['simulations'] if s['status'] == 'completed']
        
        if not completed_sims:
            print("⚠️  没有已完成的仿真，无法进行飓风消息配置")
            return False
        
        selected_sim = completed_sims[0]
        print(f"✅ 选择仿真: {selected_sim['name']} (ID: {selected_sim['id']})")
        
        # 步骤2: 获取时间片信息
        print("步骤2: 获取时间片信息用于配置")
        time_slices = adapter["get_simulation_time_slices"](selected_sim['id'])
        print(f"✅ 获取到 {time_slices['total_time_slices']} 个时间片")
        
        # 步骤3: 模拟飓风消息配置
        print("步骤3: 模拟飓风消息配置")
        hurricane_config = {
            "name": "测试飓风消息对比",
            "hurricanes": [
                {
                    "target_time_slice": 1,
                    "content": "🌪️ 测试飓风警报：这是一条测试紧急广播消息",
                    "emotion_impact": -0.7,
                    "stance_impact": 0.1,
                    "priority": 999,
                    "message_type": "disaster"
                }
            ]
        }
        print(f"✅ 配置完成: {len(hurricane_config['hurricanes'])} 条飓风消息")
        
        # 步骤4: 显示前端需要的所有数据
        print("步骤4: 前端显示数据预览")
        print(f"  原始仿真: {selected_sim['name']}")
        print(f"  Agent数量: {selected_sim['agent_count']}")
        print(f"  时间片数量: {time_slices['total_time_slices']}")
        print(f"  飓风消息数量: {len(hurricane_config['hurricanes'])}")
        
        # 显示时间片选择界面会显示的数据
        print("  时间片选择数据:")
        for ts in time_slices['time_slices'][:3]:  # 显示前3个
            print(f"    时间片 {ts['index']}: {ts['time_range']} ({ts['post_count']} 帖子)")
        
        print("✅ 前端工作流程模拟完成")
        return True
        
    except Exception as e:
        print(f"❌ 前端工作流程模拟失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 飓风消息集成测试")
    print("=" * 60)
    print(f"测试开始时间: {datetime.now()}")
    
    test_results = []
    
    # 测试1: 运行仿真生成日志
    result1 = run_test_simulation()
    test_results.append(("仿真运行", result1))
    
    # 等待日志文件写入完成
    time.sleep(2)
    
    # 测试2: 日志提取
    result2 = test_log_extraction()
    test_results.append(("日志提取", result2 is not None))
    
    # 测试3: 前端API适配器
    result3 = test_frontend_api_adapter()
    test_results.append(("前端API适配器", result3))
    
    # 测试4: 索引保存
    result4 = test_save_index()
    test_results.append(("索引保存", result4))
    
    # 测试5: 前端工作流程
    result5 = simulate_frontend_workflow()
    test_results.append(("前端工作流程", result5))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("🏁 测试结果摘要")
    print("=" * 60)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        print("📋 功能已可用:")
        print("  - 仿真运行时自动生成前端所需的元数据")
        print("  - 日志提取器可解析仿真信息")
        print("  - 前端API适配器可提供标准化数据")
        print("  - 飓风消息配置界面可获取真实仿真数据")
        print("\n🚀 下一步: 启动API服务器和前端来测试完整集成")
    else:
        print("\n⚠️  部分测试未通过，请检查相关功能")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
