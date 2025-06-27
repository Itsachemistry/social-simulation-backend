# API 文件夹详细功能说明

本文件夹包含社交仿真引擎的全部后端接口服务，基于 Flask 框架实现，负责仿真配置、仿真调度、Agent 管理、结果分析与可视化等核心功能。下述为每个文件的详细接口与功能说明：

---

## 1. `__init__.py`
- **作用**：Flask 应用工厂，统一注册所有蓝图（Blueprint），对外暴露 `/api/` 下的全部接口。
- **说明**：通过 `create_app()` 创建主应用，集成 config、simulation、agent、analysis、visualization 五大服务。
- **路由注册**：
  - `/api/simulation`：仿真配置与仿真主流程相关接口
  - `/api/agents`：Agent 管理接口
  - `/api/analysis`：仿真分析接口
  - `/api/visualization`：仿真可视化接口

---

## 2. `config_service.py`
- **作用**：仿真全局配置管理接口。
- **主要接口**：
  - `POST/PUT /api/simulation/config`：设置仿真配置（时间范围、立场/情感分布、事件描述、总数量等）。
  - `GET /api/simulation/config`：获取当前仿真配置。
  - `GET /api/simulation/posts/timeline`：获取所有帖子时间线（最早/最晚/全部时间戳）。
  - `GET /api/simulation/initial-params`：获取初始化参数（可用立场、情感、分布、总数等，供前端配置界面使用）。
- **内部算法**：
  - `sample_posts_by_quota`：复合配额采样算法，按立场+情感+数量多维度采样初始帖子。
  - `build_initial_post_pool`：根据配置筛选初始帖子池。

---

## 3. `simulation_service.py`
- **作用**：仿真主流程调度与管理接口。
- **主要接口**：
  - `POST /api/simulation/start`：启动仿真，参数为仿真配置和Agent配置，异步后台运行。
  - `GET /api/simulation/status/<simulation_id>`：查询指定仿真状态（运行中/已完成/失败等）。
  - `POST /api/simulation/inject_event`：向指定仿真注入突发事件（内容、热度、时间戳）。
  - `GET /api/simulation/results/<simulation_id>`：获取指定仿真结果（摘要、详细结果、最终帖子、Agent状态等）。
  - `POST /api/simulation/load`：加载历史仿真配置，便于前端复用。
  - `POST /api/simulation/compare`：对比多次仿真结果（摘要、Agent状态等）。
  - `GET /api/simulation/list`：获取所有仿真任务列表。
- **内部机制**：
  - 维护 `SimulationManager`，统一管理仿真生命周期、事件注入、结果存储。

---

## 4. `agent_service.py`
- **作用**：Agent 配置管理接口。
- **主要接口**：
  - `GET /api/agents/`：获取所有 Agent 配置。
  - `POST /api/agents/`：新增 Agent，校验唯一性与加入时间范围。
  - `PUT /api/agents/<agent_id>`：更新指定 Agent 配置，校验时间范围。
  - `DELETE /api/agents/<agent_id>`：软删除指定 Agent（置为不活跃）。
- **说明**：所有 Agent 配置均存储于 `config/agents.json`，接口支持前端动态管理仿真参与者。

---

## 5. `analysis_service.py`
- **作用**：仿真结果分析接口。
- **主要接口**：
  - `POST /api/analysis/temporal`：按时间粒度（小时/天/周）聚合分析指定仿真结果，返回热度、情感、立场、热门话题、活跃作者等。
  - `POST /api/analysis/comparison`：对比多个仿真的时间粒度分析结果。
  - `GET /api/analysis/granularities`：获取支持的时间粒度选项。
- **分析内容**：
  - 统计每个时间段的帖子数、平均/最大热度、点赞/分享总数、情感/立场分布、热门话题、活跃作者等。
  - 支持自定义时间范围过滤。

---

## 6. `visualization_service.py`
- **作用**：仿真结果可视化与数据筛选接口。
- **主要接口**：
  - `POST /api/visualization/posts/filter`：多条件综合筛选帖子（时间、关键词、类型、热度、排序、分页等），返回筛选结果和摘要统计。
  - `POST /api/visualization/posts/search`：关键词搜索帖子，支持分页。
  - `POST /api/visualization/posts/summary`：获取帖子摘要统计（总数、时间范围、热度、类型分布、热门话题、活跃作者等）。
  - `GET /api/visualization/options`：获取可视化选项（排序、过滤、搜索字段等）。
  - `POST /api/visualization/posts/repost_tree`：生成转播树结构（用于前端关系图展示，含节点浏览关系）。
- **说明**：所有接口均基于仿真结果数据，支持前端灵活可视化和交互分析。

---

# src 文件夹详细功能说明

本文件夹为社交仿真引擎的核心业务逻辑层，包含 Agent 行为、控制、世界状态、时间片管理、LLM 服务、数据加载等核心模块。各文件说明如下：

---

## 1. `__init__.py`
- **作用**：包初始化文件，无实际代码，仅标记 src 目录为 Python 包。

---

## 2. `agent.py`
- **作用**：定义 Agent（智能体）基类，封装个体决策、状态更新、行为生成等全部逻辑。
- **主要类与方法**：
  - `Agent`：
    - `__init__(agent_config)`：初始化 Agent，读取配置，设置类型、立场、兴趣、性格等。
    - `update_state(post_object, llm_service=None)`：根据帖子内容和 LLM 分析更新自身情绪、置信度、精力等状态，自动追踪影响最大的帖子。
    - `generate_action_prompt()`：决策是否发帖，生成发帖 Prompt。
    - `add_to_blacklist(user_id)`/`remove_from_blacklist(user_id)`/`is_blacklisted(user_id)`：黑名单管理。
    - `get_state_summary()`：返回当前状态摘要。
    - 多个属性方法（如 agent_id、agent_type、stance、interests、personality 等）供外部读取。
  - **说明**：支持多种性格、兴趣、立场、活跃度等参数，支持个性化行为建模。

---

## 3. `agent_controller.py`
- **作用**：Agent 控制器，负责管理和调度所有 Agent 的行为。
- **主要类与方法**：
  - `AgentController`：
    - `__init__(agent_configs, world_state, llm_service)`：初始化，按类型分组创建 Agent。
    - `run_time_slice(agents, world_state, llm_service)`：运行一个时间片，调度所有 Agent 行为，生成新帖子。
    - `_generate_personalized_feed(agent, all_posts, global_intensity_factor)`：为每个 Agent 生成个性化信息流，包含热度、立场、兴趣等多重筛选。
    - 多个内部方法：动态阈值、相似度、兴趣匹配等算法。
  - `PlaceholderAgent`：占位符类，便于扩展。
  - **说明**：支持意见领袖、规则 Agent、普通用户等多类型 Agent，支持优先级调度、行为分组、主流程集成。

---

## 4. `world_state.py`
- **作用**：世界状态管理器，负责维护动态帖子池和全局事件注入。
- **主要类与方法**：
  - `WorldState`：
    - `add_post(post_object)`：向帖子池添加新帖子。
    - `inject_event(event_post_object)`：强制插入高优先级事件帖子。
    - `get_all_posts()`/`get_posts_count()`/`get_event_posts()`：获取全部、计数、事件帖子。
    - `clear_posts()`：清空帖子池。
  - **说明**：所有帖子均为字典结构，支持事件优先级、转发关系、热度等属性。

---

## 5. `llm_service.py`
- **作用**：LLM（大模型）服务连接器，支持 ModelScope SDK 和 Mock 两种模式。
- **主要类与方法**：
  - `LLMService`：
    - `__init__(model_name, use_mock, api_key)`：初始化 LLM 服务。
    - `generate_post(prompt, max_length)`：生成帖子内容。
    - `switch_to_mock()`/`switch_to_modelscope()`：切换服务模式。
  - `LLMServiceFactory.create_service(config)`：工厂方法，按配置创建 LLM 服务实例。
  - **说明**：支持本地 Mock 生成和真实大模型推理，便于开发调试和生产部署。

---

## 6. `time_manager.py`
- **作用**：时间片管理器，将帖子按时间戳排序并划分为时间片。
- **主要类与方法**：
  - `TimeSliceManager`：
    - `__init__(posts, slice_size)`：初始化，按时间排序并分片。
    - `get_slice(slice_index)`：获取指定时间片的帖子列表。
    - `total_slices`/`total_posts` 属性：获取总时间片数和总帖子数。
    - `get_all_posts()`：获取全部已排序帖子。
  - **说明**：支持灵活的时间片划分和主流程调度。

---

## 7. `services.py`
- **作用**：数据加载与配置解析工具类。
- **主要类与方法**：
  - `DataLoader`：
    - `load_post_data(file_path)`：读取并解析 JSON 格式的帖子数据文件。
    - `load_agent_config(file_path)`：读取并解析 JSON/YAML 格式的 Agent 配置文件。
  - **说明**：支持健壮的文件读取、格式判断和错误处理。

---

# 总结
API 文件夹实现了社交仿真引擎的全部后端接口，涵盖仿真配置、调度、Agent 管理、结果分析与可视化等全流程，接口设计清晰、参数丰富，便于前后端协作和二次开发。 