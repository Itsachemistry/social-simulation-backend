# 社交仿真引擎学习检查清单
## 📋 学习进度跟踪

### 第一阶段：基础概念理解 ✅

#### 1.1 项目架构理解
- [ ] 理解四个核心模块的职责分工
- [ ] 掌握时间片机制的工作原理
- [ ] 理解Agent类型和优先级
- [ ] 理解个性化信息流的概念

#### 1.2 核心概念掌握
- [ ] 时间片 (Time Slice)
- [ ] Agent类型：意见领袖、规则Agent、普通用户
- [ ] 世界状态 (World State)
- [ ] 个性化信息流 (Personalized Feed)
- [ ] 突发事件注入 (Event Injection)

### 第二阶段：核心模块学习

#### 2.1 时间管理器 (`time_manager.py`) ✅
- [ ] 理解 `__init__` 方法的参数和逻辑
- [ ] 掌握 `get_slice()` 方法的工作原理
- [ ] 理解帖子排序机制
- [ ] 掌握时间片计算逻辑

**关键代码理解**：
```python
# 按时间戳排序帖子
self._posts = sorted(posts, key=lambda x: x['timestamp'])

# 计算总时间片数
self._total_slices = (len(self._posts) + slice_size - 1) // slice_size
```

#### 2.2 世界状态管理器 (`world_state.py`) ✅
- [ ] 理解帖子数据结构
- [ ] 掌握 `add_post()` 方法的逻辑
- [ ] 理解 `inject_event()` 的特殊处理
- [ ] 掌握帖子池管理机制

**关键代码理解**：
```python
# 帖子数据结构
{
    "id": str,              # 帖子唯一标识符
    "content": str,         # 帖子内容
    "author_id": str,       # 作者ID
    "timestamp": str,       # ISO格式时间戳
    "heat": int,           # 热度值 (0-100)
    "likes": int,          # 点赞数
    "shares": int,         # 分享数
    "is_event": bool,      # 是否为突发事件
    "priority": int        # 优先级
}
```

#### 2.3 Agent类 (`agent.py`) 🔄
- [ ] 理解Agent的状态属性（情绪、置信度、精力）
- [ ] 掌握 `update_state()` 方法的状态更新逻辑
- [ ] 理解 `_calculate_post_impact()` 的影响计算
- [ ] 掌握 `generate_action_prompt()` 的决策逻辑
- [ ] 理解兴趣匹配和立场相似度计算

**关键概念**：
- **情绪值** (emotion): 0-1，表示Agent的正面/负面情绪
- **置信度** (confidence): 0-1，表示Agent对当前信息的信任程度
- **精力值** (energy): 0-1，表示Agent的行动能力
- **立场值** (stance): 0-1，表示Agent的政治/社会立场

#### 2.4 Agent控制器 (`agent_controller.py`) 🔄
- [ ] 理解Agent分组和优先级机制
- [ ] 掌握 `run_time_slice()` 的调度逻辑
- [ ] 理解 `_generate_personalized_feed()` 的筛选算法
- [ ] 掌握个性化信息流的三个筛选条件
- [ ] 理解Agent行动执行流程

**关键算法理解**：
```python
# 1. 热度筛选
if post_heat < heat_threshold:
    continue

# 2. 立场相似度筛选
similarity_score = self._calculate_stance_similarity(agent, post)
if similarity_score < similarity_threshold:
    continue

# 3. 兴趣匹配筛选
if not self._check_interest_match(agent, post):
    continue
```

### 第三阶段：服务层理解

#### 3.1 LLM服务 (`llm_service.py`)
- [ ] 理解LLM服务的抽象设计
- [ ] 掌握Mock模式和真实API模式的区别
- [ ] 理解Prompt生成和内容生成流程

#### 3.2 数据服务 (`services.py`)
- [ ] 理解数据加载器的设计
- [ ] 掌握配置文件解析逻辑
- [ ] 理解错误处理机制

### 第四阶段：主程序理解

#### 4.1 仿真引擎 (`main.py`)
- [ ] 理解 `SimulationEngine` 类的初始化流程
- [ ] 掌握 `run_simulation()` 的主循环逻辑
- [ ] 理解模块间的协调机制
- [ ] 掌握结果收集和保存逻辑

**关键流程理解**：
```python
# 主仿真循环
while self.current_slice < self.total_slices:
    # 1. 获取当前时间片帖子
    current_slice_posts = self.time_manager.get_slice(self.current_slice)
    
    # 2. 获取所有历史帖子
    all_posts = self.world_state.get_all_posts()
    
    # 3. 执行时间片调度
    slice_results = self.agent_controller.run_time_slice(
        current_slice_posts, all_posts
    )
    
    # 4. 记录结果
    self.simulation_results.append({...})
    
    # 5. 移动到下一个时间片
    self.current_slice += 1
```

### 第五阶段：实践和调试

#### 5.1 运行示例
- [ ] 成功运行 `test_with_config.py`
- [ ] 理解输出结果的含义
- [ ] 分析Agent行为模式
- [ ] 观察时间片推进过程

#### 5.2 配置理解
- [ ] 理解 `config/agents.json` 的配置结构
- [ ] 掌握不同类型Agent的参数设置
- [ ] 理解LLM配置选项

#### 5.3 调试技巧
- [ ] 学会使用print语句调试
- [ ] 理解日志输出的含义
- [ ] 掌握错误定位方法

### 第六阶段：深入理解

#### 6.1 算法深入
- [ ] 理解个性化信息流的权重计算
- [ ] 掌握Agent状态更新的数学原理
- [ ] 理解时间片调度的优化策略

#### 6.2 扩展思考
- [ ] 如何添加新的Agent类型？
- [ ] 如何优化个性化推荐算法？
- [ ] 如何增加更复杂的交互机制？
- [ ] 如何提高仿真性能？

## 🎯 学习目标

### 短期目标 (1-2周)
- [ ] 能够理解所有核心模块的代码逻辑
- [ ] 能够运行和调试仿真程序
- [ ] 能够修改Agent配置和参数
- [ ] 能够分析仿真结果

### 中期目标 (1个月)
- [ ] 能够添加新的Agent类型
- [ ] 能够优化个性化推荐算法
- [ ] 能够扩展仿真功能
- [ ] 能够处理大规模数据

### 长期目标 (2-3个月)
- [ ] 能够设计新的仿真场景
- [ ] 能够优化系统性能
- [ ] 能够集成新的AI模型
- [ ] 能够进行学术研究

## 📝 学习笔记模板

### 模块学习笔记
```
模块名称：___________
学习日期：___________

#### 核心功能
- 功能1：___________
- 功能2：___________

#### 关键方法
- 方法1：___________
  - 参数：___________
  - 返回值：___________
  - 逻辑：___________

#### 重要概念
- 概念1：___________
- 概念2：___________

#### 疑问和思考
- 问题1：___________
- 问题2：___________

#### 实践心得
- 心得1：___________
- 心得2：___________
```

## 🔍 常见问题解答

### Q1: 如何理解时间片机制？
A: 时间片是将连续时间离散化处理的方法。每个时间片包含固定数量的帖子，仿真按时间片顺序推进，每个时间片内所有Agent依次行动。

### Q2: 个性化信息流是如何生成的？
A: 通过三个筛选条件：1) 热度筛选（帖子热度达到阈值），2) 立场相似度筛选（帖子与Agent立场相似），3) 兴趣匹配筛选（帖子匹配Agent兴趣）。

### Q3: Agent的状态是如何更新的？
A: Agent根据接收到的帖子计算影响值，更新情绪、置信度和精力。影响值基于帖子热度、立场相似度和兴趣匹配度计算。

### Q4: 如何添加新的Agent类型？
A: 1) 在Agent配置中添加新类型，2) 在AgentController中添加新类型的处理逻辑，3) 设置新类型的优先级和参数。

## 📚 推荐学习资源

1. **Python基础**：确保掌握类、继承、装饰器等概念
2. **数据结构**：理解列表、字典、集合的使用
3. **算法基础**：了解排序、搜索、筛选算法
4. **设计模式**：理解工厂模式、策略模式等
5. **仿真理论**：了解离散事件仿真的基本原理 

## 2024-06-09 Agent影响追踪与parent_post_id标准化实现记录

### 主要内容
1. 标准化了Agent在每个时间片内对每条帖子影响分数的计算方式：
   - 影响分数 = abs(delta_emotion) + abs(delta_confidence)
   - 在update_state中自动追踪本时间片影响最大的帖子ID（max_impact_post_id）及其分数。
2. 优化了update_state的返回值，明确包含delta_emotion、delta_confidence，便于主流程追踪。
3. 建议在Agent生成新帖子时，parent_post_id应指向max_impact_post_id，实现传播树的合理连接。

### 设计思路
- 帖子的情感和立场在仿真前已由LLM+人工标注，仿真过程中直接读取。
- Agent每处理一条帖子，都会调用update_state，自动计算并记录本次状态变化量。
- 影响分数用于追踪本时间片内对Agent影响最大的帖子，便于后续生成新帖时作为parent_post_id。
- 该机制填补了论文中"Agent新发帖应回复谁"这一实现细节的空白，保证了传播链路的合理性和可追溯性。

### 后续建议
- 可在Agent基类中进一步模板化"坚定/不坚定"立场更新规则，便于开发者复用。
- 可在主流程中自动将新帖parent_post_id赋值为max_impact_post_id。 