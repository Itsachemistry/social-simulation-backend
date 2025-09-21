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

  // 获取帖子列表
  const fetchPosts = async (params = {}) => {
    return await request('GET', '/api/posts', null, params)
  }

  // 获取主题信息
  const fetchTopic = async () => {
    return await request('GET', '/api/topic')
  }

  // 获取智能体信息
  const fetchAgents = async (params = {}) => {
    return await request('GET', '/api/agents', null, params)
  }

  // 获取时间轴数据
  const fetchTimeline = async (params = {}) => {
    return await request('GET', '/api/timeline', null, params)
  }

  // 获取转播树数据
  const fetchTree = async (params = {}) => {
    return await request('GET', '/api/tree', null, params)
  }

  // 获取词云数据
  const fetchWordcloud = async (params = {}) => {
    return await request('GET', '/api/wordcloud', null, params)
  }

  // 获取态度分析数据
  const fetchAttitude = async (params = {}) => {
    return await request('GET', '/api/attitude', null, params)
  }

  // 获取直方图数据
  const fetchHistogram = async (params = {}) => {
    return await request('GET', '/api/histogram', null, params)
  }

  // 获取单帖分析数据
  const fetchSinglePost = async (params = {}) => {
    return await request('GET', '/api/single', null, params)
  }

  // 搜索功能
  const searchPosts = async (query, params = {}) => {
    return await request('GET', '/api/search', null, { query, ...params })
  }

  // 配置相关API
  const saveConfig = async (config) => {
    return await request('POST', '/api/config', config)
  }

  const loadConfig = async () => {
    return await request('GET', '/api/config')
  }

  // 模拟控制API
  const startSimulation = async (params = {}) => {
    return await request('POST', '/api/simulation/start', params)
  }

  const stopSimulation = async () => {
    return await request('POST', '/api/simulation/stop')
  }

  const resetSimulation = async () => {
    return await request('POST', '/api/simulation/reset')
  }

  return {
    loading,
    error,
    fetchPosts,
    fetchTopic,
    fetchAgents,
    fetchTimeline,
    fetchTree,
    fetchWordcloud,
    fetchAttitude,
    fetchHistogram,
    fetchSinglePost,
    searchPosts,
    saveConfig,
    loadConfig,
    startSimulation,
    stopSimulation,
    resetSimulation
  }
}
