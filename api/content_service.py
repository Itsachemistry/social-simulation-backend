from flask import Blueprint, jsonify
import os
import re

content_bp = Blueprint('content', __name__)

@content_bp.route('/event-background', methods=['GET'])
def get_event_background():
    """获取事件背景信息"""
    try:
        # 读取prompt模板文件
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'agent_prompt_template.txt')
        
        if not os.path.exists(template_path):
            return jsonify({'error': '未找到prompt模板文件'}), 404
            
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取事件背景部分
        # 匹配从"## 1. 事件背景"开始到"## 2."之前的所有内容
        pattern = r'## 1\. 事件背景.*?(?=## 2\.)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return jsonify({'error': '未找到事件背景信息'}), 404
            
        background_text = match.group(0)
        
        # 清理格式，移除markdown标题
        background_text = re.sub(r'## 1\. 事件背景 \(Event Background\)\s*', '', background_text)
        background_text = background_text.strip()
        
        # 解析结构化信息
        lines = background_text.split('\n')
        parsed_info = {
            'event_name': '',
            'time_location': '',
            'event_process': [],
            'stance_summary': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('事件名称:'):
                parsed_info['event_name'] = line.replace('事件名称:', '').strip()
            elif line.startswith('时间与地点:'):
                parsed_info['time_location'] = line.replace('时间与地点:', '').strip()
            elif line.startswith('事件经过:'):
                current_section = 'process'
            elif line.startswith('三方立场摘要:'):
                current_section = 'stance'
            elif line.startswith('- ') and current_section == 'process':
                parsed_info['event_process'].append(line[2:])
            elif line.startswith('- ') and current_section == 'stance':
                parsed_info['stance_summary'].append(line[2:])
        
        return jsonify({
            'raw_text': background_text,
            'parsed_info': parsed_info
        })
        
    except Exception as e:
        return jsonify({'error': f'获取事件背景失败: {str(e)}'}), 500

@content_bp.route('/topic-summary', methods=['GET'])
def get_topic_summary():
    """获取主题摘要信息，用于前端主题内容区域显示"""
    try:
        # 获取事件背景
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'agent_prompt_template.txt')
        
        if not os.path.exists(template_path):
            return jsonify({'error': '未找到prompt模板文件'}), 404
            
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取事件名称和简要描述
        event_name_match = re.search(r'事件名称:\s*(.+)', content)
        time_location_match = re.search(r'时间与地点:\s*(.+)', content)
        
        event_name = event_name_match.group(1).strip() if event_name_match else '未知事件'
        time_location = time_location_match.group(1).strip() if time_location_match else '未知时间地点'
        
        # 构建主题摘要
        topic_summary = f"{event_name}\n{time_location}"
        
        return jsonify({
            'topic_title': event_name,
            'topic_summary': topic_summary,
            'time_location': time_location
        })
        
    except Exception as e:
        return jsonify({'error': f'获取主题摘要失败: {str(e)}'}), 500
