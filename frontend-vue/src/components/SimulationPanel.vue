<template>
  <div class="simulation-panel">
    <h2>社交仿真控制面板</h2>
    
    <!-- Agent选择配置 -->
    <div class="config-section">
      <h3>Agent配置</h3>
      <div class="agent-selection">
        <div class="agent-actions">
          <button @click="selectAllAgents" class="btn-secondary">全选</button>
          <button @click="deselectAllAgents" class="btn-secondary">全不选</button>
          <button @click="loadAgentsFromFile" class="btn-primary">从文件加载</button>
        </div>
        
        <div class="agent-list" v-if="availableAgents.length > 0">
          <div 
            v-for="agent in availableAgents" 
            :key="agent.agent_id"
            class="agent-item"
            :class="{ selected: selectedAgents.includes(agent.agent_id) }"
            @click="toggleAgent(agent.agent_id)"
          >
            <div class="agent-info">
              <div class="agent-id">{{ agent.agent_id }}</div>
              <div class="agent-details">
                <span class="role-type">{{ formatRoleType(agent.role_type) }}</span>
                <span class="activity">活跃度: {{ agent.activity_level }}</span>
              </div>
              <div class="agent-stats">
                情绪: {{ agent.initial_emotion }} | 立场: {{ agent.initial_stance }} | 置信度: {{ agent.initial_confidence }}
              </div>
            </div>
            <div class="selection-indicator" v-if="selectedAgents.includes(agent.agent_id)">✓</div>
          </div>
        </div>
        
        <div class="agent-summary">
          已选择 {{ selectedAgents.length }} / {{ availableAgents.length }} 个Agent
        </div>
      </div>
    </div>

    <!-- 仿真算法参数 -->
    <div class="config-section">
      <h3>算法参数</h3>
      <div class="param-grid">
        <div class="param-item">
          <label for="w_pop">热度权重 (w_pop)</label>
          <input 
            id="w_pop"
            type="number" 
            v-model.number="simulationConfig.w_pop" 
            min="0" 
            max="1" 
            step="0.1"
            class="param-input"
          />
          <small>控制热度与相关性的权重平衡 (0-1)</small>
        </div>
        
        <div class="param-item">
          <label for="k_value">Sigmoid 陡峭度 (k)</label>
          <input 
            id="k_value"
            type="number" 
            v-model.number="simulationConfig.k" 
            min="1" 
            max="10" 
            step="1"
            class="param-input"
          />
          <small>控制帖子选择的确定性程度，值越大选择越确定</small>
        </div>
        
        <div class="param-item">
          <label for="posts_per_slice">每时间片帖子数</label>
          <input 
            id="posts_per_slice"
            type="number" 
            v-model.number="simulationConfig.posts_per_slice" 
            min="10" 
            max="100" 
            step="10"
            class="param-input"
          />
          <small>每个时间片包含的帖子数量</small>
        </div>
        
        <div class="param-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="simulationConfig.skip_llm"
              class="checkbox-input"
              @change="handleSkipLlmChange"
            />
            <span>跳过大语言模型调用</span>
          </label>
          <small>启用后将跳过LLM调用，仅生成prompt（适用于测试）</small>
        </div>
        
        <div class="param-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="simulationConfig.enable_llm_test"
              class="checkbox-input"
              @change="handleEnableLlmChange"
              :disabled="simulationConfig.skip_llm"
            />
            <span>启用LLM测试模式</span>
          </label>
          <small v-if="simulationConfig.skip_llm" class="warning-text">⚠️ 请先取消"跳过大语言模型调用"</small>
          <small v-else>测试模式：第一个Agent在第一个时间片使用LLM，其他跳过</small>
        </div>
        
        <div class="param-item" v-if="simulationConfig.enable_llm_test">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="simulationConfig.llm_full_monitoring"
              class="checkbox-input"
            />
            <span>完整LLM监控模式</span>
          </label>
          <small>所有选中的Agent在所有时间片都使用LLM (推荐用于实时监控)</small>
        </div>
      </div>
    </div>

    <!-- 仿真模式配置 -->
    <div class="config-section">
      <h3>仿真模式</h3>
      <div class="mode-selection">
        <label class="mode-option">
          <input 
            type="radio" 
            v-model="simulationConfig.mode" 
            value="test"
            name="simulation_mode"
          />
          <span>测试模式 (4个时间片)</span>
        </label>
        <label class="mode-option">
          <input 
            type="radio" 
            v-model="simulationConfig.mode" 
            value="custom"
            name="simulation_mode"
          />
          <span>自定义时间片数</span>
        </label>
        <label class="mode-option">
          <input 
            type="radio" 
            v-model="simulationConfig.mode" 
            value="full"
            name="simulation_mode"
          />
          <span>完整仿真 (全部时间片)</span>
        </label>
      </div>
      
      <!-- 自定义时间片数输入框 -->
      <div class="custom-slices-input" v-if="simulationConfig.mode === 'custom'">
        <div class="param-item">
          <label for="custom_max_slices">运行到第几个时间片</label>
          <input 
            id="custom_max_slices"
            type="number" 
            v-model.number="simulationConfig.custom_max_slices"
            min="1"
            max="50"
            placeholder="请输入时间片数（如：5）"
            class="param-input"
          />
          <small>建议先用5个时间片测试完整仿真是否正常</small>
        </div>
      </div>
    </div>

    <!-- LLM配置 -->
    <div class="config-section" v-if="simulationConfig.enable_llm_test">
      <h3>LLM API 配置</h3>
      <div class="param-grid">
        <div class="param-item">
          <label for="llm_api_key">API Key</label>
          <input 
            id="llm_api_key"
            type="password" 
            v-model="llmConfig.api_key" 
            placeholder="请输入您的LLM API Key"
            class="param-input"
          />
          <small>将设置为环境变量 LLM_API_KEY</small>
        </div>
        
        <div class="param-item">
          <label for="llm_endpoint">API 端点</label>
          <input 
            id="llm_endpoint"
            type="text" 
            v-model="llmConfig.endpoint" 
            placeholder="https://www.chataiapi.com/v1/chat/completions"
            class="param-input"
          />
          <small>LLM API的端点URL</small>
        </div>
        
        <div class="param-item">
          <label for="llm_model">模型名称</label>
          <input 
            id="llm_model"
            type="text" 
            v-model="llmConfig.model" 
            placeholder="gpt-3.5-turbo"
            class="param-input"
          />
          <small>要使用的LLM模型名称</small>
        </div>
      </div>
    </div>

    <!-- 仿真控制 -->
    <div class="control-section">
      <div class="control-buttons">
        <button 
          @click="startSimulation" 
          :disabled="!canStartSimulation || isRunning"
          class="btn-start"
        >
          {{ isRunning ? '仿真运行中...' : '开始仿真' }}
        </button>
        
        <button 
          @click="stopSimulation" 
          :disabled="!isRunning"
          class="btn-stop"
        >
          停止仿真
        </button>
        
        <button 
          @click="resetSimulation" 
          :disabled="isRunning"
          class="btn-reset"
        >
          重置配置
        </button>
      </div>
    </div>

    <!-- 仿真状态 -->
    <div class="status-section" v-if="currentSimulation">
      <h3>仿真状态</h3>
      <div class="status-info">
        <div class="status-item">
          <span class="label">状态：</span>
          <span class="value" :class="currentSimulation.status">{{ formatStatus(currentSimulation.status) }}</span>
        </div>
        <div class="status-item" v-if="currentSimulation.start_time">
          <span class="label">开始时间：</span>
          <span class="value">{{ formatTime(currentSimulation.start_time) }}</span>
        </div>
        <div class="status-item" v-if="simulationProgress">
          <span class="label">进度：</span>
          <span class="value">{{ simulationProgress.current }}/{{ simulationProgress.total }} 时间片</span>
        </div>
      </div>
      
      <div class="progress-bar" v-if="simulationProgress">
        <div 
          class="progress-fill" 
          :style="{ width: (simulationProgress.current / simulationProgress.total * 100) + '%' }"
        ></div>
      </div>
      
      <!-- 实时日志控制 -->
      <div class="realtime-log-controls" v-if="currentSimulation.status === 'running' && (simulationConfig.enable_llm_test || simulationConfig.llm_full_monitoring)">
        <button 
          @click="toggleRealtimeLog" 
          class="btn-log"
          :class="{ 'active': showRealtimeLog }"
        >
          {{ showRealtimeLog ? '隐藏实时日志' : '显示实时日志' }}
        </button>
        <button 
          @click="clearRealtimeLog" 
          class="btn-clear"
          :disabled="!realtimeLogContent"
        >
          清空日志
        </button>
      </div>
    </div>

    <!-- 实时日志查看器 -->
    <div class="realtime-log-viewer" v-if="showRealtimeLog && currentSimulation">
      <div class="realtime-log-header">
        <h3>🔥 实时仿真日志</h3>
        <div class="log-controls">
          <span class="log-status" :class="realtimeLogStatus">{{ formatLogStatus(realtimeLogStatus) }}</span>
          <button @click="toggleAutoScroll" class="btn-auto-scroll" :class="{ 'active': autoScroll }">
            {{ autoScroll ? '📍 自动滚动' : '🔒 停止滚动' }}
          </button>
        </div>
      </div>
      <div class="realtime-log-content" ref="realtimeLogContainer">
        <div v-if="!realtimeLogContent" class="log-waiting">
          <div class="loading-spinner"></div>
          <p>等待日志数据...</p>
        </div>
        <pre v-else>{{ realtimeLogContent }}</pre>
      </div>
    </div>

    <!-- 仿真结果 -->
    <div class="results-section" v-if="simulationResults">
      <h3>仿真结果</h3>
      <div class="results-summary">
        <div class="result-item">
          <span class="label">总时间片：</span>
          <span class="value">{{ simulationResults.total_slices }}</span>
        </div>
        <div class="result-item">
          <span class="label">参与Agent：</span>
          <span class="value">{{ simulationResults.agent_count }}</span>
        </div>
        <div class="result-item">
          <span class="label">执行时间：</span>
          <span class="value">{{ simulationResults.duration }}秒</span>
        </div>
      </div>
      
      <div class="result-actions">
        <button @click="viewDetailedResults" class="btn-primary">查看详细结果</button>
        <button @click="viewDetailedLog" class="btn-secondary">查看详细日志</button>
        <button @click="downloadResults" class="btn-secondary">下载结果</button>
        <button @click="downloadLog" class="btn-secondary">下载日志</button>
      </div>
    </div>

    <!-- 详细日志查看器 -->
    <div class="log-viewer" v-if="showLogViewer">
      <div class="log-viewer-header">
        <h3>仿真详细日志</h3>
        <button @click="closeLogViewer" class="btn-close">×</button>
      </div>
      <div class="log-content">
        <pre>{{ detailedLog }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useApiComplete } from '../composables/useApiComplete'

export default {
  name: 'SimulationPanel',
  setup() {
    const { 
      getAgents, 
      startSimulation, 
      getSimulationStatus, 
      stopSimulation: apiStopSimulation 
    } = useApiComplete()

    // 响应式数据
    const availableAgents = ref([])
    const selectedAgents = ref([])
    const isRunning = ref(false)
    const currentSimulation = ref(null)
    const simulationResults = ref(null)
    const simulationProgress = ref(null)
    const showLogViewer = ref(false)
    const detailedLog = ref('')

    // 实时日志相关
    const showRealtimeLog = ref(false)
    const realtimeLogContent = ref('')
    const realtimeLogStatus = ref('waiting') // waiting, connected, error, finished
    const autoScroll = ref(true)
    const realtimeLogContainer = ref(null)
    let realtimeEventSource = null

    // LLM配置
    const llmConfig = reactive({
      api_key: 'sk-oPCS3RtcJEtOORaFvskbBI75eJ6jzJcs4vtK3I2vyw7DcrRK',
      endpoint: 'https://www.chataiapi.com/v1/chat/completions',
      model: 'deepseek-v3-250324'
    })

    // 仿真配置 - 基于test_with_config.py中的参数
    const simulationConfig = reactive({
      w_pop: 0.7,               // 热度权重
      k: 2,                     // 选择数量
      posts_per_slice: 30,      // 每时间片帖子数（对应test_with_config.py中的posts_per_timeslice）
      mode: 'test',             // 仿真模式：test(4个时间片) 或 custom(自定义) 或 full(全部时间片)
      custom_max_slices: 5,     // 自定义时间片数，默认5个
      skip_llm: true,           // 跳过LLM调用（默认启用，适合测试）
      enable_llm_test: false,   // LLM测试模式
      llm_full_monitoring: false // 完整LLM监控模式
    })

    // 计算属性
    const canStartSimulation = computed(() => {
      return selectedAgents.value.length > 0 && !isRunning.value
    })

    // Agent相关方法
    const loadAgentsFromFile = async () => {
      try {
        const response = await getAgents()
        if (response.success) {
          availableAgents.value = response.data
          // 默认选择所有agent（对应test_with_config.py中使用所有agents的逻辑）
          selectedAgents.value = response.data.map(agent => agent.agent_id)
        } else {
          console.error('加载Agent失败:', response.error)
        }
      } catch (error) {
        console.error('加载Agent时发生错误:', error)
      }
    }

    const toggleAgent = (agentId) => {
      const index = selectedAgents.value.indexOf(agentId)
      if (index > -1) {
        selectedAgents.value.splice(index, 1)
      } else {
        selectedAgents.value.push(agentId)
      }
    }

    const selectAllAgents = () => {
      selectedAgents.value = [...availableAgents.value.map(agent => agent.agent_id)]
    }

    const deselectAllAgents = () => {
      selectedAgents.value = []
    }

    // 仿真控制方法
    const startSimulationProcess = async () => {
      console.log('🚀 开始启动仿真流程...')
      console.log('canStartSimulation:', canStartSimulation.value)
      console.log('selectedAgents:', selectedAgents.value)
      console.log('simulationConfig:', simulationConfig)
      
      if (!canStartSimulation.value) {
        console.error('❌ 无法启动仿真：不满足启动条件')
        return
      }

      try {
        isRunning.value = true
        console.log('✅ 设置运行状态为true')
        
        // 获取选中的agent配置（需要在使用前定义）
        const selectedAgentConfigs = availableAgents.value.filter(
          agent => selectedAgents.value.includes(agent.agent_id)
        )
        console.log('📋 选中的Agent配置:', selectedAgentConfigs.map(a => a.agent_id))
        
        if (selectedAgentConfigs.length === 0) {
          console.error('❌ 没有选中任何Agent')
          isRunning.value = false
          return
        }
        
        // 准备仿真配置 - 对应test_with_config.py中的参数
        const config = {
          w_pop: simulationConfig.w_pop,
          k: simulationConfig.k,
          posts_per_slice: simulationConfig.posts_per_slice,
          skip_llm: simulationConfig.skip_llm,
          // 根据模式设置最大时间片数
          max_slices: simulationConfig.mode === 'test' ? 4 : 
                     simulationConfig.mode === 'custom' ? simulationConfig.custom_max_slices : 
                     null // full模式不限制
        }
        console.log('⚙️ 基础配置:', config)
        
        // LLM测试配置
        if (simulationConfig.enable_llm_test && selectedAgentConfigs.length > 0) {
          console.log('🤖 配置LLM测试模式...')
          // 检查是否是完整LLM监控模式
          if (simulationConfig.llm_full_monitoring) {
            // 完整监控模式：所有选中的Agent在所有时间片都启用LLM
            config.llm_config = {
              enabled_agents: selectedAgentConfigs.map(agent => agent.agent_id), // 所有选中的Agent
              enabled_timeslices: Array.from({length: config.max_slices || 10}, (_, i) => i) // 所有时间片
            }
            console.log('📊 LLM完整监控模式：', config.llm_config)
          } else {
            // 测试模式：只对第一个Agent的第一个时间片启用LLM
            config.llm_config = {
              enabled_agents: [selectedAgentConfigs[0].agent_id], // 只对第一个Agent启用LLM
              enabled_timeslices: [0] // 只在第一个时间片启用LLM
            }
            console.log('🧪 LLM测试模式：', config.llm_config)
          }
          
          config.skip_llm = false // 覆盖全局skip_llm设置
          
          // 传递LLM API配置
          config.llm_config = {
            ...config.llm_config,  // 保留enabled_agents和enabled_timeslices
            api_key: llmConfig.api_key,
            base_url: llmConfig.endpoint,
            model: llmConfig.model,
            enabled: true
          }
          
          console.log('🔑 LLM API配置：', { 
            endpoint: llmConfig.endpoint, 
            model: llmConfig.model,
            hasApiKey: !!llmConfig.api_key 
          })
        } else {
          console.log('⏭️ 跳过LLM配置（非LLM测试模式或无选中Agent）')
        }

        console.log('📤 发送仿真启动请求...')
        console.log('最终配置:', config)
        console.log('Agent列表:', selectedAgentConfigs.map(a => a.agent_id))

        // 启动仿真
        const response = await startSimulation(config, selectedAgentConfigs)
        console.log('📥 仿真启动响应:', response)
        
        if (response.status === 'success') {
          console.log('✅ 仿真启动成功，ID:', response.simulation_id)
          currentSimulation.value = {
            id: response.simulation_id,
            status: 'running',
            start_time: new Date().toISOString()
          }
          
          // 开始监控仿真状态
          console.log('👀 开始监控仿真状态...')
          monitorSimulation(response.simulation_id)
        } else {
          console.error('❌ 启动仿真失败:', response.error || response.message || '未知错误')
          isRunning.value = false
        }
      } catch (error) {
        console.error('💥 启动仿真时发生错误:', error)
        console.error('错误堆栈:', error.stack)
        isRunning.value = false
      }
    }

    const stopSimulationProcess = async () => {
      if (!currentSimulation.value) return

      try {
        const response = await apiStopSimulation(currentSimulation.value.id)
        if (response.status === 'success') {
          isRunning.value = false
          currentSimulation.value.status = 'stopped'
          console.log('仿真已停止')
        } else {
          console.error('停止仿真失败:', response.error || response.message)
        }
      } catch (error) {
        console.error('停止仿真时发生错误:', error)
      }
    }

    const resetSimulation = () => {
      currentSimulation.value = null
      simulationResults.value = null
      simulationProgress.value = null
      isRunning.value = false
      showLogViewer.value = false
      detailedLog.value = ''
      showRealtimeLog.value = false
      realtimeLogContent.value = ''
      stopRealtimeLog()
    }

    // 仿真监控
    const monitorSimulation = async (simulationId) => {
      console.log('👀 开始监控仿真，ID:', simulationId)
      console.log('🔧 LLM配置状态:', {
        enable_llm_test: simulationConfig.enable_llm_test,
        llm_full_monitoring: simulationConfig.llm_full_monitoring
      })
      
      // 如果启用了LLM测试模式或完整监控模式，自动开启实时日志
      if (simulationConfig.enable_llm_test || simulationConfig.llm_full_monitoring) {
        console.log('📡 启用实时日志监控...')
        showRealtimeLog.value = true
        startRealtimeLog(simulationId)
      } else {
        console.log('⏭️ 跳过实时日志监控（未启用LLM模式）')
      }

      const pollInterval = setInterval(async () => {
        try {
          const response = await getSimulationStatus(simulationId)
          console.log('📊 仿真状态响应:', response)
          
          if (response.success) {
            const status = response.data
            console.log('📈 仿真状态更新:', status.status, status.progress)
            currentSimulation.value = { ...currentSimulation.value, ...status }
            
            // 更新进度
            if (status.progress) {
              simulationProgress.value = status.progress
            }
            
            // 检查是否完成
            if (status.status === 'completed' || status.status === 'error') {
              clearInterval(pollInterval)
              isRunning.value = false
              stopRealtimeLog() // 停止实时日志
              
              if (status.status === 'completed' && status.results) {
                simulationResults.value = status.results
                // 保存详细日志
                if (status.detailed_log) {
                  detailedLog.value = status.detailed_log
                }
                console.log('仿真完成，结果:', status.results)
              }
            }
          }
        } catch (error) {
          console.error('监控仿真状态时发生错误:', error)
          clearInterval(pollInterval)
          isRunning.value = false
        }
      }, 1000) // 每秒检查一次
    }

    // 结果处理方法
    const viewDetailedResults = () => {
      // 跳转到可视化面板查看详细结果
      console.log('查看详细结果')
    }

    const viewDetailedLog = () => {
      if (detailedLog.value) {
        showLogViewer.value = true
      } else {
        console.log('没有详细日志可显示')
      }
    }

    const closeLogViewer = () => {
      showLogViewer.value = false
    }

    const downloadResults = () => {
      if (!simulationResults.value) return
      
      const dataStr = JSON.stringify(simulationResults.value, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `simulation_results_${Date.now()}.json`
      link.click()
      
      URL.revokeObjectURL(url)
    }

    const downloadLog = () => {
      if (!detailedLog.value) return
      
      const dataBlob = new Blob([detailedLog.value], { type: 'text/plain' })
      const url = URL.createObjectURL(dataBlob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `simulation_log_${Date.now()}.txt`
      link.click()
      
      URL.revokeObjectURL(url)
    }

    // 格式化方法
    const formatRoleType = (roleType) => {
      const roleMap = {
        'ordinary_user': '普通用户',
        'opinion_leader': '意见领袖',
        'bot': '机器人'
      }
      return roleMap[roleType] || roleType
    }

    const formatStatus = (status) => {
      const statusMap = {
        'running': '运行中',
        'completed': '已完成',
        'error': '错误',
        'stopped': '已停止'
      }
      return statusMap[status] || status
    }

    const formatTime = (timeStr) => {
      return new Date(timeStr).toLocaleString()
    }

    // 实时日志相关方法
    const formatLogStatus = (status) => {
      const statusMap = {
        'waiting': '等待连接',
        'connected': '正在接收',
        'error': '连接错误',
        'finished': '已完成'
      }
      return statusMap[status] || status
    }

    const toggleRealtimeLog = () => {
      showRealtimeLog.value = !showRealtimeLog.value
      if (showRealtimeLog.value && currentSimulation.value) {
        startRealtimeLog(currentSimulation.value.id)
      } else {
        stopRealtimeLog()
      }
    }

    const clearRealtimeLog = () => {
      realtimeLogContent.value = ''
    }

    const toggleAutoScroll = () => {
      autoScroll.value = !autoScroll.value
    }

    const scrollToBottom = () => {
      if (autoScroll.value && realtimeLogContainer.value) {
        const container = realtimeLogContainer.value
        container.scrollTop = container.scrollHeight
      }
    }

    const startRealtimeLog = (simulationId) => {
      console.log('📡 启动实时日志连接，仿真ID:', simulationId)
      
      if (realtimeEventSource) {
        console.log('🔄 关闭现有的实时日志连接')
        realtimeEventSource.close()
      }

      realtimeLogStatus.value = 'waiting'
      realtimeLogContent.value = ''

      // 创建EventSource连接
      const logUrl = `http://localhost:5000/api/simulation/realtime_log/${simulationId}`
      console.log('🌐 连接实时日志URL:', logUrl)
      
      realtimeEventSource = new EventSource(logUrl)

      realtimeEventSource.onopen = () => {
        realtimeLogStatus.value = 'connected'
        console.log('✅ 实时日志连接已建立')
      }

      realtimeEventSource.onmessage = (event) => {
        console.log('📝 收到实时日志数据:', event.data)
        try {
          const data = JSON.parse(event.data)
          
          if (data.error) {
            console.error('❌ 实时日志错误:', data.error)
            realtimeLogStatus.value = 'error'
            return
          }

          if (data.content) {
            // 安全地解析repr字符串，避免使用eval
            try {
              const content = JSON.parse(data.content)
              realtimeLogContent.value += content
              console.log('📄 添加日志内容，长度:', content.length)
            } catch {
              // 如果JSON解析失败，直接使用原始内容
              realtimeLogContent.value += data.content
              console.log('📄 添加原始日志内容，长度:', data.content.length)
            }
            
            // 自动滚动到底部
            setTimeout(scrollToBottom, 50)
          }

          if (data.finished) {
            console.log('🏁 实时日志接收完成')
            realtimeLogStatus.value = 'finished'
            realtimeEventSource.close()
            realtimeEventSource = null
          }

        } catch (error) {
          console.error('💥 解析实时日志数据失败:', error)
          console.error('原始数据:', event.data)
        }
      }

      realtimeEventSource.onerror = (error) => {
        console.error('🚫 实时日志连接错误:', error)
        realtimeLogStatus.value = 'error'
        realtimeEventSource.close()
        realtimeEventSource = null
      }
    }

    const stopRealtimeLog = () => {
      if (realtimeEventSource) {
        realtimeEventSource.close()
        realtimeEventSource = null
      }
      realtimeLogStatus.value = 'waiting'
    }

    // 处理选项冲突的方法
    const handleSkipLlmChange = () => {
      // 当启用"跳过LLM"时，自动禁用其他LLM相关选项
      if (simulationConfig.skip_llm) {
        simulationConfig.enable_llm_test = false
        simulationConfig.llm_full_monitoring = false
      }
    }

    const handleEnableLlmChange = () => {
      // 当启用"LLM测试模式"时，自动禁用"跳过LLM"
      if (simulationConfig.enable_llm_test) {
        simulationConfig.skip_llm = false
      }
    }

    // 生命周期
    onMounted(() => {
      loadAgentsFromFile()
    })

    return {
      // 数据
      availableAgents,
      selectedAgents,
      simulationConfig,
      isRunning,
      currentSimulation,
      simulationResults,
      simulationProgress,
      showLogViewer,
      detailedLog,
      llmConfig,
      
      // 实时日志相关
      showRealtimeLog,
      realtimeLogContent,
      realtimeLogStatus,
      autoScroll,
      realtimeLogContainer,
      
      // 计算属性
      canStartSimulation,
      
      // 方法
      loadAgentsFromFile,
      toggleAgent,
      selectAllAgents,
      deselectAllAgents,
      startSimulation: startSimulationProcess,
      stopSimulation: stopSimulationProcess,
      resetSimulation,
      viewDetailedResults,
      viewDetailedLog,
      closeLogViewer,
      downloadResults,
      downloadLog,
      formatRoleType,
      formatStatus,
      formatTime,
      formatLogStatus,
      toggleRealtimeLog,
      clearRealtimeLog,
      toggleAutoScroll,
      handleSkipLlmChange,
      handleEnableLlmChange
    }
  }
}
</script>

<style scoped>
.simulation-panel {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  max-height: 80vh;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 自定义滚动条样式 */
.simulation-panel::-webkit-scrollbar {
  width: 8px;
}

.simulation-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.simulation-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.simulation-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.simulation-panel h2 {
  margin-bottom: 24px;
  color: #333;
  font-size: 24px;
}

.config-section {
  margin-bottom: 32px;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
}

.config-section h3 {
  margin: 0 0 16px 0;
  color: #555;
  font-size: 18px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 8px;
}

/* Agent选择样式 */
.agent-actions {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.agent-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.agent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.agent-item:hover {
  background-color: #f0f8ff;
}

.agent-item.selected {
  background-color: #e3f2fd;
  border-left: 4px solid #2196F3;
}

.agent-info {
  flex: 1;
}

.agent-id {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.agent-details {
  display: flex;
  gap: 16px;
  margin-bottom: 4px;
}

.role-type {
  background: #e1f5fe;
  color: #0277bd;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.activity {
  color: #666;
  font-size: 12px;
}

.agent-stats {
  color: #666;
  font-size: 11px;
}

.selection-indicator {
  color: #4CAF50;
  font-size: 18px;
  font-weight: bold;
}

.agent-summary {
  margin-top: 12px;
  padding: 8px 12px;
  background: #e8f5e8;
  border-radius: 4px;
  color: #2e7d32;
  font-weight: 500;
}

/* 参数配置样式 */
.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item label {
  font-weight: 500;
  color: #555;
}

.param-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.param-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.param-item small {
  color: #666;
  font-size: 12px;
}

/* 复选框样式 */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #555;
}

.checkbox-input {
  margin: 0;
  transform: scale(1.2);
}

/* 模式选择样式 */
.mode-selection {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  transition: all 0.2s;
}

.mode-option:hover {
  background: #f5f5f5;
}

.mode-option input[type="radio"] {
  margin: 0;
}

/* 自定义时间片输入样式 */
.custom-slices-input {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.custom-slices-input .param-item {
  max-width: 300px;
}

.custom-slices-input input[type="number"] {
  font-size: 16px;
  padding: 10px 12px;
}

/* 控制按钮样式 */
.control-section {
  margin-bottom: 24px;
}

.control-buttons {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary, .btn-start, .btn-stop, .btn-reset {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover {
  background: #45a049;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-start {
  background: #2196F3;
  color: white;
}

.btn-start:hover:not(:disabled) {
  background: #1976D2;
}

.btn-stop {
  background: #f44336;
  color: white;
}

.btn-stop:hover:not(:disabled) {
  background: #d32f2f;
}

.btn-reset {
  background: #ff9800;
  color: white;
}

.btn-reset:hover:not(:disabled) {
  background: #f57c00;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 状态显示样式 */
.status-section {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.status-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item .label {
  font-weight: 500;
  color: #666;
}

.status-item .value {
  font-weight: bold;
}

.status-item .value.running {
  color: #2196F3;
}

.status-item .value.completed {
  color: #4CAF50;
}

.status-item .value.error {
  color: #f44336;
}

.status-item .value.stopped {
  color: #ff9800;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4CAF50;
  transition: width 0.3s ease;
}

/* 结果显示样式 */
.results-section {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-item .label {
  font-weight: 500;
  color: #666;
}

.result-item .value {
  font-weight: bold;
  color: #333;
}

.result-actions {
  display: flex;
  gap: 12px;
}

/* 日志查看器样式 */
.log-viewer {
  position: fixed;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.log-viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #ddd;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.log-viewer-header h3 {
  margin: 0;
  color: #333;
}

.btn-close {
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: #d32f2f;
}

.log-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.log-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 警告文本样式 */
.warning-text {
  color: #ff9800 !important;
  font-weight: 500;
}

/* 实时日志控制样式 */
.realtime-log-controls {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-log {
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-log:hover {
  background: #1976D2;
}

.btn-log.active {
  background: #4CAF50;
}

.btn-clear {
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-clear:hover:not(:disabled) {
  background: #f57c00;
}

.btn-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 实时日志查看器样式 */
.realtime-log-viewer {
  margin-top: 20px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-height: 60vh;
  display: flex;
  flex-direction: column;
}

.realtime-log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #ddd;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 8px 0 0;
}

.realtime-log-header h3 {
  margin: 0;
  font-size: 16px;
}

.log-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.log-status.waiting {
  background: rgba(255, 193, 7, 0.2);
  color: #fff59d;
}

.log-status.connected {
  background: rgba(76, 175, 80, 0.2);
  color: #c8e6c9;
}

.log-status.error {
  background: rgba(244, 67, 54, 0.2);
  color: #ffcdd2;
}

.log-status.finished {
  background: rgba(156, 39, 176, 0.2);
  color: #e1bee7;
}

.btn-auto-scroll {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-auto-scroll:hover {
  background: rgba(255, 255, 255, 0.2);
}

.btn-auto-scroll.active {
  background: rgba(76, 175, 80, 0.3);
  border-color: rgba(76, 175, 80, 0.5);
}

.realtime-log-content {
  flex: 1;
  padding: 16px;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: calc(60vh - 60px);
}

.realtime-log-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #888;
}

.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2196F3;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 自定义滚动条样式 */
.realtime-log-content::-webkit-scrollbar {
  width: 8px;
}

.realtime-log-content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.realtime-log-content::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.realtime-log-content::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>
