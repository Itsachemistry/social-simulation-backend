  # 可视化API文档

## API接口列表

### 1. 获取帖子列表

**请求方式**: GET

**描述**: 根据时间范围、标签、筛选条件获取帖子列表及其元数据。

**请求路径**:/api/posts

**请求参数**:
```json
{
  "start_time": "2016-10-31T18:59:35",
  "end_time": "2017-01-01T17:42:26",
  "tags": ["标签1", "标签2"],
  "keyword": "关键词",
  "sort_by": "time|hotness",
  "min_hotness": 0
}
```
**响应示例**:
```json
{
    "posts": [
      {
        "id": "123456",
        "timestamp": "2016-10-31T19:00:00",
        "user": {
          "id": "u001",
          "name": "飞鱼警察"
        },
        "content": "帖子内容文本",
        "comments_count": 62,
        "hotness": 1200,
        "url": "http://weibo.com/xxx"
      }
    ],
    "total": 67
}
  ```

### 2.获取时间轴热度数据

**请求方式**: GET

**描述**: 获取指定时间范围内的热度统计数据（用于时间轴和直方图）。

**请求路径**:/api/timeline

**请求参数**:
```json
{
    "start_time": "2016-10-31T18:59:35",
    "end_time": "2017-01-01T17:42:26",
    "interval": "hour|day"
}
```
**响应示例**:
```json
{ 
    "timeline": [
      {
        "time": "2016-10-31T19:00:00",
        "hotness": 1200
      }
    ]
}
  ```
### 3 新增/高亮突发事件

**请求方式**: POST

**描述**: 在时间轴上添加突发事件并高亮显示。

**请求路径**:/api/events

**请求参数**:
```json
{
    "time": "2016-11-01T08:00:00",
    "content": "突发事件内容"
}
```
**响应示例**:
```json
{ 
    "success": true,
    "event_id": "evt001"
}
  ```
### 4 获取/保存模拟环境设置

**请求方式**: POST

**描述**: 获取或保存模拟环境参数。

**请求路径**:/api/environment

**请求参数**:
```json
{
    "start_time": "2016-10-31T18:59:35",
    "end_time": "2017-01-01T17:42:26",
    "emotion": 0.5,
    "stance": 0.2,
    "scale": 67,
    "description": "事件介绍文本"
}
```
**响应示例**:
```json
{ 
    "success": true,
    "current_scale": 67
}
  ```
### 5 智能体管理（添加/删除/获取）

**请求方式**: POST

**描述**: 添加、删除、获取智能体信息

**请求路径**:/api/agents

**请求参数**:
```json
{
   "kol": true,
    "start_time": "2016-10-31T18:59:35",
    "personality": {
      "firm": true,
      "filter_opposite": false,
      "active": true
    },
    "emotion": "positive",
    "stance": "patient",
    "stance_confidence": 100
}
```
**响应示例**:
```json
{ 
    "success": true,
    "agent_id": "agent001"
}
  ```
### 6 群体情绪与立场分析

**请求方式**: GET

**描述**: 获取指定时间段内群体情绪、立场等统计数据。

**请求路径**:/api/group_analysis

**请求参数**:
```json
{
   "start_time": "2016-10-31T18:59:35",
    "end_time": "2017-01-01T17:42:26",
    "interval": "hour|day"
}
```
**响应示例**:
```json
{ 
    "data": [
      {
        "time": "2016-10-31T19:00:00",
        "emotion": 0.5,
        "stance": 0.2,
        "scale": 30,
        "pie": {
          "patient": 0.4,
          "neutral": 0.3,
          "hospital": 0.3
        }
      }
    ]
}
  ```
### 7 词云生成

**请求方式**: GET

**描述**: 生成指定时间段内的词云数据。

**请求路径**:/api/wordcloud

**请求参数**:
```json
{
   "start_time": "2016-10-31T18:59:35",
    "end_time": "2017-01-01T17:42:26"
}
```
**响应示例**:
```json
{ 
     "words": [
      {"text": "事件", "weight": 120},
      {"text": "媒体", "weight": 80}
    ]
}
  ```
### 8 转发树数据

**请求方式**: GET

**描述**: 获取事件转发树结构数据。

**请求路径**:/api/retweet_tree

**请求参数**:
```json
{
  "start_time": "2016-10-31T18:59:35",
    "end_time": "2017-01-01T17:42:26"
}
```
**响应示例**:
```json
{ 
    "nodes": [
      {"id": "root", "content": "根节点", "level": 0, "retweeted": 238, "total_retweeted": 296}
    ],
    "links": [
      {"source": "root", "target": "node1"}
    ]
}
  ```
