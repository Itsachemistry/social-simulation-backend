#!/usr/bin/env python3
"""
前端仿真调试工具
帮助诊断前端仿真状态显示错误的问题
监控后端仿真状态和LLM调用情况
"""

import requests
import json
import time
import sys

API_BASE_URL = 'http://localhost:5000'

def check_backend_status():
    """检查后端服务是否正常运行"""
    print("=== 检查后端服务状态 ===")
    
    try:
        # 检查基础API
        response = requests.get(f"{API_BASE_URL}/api/visualization/options", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
            print(f"   状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 后端服务异常，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:5000)")
        print("   请确保后端服务已启动")
        return False
    except Exception as e:
        print(f"❌ 检查后端服务时出错: {e}")
        return False

def get_available_agents():
    """获取可用的Agent列表"""
    print("\n=== 获取Agent列表 ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/agents", timeout=10)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success') and 'data' in response_data:
                agents = response_data['data']
                print(f"✅ 成功获取 {len(agents)} 个Agent")
                for i, agent in enumerate(agents):
                    if i >= 3:  # 只显示前3个
                        break
                    print(f"   - {agent['agent_id']}: {agent['role_type']}")
                if len(agents) > 3:
                    print(f"   ... 还有 {len(agents) - 3} 个Agent")
                return agents
            else:
                print(f"❌ API响应格式错误: {response_data}")
                return []
        else:
            print(f"❌ 获取Agent失败，状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取Agent时出错: {e}")
        return []

def start_debug_simulation():
    """启动一个调试仿真"""
    print("\n=== 启动调试仿真 ===")
    
    # 获取Agent列表
    agents = get_available_agents()
    if not agents:
        print("❌ 无法获取Agent列表，终止仿真")
        return None
    
    # 选择前2个Agent进行测试
    selected_agents = agents[:2]
    print(f"选择用于测试的Agent: {[a['agent_id'] for a in selected_agents]}")
    
    # 配置仿真参数
    config = {
        "w_pop": 0.7,
        "k": 2,
        "posts_per_slice": 30,
        "max_slices": 2,  # 只运行2个时间片用于测试
        "skip_llm": False,  # 启用LLM调用来测试
        "llm_config": {
            "enabled_agents": [selected_agents[0]['agent_id']],  # 只对第一个Agent启用LLM
            "enabled_timeslices": [0]  # 只在第一个时间片启用LLM
        },
        "llm": {
            "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
            "endpoint": "https://www.chataiapi.com/v1/chat/completions",
            "model": "deepseek-v3-250324"
        }
    }
    
    request_data = {
        "config": config,
        "agent_configs": selected_agents  # 使用正确的字段名
    }
    
    print("仿真配置:")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    try:
        print("\n🚀 发送仿真启动请求...")
        response = requests.post(
            f"{API_BASE_URL}/api/simulation/start", 
            json=request_data,
            timeout=30
        )
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            simulation_id = result.get('simulation_id')
            if simulation_id:
                print(f"✅ 仿真启动成功！")
                print(f"   仿真ID: {simulation_id}")
                return simulation_id
            else:
                print("❌ 仿真启动失败：响应中没有simulation_id")
                return None
        else:
            print(f"❌ 仿真启动失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 启动仿真时出错: {e}")
        return None

def monitor_simulation(simulation_id):
    """监控仿真状态"""
    print(f"\n=== 监控仿真状态 (ID: {simulation_id}) ===")
    
    start_time = time.time()
    check_count = 0
    
    while True:
        check_count += 1
        elapsed = time.time() - start_time
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/simulation/status/{simulation_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'data' in result:
                    status_data = result['data']
                    status = status_data.get('status', 'unknown')
                else:
                    status_data = result
                    status = status_data.get('status', 'unknown')
                
                print(f"\n📊 检查 #{check_count} (耗时: {elapsed:.1f}s)")
                print(f"   状态: {status}")
                
                if 'start_time' in status_data:
                    print(f"   开始时间: {status_data['start_time']}")
                
                if 'results' in status_data:
                    results = status_data['results']
                    if results:
                        print(f"   总时间片: {results.get('total_slices', 'N/A')}")
                        print(f"   Agent数量: {results.get('agent_count', 'N/A')}")
                
                # 检查详细日志
                if 'detailed_log' in status_data and status_data['detailed_log']:
                    log_lines = status_data['detailed_log'].split('\n')
                    llm_lines = [line for line in log_lines if 'LLM' in line or '🤖' in line or 'DeepSeek' in line]
                    
                    if llm_lines:
                        print(f"   🤖 发现LLM相关日志 ({len(llm_lines)} 行):")
                        for line in llm_lines[-3:]:  # 显示最后3行LLM日志
                            print(f"       {line.strip()}")
                    else:
                        print("   📝 暂无LLM调用日志")
                
                # 检查是否完成
                if status in ['completed', 'error']:
                    print(f"\n🎯 仿真 {status}!")
                    
                    if status == 'completed':
                        print("仿真成功完成")
                        if 'detailed_log' in status_data:
                            log_content = status_data['detailed_log']
                            # 保存详细日志到文件
                            log_filename = f"debug_simulation_log_{simulation_id[:8]}.txt"
                            with open(log_filename, 'w', encoding='utf-8') as f:
                                f.write(log_content)
                            print(f"📄 详细日志已保存到: {log_filename}")
                    else:
                        print("仿真执行出错")
                        if 'error' in status_data:
                            print(f"错误信息: {status_data['error']}")
                    
                    break
                    
            else:
                print(f"❌ 获取仿真状态失败，状态码: {response.status_code}")
                print(f"   响应: {response.text}")
                break
                
        except Exception as e:
            print(f"❌ 监控仿真时出错: {e}")
            break
        
        # 等待1秒后继续检查
        time.sleep(1)
        
        # 超时保护（最多监控60秒）
        if elapsed > 60:
            print("\n⏰ 监控超时（60秒），停止监控")
            break

def main():
    """主函数"""
    print("🔍 前端仿真调试工具")
    print("=" * 50)
    
    # 1. 检查后端服务
    if not check_backend_status():
        print("\n❌ 后端服务不可用，请先启动后端服务")
        print("   运行命令: python run_server.py")
        return
    
    # 2. 启动调试仿真
    simulation_id = start_debug_simulation()
    if not simulation_id:
        print("\n❌ 仿真启动失败，无法继续调试")
        return
    
    # 3. 监控仿真状态
    monitor_simulation(simulation_id)
    
    print("\n🔍 调试完成！")
    print("如果仍有问题，请检查：")
    print("1. 前端控制台是否有错误信息")
    print("2. 后端控制台是否有错误信息")
    print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()
