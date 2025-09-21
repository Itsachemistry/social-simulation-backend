# 前端与后端对接接口清单

本文件统计了前端代码中所有需要与后端对接的接口，包含接口路径、用途、请求方式、参数说明及前端期望返回的数据结构。请在前后端合龙时逐条对接、确认。

---

## 1. 帖子列表接口
- **接口路径**：`/api/posts`
- **用途**：获取指定时间范围、标签下的帖子列表
- **请求方式**：GET
- **参数**：
  - `start_time`（起始时间，字符串）
  - `end_time`（结束时间，字符串）
  - `tags`（标签，字符串，可选）
- **前端期望返回**：
```json
{
  "posts": [
    {
      "id": 1,
      "user": { "name": "用户名", "avatar": "头像URL" },
      "content": "帖子内容",
      "timestamp": "ISO时间字符串",
      "comments_count": 12,
      "hotness": 88,
      "tags": ["标签1", "标签2"]
    }
  ]
}
```

---

## 2. 时间轴数据接口
- **接口路径**：`/api/timeline`
- **用途**：获取时间区间内的热度变化及每个时间点的帖子
- **请求方式**：GET
- **参数**：
  - `start_time`
  - `end_time`
  - `interval`（如 hour）
- **前端期望返回**：
```json
{
  "timeline": [
    {
      "timestamp": "ISO时间字符串",
      "hotness": 88,
      "posts": [ ... ]
    }
  ]
}
```

---

## 3. 直方图数据接口
- **接口路径**：`/api/histogram`
- **用途**：获取指定时间范围内的帖子热度分布
- **请求方式**：GET
- **参数**：
  - `start_time`
  - `end_time`
- **前端期望返回**：
```json
{
  "posts": [ ... ]
}
```

---

## 4. 情绪/立场分析接口
- **接口路径**：`/api/attitude`
- **用途**：获取群体情绪和立场的时间序列分析
- **请求方式**：GET
- **参数**：
  - `start_time`
  - `end_time`
  - `unit`（hour/day）
  - `range`（数值，时间跨度）
- **前端期望返回**：
```json
{
  "hourly_data": [
    { "timestamp": "ISO时间字符串", "emotion": -1, "stance": 1 }
  ],
  "daily_data": [
    { "date": "YYYY-MM-DD", "emotion": -1, "stance": 1 }
  ]
}
```

---

## 5. 词云数据接口
- **接口路径**：`/api/wordcloud`
- **用途**：获取关键词及其频率
- **请求方式**：GET
- **参数**：无
- **前端期望返回**：
```json
{
  "words": [
    { "text": "关键词", "frequency": 120 }
  ]
}
```

---

## 6. 转发树数据接口
- **接口路径**：`/api/tree`
- **用途**：获取某个主题或帖子的转发树结构
- **请求方式**：GET
- **参数**：可根据实际需求补充
- **前端期望返回**：
```json
{
  "tree": {
    "id": "节点ID",
    "content": "节点内容",
    "forwards": 5,
    "totalForwards": 20,
    "isAgent": true,
    "children": [ ... ]
  }
}
```

---

## 7. 智能体列表接口
- **接口路径**：`/api/agents`
- **用途**：获取所有智能体信息
- **请求方式**：GET
- **参数**：无
- **前端期望返回**：
```json
{
  "agents": [
    {
      "id": 1,
      "emotion": "positive",
      "stance": "patient",
      "confidence": 80
    }
  ]
}
```

---

## 8. 单个智能体时间线接口
- **接口路径**：`/api/agent/{id}/timeline`
- **用途**：获取某个智能体的行为轨迹
- **请求方式**：GET
- **参数**：智能体ID
- **前端期望返回**：
```json
{
  "timeline": [
    { "timestamp": "ISO时间字符串", "emotion": -1, "stance": "patient" }
  ],
  "agent": {
    "id": 1,
    "emotion": "positive",
    "stance": "patient",
    "confidence": 80
  }
}
```

---

## 9. 环境参数接口
- **接口路径**：`/api/environment`
- **用途**：获取/设置仿真环境参数
- **请求方式**：GET/POST
- **参数**（POST）：
  - `start_time`
  - `end_time`
  - `emotion`
  - `stance`
  - `scale`
  - `description`
- **前端期望返回**（GET/POST）：
```json
{
  "current_scale": 67
}
```

---

## 10. 智能体模拟接口
- **接口路径**：`/api/simulate`
- **用途**：触发智能体模拟
- **请求方式**：POST
- **参数**：根据实际需求补充
- **前端期望返回**：
```json
{
  "success": true
}
```

---

> 请逐条对接上述接口，保证数据结构和字段与前端一致。如需详细字段说明、样例数据或对接建议，请随时补充！ 