#!/usr/bin/env python3
"""
仿真日志元数据提取器
从simulation_log_*.txt文件中提取前端飓风消息功能需要的仿真信息
"""

import os
import re
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional


class SimulationLogExtractor:
    """仿真日志元数据提取器"""
    
    def __init__(self):
        self.metadata_start_pattern = r"=== SIMULATION_METADATA_START ==="
        self.metadata_end_pattern = r"=== SIMULATION_METADATA_END ==="
        self.completion_start_pattern = r"=== SIMULATION_COMPLETION_METADATA_START ==="
        self.completion_end_pattern = r"=== SIMULATION_COMPLETION_METADATA_END ==="
    
    def extract_json_block(self, content: str, start_pattern: str, end_pattern: str) -> Optional[Dict]:
        """从文本中提取JSON块"""
        start_match = re.search(start_pattern, content)
        end_match = re.search(end_pattern, content)
        
        if not start_match or not end_match:
            return None
        
        start_pos = start_match.end()
        end_pos = end_match.start()
        
        json_text = content[start_pos:end_pos].strip()
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
    
    def extract_from_file(self, log_file_path: str) -> Dict[str, Any]:
        """从单个日志文件提取元数据"""
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取基本元数据
            metadata = self.extract_json_block(content, self.metadata_start_pattern, self.metadata_end_pattern)
            
            # 提取完成状态元数据
            completion_data = self.extract_json_block(content, self.completion_start_pattern, self.completion_end_pattern)
            
            # 合并数据
            result = {
                "log_file": log_file_path,
                "file_size": os.path.getsize(log_file_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(log_file_path)).isoformat(),
                "extracted_at": datetime.now().isoformat()
            }
            
            if metadata:
                result.update(metadata)
            
            if completion_data:
                result.update(completion_data)
                # 如果有完成数据，更新状态
                result["status"] = completion_data.get("status", "completed")
            else:
                # 如果没有完成数据，可能仍在运行或异常终止
                if metadata:
                    result["status"] = "running"
                else:
                    result["status"] = "unknown"
            
            return result
            
        except Exception as e:
            return {
                "log_file": log_file_path,
                "error": str(e),
                "status": "error",
                "extracted_at": datetime.now().isoformat()
            }
    
    def extract_all_simulations(self, pattern: str = "simulation_log_*.txt") -> List[Dict[str, Any]]:
        """提取所有仿真的元数据"""
        log_files = glob.glob(pattern)
        simulations = []
        
        for log_file in log_files:
            simulation_data = self.extract_from_file(log_file)
            simulations.append(simulation_data)
        
        # 按时间排序（最新的在前）
        simulations.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return simulations
    
    def get_completed_simulations(self) -> List[Dict[str, Any]]:
        """获取所有已完成的仿真"""
        all_sims = self.extract_all_simulations()
        return [sim for sim in all_sims if sim.get("status") == "completed"]
    
    def get_simulation_by_id(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取特定仿真的信息"""
        all_sims = self.extract_all_simulations()
        for sim in all_sims:
            if sim.get("simulation_id") == simulation_id:
                return sim
        return None
    
    def save_simulations_index(self, output_file: str = "simulations_index.json") -> str:
        """保存仿真索引到JSON文件"""
        simulations = self.extract_all_simulations()
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_simulations": len(simulations),
            "completed_simulations": len([s for s in simulations if s.get("status") == "completed"]),
            "simulations": simulations
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        return output_file


def create_frontend_api_adapter():
    """创建前端API适配器，将提取的数据转换为前端期望的格式"""
    
    def get_simulation_list():
        """获取仿真列表（前端API格式）"""
        extractor = SimulationLogExtractor()
        simulations = extractor.extract_all_simulations()
        
        # 转换为前端期望的格式
        frontend_simulations = []
        for sim in simulations:
            frontend_sim = {
                "id": sim.get("simulation_id", "unknown"),
                "name": sim.get("name", "未命名仿真"),
                "status": sim.get("status", "unknown"),
                "start_time": sim.get("start_time", ""),
                "end_time": sim.get("end_time", ""),
                "agent_count": sim.get("agent_count", 0),
                "total_time_slices": sim.get("total_time_slices", 0),
                "duration_seconds": sim.get("duration_seconds", 0),
                "log_file": sim.get("log_file", "")
            }
            frontend_simulations.append(frontend_sim)
        
        return {"simulations": frontend_simulations}
    
    def get_simulation_time_slices(simulation_id: str):
        """获取仿真时间片信息（前端API格式）"""
        extractor = SimulationLogExtractor()
        sim = extractor.get_simulation_by_id(simulation_id)
        
        if not sim:
            raise ValueError(f"仿真 {simulation_id} 不存在")
        
        time_slices = sim.get("time_slices", [])
        
        return {
            "simulation_id": simulation_id,
            "total_time_slices": len(time_slices),
            "time_slices": time_slices
        }
    
    def get_simulation_details(simulation_id: str):
        """获取仿真详细信息（前端API格式）"""
        extractor = SimulationLogExtractor()
        sim = extractor.get_simulation_by_id(simulation_id)
        
        if not sim:
            raise ValueError(f"仿真 {simulation_id} 不存在")
        
        return sim
    
    return {
        "get_simulation_list": get_simulation_list,
        "get_simulation_time_slices": get_simulation_time_slices,
        "get_simulation_details": get_simulation_details
    }


def main():
    """命令行工具主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="仿真日志元数据提取器")
    parser.add_argument("--list", action="store_true", help="列出所有仿真")
    parser.add_argument("--completed", action="store_true", help="只显示已完成的仿真")
    parser.add_argument("--id", type=str, help="显示特定ID的仿真详情")
    parser.add_argument("--save-index", action="store_true", help="保存仿真索引到JSON文件")
    parser.add_argument("--output", type=str, default="simulations_index.json", help="输出文件名")
    
    args = parser.parse_args()
    
    extractor = SimulationLogExtractor()
    
    if args.id:
        # 显示特定仿真
        sim = extractor.get_simulation_by_id(args.id)
        if sim:
            print(json.dumps(sim, ensure_ascii=False, indent=2))
        else:
            print(f"仿真 {args.id} 不存在")
    
    elif args.completed:
        # 显示已完成的仿真
        simulations = extractor.get_completed_simulations()
        print(f"找到 {len(simulations)} 个已完成的仿真:")
        for sim in simulations:
            print(f"  {sim.get('simulation_id', 'unknown')}: {sim.get('name', '未命名')} ({sim.get('status', 'unknown')})")
    
    elif args.list:
        # 显示所有仿真
        simulations = extractor.extract_all_simulations()
        print(f"找到 {len(simulations)} 个仿真:")
        for sim in simulations:
            status = sim.get('status', 'unknown')
            name = sim.get('name', '未命名')
            sim_id = sim.get('simulation_id', 'unknown')
            print(f"  {sim_id}: {name} ({status})")
    
    elif args.save_index:
        # 保存索引
        output_file = extractor.save_simulations_index(args.output)
        print(f"仿真索引已保存到: {output_file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
