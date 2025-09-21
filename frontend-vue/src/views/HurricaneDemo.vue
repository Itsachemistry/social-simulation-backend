<template>
  <div class="hurricane-demo">
    <div class="demo-header">
      <h1>🌪️ 飓风消息仿真对比演示</h1>
      <p>展示如何在仿真完成后添加飓风消息进行对比分析</p>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
        <div class="step-number">1</div>
        <div class="step-label">选择原始仿真</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
        <div class="step-number">2</div>
        <div class="step-label">配置飓风消息</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
        <div class="step-number">3</div>
        <div class="step-label">运行对比仿真</div>
      </div>
      <div class="step" :class="{ active: currentStep >= 4 }">
        <div class="step-number">4</div>
        <div class="step-label">分析对比结果</div>
      </div>
    </div>

    <!-- 步骤1: 选择原始仿真 -->
    <div v-if="currentStep === 1" class="step-content">
      <h2>选择要进行对比的原始仿真</h2>
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
          </div>
          <div class="simulation-status" :class="simulation.status">
            {{ getStatusIcon(simulation.status) }}
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <button 
          class="btn btn-primary" 
          @click="nextStep" 
          :disabled="!selectedSimulation"
        >
          下一步：配置飓风消息
        </button>
      </div>
    </div>

    <!-- 步骤2: 配置飓风消息（使用组件） -->
    <div v-if="currentStep === 2" class="step-content">
      <HurricaneConfigDialog
        v-if="selectedSimulation"
        :original-simulation="selectedSimulation"
        @close="prevStep"
        @confirm="onHurricaneConfigConfirm"
      />
    </div>

    <!-- 步骤3: 运行对比仿真 -->
    <div v-if="currentStep === 3" class="step-content">
      <h2>运行对比仿真</h2>
      <div class="progress-section">
        <div class="progress-card">
          <h3>🌪️ 对比仿真进度</h3>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${comparisonProgress}%` }"></div>
          </div>
          <p>{{ comparisonStatus }}</p>
          
          <div class="hurricane-summary">
            <h4>已配置的飓风消息:</h4>
            <ul>
              <li v-for="(hurricane, index) in hurricaneConfig?.hurricanes" :key="index">
                时间片 {{ hurricane.target_time_slice }}: {{ hurricane.content.substring(0, 40) }}...
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button class="btn btn-secondary" @click="prevStep">返回配置</button>
        <button 
          class="btn btn-primary" 
          @click="nextStep" 
          :disabled="comparisonProgress < 100"
        >
          查看对比结果
        </button>
      </div>
    </div>

    <!-- 步骤4: 对比结果（使用组件） -->
    <div v-if="currentStep === 4" class="step-content">
      <SimulationComparison
        v-if="comparisonSimulationId"
        :original-simulation-id="selectedSimulation.id"
        :comparison-simulation-id="comparisonSimulationId"
        :hurricane-config="hurricaneConfig"
      />
      
      <div class="step-actions">
        <button class="btn btn-secondary" @click="restart">重新开始</button>
        <button class="btn btn-primary" @click="exportResults">导出结果</button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApiComplete.js'
import HurricaneConfigDialog from '../components/HurricaneConfigDialog.vue'
import SimulationComparison from '../components/SimulationComparison.vue'

// Composables
const api = useApi()

// 响应式数据
const currentStep = ref(1)
const loading = ref(false)
const loadingMessage = ref('')

const availableSimulations = ref([])
const selectedSimulation = ref(null)
const hurricaneConfig = ref(null)
const comparisonSimulationId = ref(null)
const comparisonProgress = ref(0)
const comparisonStatus = ref('准备启动对比仿真...')

// 方法
const loadSimulations = async () => {
  try {
    loading.value = true
    loadingMessage.value = '加载仿真列表...'
    
    const response = await api.getSimulationList()
    // 只显示从20250730_110327开始的仿真（包含完整元数据的仿真）
    const cutoffTimestamp = '20250730_110327'
    availableSimulations.value = response.simulations.filter(s => {
      // 排除错误状态的仿真
      if (s.status === 'error') return false
      // 排除unknown仿真
      if (s.id === 'unknown') return false
      // 只保留ID中包含时间戳且大于等于cutoff的仿真
      const match = s.id.match(/sim_(\d{8}_\d{6})/)
      if (match) {
        return match[1] >= cutoffTimestamp
      }
      return false
    })
    
    // 如果没有有效仿真，添加一些模拟数据
    if (availableSimulations.value.length === 0) {
      availableSimulations.value = [
        {
          id: 'demo-simulation-1',
          name: '社交媒体情绪传播仿真',
          status: 'completed',
          start_time: new Date(Date.now() - 3600000).toISOString(),
          agent_count: 20
        },
        {
          id: 'demo-simulation-2',
          name: '舆论极化现象仿真',
          status: 'completed',
          start_time: new Date(Date.now() - 7200000).toISOString(),
          agent_count: 15
        }
      ]
    }
    
  } catch (error) {
    console.error('加载仿真列表失败:', error)
    api.showMessage('加载仿真列表失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

const selectSimulation = (simulation) => {
  selectedSimulation.value = simulation
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

const onHurricaneConfigConfirm = async (config) => {
  hurricaneConfig.value = config.hurricaneConfig
  comparisonSimulationId.value = config.comparisonSimulationId
  
  currentStep.value = 3
  
  // 模拟仿真进度
  simulateComparisonProgress()
}

const simulateComparisonProgress = () => {
  comparisonProgress.value = 0
  const progressInterval = setInterval(() => {
    comparisonProgress.value += Math.random() * 15
    
    if (comparisonProgress.value < 30) {
      comparisonStatus.value = '初始化对比仿真环境...'
    } else if (comparisonProgress.value < 60) {
      comparisonStatus.value = '注入飓风消息...'
    } else if (comparisonProgress.value < 90) {
      comparisonStatus.value = '运行Agent交互模拟...'
    } else if (comparisonProgress.value < 100) {
      comparisonStatus.value = '生成对比分析结果...'
    } else {
      comparisonProgress.value = 100
      comparisonStatus.value = '对比仿真完成！'
      clearInterval(progressInterval)
    }
  }, 1000)
}

const restart = () => {
  currentStep.value = 1
  selectedSimulation.value = null
  hurricaneConfig.value = null
  comparisonSimulationId.value = null
  comparisonProgress.value = 0
  comparisonStatus.value = '准备启动对比仿真...'
}

const exportResults = () => {
  // 导出结果逻辑
  api.showMessage('对比结果已导出', 'success')
}

const getStatusText = (status) => {
  const statusMap = {
    completed: '已完成',
    running: '运行中',
    failed: '失败',
    pending: '等待中'
  }
  return statusMap[status] || status
}

const getStatusIcon = (status) => {
  const iconMap = {
    completed: '✅',
    running: '⏳',
    failed: '❌',
    pending: '⏸️'
  }
  return iconMap[status] || '❓'
}

const formatTime = (timeString) => {
  return new Date(timeString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadSimulations()
})
</script>

<style scoped>
.hurricane-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.demo-header {
  text-align: center;
  margin-bottom: 40px;
}

.demo-header h1 {
  margin: 0 0 12px 0;
  color: #1f2937;
  font-size: 32px;
}

.demo-header p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

.steps-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40px;
  gap: 40px;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
  opacity: 0.4;
  transition: all 0.3s ease;
}

.step.active {
  opacity: 1;
}

.step.completed {
  opacity: 0.7;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step.active .step-number {
  background: #3b82f6;
  color: white;
}

.step.completed .step-number {
  background: #10b981;
  color: white;
}

.step-label {
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.step-content {
  min-height: 400px;
}

.step-content h2 {
  margin: 0 0 24px 0;
  color: #1f2937;
  font-size: 24px;
  text-align: center;
}

.simulation-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.simulation-card {
  padding: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.simulation-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.simulation-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.simulation-info h3 {
  margin: 0 0 12px 0;
  color: #1f2937;
  font-size: 18px;
}

.simulation-info p {
  margin: 4px 0;
  color: #6b7280;
  font-size: 14px;
}

.simulation-status {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 20px;
}

.progress-section {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
}

.progress-card {
  width: 100%;
  max-width: 600px;
  padding: 24px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.progress-card h3 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 20px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 6px;
  transition: width 0.5s ease;
}

.progress-card p {
  text-align: center;
  color: #6b7280;
  margin-bottom: 20px;
}

.hurricane-summary h4 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 16px;
}

.hurricane-summary ul {
  margin: 0;
  padding-left: 20px;
  color: #6b7280;
}

.hurricane-summary li {
  margin-bottom: 8px;
  line-height: 1.4;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 2px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-overlay p {
  color: white;
  font-size: 16px;
  font-weight: 500;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
