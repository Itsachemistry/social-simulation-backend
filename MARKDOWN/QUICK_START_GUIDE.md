# 社交仿真引擎快速开始指南

## 🚀 快速上手

### 第一步：环境准备

1. **确保Python环境**：
   ```bash
   python --version  # 确保Python 3.7+
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

### 第二步：运行第一个仿真

1. **运行测试程序**：
   ```bash
   python test_with_config.py
   ```

2. **观察输出**：
   - 查看Agent初始化信息
   - 观察时间片推进过程
   - 分析Agent行为模式

### 第三步：理解输出结果

运行后你会看到类似这样的输出：

```
=== 开始仿真 ===
总时间片数: 2
Agent数量: 7

--- 时间片 1/2 ---
=== 开始执行时间片调度 ===
当前时间片新帖子数: 5
历史帖子总数: 6

--- 处理 意见领袖 类型Agent ---
该类型共有 2 个Agent
  处理Agent: leader_001
    为Agent生成了 3 条个性化帖子
    Agent行动: 发帖
  处理Agent: leader_002
    为Agent生成了 2 条个性化帖子
    Agent行动: 浏览

=== 时间片调度完成 ===
处理Agent数: 7
生成行动数: 3
```

## 📊 关键概念速览

### 1. 时间片机制
```python
# 每个时间片包含固定数量的帖子
posts_per_slice = 5

# 仿真按时间片顺序推进
for slice_index in range(total_slices):
    current_posts = time_manager.get_slice(slice_index)
    # 处理当前时间片...
```

### 2. Agent类型和优先级
```python
action_priority = {
    "意见领袖": 1,    # 最高优先级，最先行动
    
            "普通用户": 2     # 最低优先级，最后行动
}
```

### 3. 个性化信息流生成
```python
# 三个筛选条件
if post_heat < heat_threshold: continue      # 热度筛选
if similarity < similarity_threshold: continue # 立场相似度筛选
if not interest_match: continue              # 兴趣匹配筛选
```

### 4. Agent状态更新
```python
# Agent的核心状态
emotion = 0.5      # 情绪值 (0-1)
confidence = 0.5   # 置信度 (0-1)
```

## 🔧 配置修改

### 修改Agent配置

编辑 `config/agents.json`：

```json
{
  "agent_id": "new_agent",
  "type": "普通用户",
  "stance": 0.6,
  "interests": ["科技", "创新"],
  "influence": 1.0,
  "post_probability": 0.3,
  "max_posts_per_slice": 1
}
```

### 修改仿真参数

编辑 `test_with_config.py`：

```python
config = {
    "posts_per_slice": 10,  # 增加每个时间片的帖子数
    "llm": {
        "use_mock": True,   # 使用Mock模式（快速测试）
        "use_mock": False   # 使用真实LLM（需要API密钥）
    }
}
```

## 📈 结果分析

### 查看仿真摘要
```python
summary = engine.get_simulation_summary()
print(f"总时间片数: {summary['total_slices']}")
print(f"总Agent数: {summary['total_agents']}")
print(f"总帖子数: {summary['total_posts']}")
print(f"总行动数: {summary['total_actions']}")
```

### 查看Agent状态
```python
for agent_type, agents in engine.agent_controller.agents.items():
    print(f"{agent_type}:")
    for agent in agents:
        state = agent.get_state_summary()
        print(f"  {agent.agent_id}: 情绪={state['emotion']:.2f}")
```

## 🐛 常见问题

### Q1: 运行时报错 "ModuleNotFoundError"
A: 确保在项目根目录运行，并且已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q2: 仿真运行很慢
A: 使用Mock模式进行快速测试：
```python
"llm": {"use_mock": True}
```

### Q3: 如何添加更多Agent？
A: 在 `config/agents.json` 中添加新的Agent配置，或修改 `main.py` 中的默认配置。

### Q4: 如何理解个性化信息流？
A: 观察输出中的 "为Agent生成了 X 条个性化帖子"，这表示经过筛选后该Agent能看到的帖子数量。

## 🎯 下一步学习

1. **阅读代码注释**：每个模块都有详细的中文注释
2. **修改参数**：尝试不同的配置参数，观察结果变化
3. **添加日志**：在关键位置添加print语句，理解执行流程
4. **阅读文档**：查看 `PROJECT_OVERVIEW.md` 了解项目架构

## 📚 学习路径

1. **Day 1**: 运行示例，理解基本概念
2. **Day 2-3**: 阅读核心模块代码，理解实现逻辑
3. **Day 4-5**: 修改配置，观察行为变化
4. **Day 6-7**: 尝试添加新功能，深入理解架构

记住：**实践是最好的学习方式**！多运行、多修改、多观察，你很快就能掌握这个项目。 