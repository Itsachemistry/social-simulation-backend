#!/usr/bin/env python3
"""
测试官方声明LLM注解功能（使用重用的data/promptdataprocess.txt模板）
"""

import os
import requests
import json

def test_official_statement_llm_annotation():
    """测试官方声明LLM注解功能"""
    print("=== 官方声明LLM注解功能测试（重用现有模板）===")
    
    # 检查环境变量
    api_key = os.getenv('LLM_API_KEY')
    endpoint = os.getenv('LLM_ENDPOINT')
    model = os.getenv('LLM_MODEL', 'deepseek-v3')
    
    print(f"1. API Key: {'已设置' if api_key else '未设置'}")
    print(f"2. Endpoint: {endpoint}")
    print(f"3. Model: {model}")
    
    if not api_key or not endpoint:
        print("❌ LLM API未配置")
        return False
    
    # 读取现有的promptdataprocess模板
    try:
        with open('data/promptdataprocess.txt', 'r', encoding='utf-8') as f:
            template = f.read()
        print(f"4. 现有Prompt模板已加载，长度: {len(template)} 字符")
    except FileNotFoundError:
        print("❌ 未找到 data/promptdataprocess.txt 文件")
        return False
    
    # 测试内容
    test_content = "经过详细调查，医院在此次事件中严格按照医疗规程操作，纱布填塞是为了挽救产妇生命的必要措施。我们已与患者家属充分沟通，愿意承担相应责任并积极配合后续治疗。"
    
    # 为官方声明构建prompt（省略对话上下文）
    annotation_prompt = template.replace(
        '[目标帖子 (回复 4)]: 走正常途径不如闹来钱多又快',
        f'[目标帖子 (官方声明)]: {test_content}'
    ).replace(
        '[目标帖子]: "走正常途径不如闹来钱多又快"',
        f'[目标帖子]: "{test_content}"'
    )
    
    # 简化对话上下文部分
    context_start = annotation_prompt.find('## 2. 对话上下文 (Conversational Context)')
    context_end = annotation_prompt.find('## 3. 你的任务 (Your Task)')
    
    if context_start != -1 and context_end != -1:
        simplified_context = """## 2. 对话上下文 (Conversational Context)
这是一个官方声明，无需考虑对话上下文，请直接分析官方声明的内容倾向。

"""
        annotation_prompt = (annotation_prompt[:context_start] + 
                            simplified_context + 
                            annotation_prompt[context_end:])
    
    print(f"5. 测试内容: {test_content}")
    print(f"6. 完整Prompt长度: {len(annotation_prompt)} 字符")
    
    try:
        print(f"7. 开始调用LLM API...")
        
        response = requests.post(
            endpoint,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
            json={'model': model, 'messages': [{'role': 'user', 'content': annotation_prompt}]},
            timeout=30
        )
        response.raise_for_status()
        
        api_response = response.json()
        llm_content = api_response['choices'][0]['message']['content']
        
        print(f"8. LLM原始响应:")
        print(f"   {llm_content}")
        
        # 使用与agent_controller相同的JSON解析逻辑
        try:
            if '{' in llm_content and '}' in llm_content:
                json_start = llm_content.find('{')
                json_end = llm_content.rfind('}') + 1
                json_str = llm_content[json_start:json_end]
                annotations = json.loads(json_str)
                
                print(f"9. ✅ JSON解析成功:")
                print(f"   - 情绪分数: {annotations.get('emotion_score')}")
                print(f"   - 立场分数: {annotations.get('stance_score')}")
                print(f"   - 立场类别: {annotations.get('stance_category')}")
                print(f"   - 立场置信度: {annotations.get('stance_confidence')}")
                print(f"   - 信息强度: {annotations.get('information_strength')}")
                print(f"   - 关键词: {annotations.get('keywords')}")
                
                return True
            else:
                print(f"❌ 响应中未找到JSON格式")
                return False
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"   响应内容: {llm_content}")
            return False
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

if __name__ == "__main__":
    test_official_statement_llm_annotation()
