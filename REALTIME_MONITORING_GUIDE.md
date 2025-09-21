# 社交仿真引擎实时监控系统使用指南

## 📊 功能概述

实时监控系统已成功集成到社交仿真引擎中，提供完整的仿真过程可视化。

## 🚀 主要特性

### 1. 实时日志记录
- **自动生成日志文件**: 每次仿真运行时自动创建带时间戳的日志文件
- **格式**: `simulation_log_YYYYMMDD_HHMMSS.txt`
- **位置**: 仿真引擎根目录

### 2. 监控内容

#### Agent状态监控
- ✅ Agent情绪和立场变化
- ✅ 意见领袖决策过程  
- ✅ Agent个性化信息流生成
- ✅ 发帖概率计算和决策

#### LLM交互监控
- ✅ LLM请求和响应记录
- ✅ 完整的Prompt内容
- ✅ 生成的回复内容
- ✅ API调用状态

#### 仿真流程监控
- ✅ 时间片进度跟踪
- ✅ 宏观统计简报
- ✅ 帖子数量统计
- ✅ 性能指标记录

## 📋 使用方法

### 方法一：直接运行仿真
```python
from src.main import SimulationEngine

# 配置仿真参数
config = {
    "max_slices": 5,
    "llm_config": {
        "api_key": "your_api_key",
        "base_url": "https://www.chataiapi.com/v1/chat/completions",
        "model": "gpt-3.5-turbo"
    }
}

# 创建引擎并运行
engine = SimulationEngine(config)
results = engine.run_simulation(max_slices=5)

# 日志文件会自动生成
```

### 方法二：通过Web界面
1. 启动前端系统: `start_all_vue.bat`
2. 配置DeepSeek API参数
3. 开始仿真
4. 实时日志自动保存

### 方法三：使用测试脚本
```bash
# 基础实时监控测试
python test_realtime_monitoring.py

# 带发帖功能的监控测试  
python test_realtime_posting.py

# 带真实LLM调用的监控测试
python test_realtime_llm_monitoring.py
```

## 📈 日志内容示例

### 典型日志结构
```
=== 详细日志记录开始 ===
日志文件: simulation_log_20250127_224142.txt
包含: 所有LLM Prompt、响应、Agent状态变化

--- 时间片 1/5 ---
本时间片帖子数量: 3
活跃Agent数量: 4

=== 开始Agent情绪更新和发帖判定 ===
[宏观简报] {'average_emotion': 0.05, 'average_stance': 0.15, 'agent_count': 4}
[Leader] agent_003 读简报后状态: 情绪=0.287, 立场=0.500
[Feed] Agent agent_001 候选池大小: 2 (k=2, x0=auto)
Agent agent_001 不发帖 (波动量: 0.000, 阈值: 0.050)

[LLM Request] 开始处理prompt (长度: 245)
[Prompt] 作为社交媒体智能体，你的特征：
- 角色类型：普通用户
- 当前状态：情绪：0.8, 立场：0.7
请生成一段符合以上特征的社交媒体帖子内容...

[LLM Response] 生成完成 (长度: 87)
[Response] 今天看到这个新闻真的很激动！科技发展太快了，希望能带来更多正面变化！

📊 本时间片发帖统计: Agent_001发帖1条
```

## 🔧 配置选项

### DeepSeek API配置
```json
{
  "llm_config": {
    "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
    "base_url": "https://www.chataiapi.com/v1/chat/completions", 
    "model": "gpt-3.5-turbo",
    "enabled": true
  }
}
```

### 监控详细程度
- **基础监控**: Agent状态变化
- **详细监控**: 包含LLM交互详情
- **完整监控**: 包含所有调试信息

## 📊 监控统计信息

每次仿真完成后，系统会提供统计摘要：
- LLM调用次数
- Agent活动记录数
- 意见领袖决策次数  
- 发帖生成记录数
- 总日志行数和文件大小

## 🔍 故障排除

### 常见问题

1. **没有生成日志文件**
   - 检查文件写入权限
   - 确保仿真正常启动

2. **日志内容较少**
   - 增加仿真时间片数量
   - 调整Agent活跃度参数
   - 注入更多高热度事件

3. **LLM交互记录缺失**
   - 验证API配置正确
   - 检查网络连接
   - 确认API key有效

## 💡 最佳实践

1. **长时间仿真**: 定期检查日志文件大小，避免过大
2. **调试模式**: 使用较少Agent和时间片进行测试
3. **生产模式**: 配置合适的日志级别平衡性能和可观测性
4. **日志分析**: 可以编写脚本分析日志中的关键模式

## 🎯 下一步发展

- [ ] 添加日志轮转机制
- [ ] 实现实时Web界面显示  
- [ ] 支持自定义日志过滤
- [ ] 集成性能监控指标
- [ ] 添加日志可视化工具

---

**当前状态**: ✅ 实时监控系统已成功部署并可正常使用

您现在可以在任何仿真运行时实时查看详细的执行过程，包括Agent决策、LLM交互和系统状态变化！
