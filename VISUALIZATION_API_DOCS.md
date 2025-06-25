# 可视化API文档

## 概述

可视化API提供了丰富的交互式数据筛选和分析功能，支持用户通过多种方式探索和分析仿真结果。

## 基础URL

```
http://localhost:5000/api/visualization
```

## API接口列表

### 1. 获取可视化选项

**接口**: `GET /options`

**描述**: 获取所有可用的排序、筛选和搜索选项

**响应示例**:
```json
{
  "status": "success",
  "sort_options": [
    {"value": "time", "label": "按时间"},
    {"value": "popularity", "label": "按热度"},
    {"value": "heat", "label": "按热度值"},
    {"value": "likes", "label": "按点赞数"},
    {"value": "shares", "label": "按分享数"}
  ],
  "filter_options": [
    {"value": "all", "label": "全部帖子"},
    {"value": "original", "label": "原创内容"},
    {"value": "reposted", "label": "转发内容"},
    {"value": "events", "label": "事件帖子"}
  ],
  "search_fields": [
    {"value": "content", "label": "帖子内容"},
    {"value": "author_id", "label": "作者ID"},
    {"value": "id", "label": "帖子ID"}
  ]
}
```

### 2. 综合帖子筛选

**接口**: `POST /posts/filter`

**描述**: 综合筛选帖子，支持时间范围、关键词搜索、排序、热度阈值等多种筛选条件

**请求参数**:
```json
{
  "simulation_id": "string",           // 必需：仿真ID
  "time_range": {                      // 可选：时间范围
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  },
  "keywords": "string",                // 可选：搜索关键词
  "search_fields": ["content", "author_id"], // 可选：搜索字段
  "sort_by": "time",                   // 可选：排序方式 (time|popularity|heat|likes|shares)
  "sort_reverse": false,               // 可选：是否倒序
  "min_popularity": 0,                 // 可选：最小热度阈值
  "filter_type": "all",                // 可选：筛选类型 (all|original|reposted|events)
  "include_reposts": true,             // 可选：是否包含转发
  "limit": 100                         // 可选：返回数量限制
}
```

**响应示例**:
```json
{
  "status": "success",
  "simulation_id": "sim_123",
  "filter_params": {
    "time_range": {"start": "2024-01-01T00:00:00", "end": "2024-01-02T00:00:00"},
    "keywords": "产品",
    "sort_by": "popularity",
    "sort_reverse": true,
    "min_popularity": 10,
    "filter_type": "original",
    "include_reposts": false,
    "limit": 100
  },
  "summary": {
    "total_posts": 45,
    "time_range": {"start": "2024-01-01T06:00:00", "end": "2024-01-01T18:00:00"},
    "popularity_stats": {
      "total_likes": 1250,
      "total_shares": 320,
      "avg_heat": 45.6,
      "max_heat": 95,
      "avg_likes": 27.8,
      "avg_shares": 7.1
    },
    "type_distribution": {
      "original": 35,
      "reposts": 8,
      "events": 2
    },
    "top_authors": [
      ["user_001", 8],
      ["user_002", 6],
      ["user_003", 5]
    ],
    "hot_topics": [
      ["产品", 15],
      ["发布", 12],
      ["创新", 8],
      ["技术", 6],
      ["市场", 5]
    ]
  },
  "posts": [
    {
      "id": "post_001",
      "content": "新产品发布内容...",
      "author_id": "user_001",
      "timestamp": "2024-01-01T10:30:00",
      "heat": 85,
      "likes": 45,
      "shares": 12,
      "is_event": false,
      "is_repost": false
    }
  ],
  "total_filtered": 45
}
```

### 3. 关键词搜索

**接口**: `POST /posts/search`

**描述**: 专门用于关键词搜索的接口

**请求参数**:
```json
{
  "simulation_id": "string",           // 必需：仿真ID
  "keywords": "string",                // 必需：搜索关键词
  "search_fields": ["content", "author_id"], // 可选：搜索字段
  "limit": 50                          // 可选：返回数量限制
}
```

**响应示例**:
```json
{
  "status": "success",
  "keywords": "产品 发布",
  "search_fields": ["content"],
  "results": [
    {
      "id": "post_001",
      "content": "新产品发布内容...",
      "author_id": "user_001",
      "timestamp": "2024-01-01T10:30:00",
      "heat": 85,
      "likes": 45,
      "shares": 12,
      "_search_score": 2
    }
  ],
  "total_found": 15
}
```

### 4. 帖子摘要统计

**接口**: `POST /posts/summary`

**描述**: 获取帖子的统计摘要信息

**请求参数**:
```json
{
  "simulation_id": "string",           // 必需：仿真ID
  "time_range": {                      // 可选：时间范围
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  },
  "filter_type": "all",                // 可选：筛选类型
  "include_reposts": true              // 可选：是否包含转发
}
```

**响应示例**:
```json
{
  "status": "success",
  "simulation_id": "sim_123",
  "summary": {
    "total_posts": 100,
    "time_range": {"start": "2024-01-01T00:00:00", "end": "2024-01-02T00:00:00"},
    "popularity_stats": {
      "total_likes": 2500,
      "total_shares": 650,
      "avg_heat": 52.3,
      "max_heat": 98,
      "avg_likes": 25.0,
      "avg_shares": 6.5
    },
    "type_distribution": {
      "original": 75,
      "reposts": 20,
      "events": 5
    },
    "top_authors": [
      ["user_001", 12],
      ["user_002", 10],
      ["user_003", 8],
      ["user_004", 7],
      ["user_005", 6]
    ],
    "hot_topics": [
      ["产品", 25],
      ["发布", 20],
      ["创新", 15],
      ["技术", 12],
      ["市场", 10],
      ["用户", 8],
      ["体验", 7],
      ["功能", 6],
      ["设计", 5],
      ["质量", 4]
    ]
  }
}
```

## 使用场景示例

### 场景1: 时间刷选交互

用户通过时间轴刷选特定时间段的数据：

```javascript
// 前端时间刷选事件
function onTimeBrushChange(startTime, endTime) {
  const filterParams = {
    simulation_id: currentSimulationId,
    time_range: {
      start: startTime,
      end: endTime
    },
    sort_by: 'time',
    limit: 50
  };
  
  fetch('/api/visualization/posts/filter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(filterParams)
  })
  .then(response => response.json())
  .then(data => {
    updatePostList(data.posts);
    updateSummary(data.summary);
  });
}
```

### 场景2: 关键词搜索

用户在搜索框中输入关键词：

```javascript
function searchPosts(keywords) {
  const searchParams = {
    simulation_id: currentSimulationId,
    keywords: keywords,
    search_fields: ['content', 'author_id'],
    limit: 30
  };
  
  fetch('/api/visualization/posts/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(searchParams)
  })
  .then(response => response.json())
  .then(data => {
    displaySearchResults(data.results);
    showSearchSummary(data.total_found);
  });
}
```

### 场景3: 排序方式切换

用户切换排序方式（时间/热度）：

```javascript
function changeSortOrder(sortBy, reverse = false) {
  const filterParams = {
    simulation_id: currentSimulationId,
    sort_by: sortBy,
    sort_reverse: reverse,
    limit: 100
  };
  
  fetch('/api/visualization/posts/filter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(filterParams)
  })
  .then(response => response.json())
  .then(data => {
    updatePostList(data.posts);
    highlightTopPosts(data.posts.slice(0, 5));
  });
}
```

### 场景4: 热度阈值调整

用户调整热度阈值来过滤低质量内容：

```javascript
function adjustPopularityThreshold(threshold) {
  const filterParams = {
    simulation_id: currentSimulationId,
    min_popularity: threshold,
    sort_by: 'popularity',
    sort_reverse: true,
    limit: 50
  };
  
  fetch('/api/visualization/posts/filter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(filterParams)
  })
  .then(response => response.json())
  .then(data => {
    updatePostList(data.posts);
    updateFilterStats(data.total_filtered, threshold);
  });
}
```

### 场景5: 转发内容控制

用户控制是否显示转发内容：

```javascript
function toggleReposts(includeReposts) {
  const filterParams = {
    simulation_id: currentSimulationId,
    include_reposts: includeReposts,
    filter_type: includeReposts ? 'all' : 'original',
    limit: 100
  };
  
  fetch('/api/visualization/posts/filter', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(filterParams)
  })
  .then(response => response.json())
  .then(data => {
    updatePostList(data.posts);
    updateTypeDistribution(data.summary.type_distribution);
  });
}
```

## 错误处理

所有接口都可能返回以下错误：

### 400 Bad Request
```json
{
  "error": "缺少simulation_id参数"
}
```

### 404 Not Found
```json
{
  "error": "仿真不存在"
}
```

### 500 Internal Server Error
```json
{
  "error": "筛选失败: 具体错误信息"
}
```

## 性能优化建议

1. **分页加载**: 对于大量数据，建议使用 `limit` 参数进行分页
2. **缓存结果**: 对于相同的筛选条件，可以缓存结果以提高响应速度
3. **异步处理**: 对于复杂的筛选操作，可以考虑异步处理
4. **索引优化**: 在数据库层面为常用筛选字段建立索引

## 前端集成建议

1. **实时更新**: 使用 WebSocket 或轮询机制实时更新数据
2. **防抖处理**: 对于用户输入（如搜索），使用防抖处理避免频繁请求
3. **加载状态**: 显示加载状态以提升用户体验
4. **错误提示**: 提供友好的错误提示和处理机制
5. **响应式设计**: 适配不同屏幕尺寸的显示需求 