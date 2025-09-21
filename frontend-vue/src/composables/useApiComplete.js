// API服务文件，提供与后端的完整接口对应
import { ref } from 'vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API错误:', error)
    if (error.response?.status === 404) {
      throw new Error('接口不存在')
    } else if (error.response?.status >= 500) {
      throw new Error('服务器错误')
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('无法连接到服务器')
    }
    throw new Error(error.message || '网络错误')
  }
)

export const useApi = () => {
  const loading = ref(false)
  const error = ref(null)

  const setLoading = (value) => {
    loading.value = value
  }

  const setError = (err) => {
    error.value = err
  }

  // 消息提示函数
  const showMessage = (message, type = 'info') => {
    console.log(`[${type.toUpperCase()}] ${message}`)
    // 这里可以添加更复杂的消息提示逻辑，比如toast等
  }

  // 通用请求方法
  const request = async (method, url, data = null, params = null) => {
    setLoading(true)
    setError(null)
    
    try {
      const config = { method, url }
      if (data) config.data = data
      if (params) config.params = params
      
      const response = await api(config)
      return response
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    isLoading: loading,  // 添加别名
    error,
    showMessage,  // 添加消息函数
    
    // ===== 可视化API =====
    // 获取帖子列表 (对应原始: /api/visualization/posts)
    getPosts: async (startTime, endTime, tags = '') => {
      const params = { start_time: startTime, end_time: endTime }
      if (tags) params.tags = tags
      return await request('GET', '/api/visualization/posts', null, params)
    },

    // 获取时间轴数据 (对应原始: /api/visualization/timeline) 
    getTimeline: async (startTime, endTime, interval = 'hour') => {
      return await request('GET', '/api/visualization/timeline', null, {
        start_time: startTime,
        end_time: endTime,
        interval
      })
    },

    // 获取直方图数据 (对应原始: /api/visualization/histogram)
    getHistogram: async (params = {}) => {
      // 支持两种调用方式：
      // 1. getHistogram(startTime, endTime) - 传统方式
      // 2. getHistogram({type, bins, ...}) - 参数对象方式
      
      if (typeof params === 'string') {
        // 传统方式：两个字符串参数
        const startTime = params
        const endTime = arguments[1]
        return await request('GET', '/api/visualization/histogram', null, {
          start_time: startTime,
          end_time: endTime
        })
      } else {
        // 参数对象方式
        return await request('GET', '/api/visualization/histogram', null, params)
      }
    },

    // 获取态度分析数据 (对应原始: /api/visualization/attitude)
    getAttitude: async (startTime, endTime, unit, range) => {
      return await request('GET', '/api/visualization/attitude', null, {
        start_time: startTime,
        end_time: endTime,
        unit,
        range
      })
    },

    // 获取词云数据 (对应原始: /api/visualization/wordcloud)
    getWordcloud: async (startTime, endTime) => {
      return await request('GET', '/api/visualization/wordcloud', null, {
        start_time: startTime,
        end_time: endTime
      })
    },

    // 获取转播树数据 (对应原始: /api/visualization/tree)
    getTree: async (startTime, endTime, dataSource = 'original', agentFile = null) => {
      const params = {
        start_time: startTime,
        end_time: endTime,
        data_source: dataSource
      }
      
      if (agentFile) {
        params.agent_posts_file = agentFile
      }
      
      return await request('GET', '/api/visualization/tree', null, params)
    },

    // 获取可视化选项配置
    getVisualizationOptions: async () => {
      return await request('GET', '/api/visualization/options')
    },

    // ===== 内容API =====
    // 获取主题摘要 (对应原始: /api/content/topic-summary)
    getTopicSummary: async () => {
      return await request('GET', '/api/content/topic-summary')
    },

    // 获取单个帖子详情
    fetchSinglePost: async (params = {}) => {
      return await request('GET', '/api/content/single-post', null, params)
    },

    // 获取态度分析数据
    fetchAttitude: async (params = {}) => {
      return await request('GET', '/api/visualization/attitude', null, params)
    },

    // 获取词云数据
    fetchWordcloud: async (params = {}) => {
      return await request('GET', '/api/visualization/wordcloud', null, params)
    },

    // ===== 智能体API =====
    // 获取智能体列表 (对应原始: /api/agents/)
    getAgents: async () => {
      return await request('GET', '/api/agents/')
    },

    // 添加智能体 (对应原始: /api/agents/add)
    addAgent: async (agentData) => {
      return await request('POST', '/api/agents/add', agentData)
    },

    // 更新智能体 (对应原始: /api/agents/update/{id})
    updateAgent: async (agentId, agentData) => {
      return await request('PUT', `/api/agents/update/${agentId}`, agentData)
    },

    // 删除智能体 (对应原始: /api/agents/delete/{id})
    deleteAgent: async (agentId) => {
      return await request('DELETE', `/api/agents/delete/${agentId}`)
    },

    // ===== 环境API =====
    // 获取环境配置 (对应原始: /api/environment)
    getEnvironment: async () => {
      return await request('GET', '/api/environment')
    },

    // 更新环境配置 (对应原始: /api/environment)
    updateEnvironment: async (envData) => {
      return await request('POST', '/api/environment', envData)
    },

    // ===== 模拟API =====
    // 开始模拟 (对应原始: /api/simulation/start)
    startSimulation: async (config, agentConfigs) => {
      const requestData = {
        config: config,
        agents: agentConfigs
      }
      return await request('POST', '/api/simulation/start', requestData)
    },

    // 停止仿真
    stopSimulation: async (simulationId) => {
      return await request('POST', `/api/simulation/stop/${simulationId}`)
    },

    // 获取仿真状态 (对应原始: /api/simulation/status/{id})
    getSimulationStatus: async (simulationId) => {
      return await request('GET', `/api/simulation/status/${simulationId}`)
    },

    // 获取仿真结果 (对应原始: /api/simulation/results/{id})
    getSimulationResults: async (simulationId) => {
      return await request('GET', `/api/simulation/results/${simulationId}`)
    },

    // 注入事件 (对应原始: /api/simulation/inject_event)
    injectEvent: async (eventData) => {
      return await request('POST', '/api/simulation/inject_event', eventData)
    },

    // 注入飓风消息（紧急广播）- 原始版本
    injectHurricaneMessage: async (simulationId, hurricaneData) => {
      const requestData = {
        simulation_id: simulationId,
        content: hurricaneData.content,
        target_time_slice: hurricaneData.target_time_slice,
        emotion_impact: hurricaneData.emotion_impact || -0.5,
        stance_impact: hurricaneData.stance_impact || 0.0,
        priority: hurricaneData.priority || 999,
        ...hurricaneData
      }
      return await request('POST', '/api/simulation/inject_hurricane', requestData)
    },

    // 注入飓风消息（使用LLM标注并保存到JSON）
    injectHurricaneMessageWithLLM: async (simulationId, content, targetTimeSlice = 0) => {
      const requestData = {
        simulation_id: simulationId,
        content: content,
        target_time_slice: targetTimeSlice
      }
      return await request('POST', '/api/simulation/inject_hurricane_with_llm', requestData)
    },

    // 批量注入多个飓风消息
    injectMultipleHurricanes: async (simulationId, hurricaneList) => {
      const requestData = {
        simulation_id: simulationId,
        hurricanes: hurricaneList
      }
      return await request('POST', '/api/simulation/inject_multiple_hurricanes', requestData)
    },

    // 获取仿真的时间片信息
    getSimulationTimeSlices: async (simulationId) => {
      return await request('GET', `/api/simulation/${simulationId}/timeslices`)
    },

    // 创建对比仿真（基于原仿真+飓风消息）
    createComparisonSimulation: async (originalSimulationId, hurricaneConfig) => {
      const requestData = {
        original_simulation_id: originalSimulationId,
        hurricane_config: hurricaneConfig,
        comparison_name: hurricaneConfig.name || `对比仿真_${new Date().getTime()}`
      }
      return await request('POST', '/api/simulation/create_comparison', requestData)
    },

    // ===== 官方声明API =====
    // 获取官方声明配置面板数据
    getOfficialStatementConfigPanel: async () => {
      return await request('GET', '/api/simulation/official_statement/config_panel')
    },

    // 获取仿真的官方声明详情
    getOfficialStatementSimulationDetails: async (simulationId) => {
      return await request('GET', `/api/simulation/official_statement/simulation_details/${simulationId}`)
    },

    // 注入官方声明（支持Agent配置）
    injectOfficialStatement: async (simulationId, statementConfig, agentConfigs = null) => {
      const requestData = {
        simulation_id: simulationId,
        content: statementConfig.content,
        target_time_slice: statementConfig.target_time_slice,
        statement_type: statementConfig.statement_type,
        authority_level: statementConfig.authority_level,
        custom_tags: statementConfig.custom_tags || [],
        notes: statementConfig.notes || '',
        enable_tracking: statementConfig.enable_tracking || false
      }
      
      // 如果提供了Agent配置，添加到请求中
      if (agentConfigs && agentConfigs.length > 0) {
        requestData.agent_configs = agentConfigs
      }
      
      return await request('POST', '/api/simulation/inject_official_statement', requestData)
    },

    // 获取仿真列表 (使用基于日志的API)
    getSimulationList: async () => {
      return await request('GET', '/api/simulation/log_based/list')
    },

    // 获取仿真的时间片信息（基于日志）
    getSimulationTimeSlices: async (simulationId) => {
      return await request('GET', `/api/simulation/log_based/${simulationId}/time_slices`)
    },

    // 获取仿真详细信息（基于日志）
    getSimulationDetails: async (simulationId) => {
      return await request('GET', `/api/simulation/log_based/${simulationId}/details`)
    },

    // 刷新仿真索引
    refreshSimulationIndex: async () => {
      return await request('POST', '/api/simulation/log_based/refresh_index')
    },

    // 对比仿真结果 (对应原始: /api/simulation/compare)
    compareSimulations: async (simulationIds) => {
      return await request('POST', '/api/simulation/compare', { simulation_ids: simulationIds })
    },

    // ===== 其他API =====
    // 通用搜索
    search: async (query, params = {}) => {
      return await request('GET', '/api/search', null, { query, ...params })
    }
  }
}

// 时间范围管理
export const useTimeRange = () => {
  const timeRange = ref({
    start: '2016-01-01T00:00:00',
    end: '2016-12-31T23:59:59'
  })

  const setTimeRange = (start, end) => {
    timeRange.value = { start, end }
  }

  const formatTimeForAPI = (timeString) => {
    return new Date(timeString).toISOString()
  }

  return {
    timeRange,
    setTimeRange,
    formatTimeForAPI
  }
}

// 为了兼容性，导出useApiComplete作为useApi的别名
export const useApiComplete = useApi
