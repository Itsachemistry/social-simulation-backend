<template>
  <div class="official-statement-demo">
    <div class="demo-header">
      <h1>🏛️ 官方声明仿真对比演示</h1>
      <p>展示如何在原始仿真基础上添加官方声明（辟谣、澄清、通知）进行舆论干预效果分析</p>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
        <div class="step-number">1</div>
        <div class="step-label">选择基础仿真</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
        <div class="step-number">2</div>
        <div class="step-label">选择Agent配置</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
        <div class="step-number">3</div>
        <div class="step-label">配置官方声明</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 4, completed: currentStep > 4 }">
        <div class="step-number">4</div>
        <div class="step-label">启动对比仿真</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 5 }">
        <div class="step-number">5</div>
        <div class="step-label">分析干预效果</div>
      </div>
    </div>

    <!-- 步骤1: 选择基础仿真 -->
    <div v-if="currentStep === 1" class="step-content">
      <h2>选择要进行舆论干预分析的基础仿真</h2>
      <div class="refresh-actions">
        <button @click="refreshSimulations" class="btn-refresh" :disabled="loading">
          <span v-if="loading">🔄</span>
          <span v-else>🔄</span>
          刷新仿真列表
        </button>
      </div>
      <div class="simulation-list">
        <div
          v-for="simulation in availableSimulations"
          :key="simulation.id"
          class="simulation-card"
          :class="{ selected: selectedSimulation?.id === simulation.id }"
          @click="selectSimulation(simulation)"
        >
          <div class="simulation-info">
            <h3>{{ simulation.name || `仿真 ${simulation.id.substring(0, 8)}` }}</h3>
            <p>状态: {{ getStatusText(simulation.status) }}</p>
            <p>开始时间: {{ formatTime(simulation.start_time) }}</p>
            <p>Agent数量: {{ simulation.agent_count }}</p>
            <p>时间片数: {{ simulation.total_time_slices || 'N/A' }}</p>
          </div>
          <div class="simulation-status" :class="simulation.status">
            {{ getStatusIcon(simulation.status) }}
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button 
          @click="nextStep" 
          :disabled="!selectedSimulation"
          class="btn-primary"
        >
          下一步：配置官方声明
        </button>
      </div>
    </div>

    <!-- 步骤2: 配置官方声明 -->
    <!-- 步骤2: 选择Agent配置 -->
    <div v-if="currentStep === 2" class="step-content">
      <h2>选择参与仿真的Agent</h2>
      <p class="step-description">
        <strong>💡 实验建议：</strong> 为了确保对比实验的有效性，建议选择与原始仿真相同的Agent配置。
        但如果您有特殊的实验设计需求，也可以选择不同的Agent组合。
      </p>
      
      <div class="agent-selection">
        <div class="selection-header">
          <h3>可用Agent列表 ({{ availableAgents.length }} 个)</h3>
          <div class="batch-actions">
            <button @click="selectAllAgents" class="btn-secondary btn-small">全选</button>
            <button @click="clearAllAgents" class="btn-secondary btn-small">清空</button>
          </div>
        </div>

        <div class="agent-grid">
          <div
            v-for="agent in availableAgents"
            :key="agent.agent_id"
            class="agent-card"
            :class="{ selected: isAgentSelected(agent.agent_id) }"
            @click="toggleAgent(agent)"
          >
            <div class="agent-header">
              <h4>{{ agent.agent_id }}</h4>
              <span class="role-badge" :class="agent.role_type">
                {{ getRoleTypeName(agent.role_type) }}
              </span>
            </div>
            <div class="agent-details">
              <div class="agent-stat">
                <label>态度坚定性:</label>
                <span>{{ agent.attitude_firmness }}</span>
              </div>
              <div class="agent-stat">
                <label>观点阻塞:</label>
                <span>{{ agent.opinion_blocking }}</span>
              </div>
              <div class="agent-stat">
                <label>活跃度:</label>
                <span>{{ agent.activity_level }}</span>
              </div>
            </div>
            <div class="agent-emotions">
              <div class="emotion-stat">
                <label>初始情绪:</label>
                <span :class="getEmotionClass(agent.initial_emotion)">
                  {{ agent.initial_emotion }}
                </span>
              </div>
              <div class="emotion-stat">
                <label>初始立场:</label>
                <span :class="getStanceClass(agent.initial_stance)">
                  {{ agent.initial_stance }}
                </span>
              </div>
              <div class="emotion-stat">
                <label>初始信心:</label>
                <span>{{ agent.initial_confidence }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="selection-summary">
          <p><strong>已选择:</strong> {{ selectedAgents.length }} 个Agent</p>
          <div v-if="selectedAgents.length > 0" class="selected-agents">
            <span 
              v-for="agentId in selectedAgents" 
              :key="agentId" 
              class="selected-agent-tag"
            >
              {{ agentId }}
            </span>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button @click="prevStep" class="btn-secondary">上一步</button>
        <button 
          @click="nextStep" 
          :disabled="selectedAgents.length === 0"
          class="btn-primary"
        >
          下一步：配置官方声明 ({{ selectedAgents.length }} 个Agent)
        </button>
      </div>
    </div>

    <!-- 步骤3: 配置官方声明 -->
    <div v-if="currentStep === 3" class="step-content">
      <h2>配置官方声明内容</h2>
      
      <div class="statement-config">
        <div class="basic-config">
          <div class="form-group">
            <label>声明内容:</label>
            <textarea 
              v-model="statementConfig.content"
              placeholder="输入官方声明内容，例如：【官方澄清】经核实，网传相关信息不属实，请广大网友理性判断..."
              rows="4"
              class="statement-content"
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>发布时间片:</label>
              <select v-model="statementConfig.target_time_slice">
                <option
                  v-for="slice in timeSlices"
                  :key="slice.index"
                  :value="slice.index"
                >
                  时间片 {{ slice.index + 1 }} ({{ slice.timeRange }})
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>声明类型:</label>
              <select v-model="statementConfig.statement_type">
                <option 
                  v-for="type in statementTypes" 
                  :key="type.id" 
                  :value="type.id"
                >
                  {{ type.name }} - {{ type.description }}
                </option>
              </select>
              <div class="field-hint">
                💡 所有声明都会被强制阅读，类型主要影响情绪和立场倾向
              </div>
            </div>

            <div class="form-group">
              <label>权威级别:</label>
              <select v-model="statementConfig.authority_level">
                <option 
                  v-for="level in authorityLevels" 
                  :key="level.id" 
                  :value="level.id"
                >
                  {{ level.name }} - {{ level.description }}
                </option>
              </select>
              <div class="field-hint">
                🎯 影响传播热度和影响强度，但不影响是否被阅读
              </div>
            </div>
          </div>

          <!-- 效果预览 -->
          <div class="effect-preview">
            <h3>预期影响效果:</h3>
            <div class="effect-grid">
              <div class="effect-item">
                <label>情绪影响:</label>
                <span>{{ getSelectedType()?.emotion_effect || '未知' }}</span>
              </div>
              <div class="effect-item">
                <label>立场影响:</label>
                <span>{{ getSelectedType()?.stance_effect || '未知' }}</span>
              </div>
              <div class="effect-item">
                <label>影响强度:</label>
                <span>{{ getSelectedLevel()?.influence_multiplier * 100 }}%</span>
              </div>
            </div>
            <div class="llm-info">
              <p><strong>🤖 智能标记：</strong>声明内容将结合类型和权威级别发送给LLM进行智能分析，LLM标记结果将覆盖上述默认效果。如果LLM标记失败，则使用上述默认参数。</p>
            </div>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button @click="prevStep" class="btn-secondary">上一步</button>
        <button 
          @click="nextStep" 
          :disabled="!isStatementConfigValid"
          class="btn-primary"
        >
          下一步：启动对比仿真
        </button>
      </div>
    </div>

    <!-- 步骤4: 启动对比仿真 -->
    <div v-if="currentStep === 4" class="step-content">
      <h2>启动对比仿真</h2>
      
      <div class="comparison-summary">
        <h3>对比仿真配置总览:</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <label>原始仿真:</label>
            <span>{{ selectedSimulation.name || selectedSimulation.id.substring(0, 8) }}</span>
          </div>
          <div class="summary-item full-width">
            <label>完整声明内容:</label>
            <span class="statement-preview">【{{ getSelectedType()?.name || '官方声明' }}】【{{ getSelectedLevel()?.name || '高权威' }}】{{ statementConfig.content }}</span>
          </div>
          <div class="summary-item">
            <label>声明类型:</label>
            <span>{{ getSelectedType()?.name }}</span>
          </div>
          <div class="summary-item">
            <label>权威级别:</label>
            <span>{{ getSelectedLevel()?.name }}</span>
          </div>
          <div class="summary-item">
            <label>发布时机:</label>
            <span>时间片 {{ statementConfig.target_time_slice + 1 }}</span>
          </div>
        </div>
      </div>

      <div class="launch-controls">
        <button 
          @click="startComparison" 
          :disabled="comparisonRunning"
          class="btn-primary btn-large"
        >
          <span v-if="comparisonRunning">🚀 仿真运行中...</span>
          <span v-else>🚀 启动对比仿真</span>
        </button>
      </div>

      <!-- 仿真状态 -->
      <div v-if="comparisonResult" class="simulation-status">
        <h3>仿真状态:</h3>
        <div class="status-info">
          <p>新仿真ID: {{ comparisonResult.new_simulation_id }}</p>
          <p>状态: {{ comparisonStatus }}</p>
          <div v-if="comparisonStatus === 'completed'" class="completion-message">
            ✅ 对比仿真完成！您可以继续分析干预效果。
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button @click="prevStep" class="btn-secondary" :disabled="comparisonRunning">上一步</button>
        <button 
          @click="nextStep" 
          :disabled="!comparisonResult || comparisonStatus !== 'completed'"
          class="btn-primary"
        >
          下一步：分析结果
        </button>
      </div>
    </div>

    <!-- 步骤5: 分析干预效果 -->
    <div v-if="currentStep === 5" class="step-content">
      <h2>舆论干预效果分析</h2>
      
      <div class="comparison-results">
        <div class="result-summary">
          <h3>对比结果摘要:</h3>
          <div class="result-grid">
            <div class="result-card">
              <h4>原始仿真</h4>
              <p>仿真ID: {{ selectedSimulation.id.substring(0, 8) }}</p>
              <p>无官方干预</p>
            </div>
            <div class="result-card intervention">
              <h4>干预仿真</h4>
              <p>仿真ID: {{ comparisonResult.new_simulation_id.substring(0, 8) }}</p>
              <p>{{ getSelectedType()?.name }}干预</p>
            </div>
          </div>
        </div>

        <div class="analysis-tools">
          <h3>深入分析工具:</h3>
          <div class="tool-buttons">
            <button @click="viewDetailedComparison" class="btn-analysis">
              📊 详细对比图表
            </button>
            <button @click="exportResults" class="btn-analysis">
              📁 导出分析报告
            </button>
            <button @click="viewAgentStates" class="btn-analysis">
              👥 Agent状态对比
            </button>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button @click="resetDemo" class="btn-secondary">重新开始</button>
        <button @click="viewMainDashboard" class="btn-primary">返回主面板</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useApiComplete } from '@/composables/useApiComplete'

// API 调用
const { 
  getOfficialStatementConfigPanel, 
  getOfficialStatementSimulationDetails,
  injectOfficialStatement,
  getSimulationStatus
} = useApiComplete()

// 响应式数据
const currentStep = ref(1)
const loading = ref(false)
const availableSimulations = ref([])
const selectedSimulation = ref(null)
const timeSlices = ref([])
const statementTypes = ref([])
const authorityLevels = ref([])
const comparisonRunning = ref(false)
const comparisonResult = ref(null)
const comparisonStatus = ref('pending')

// Agent选择相关
const availableAgents = ref([])
const selectedAgents = ref([])

// 官方声明配置
const statementConfig = reactive({
  content: '',
  target_time_slice: 0,
  statement_type: 'clarification',
  authority_level: 'high'
})

// 计算属性
const isStatementConfigValid = computed(() => {
  return statementConfig.content.trim().length > 10
})

// 方法
const refreshSimulations = async () => {
  loading.value = true
  try {
    const response = await getOfficialStatementConfigPanel()
    if (response.status === 'success') {
      availableSimulations.value = response.simulations
      statementTypes.value = response.statement_types
      authorityLevels.value = response.authority_levels
      availableAgents.value = response.available_agents || []  // 新增：获取可用Agent
      console.log('获取到Agent列表:', availableAgents.value.length, '个Agent')
    }
  } catch (error) {
    console.error('获取仿真列表失败:', error)
  } finally {
    loading.value = false
  }
}

const selectSimulation = async (simulation) => {
  selectedSimulation.value = simulation
  
  // 获取仿真详情
  try {
    const response = await getOfficialStatementSimulationDetails(simulation.id)
    console.log('获取仿真详情响应:', response)
    // API直接返回仿真详情数据，不是包装在status字段中
    if (response && response.time_slices) {
      timeSlices.value = response.time_slices
      console.log('时间片数据已更新:', response.time_slices)
    } else {
      console.warn('响应中没有time_slices数据:', response)
    }
  } catch (error) {
    console.error('获取仿真详情失败:', error)
  }
}

const nextStep = () => {
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Agent选择方法
const isAgentSelected = (agentId) => {
  return selectedAgents.value.includes(agentId)
}

const toggleAgent = (agent) => {
  const agentId = agent.agent_id
  const index = selectedAgents.value.indexOf(agentId)
  if (index > -1) {
    selectedAgents.value.splice(index, 1)
  } else {
    selectedAgents.value.push(agentId)
  }
}

const selectAllAgents = () => {
  selectedAgents.value = availableAgents.value.map(agent => agent.agent_id)
}

const clearAllAgents = () => {
  selectedAgents.value = []
}

const getRoleTypeName = (roleType) => {
  const roleNames = {
    'ordinary_user': '普通用户',
    'opinion_leader': '意见领袖',
    'bot': '机器人'
  }
  return roleNames[roleType] || roleType
}

const getEmotionClass = (emotion) => {
  if (emotion > 0.3) return 'positive'
  if (emotion < -0.3) return 'negative'
  return 'neutral'
}

const getStanceClass = (stance) => {
  if (stance > 0.3) return 'positive'
  if (stance < -0.3) return 'negative'
  return 'neutral'
}

const startComparison = async () => {
  comparisonRunning.value = true
  comparisonStatus.value = 'running'
  
  try {
    // 构建带有类型和级别信息的完整声明内容
    const selectedType = getSelectedType()
    const selectedLevel = getSelectedLevel()
    
    const enhancedContent = `【${selectedType?.name || '官方声明'}】【${selectedLevel?.name || '高权威'}】${statementConfig.content}`
    
    // 创建增强的配置对象
    const enhancedConfig = {
      ...statementConfig,
      content: enhancedContent
    }
    
    // 获取选中的Agent配置
    const selectedAgentConfigs = availableAgents.value.filter(agent => 
      selectedAgents.value.includes(agent.agent_id)
    )
    
    console.log('发送增强后的声明内容:', enhancedContent)
    console.log('选中的Agent配置:', selectedAgentConfigs.length, '个Agent')
    
    const response = await injectOfficialStatement(
      selectedSimulation.value.id,
      enhancedConfig,
      selectedAgentConfigs  // 传递Agent配置
    )
    
    if (response.status === 'success') {
      comparisonResult.value = response
      console.log('对比仿真启动成功，Agent来源:', response.agent_source)
      
      // 监控仿真状态
      await monitorSimulationStatus(response.new_simulation_id)
    }
  } catch (error) {
    console.error('启动对比仿真失败:', error)
    comparisonStatus.value = 'error'
  } finally {
    comparisonRunning.value = false
  }
}

const monitorSimulationStatus = async (simulationId) => {
  const checkStatus = async () => {
    try {
      const response = await getSimulationStatus(simulationId)
      comparisonStatus.value = response.data.status
      
      if (response.data.status === 'running') {
        setTimeout(checkStatus, 2000) // 每2秒检查一次
      }
    } catch (error) {
      console.error('监控仿真状态失败:', error)
      comparisonStatus.value = 'error'
    }
  }
  
  setTimeout(checkStatus, 1000)
}

const getSelectedType = () => {
  return statementTypes.value.find(t => t.id === statementConfig.statement_type)
}

const getSelectedLevel = () => {
  return authorityLevels.value.find(l => l.id === statementConfig.authority_level)
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'running': '运行中',
    'pending': '等待中',
    'error': '错误'
  }
  return statusMap[status] || status
}

const getStatusIcon = (status) => {
  const iconMap = {
    'completed': '✅',
    'running': '🔄',
    'pending': '⏳',
    'error': '❌'
  }
  return iconMap[status] || '❓'
}

const formatTime = (timeString) => {
  if (!timeString) return 'N/A'
  return new Date(timeString).toLocaleString('zh-CN')
}

const resetDemo = () => {
  currentStep.value = 1
  selectedSimulation.value = null
  comparisonResult.value = null
  comparisonStatus.value = 'pending'
  statementConfig.content = ''
  statementConfig.target_time_slice = 0
  statementConfig.statement_type = 'clarification'
  statementConfig.authority_level = 'high'
}

const viewDetailedComparison = () => {
  // 跳转到详细对比页面
  console.log('查看详细对比')
}

const exportResults = () => {
  // 导出分析报告
  console.log('导出结果')
}

const viewAgentStates = () => {
  // 查看Agent状态对比
  console.log('查看Agent状态')
}

const viewMainDashboard = () => {
  // 返回主面板
  console.log('返回主面板')
}

// 组件挂载时初始化
onMounted(() => {
  refreshSimulations()
})
</script>

<style scoped>
.official-statement-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.demo-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

.demo-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
  font-weight: bold;
}

.demo-header p {
  margin: 0;
  font-size: 1.1em;
  opacity: 0.9;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  justify-content: center;
  margin: 40px 0;
  position: relative;
}

.steps-indicator::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 25%;
  right: 25%;
  height: 2px;
  background: #e0e0e0;
  z-index: 1;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  flex: 1;
  max-width: 200px;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e0e0e0;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s;
}

.step.active .step-number {
  background: #667eea;
  color: white;
}

.step.completed .step-number {
  background: #4CAF50;
  color: white;
}

.step-label {
  font-size: 0.9em;
  color: #666;
  text-align: center;
}

.step.active .step-label {
  color: #667eea;
  font-weight: 600;
}

/* 步骤内容 */
.step-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  margin: 20px 0;
}

.step-content h2 {
  color: #333;
  margin: 0 0 20px 0;
  font-size: 1.8em;
}

/* 仿真列表 */
.refresh-actions {
  margin-bottom: 20px;
  text-align: right;
}

.btn-refresh {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-refresh:hover {
  background: #e0e0e0;
}

.simulation-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.simulation-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  position: relative;
}

.simulation-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.simulation-card.selected {
  border-color: #667eea;
  background: #f8f9ff;
}

.simulation-info h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.simulation-info p {
  margin: 5px 0;
  color: #666;
  font-size: 0.9em;
}

.simulation-status {
  position: absolute;
  top: 15px;
  right: 15px;
  font-size: 1.5em;
}

/* 官方声明配置 */
.statement-config {
  margin: 20px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.statement-content {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
  resize: vertical;
  font-family: inherit;
}

.statement-content:focus {
  outline: none;
  border-color: #667eea;
}

select {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

select:focus {
  outline: none;
  border-color: #667eea;
}

.field-hint {
  font-size: 0.85em;
  color: #666;
  margin-top: 5px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #667eea;
}

/* 效果预览 */
.effect-preview {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.effect-preview h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.effect-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.effect-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.effect-item label {
  font-weight: 500;
  color: #333;
}

.effect-item span {
  color: #667eea;
  font-weight: 600;
}

.llm-info {
  margin-top: 15px;
  padding: 12px;
  background: linear-gradient(135deg, #e8f4f8 0%, #f0f8ff 100%);
  border-radius: 8px;
  border-left: 4px solid #4CAF50;
}

.llm-info p {
  margin: 0;
  font-size: 0.9em;
  color: #555;
  line-height: 1.4;
}

/* 对比摘要 */
.comparison-summary {
  background: #f8f9ff;
  border: 2px solid #667eea;
  border-radius: 12px;
  padding: 20px;
  margin: 20px 0;
}

.comparison-summary h3 {
  margin: 0 0 15px 0;
  color: #667eea;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: white;
  border-radius: 8px;
}

.summary-item.full-width {
  grid-column: 1 / -1;
  flex-direction: column;
  gap: 8px;
}

.statement-preview {
  background: #f8f9ff;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 4px solid #667eea;
  font-style: italic;
  line-height: 1.4;
}

.summary-item label {
  font-weight: 600;
  color: #333;
}

.summary-item span {
  color: #667eea;
}

/* 启动控制 */
.launch-controls {
  text-align: center;
  margin: 30px 0;
}

.btn-large {
  padding: 15px 40px;
  font-size: 1.2em;
  border-radius: 10px;
}

/* 仿真状态 */
.simulation-status {
  background: #f0f8ff;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.status-info p {
  margin: 8px 0;
  color: #333;
}

.completion-message {
  background: #d4edda;
  color: #155724;
  padding: 10px;
  border-radius: 6px;
  margin: 10px 0;
  font-weight: 600;
}

/* 分析结果 */
.comparison-results {
  margin: 20px 0;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 20px 0;
}

.result-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.result-card.intervention {
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
  border: 2px solid #4CAF50;
}

.result-card h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.analysis-tools {
  margin: 30px 0;
}

.tool-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.btn-analysis {
  background: white;
  border: 2px solid #667eea;
  color: #667eea;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-analysis:hover {
  background: #667eea;
  color: white;
}

/* 按钮样式 */
.step-actions {
  display: flex;
  justify-content: space-between;
  margin: 30px 0 0 0;
  padding: 20px 0 0 0;
  border-top: 1px solid #e0e0e0;
}

.btn-primary, .btn-secondary {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-secondary:hover {
  background: #f8f9ff;
}
/* Agent选择样式 */
.agent-selection {
  margin: 20px 0;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.selection-header h3 {
  margin: 0;
  color: #333;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 0.9em;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.agent-card {
  background: white;
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.agent-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.agent-card.selected {
  border-color: #4CAF50;
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.agent-header h4 {
  margin: 0;
  color: #333;
  font-size: 1.1em;
}

.role-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8em;
  font-weight: 600;
}

.role-badge.ordinary_user {
  background: #e3f2fd;
  color: #0277bd;
}

.role-badge.opinion_leader {
  background: #fff3e0;
  color: #e65100;
}

.role-badge.bot {
  background: #f3e5f5;
  color: #7b1fa2;
}

.agent-details, .agent-emotions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 10px 0;
}

.agent-stat, .emotion-stat {
  display: flex;
  justify-content: space-between;
  font-size: 0.9em;
}

.agent-stat label, .emotion-stat label {
  color: #666;
  font-weight: 500;
}

.agent-stat span, .emotion-stat span {
  font-weight: 600;
}

.emotion-stat span.positive {
  color: #4CAF50;
}

.emotion-stat span.negative {
  color: #f44336;
}

.emotion-stat span.neutral {
  color: #666;
}

.selection-summary {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin: 20px 0;
}

.selection-summary p {
  margin: 0 0 10px 0;
  font-weight: 600;
  color: #333;
}

.selected-agents {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-agent-tag {
  background: #4CAF50;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 500;
}

.step-description {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  color: #856404;
  font-size: 0.95em;
  line-height: 1.5;
}

</style>
