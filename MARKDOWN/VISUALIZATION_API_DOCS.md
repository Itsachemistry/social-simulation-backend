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

**描述**: 获取可视化相关的选项配置，包括排序、筛选、搜索字段等选项

**请求参数**: 无

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
    {"value": "id", "label": "帖子ID"},
    {"value": "tags", "label": "标签"}        // 新增：标签搜索字段
  ],
  "tag_options": {                            // 新增：标签选项
    "description": "支持微博标签筛选，标签格式为 #XXXX#",
    "match_modes": [
      {"value": false, "label": "匹配任一标签"},
      {"value": true, "label": "匹配所有标签"}
    ],
    "example": ["科技", "创新", "产品"]
  }
}
```

### 2. 综合帖子筛选

**接口**: `POST /posts/filter`

**描述**: 综合筛选接口，支持多种筛选条件组合

**请求参数**:
```json
{
  "simulation_id": "string",           // 必需：仿真ID
  "time_range": {                      // 可选：时间范围
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  },
  "keywords": "string",                // 可选：关键词搜索
  "search_fields": ["content", "author_id"], // 可选：搜索字段
  "sort_by": "time|popularity|heat|likes|shares", // 可选：排序方式
  "sort_reverse": false,               // 可选：是否降序
  "min_popularity": 0,                 // 可选：最低热度阈值
  "filter_type": "all|original|reposted|events", // 可选：内容类型
  "include_reposts": true,             // 可选：是否包含转发
  "limit": 100,                        // 可选：返回数量限制
  "tags": ["科技", "创新"],            // 新增：标签筛选
  "match_all_tags": false              // 新增：是否必须匹配所有标签
}
```

**新增标签参数说明**:
- `tags`: 标签列表，如 `["科技", "创新"]`。帖子内容中的标签格式为 `#XXXX#`，筛选时使用 `XXXX` 部分
- `match_all_tags`: 
  - `false` (默认): 匹配任一标签即可
  - `true`: 必须匹配所有标签

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
    "limit": 100,
    "tags": ["科技", "创新"],
    "match_all_tags": false
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
    "top_tags": [                    // 新增：热门标签统计
      ["科技", 15],
      ["创新", 12],
      ["产品", 8],
      ["技术", 6],
      ["市场", 5]
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
      "content": "新产品发布内容 #科技# #创新#",
      "author_id": "user_001",
      "timestamp": "2024-01-01T10:30:00",
      "heat": 85,
      "likes": 45,
      "shares": 12,
      "is_event": false,
      "is_repost": false,
      "tags": ["科技", "创新"]        // 新增：帖子标签
    }
  ],
  "total_filtered": 45
}
```

### 3. 关键词搜索

**接口**: `POST /posts/search`

**描述**: 专门用于关键词搜索的接口，支持标签搜索

**请求参数**:
```json
{
  "simulation_id": "string",           // 必需：仿真ID
  "keywords": "string",                // 必需：搜索关键词
  "search_fields": ["content", "author_id", "tags"], // 可选：搜索字段，新增tags
  "page": 1,                           // 可选：页码
  "page_size": 20                      // 可选：每页数量
}
```

**新增搜索字段说明**:
- `tags`: 在帖子标签中进行搜索，支持部分匹配

**响应示例**:
```json
{
  "status": "success",
  "keywords": "科技 创新",
  "search_fields": ["content", "tags"],
  "results": [
    {
      "id": "post_001",
      "content": "新产品发布内容 #科技# #创新#",
      "author_id": "user_001",
      "timestamp": "2024-01-01T10:30:00",
      "heat": 85,
      "likes": 45,
      "shares": 12,
      "tags": ["科技", "创新"],
      "_search_score": 2
    }
  ],
  "total_found": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
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

### 5. 获取转播树结构

**接口**: `POST /posts/repost_tree`

**描述**: 获取指定仿真的转播树（Repost Tree）结构数据，便于前端可视化信息扩散路径。

**请求参数**:
```json
{
  "simulation_id": "string" // 必需：仿真ID
}
```

**响应示例**:
```json
{
  "id": "virtual_root",
  "children": [
    {
      "id": "post_001",
      "content": "原始帖子内容...",
      "author_id": "user_001",
      "timestamp": "2024-01-01T10:00:00",
      "is_repost": false,
      "parent_post_id": null,
      "children": [
        {
          "id": "post_002",
          "content": "转发内容...",
          "author_id": "user_002",
          "timestamp": "2024-01-01T10:30:00",
          "is_repost": true,
          "parent_post_id": "post_001",
          "children": []
        }
      ]
    }
  ]
}
```

**说明**:
- 根节点为虚拟节点，所有 parent_post_id 为 null 的帖子为一级子节点。
- 每个节点包含原始帖子字段和 children 数组，children 为空表示叶子节点。
- 前端可递归渲染该结构实现转播树可视化。

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
// 前端搜索事件
function onSearchSubmit(keywords) {
  const searchParams = {
    simulation_id: currentSimulationId,
    keywords: keywords,
    search_fields: ['content', 'tags'],  // 在内容和标签中搜索
    page: 1,
    page_size: 20
  };
  
  fetch('/api/visualization/posts/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(searchParams)
  })
  .then(response => response.json())
  .then(data => {
    updateSearchResults(data.results);
    updatePagination(data.page, data.total_pages);
  });
}
```

### 场景3: 标签筛选

用户选择特定标签进行筛选：

```javascript
// 前端标签筛选事件
function onTagFilter(tags, matchAll = false) {
  const filterParams = {
    simulation_id: currentSimulationId,
    tags: tags,                    // 标签列表
    match_all_tags: matchAll,      // 是否必须匹配所有标签
    sort_by: 'popularity',
    sort_reverse: true,
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
    updateTagCloud(data.summary.top_tags);  // 更新标签云
  });
}

// 标签云点击事件
function onTagCloudClick(tag) {
  onTagFilter([tag], false);  // 筛选包含该标签的帖子
}
```

### 场景4: 组合筛选

用户组合多种筛选条件：

```javascript
// 高级筛选
function advancedFilter(params) {
  const filterParams = {
    simulation_id: currentSimulationId,
    time_range: params.timeRange,
    tags: params.tags,
    match_all_tags: params.matchAllTags,
    keywords: params.keywords,
    search_fields: ['content', 'tags'],
    min_popularity: params.minPopularity,
    filter_type: params.filterType,
    sort_by: params.sortBy,
    sort_reverse: params.sortReverse,
    limit: params.limit || 50
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
    updateFilterHistory(data.filter_params);  // 保存筛选历史
  });
}
```

### 场景5: 标签统计分析

分析特定时间段的标签使用情况：

```javascript
// 获取标签统计
function getTagStatistics(timeRange) {
  const summaryParams = {
    simulation_id: currentSimulationId,
    time_range: timeRange
  };
  
  fetch('/api/visualization/posts/summary', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(summaryParams)
  })
  .then(response => response.json())
  .then(data => {
    // 绘制标签使用频率图表
    drawTagFrequencyChart(data.summary.top_tags);
    
    // 显示热门标签
    displayHotTags(data.summary.top_tags.slice(0, 10));
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