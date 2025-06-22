try:
    import pytest
except ImportError:
    # 如果pytest未安装，提供安装指导
    raise ImportError(
        "pytest未安装。请运行以下命令安装：\n"
        "pip install pytest\n"
        "或者\n"
        "pip install -r requirements.txt"
    )
import json
import tempfile
import os
from pathlib import Path
from src.services import DataLoader


class TestDataLoader:
    """DataLoader类的测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.data_loader = DataLoader()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_temp_json_file(self, data, filename):
        """创建临时JSON文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    def test_load_post_data_success(self):
        """测试成功加载帖子数据"""
        # 准备测试数据
        test_posts = [
            {
                "id": "post_001",
                "content": "这是一条测试帖子",
                "author": "user_001",
                "timestamp": "2024-01-01T10:00:00Z",
                "likes": 10,
                "shares": 5
            },
            {
                "id": "post_002", 
                "content": "这是另一条测试帖子",
                "author": "user_002",
                "timestamp": "2024-01-01T11:00:00Z",
                "likes": 20,
                "shares": 8
            }
        ]
        
        # 创建临时文件
        file_path = self.create_temp_json_file(test_posts, "test_posts.json")
        
        # 执行测试
        result = self.data_loader.load_post_data(file_path)
        
        # 验证结果
        assert result == test_posts
        assert len(result) == 2
        assert result[0]["id"] == "post_001"
        assert result[1]["content"] == "这是另一条测试帖子"
    
    def test_load_agent_config_success(self):
        """测试成功加载Agent配置"""
        # 准备测试数据
        test_config = {
            "agents": [
                {
                    "id": "agent_001",
                    "type": "opinion_leader",
                    "name": "意见领袖A",
                    "personality": {
                        "openness": 0.8,
                        "conscientiousness": 0.7
                    }
                },
                {
                    "id": "agent_002",
                    "type": "regular_user", 
                    "name": "普通用户B",
                    "personality": {
                        "openness": 0.5,
                        "conscientiousness": 0.6
                    }
                }
            ],
            "simulation_settings": {
                "time_slice_size": 50,
                "max_iterations": 100
            }
        }
        
        # 创建临时文件
        file_path = self.create_temp_json_file(test_config, "test_agents.json")
        
        # 执行测试
        result = self.data_loader.load_agent_config(file_path)
        
        # 验证结果
        assert result == test_config
        assert "agents" in result
        assert "simulation_settings" in result
        assert len(result["agents"]) == 2
        assert result["agents"][0]["type"] == "opinion_leader"
    
    def test_load_post_data_file_not_found(self):
        """测试加载帖子数据时文件不存在的情况"""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        
        # 验证抛出FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            self.data_loader.load_post_data(non_existent_file)
        
        assert "帖子数据文件未找到" in str(exc_info.value)
    
    def test_load_agent_config_file_not_found(self):
        """测试加载Agent配置时文件不存在的情况"""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        
        # 验证抛出FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            self.data_loader.load_agent_config(non_existent_file)
        
        assert "Agent配置文件未找到" in str(exc_info.value)
    
    def test_load_post_data_invalid_json(self):
        """测试加载无效JSON格式的帖子数据"""
        # 创建包含无效JSON的文件
        file_path = os.path.join(self.temp_dir, "invalid.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json content}')
        
        # 验证抛出JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            self.data_loader.load_post_data(file_path)
    
    def test_load_agent_config_invalid_json(self):
        """测试加载无效JSON格式的Agent配置"""
        # 创建包含无效JSON的文件
        file_path = os.path.join(self.temp_dir, "invalid_config.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json content}')
        
        # 验证抛出JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            self.data_loader.load_agent_config(file_path)
