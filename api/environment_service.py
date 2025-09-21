from flask import Blueprint, request, jsonify
import os
import json

environment_bp = Blueprint('environment', __name__)

# 全局环境配置存储
ENVIRONMENT_CONFIG_FILE = 'config/environment.json'
default_environment_config = {
    "seed": 42,
    "population_size": 100,
    "duration": 1000,
    "network_topology": "small_world",
    "influence_radius": 2.0,
    "emotion_decay": 0.95,
    "stance_threshold": 0.5,
    "llm": {
        "model": "qwen",
        "base_url": "http://localhost:11434",
        "temperature": 0.7
    }
}

def load_environment_config():
    """加载环境配置"""
    if os.path.exists(ENVIRONMENT_CONFIG_FILE):
        try:
            with open(ENVIRONMENT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载环境配置失败: {e}")
    return default_environment_config.copy()

def save_environment_config(config):
    """保存环境配置"""
    try:
        os.makedirs(os.path.dirname(ENVIRONMENT_CONFIG_FILE), exist_ok=True)
        with open(ENVIRONMENT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存环境配置失败: {e}")
        return False

@environment_bp.route('/environment', methods=['GET'])
def get_environment():
    """获取环境配置"""
    try:
        config = load_environment_config()
        return jsonify({
            'status': 'success',
            **config
        })
    except Exception as e:
        return jsonify({'error': f'获取环境配置失败: {str(e)}'}), 500

@environment_bp.route('/environment', methods=['POST'])
def update_environment():
    """更新环境配置"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证必要字段
        required_fields = ['seed', 'population_size', 'duration']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要字段: {field}'}), 400
        
        # 验证数据类型
        if not isinstance(data['seed'], int):
            return jsonify({'error': 'seed必须是整数'}), 400
        if not isinstance(data['population_size'], int) or data['population_size'] <= 0:
            return jsonify({'error': 'population_size必须是正整数'}), 400
        if not isinstance(data['duration'], int) or data['duration'] <= 0:
            return jsonify({'error': 'duration必须是正整数'}), 400
        
        # 保存配置
        if save_environment_config(data):
            return jsonify({
                'status': 'success',
                'message': '环境配置已保存',
                'config': data
            })
        else:
            return jsonify({'error': '保存环境配置失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新环境配置失败: {str(e)}'}), 500

@environment_bp.route('/environment/reset', methods=['POST'])
def reset_environment():
    """重置环境配置到默认值"""
    try:
        if save_environment_config(default_environment_config):
            return jsonify({
                'status': 'success',
                'message': '环境配置已重置',
                'config': default_environment_config
            })
        else:
            return jsonify({'error': '重置环境配置失败'}), 500
    except Exception as e:
        return jsonify({'error': f'重置环境配置失败: {str(e)}'}), 500
