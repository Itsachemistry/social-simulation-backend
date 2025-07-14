# 属性名映射文档

本文档详细说明了当前代码中使用的属性名与规划中定义的属性名之间的映射关系。

## 帖子对象 (Post Object) 属性映射

| 规划中的属性名 | 当前代码中使用的属性名 | 状态 | 建议操作 |
|---|---|---|---|
| `post_id` | `id` | ✅ 匹配 | 保持现状 |
| `author_id` | `author_id` | ✅ 匹配 | 保持现状 |
| `content` | `content` | ✅ 匹配 | 保持现状 |
| `timestamp` | `timestamp` | ✅ 匹配 | 保持现状 |
| `emotion_category` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `emotion_score` | `emotion` | ⚠️ 部分匹配 | **建议重命名为 `emotion_score`** |
| `stance_category` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `stance_score` | `stance` | ⚠️ 部分匹配 | **建议重命名为 `stance_score`** |
| `information_strength` | `strength` | ⚠️ 部分匹配 | **建议重命名为 `information_strength`** |
| `keywords` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `is_repost` | `is_repost` | ✅ 匹配 | 保持现状 |
| `parent_post_id` | `parent_post_id` | ✅ 匹配 | 保持现状 |

### 当前代码中额外使用的帖子属性（不在规划中）

| 属性名 | 用途 | 建议 |
|---|---|---|
| `heat` | 热度值 | 保留，用于排序 |
| `likes` | 点赞数 | 保留，用于统计 |
| `shares` | 分享数 | 保留，用于统计 |
| `is_event` | 是否为事件帖子 | 保留，用于优先级 |
| `priority` | 优先级 | 保留，用于排序 |
| `tags` | 标签列表 | 保留，用于分类 |
| `popularity` | 流行度 | 保留，用于排序 |

## 智能体对象 (Agent Object) 属性映射

| 规划中的属性名 | 当前代码中使用的属性名 | 状态 | 建议操作 |
|---|---|---|---|
| `agent_id` | `agent_id` | ✅ 匹配 | 保持现状 |
| `role_type` | `agent_type` | ⚠️ 部分匹配 | **建议重命名为 `role_type`** |
| `attitude_firmness` | `attitude_firmness` | ✅ 匹配 | 保持现状 |
| `opinion_blocking` | `opinion_blocking_degree` | ⚠️ 部分匹配 | **建议重命名为 `opinion_blocking`** |
| `activity_level` | `activity_level` | ✅ 匹配 | 保持现状 |
| `initial_emotion` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `initial_stance` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `initial_confidence` | ❌ 缺失 | ❌ 缺失 | **需要添加** |
| `current_emotion` | `emotion` | ⚠️ 部分匹配 | **建议重命名为 `current_emotion`** |
| `current_stance` | `stance` | ⚠️ 部分匹配 | **建议重命名为 `current_stance`** |
| `current_confidence` | `confidence` | ⚠️ 部分匹配 | **建议重命名为 `current_confidence`** |
| `browsed_posts_ids` | `memory` | ⚠️ 部分匹配 | **建议重命名为 `browsed_posts_ids`** |
| `blocked_user_ids` | `blocked_users` | ⚠️ 部分匹配 | **建议重命名为 `blocked_user_ids`** |

### 当前代码中额外使用的智能体属性（不在规划中）

| 属性名 | 用途 | 建议 |
|---|---|---|
| `attitude_stability` | 态度稳定性枚举 | 保留，用于分类 |
| `response_style` | 回应方式枚举 | 保留，用于行为控制 |
| `emotion_update_mode` | 情绪更新模式 | 保留，用于算法选择 |
| `emotion_sensitivity` | 情绪敏感度 | 保留，用于算法参数 |

## 需要清理的代码问题

### 1. 类型错误修复
- ✅ 已修复：LLM API调用的类型错误（`self.llm_endpoint`可能为None）

### 2. 命名不一致问题
- `user_id` vs `author_id`：建议统一使用 `author_id`
- `post_id` vs `id`：建议统一使用 `post_id`

### 3. 重复属性定义
- 多个类中重复定义了相同的属性，建议统一到基类

### 4. 缺失的枚举定义
- 需要添加 `EmotionCategory` 和 `StanceCategory` 枚举

## 建议的迁移步骤

### 第一阶段：添加缺失的枚举和属性
1. ✅ 已创建 `src/data_models.py` 文件，定义了标准的数据模型
2. 添加 `EmotionCategory` 和 `StanceCategory` 枚举
3. 在帖子对象中添加 `emotion_category`、`stance_category`、`keywords` 属性

### 第二阶段：重命名属性
1. 将 `emotion` 重命名为 `emotion_score`
2. 将 `stance` 重命名为 `stance_score`
3. 将 `strength` 重命名为 `information_strength`
4. 将 `agent_type` 重命名为 `role_type`
5. 将 `opinion_blocking_degree` 重命名为 `opinion_blocking`
6. 将 `memory` 重命名为 `browsed_posts_ids`
7. 将 `blocked_users` 重命名为 `blocked_user_ids`

### 第三阶段：添加初始状态属性
1. 添加 `initial_emotion`、`initial_stance`、`initial_confidence` 属性
2. 将当前的 `emotion`、`stance`、`confidence` 重命名为 `current_*`

### 第四阶段：清理和优化
1. 移除重复的属性定义
2. 统一命名规范
3. 更新所有相关的测试和文档

## 兼容性考虑

在迁移过程中，建议：
1. 保持向后兼容性，提供属性别名
2. 逐步迁移，避免一次性大规模修改
3. 更新所有相关的测试用例
4. 更新API文档和示例代码 