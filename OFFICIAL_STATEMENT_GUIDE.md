# 官方声明系统使用指南

## 概述

新的官方声明系统替代了之前的"飓风消息"功能，专门用于社交媒体仿真中的**官方舆论干预**测试。这个系统允许研究人员模拟政府机构或权威组织发布澄清、辟谣或官方通知，观察这些干预对agent群体情绪和立场的影响。

## 核心概念

### 1. 官方声明 vs 飓风消息
- **旧系统（飓风消息）**：误导性命名，实际是灾难预警
- **新系统（官方声明）**：准确反映功能 - 官方舆论干预和辟谣澄清

### 2. 声明类型
- **澄清说明 (clarification)**：对事件进行官方澄清，情绪影响轻微正面
- **辟谣声明 (refutation)**：官方辟谣虚假信息，负面转正面情绪，正面立场引导
- **官方通知 (official_notice)**：发布官方政策或通知，中性情绪，轻微正面立场

### 3. 权威级别
- **高权威 (high)**：政府机构、官方媒体，影响力100%
- **中权威 (medium)**：专业机构、知名专家，影响力70%
- **低权威 (low)**：一般组织、普通账号，影响力40%

## API使用指南

### 1. 获取配置面板数据
```http
GET /api/simulation/official_statement/config_panel
```

返回：
- 可用的已完成仿真列表
- 支持的声明类型和权威级别选项

### 2. 获取仿真详情
```http
GET /api/simulation/official_statement/simulation_details/{simulation_id}
```

返回：
- 仿真的时间片信息
- Agent数量等基本信息

### 3. 注入官方声明
```http
POST /api/simulation/inject_official_statement
```

请求体：
```json
{
  "original_simulation_id": "sim_20250730_110327",
  "statement_config": {
    "content": "【官方澄清】经核实，网传相关信息不属实，请广大网友理性判断，不信谣不传谣。",
    "target_time_slice": 3,
    "statement_type": "refutation",
    "authority_level": "high"
  }
}
```

## 工作流程

1. **基础仿真**：运行原始仿真，获得基线数据
2. **配置干预**：选择仿真，配置官方声明的内容、时间片、类型和权威级别
3. **对比仿真**：系统自动创建新仿真，在指定时间片注入官方声明
4. **效果分析**：对比原始仿真和干预仿真的agent状态变化

## 技术实现

### 1. 数据结构
官方声明具有以下特殊属性：
- `is_official_statement: true` - 标识为官方声明
- `force_read: true` - 强制所有agent阅读
- `priority: 999` - 最高优先级
- `authority_level` - 影响力级别
- `statement_type` - 声明类型

### 2. 影响机制
- **情绪影响**：根据声明类型和权威级别计算
- **立场影响**：官方声明倾向于正面引导立场
- **屏蔽绕过**：官方声明不受agent的屏蔽机制影响
- **可信度加成**：权威来源降低情绪波动，增强立场影响

### 3. 注入机制
- 使用`pre_injected_events`在仿真开始前预设事件
- 在指定时间片自动注入到帖子池
- 同时更新世界状态和时间片数据

## 迁移指南

### 废弃的API
- `/inject_hurricane` - 保留兼容性，但建议迁移
- `/inject_hurricane_with_llm` - 已废弃，返回410状态码
- `/inject_multiple_hurricanes` - 已废弃，返回410状态码

### 推荐的新API
- `/inject_official_statement` - 替代所有旧的飓风消息API

## 示例用法

### Python示例
```python
import requests

# 1. 获取可用仿真
response = requests.get("http://localhost:5000/api/simulation/official_statement/config_panel")
simulations = response.json()["simulations"]

# 2. 选择仿真并获取详情
sim_id = simulations[0]["id"]
response = requests.get(f"http://localhost:5000/api/simulation/official_statement/simulation_details/{sim_id}")
details = response.json()

# 3. 注入官方澄清
payload = {
    "original_simulation_id": sim_id,
    "statement_config": {
        "content": "【官方澄清】经核实，网传相关信息不属实。",
        "target_time_slice": 2,
        "statement_type": "clarification", 
        "authority_level": "high"
    }
}
response = requests.post("http://localhost:5000/api/simulation/inject_official_statement", json=payload)
result = response.json()
print(f"新仿真ID: {result['new_simulation_id']}")
```

## 测试脚本

运行 `test_official_statement.py` 进行完整的功能测试：

```bash
python test_official_statement.py
```

## 注意事项

1. **时间片选择**：确保目标时间片在仿真范围内
2. **内容长度**：官方声明内容建议控制在200字以内
3. **权威性**：选择合适的权威级别以获得预期的影响效果
4. **对比分析**：建议保存原始仿真和干预仿真的结果进行对比

## 未来扩展

- 支持批量官方声明注入
- 添加声明发布时机的智能推荐
- 增加多轮干预的链式效应分析
- 提供可视化的影响力对比图表
