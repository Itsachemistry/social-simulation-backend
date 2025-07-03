# 项目更新日志

## 2024-12-19 - 信息强度权重机制与置信度更新逻辑完善

### 🎯 核心改进
基于论文中"信息强度"概念，将原有的硬性过滤门槛改为影响权重机制，并完善了置信度更新逻辑，实现了更符合现实的信息处理机制。

### ✨ 主要功能改进

#### 1. 信息强度权重机制（替代硬性过滤）
- **新增**：信息强度过滤，只过滤 `strength` 为 `null` 的帖子
- **新增**：影响权重应用，`strength` 值（1.0, 2.0, 3.0）直接作为影响权重
- **改进**：状态更新时所有影响值都乘以 `strength_weight`
- **移除**：硬性热度阈值过滤机制

#### 2. 完善置信度更新逻辑
- **新增**：立场一致性判断，基于立场相似度区分帖子与Agent立场是否一致
- **新增**：差异化影响机制
  - 立场一致时：帖子强度越高，置信度提升越多
  - 立场不一致时：帖子强度越高，对置信度的削弱也越厉害（但幅度稍小）

#### 3. 筛选逻辑优化
- **改进**：`AgentController._generate_personalized_feed` 方法
- **移除**：硬性热度阈值过滤
- **新增**：综合权重排序（`heat * strength`）

#### 4. 状态更新流程优化
- **新增**：信息强度过滤检查
- **新增**：`filtered_by_strength` 状态返回
- **改进**：避免重复处理和状态更新

### 🔧 技术实现

#### 数据结构扩展
```python
# _calculate_post_impact 返回值新增字段
{
    "emotion_change": float,
    "confidence_change": float,
    "base_impact": float,
    "stance_similarity": float,
    "interest_match": float,
    "strength_weight": float,  # 新增：信息强度权重
    "filtered": bool          # 新增：是否被过滤
}
```

#### 核心算法改进
```python
# 信息强度权重应用
strength_weight = float(post_strength)

# 情绪变化应用强度权重
emotion_change = base_emotion_change * strength_weight

# 置信度变化（区分立场一致性）
if stance_similarity > 0.5:  # 立场一致
    confidence_change = interest_match * post_heat * 0.05 * strength_weight
else:  # 立场不一致
    confidence_change = -interest_match * post_heat * 0.03 * strength_weight
```

### 🧪 测试验证
创建了 `test_strength_weight.py` 测试脚本，验证：
- ✅ `strength` 为 `null` 的帖子被完全过滤
- ✅ `strength` 值作为影响权重影响状态更新
- ✅ 立场一致/不一致对置信度有不同影响
- ✅ 移除了硬性热度阈值过滤
- ✅ 信息强度权重影响帖子排序

### 📊 影响范围
- **Agent状态更新**：所有Agent的状态更新逻辑都应用了新的权重机制
- **信息流筛选**：个性化信息流生成逻辑完全重构
- **数据利用**：充分利用了帖子数据中的 `strength` 字段
- **向后兼容**：对现有数据结构和接口保持兼容

### 🎨 设计理念
1. **符合论文逻辑**：与论文中"按信息强度加权求和"的思想完全一致
2. **更真实的模拟**：现实中人们并非完全不看"分量较轻"的新闻，只是这些新闻对他们思想的改变较小
3. **充分利用数据**：充分利用了 1, 2, 3 这三个数值等级的差异
4. **避免数据损失**：移除了硬性热度阈值过滤，避免大量有效帖子被忽视

### 🔮 后续优化建议
1. **权重参数调优**：可根据实际效果调整置信度提升/降低的系数
2. **情绪更新完善**：可考虑添加帖子自身情绪值对Agent情绪的影响
3. **动态权重**：可考虑根据Agent性格特征动态调整权重敏感度

---

## 2024-12-18 - 立场映射修复

### 🐛 问题修复
- **修复**：`_estimate_post_stance` 方法使用伪随机数的问题
- **改进**：使用真实的 `group` 字段映射立场值
- **统一**：与 `AgentController._calculate_stance_similarity` 保持一致

### 🔧 技术细节
```python
# 立场映射规则（与AgentController保持一致）
# group=1 (支持患者) → 0.0
# group=0 (中立) → 0.5  
# group=2 (支持医院) → 1.0
```

---

## 2024-06-10 - Agent编号与转播树节点高亮

### ✨ 新增功能
- **Agent编号**：统一加上 'agent_' 前缀，便于后端和前端区分Agent生成的内容
- **时序记录**：在Agent类中增加 `state_history` 属性，每次 `update_state` 时自动记录情感和立场的时序变化
- **转播树高亮**：转播树API每个节点增加 `is_agent_post` 和 `viewed_by_agents` 字段

### 🔧 技术实现
```python
# 转播树节点新增字段
{
    "is_agent_post": bool,           # author_id以'agent_'开头即为Agent生成
    "viewed_by_agents": List[str],   # 该帖子被哪些Agent浏览过
    # ... 其他字段
}
```

---

## 2024-06-09 - Agent影响追踪与parent_post_id标准化

### ✨ 新增功能
- **影响分数计算**：标准化了Agent在每个时间片内对每条帖子影响分数的计算方式
- **影响追踪**：在 `update_state` 中自动追踪本时间片影响最大的帖子ID
- **传播树连接**：Agent发帖时，`parent_post_id` 指向影响最大的帖子ID

### 🔧 技术实现
```python
# 影响分数计算
influence_score = abs(delta_emotion) + abs(delta_confidence)

# 影响追踪
if influence_score > max_impact_score:
    max_impact_score = influence_score
    max_impact_post_id = post_id
``` 