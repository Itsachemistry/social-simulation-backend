# 🚀 前端实时监控使用指南

## 📋 完整的实时监控流程

### 1. 启动系统

#### 启动后端服务
```bash
cd d:\social_simulation_engine
python run_server.py
```
后端会在 http://localhost:5000 启动

#### 启动前端界面
```bash
cd d:\social_simulation_engine
start_all_vue.bat
```
前端会在 http://localhost:3000 启动

### 2. 配置仿真参数

在前端界面中：

#### 2.1 LLM配置 (实时监控关键)

**完整LLM监控模式 (推荐)**
1. ✅ 勾选"启用LLM测试模式"
2. ✅ 勾选"完整LLM监控模式"
3. 配置LLM API信息：
```json
{
  "api_key": "sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK",
  "base_url": "https://www.chataiapi.com/v1/chat/completions", 
  "model": "gpt-3.5-turbo",
  "enabled": true
}
```

**LLM测试模式 (调试用)**
1. ✅ 勾选"启用LLM测试模式"
2. ❌ 不勾选"完整LLM监控模式"
- 只有第一个Agent在第一个时间片使用LLM
- 适合测试LLM连接和配置

#### 2.2 Agent选择
- 选择2-4个Agent进行测试
- 包含至少1个意见领袖
- 配置不同的初始情绪和立场值

#### 2.3 仿真参数
- **时间片数量**: 2-5个 (便于观察)
- **w_pop**: 0.7 (热度权重)
- **k**: 2 (选择帖子数量)

### 3. 启动仿真并监控

#### 3.1 前端启动
1. 点击"开始仿真"按钮
2. 仿真会在后台开始运行
3. 前端显示仿真状态

#### 3.2 实时监控方式

**方式一：控制台输出 (推荐)**
- 查看后端服务的控制台输出
- 能看到完整的LLM交互过程
- 实时显示Agent状态变化

**方式二：日志文件 (详细)**
- 每次仿真自动生成 `simulation_log_YYYYMMDD_HHMMSS.txt`
- 包含完整的仿真过程记录
- 可以在仿真运行时实时查看文件内容

**方式三：前端日志 (简化)**
- 在前端界面查看仿真结果
- 显示仿真完成后的详细日志
- 适合查看最终结果

### 4. 实时监控内容

#### 4.1 仿真启动信息
```
=== 社交仿真引擎（Web版本 - 实时监控模式）===
仿真ID: xxxxx-xxxx-xxxx
LLM启用状态：True
[参数] w_pop=0.7, k=2
💡 实时日志将保存到: simulation_log_*.txt
```

#### 4.2 Agent创建和配置
```
=== Agent配置 ===
总共选择了 4 个Agent:
[LLM Config] 为 4 个Agent配置LLM: gpt-3.5-turbo
  - Agent agent_001: LLM已配置
  - Agent agent_002: LLM已配置
```

#### 4.3 仿真执行过程
```
--- 时间片 1/2 ---
本时间片帖子数量: 3
活跃Agent数量: 4

=== 开始Agent情绪更新和发帖判定 ===
[LLM Config] 为 4 个Agent启用LLM调用
[宏观简报] {'average_emotion': 0.05, 'average_stance': 0.15}
[Leader] agent_003 读简报后状态: 情绪=0.287, 立场=0.500
```

#### 4.4 LLM交互详情
```
🤖 Agent agent_001 在时间片 0 使用LLM
[Feed] Agent agent_001 候选池大小: 3 (k=2, x0=auto)

[LLM Request] Agent agent_001 分析帖子: 高热度政治话题讨论：最新政策变化引发热议...
[LLM Prompt] 长度: 2156 字符
[Prompt内容]
你是一个社交媒体智能体...
[详细的prompt内容]

[LLM Response] Agent agent_001 收到响应，长度: 245 字符
[LLM 原始响应] {"emotion_change": 0.1, "stance_suggested": 0.65, ...}
[LLM 解析结果] Agent agent_001 建议立场值: 0.65
```

#### 4.5 Agent状态变化
```
Agent agent_001 阅读帖子 post_001: 情绪 0.654, 立场 0.623, 置信度 0.534 [LLM]
Agent agent_001 阅读帖子 post_002: 情绪 0.698, 立场 0.645, 置信度 0.587 [LLM]
Agent agent_001 不发帖 (波动量: 0.089, 阈值: 0.050)
```

### 5. 实时监控的优势

#### 5.1 调试LLM交互
- **看到完整Prompt**: 验证Agent状态是否正确传递
- **监控API调用**: 确认LLM服务是否正常响应
- **分析响应质量**: 判断LLM返回是否合理

#### 5.2 理解Agent行为
- **情绪立场变化**: 观察Agent如何受帖子影响
- **发帖决策过程**: 理解什么情况下Agent会发帖
- **个性化推荐**: 看到每个Agent获得的不同帖子推荐

#### 5.3 优化仿真参数
- **调整权重参数**: 基于实际效果调整w_pop、k等参数
- **修正Agent配置**: 优化Agent的初始状态和个性特征
- **改进算法逻辑**: 发现并修复仿真算法中的问题

### 6. 故障排除

#### 6.1 没有LLM调用
- 确认LLM配置enabled=true
- 检查API key是否正确
- 验证网络连接

#### 6.2 Agent不发帖
- 提高Agent的activity_level
- 降低expression_threshold
- 增加帖子的information_strength

#### 6.3 日志文件过大
- 减少仿真时间片数量
- 使用较少的Agent
- 关闭详细调试输出

### 7. 最佳实践

#### 7.1 测试建议
- **小规模测试**: 先用2-3个Agent、2-3个时间片
- **逐步扩大**: 确认无误后增加规模
- **保存日志**: 重要的仿真结果要备份日志文件

#### 7.2 监控要点
- **关注LLM响应时间**: 如果太慢考虑优化prompt
- **观察Agent多样性**: 确保不同Agent有不同行为
- **验证逻辑正确性**: 检查情绪立场变化是否合理

---

## 🎯 快速开始

### 方案一：完整LLM监控模式 (推荐用于实时监控)

1. **启动系统**: 
   ```bash
   python run_server.py
   start_all_vue.bat
   ```

2. **配置参数**:
   - ✅ 勾选"启用LLM测试模式"
   - ✅ 勾选"完整LLM监控模式"
   - 配置LLM API信息
   - 选择2-4个Agent
   - 设置时间片数量: 2-5个

3. **开始仿真**: 点击开始按钮

4. **实时监控**: 查看后端控制台，观察所有Agent在所有时间片的LLM调用

### 方案二：测试模式 (用于调试LLM连接)

1. **启动系统**: 同上

2. **配置参数**:
   - ✅ 勾选"启用LLM测试模式"
   - ❌ 不勾选"完整LLM监控模式"
   - 配置LLM API信息

3. **验证效果**: 只有第一个Agent在第一个时间片使用LLM

---

## 🔧 故障排除

### Q: 为什么只有第一个Agent使用LLM？
A: 检查是否勾选了"完整LLM监控模式"。如果没有勾选，系统会运行在测试模式下。

### Q: 如何确认LLM配置正确？
A: 在后端控制台查看是否有 `[LLM Request]` 和 `[LLM Prompt]` 输出。

### Q: 仿真运行但看不到实时输出？
A: 确保查看的是后端控制台（运行`python run_server.py`的窗口），而不是前端窗口。

现在您可以享受完整的实时仿真监控体验！🎉
