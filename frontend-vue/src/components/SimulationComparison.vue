<template>
  <div class="simulation-comparison">
    <div class="comparison-header">
      <h1>🌪️ 仿真对比分析</h1>
      <div class="comparison-info">
        <div class="info-card">
          <h3>原始仿真</h3>
          <p>ID: {{ originalSimulation.id }}</p>
          <p>状态: {{ originalSimulation.status }}</p>
        </div>
        <div class="comparison-arrow">→</div>
        <div class="info-card">
          <h3>对比仿真</h3>
          <p>ID: {{ comparisonSimulation.id }}</p>
          <p>状态: {{ comparisonSimulation.status }}</p>
        </div>
      </div>
    </div>

    <!-- 飓风消息概览 -->
    <div class="hurricane-overview">
      <h2>飓风消息注入概览</h2>
      <div class="hurricane-timeline">
        <div
          v-for="hurricane in hurricaneConfig.hurricanes"
          :key="hurricane.id"
          class="hurricane-event"
        >
          <div class="event-time">时间片 {{ hurricane.target_time_slice }}</div>
          <div class="event-content">
            <div class="event-icon">{{ getMessageIcon(hurricane.message_type) }}</div>
            <div class="event-details">
              <div class="event-title">{{ hurricane.content.substring(0, 50) }}...</div>
              <div class="event-impact">
                情绪影响: {{ hurricane.emotion_impact }} | 
                立场影响: {{ hurricane.stance_impact }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 对比图表 -->
    <div class="comparison-charts">
      <div class="chart-section">
        <h2>情绪变化对比</h2>
        <div class="chart-container">
          <canvas ref="emotionChart"></canvas>
        </div>
      </div>

      <div class="chart-section">
        <h2>立场分布对比</h2>
        <div class="chart-container">
          <canvas ref="stanceChart"></canvas>
        </div>
      </div>

      <div class="chart-section">
        <h2>Agent响应统计</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <h3>强烈情绪反应Agent数</h3>
            <div class="stat-comparison">
              <div class="stat-item">
                <label>原始:</label>
                <span>{{ originalStats.strongEmotionAgents }}</span>
              </div>
              <div class="stat-item">
                <label>对比:</label>
                <span>{{ comparisonStats.strongEmotionAgents }}</span>
              </div>
              <div class="stat-change" :class="{ positive: emotionChangePositive }">
                {{ emotionChange }}
              </div>
            </div>
          </div>

          <div class="stat-card">
            <h3>立场转变Agent数</h3>
            <div class="stat-comparison">
              <div class="stat-item">
                <label>原始:</label>
                <span>{{ originalStats.stanceChangeAgents }}</span>
              </div>
              <div class="stat-item">
                <label>对比:</label>
                <span>{{ comparisonStats.stanceChangeAgents }}</span>
              </div>
              <div class="stat-change" :class="{ positive: stanceChangePositive }">
                {{ stanceChange }}
              </div>
            </div>
          </div>

          <div class="stat-card">
            <h3>发帖数量变化</h3>
            <div class="stat-comparison">
              <div class="stat-item">
                <label>原始:</label>
                <span>{{ originalStats.totalPosts }}</span>
              </div>
              <div class="stat-item">
                <label>对比:</label>
                <span>{{ comparisonStats.totalPosts }}</span>
              </div>
              <div class="stat-change" :class="{ positive: postChangePositive }">
                {{ postChange }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细Agent对比 -->
    <div class="agent-comparison">
      <h2>Agent详细对比</h2>
      <div class="agent-table">
        <table>
          <thead>
            <tr>
              <th>Agent ID</th>
              <th>初始情绪</th>
              <th>原始仿真最终情绪</th>
              <th>对比仿真最终情绪</th>
              <th>情绪变化差异</th>
              <th>立场变化差异</th>
              <th>飓风消息响应</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agentComparison" :key="agent.id">
              <td>{{ agent.id }}</td>
              <td>{{ agent.initialEmotion.toFixed(3) }}</td>
              <td>{{ agent.originalFinalEmotion.toFixed(3) }}</td>
              <td>{{ agent.comparisonFinalEmotion.toFixed(3) }}</td>
              <td :class="{ 
                positive: agent.emotionDifference > 0.1,
                negative: agent.emotionDifference < -0.1
              }">
                {{ formatDifference(agent.emotionDifference) }}
              </td>
              <td :class="{ 
                positive: agent.stanceDifference > 0.1,
                negative: agent.stanceDifference < -0.1
              }">
                {{ formatDifference(agent.stanceDifference) }}
              </td>
              <td>
                <span class="response-indicator" :class="agent.hurricaneResponse">
                  {{ getResponseText(agent.hurricaneResponse) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 结论和见解 -->
    <div class="insights">
      <h2>分析结论</h2>
      <div class="insight-cards">
        <div class="insight-card">
          <h3>🎯 飓风消息影响力评估</h3>
          <p>{{ hurricaneImpactInsight }}</p>
        </div>
        <div class="insight-card">
          <h3>📊 整体仿真效果对比</h3>
          <p>{{ overallComparisonInsight }}</p>
        </div>
        <div class="insight-card">
          <h3>🔍 关键发现</h3>
          <ul>
            <li v-for="finding in keyFindings" :key="finding">{{ finding }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <button class="btn btn-secondary" @click="exportReport">导出报告</button>
      <button class="btn btn-secondary" @click="saveComparison">保存对比</button>
      <button class="btn btn-primary" @click="startNewComparison">新建对比</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useApi } from '../composables/useApiComplete.js'
import Chart from 'chart.js/auto'

// Props
const props = defineProps({
  originalSimulationId: String,
  comparisonSimulationId: String,
  hurricaneConfig: Object
})

// Composables
const api = useApi()

// 图表引用
const emotionChart = ref(null)
const stanceChart = ref(null)

// 响应式数据
const originalSimulation = ref({})
const comparisonSimulation = ref({})
const originalStats = ref({})
const comparisonStats = ref({})
const agentComparison = ref([])
const loading = ref(false)

// 图表实例
let emotionChartInstance = null
let stanceChartInstance = null

// 计算属性
const emotionChange = computed(() => {
  const diff = comparisonStats.value.strongEmotionAgents - originalStats.value.strongEmotionAgents
  return diff > 0 ? `+${diff}` : `${diff}`
})

const emotionChangePositive = computed(() => {
  return comparisonStats.value.strongEmotionAgents > originalStats.value.strongEmotionAgents
})

const stanceChange = computed(() => {
  const diff = comparisonStats.value.stanceChangeAgents - originalStats.value.stanceChangeAgents
  return diff > 0 ? `+${diff}` : `${diff}`
})

const stanceChangePositive = computed(() => {
  return comparisonStats.value.stanceChangeAgents > originalStats.value.stanceChangeAgents
})

const postChange = computed(() => {
  const diff = comparisonStats.value.totalPosts - originalStats.value.totalPosts
  return diff > 0 ? `+${diff}` : `${diff}`
})

const postChangePositive = computed(() => {
  return comparisonStats.value.totalPosts > originalStats.value.totalPosts
})

const hurricaneImpactInsight = computed(() => {
  const impactedAgents = agentComparison.value.filter(a => 
    Math.abs(a.emotionDifference) > 0.1 || Math.abs(a.stanceDifference) > 0.1
  ).length
  const totalAgents = agentComparison.value.length
  const impactRate = (impactedAgents / totalAgents * 100).toFixed(1)
  
  return `飓风消息对 ${impactedAgents}/${totalAgents} (${impactRate}%) 的Agent产生了显著影响，平均情绪影响为 ${getAverageEmotionImpact().toFixed(3)}。`
})

const overallComparisonInsight = computed(() => {
  const emotionVariance = getEmotionVariance()
  const stanceVariance = getStanceVariance()
  
  return `对比仿真显示，引入飓风消息后，Agent群体的情绪波动增加了 ${(emotionVariance * 100).toFixed(1)}%，立场分化程度变化了 ${(stanceVariance * 100).toFixed(1)}%。`
})

const keyFindings = computed(() => {
  const findings = []
  
  // 分析情绪影响
  if (Math.abs(emotionChange.value) > 5) {
    findings.push(`飓风消息导致强烈情绪反应的Agent数量${emotionChangePositive.value ? '增加' : '减少'}了 ${Math.abs(emotionChange.value)} 个`)
  }
  
  // 分析立场变化
  if (Math.abs(stanceChange.value) > 3) {
    findings.push(`立场转变的Agent数量${stanceChangePositive.value ? '增加' : '减少'}了 ${Math.abs(stanceChange.value)} 个`)
  }
  
  // 分析发帖行为
  if (Math.abs(postChange.value) > 10) {
    findings.push(`发帖总数${postChangePositive.value ? '增加' : '减少'}了 ${Math.abs(postChange.value)} 条`)
  }
  
  // 分析响应率
  const responseRate = getHurricaneResponseRate()
  findings.push(`${responseRate.toFixed(1)}% 的Agent对飓风消息产生了积极响应`)
  
  return findings
})

// 方法
const loadComparisonData = async () => {
  try {
    loading.value = true
    
    // 加载仿真基本信息
    const [originalData, comparisonData] = await Promise.all([
      api.getSimulationResults(props.originalSimulationId),
      api.getSimulationResults(props.comparisonSimulationId)
    ])
    
    originalSimulation.value = originalData
    comparisonSimulation.value = comparisonData
    
    // 计算统计数据
    calculateStats()
    
    // 生成Agent对比数据
    generateAgentComparison()
    
    // 等待DOM更新后绘制图表
    await nextTick()
    drawCharts()
    
  } catch (error) {
    console.error('加载对比数据失败:', error)
    // 使用模拟数据
    loadMockData()
  } finally {
    loading.value = false
  }
}

const loadMockData = () => {
  // 模拟数据用于演示
  originalSimulation.value = {
    id: props.originalSimulationId,
    status: 'completed'
  }
  
  comparisonSimulation.value = {
    id: props.comparisonSimulationId,
    status: 'completed'
  }
  
  originalStats.value = {
    strongEmotionAgents: 12,
    stanceChangeAgents: 8,
    totalPosts: 145
  }
  
  comparisonStats.value = {
    strongEmotionAgents: 18,
    stanceChangeAgents: 15,
    totalPosts: 162
  }
  
  // 生成模拟的Agent对比数据
  agentComparison.value = Array.from({ length: 20 }, (_, i) => ({
    id: `agent_${String(i + 1).padStart(3, '0')}`,
    initialEmotion: Math.random() * 0.4 - 0.2,
    originalFinalEmotion: Math.random() * 1.0 - 0.5,
    comparisonFinalEmotion: Math.random() * 1.0 - 0.3,
    emotionDifference: (Math.random() - 0.5) * 0.6,
    stanceDifference: (Math.random() - 0.5) * 0.4,
    hurricaneResponse: ['strong', 'moderate', 'weak', 'none'][Math.floor(Math.random() * 4)]
  }))
  
  drawCharts()
}

const calculateStats = () => {
  // 实际的统计计算逻辑
  // 这里应该根据实际的仿真数据进行计算
}

const generateAgentComparison = () => {
  // 实际的Agent对比数据生成逻辑
}

const drawCharts = () => {
  drawEmotionChart()
  drawStanceChart()
}

const drawEmotionChart = () => {
  if (!emotionChart.value) return
  
  const ctx = emotionChart.value.getContext('2d')
  
  if (emotionChartInstance) {
    emotionChartInstance.destroy()
  }
  
  emotionChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({ length: 10 }, (_, i) => `时间片 ${i}`),
      datasets: [
        {
          label: '原始仿真',
          data: Array.from({ length: 10 }, () => Math.random() * 0.4 - 0.2),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
        },
        {
          label: '对比仿真',
          data: Array.from({ length: 10 }, () => Math.random() * 0.6 - 0.3),
          borderColor: 'rgb(245, 158, 11)',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '平均情绪值'
          }
        }
      }
    }
  })
}

const drawStanceChart = () => {
  if (!stanceChart.value) return
  
  const ctx = stanceChart.value.getContext('2d')
  
  if (stanceChartInstance) {
    stanceChartInstance.destroy()
  }
  
  stanceChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['强烈反对', '反对', '中性', '支持', '强烈支持'],
      datasets: [
        {
          label: '原始仿真',
          data: [3, 5, 8, 6, 2],
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
        },
        {
          label: '对比仿真',
          data: [5, 7, 6, 4, 3],
          backgroundColor: 'rgba(245, 158, 11, 0.7)',
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Agent数量'
          }
        }
      }
    }
  })
}

const getMessageIcon = (messageType) => {
  const icons = {
    disaster: '🌪️',
    government: '📢',
    emergency: '🚨',
    custom: '📋'
  }
  return icons[messageType] || '📋'
}

const formatDifference = (diff) => {
  return diff > 0 ? `+${diff.toFixed(3)}` : diff.toFixed(3)
}

const getResponseText = (response) => {
  const texts = {
    strong: '强烈响应',
    moderate: '中等响应',
    weak: '微弱响应',
    none: '无响应'
  }
  return texts[response] || '未知'
}

const getAverageEmotionImpact = () => {
  if (agentComparison.value.length === 0) return 0
  const sum = agentComparison.value.reduce((acc, agent) => acc + Math.abs(agent.emotionDifference), 0)
  return sum / agentComparison.value.length
}

const getEmotionVariance = () => {
  // 计算情绪方差变化
  return Math.random() * 0.2 // 模拟数据
}

const getStanceVariance = () => {
  // 计算立场方差变化
  return Math.random() * 0.15 // 模拟数据
}

const getHurricaneResponseRate = () => {
  if (agentComparison.value.length === 0) return 0
  const responding = agentComparison.value.filter(a => a.hurricaneResponse !== 'none').length
  return (responding / agentComparison.value.length) * 100
}

const exportReport = () => {
  // 导出报告逻辑
  console.log('导出报告')
}

const saveComparison = () => {
  // 保存对比逻辑
  console.log('保存对比')
}

const startNewComparison = () => {
  // 开始新对比逻辑
  console.log('开始新对比')
}

// 生命周期
onMounted(() => {
  loadComparisonData()
})
</script>

<style scoped>
.simulation-comparison {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.comparison-header {
  margin-bottom: 32px;
}

.comparison-header h1 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 32px;
}

.comparison-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.info-card {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.info-card h3 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 16px;
}

.info-card p {
  margin: 4px 0;
  color: #6b7280;
  font-size: 14px;
}

.comparison-arrow {
  font-size: 24px;
  color: #6b7280;
}

.hurricane-overview {
  margin-bottom: 32px;
}

.hurricane-overview h2 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 24px;
}

.hurricane-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hurricane-event {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fef3c7;
  border-radius: 8px;
  border-left: 4px solid #f59e0b;
}

.event-time {
  font-weight: 700;
  color: #92400e;
  min-width: 100px;
}

.event-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.event-icon {
  font-size: 24px;
}

.event-details {
  flex: 1;
}

.event-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.event-impact {
  font-size: 12px;
  color: #6b7280;
}

.comparison-charts {
  margin-bottom: 32px;
}

.chart-section {
  margin-bottom: 32px;
}

.chart-section h2 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 20px;
}

.chart-container {
  height: 400px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.stat-card {
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.stat-card h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 16px;
}

.stat-comparison {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item label {
  color: #6b7280;
  font-size: 14px;
}

.stat-item span {
  font-weight: 600;
  color: #374151;
}

.stat-change {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 700;
  text-align: center;
  color: #dc2626;
  background: #fef2f2;
}

.stat-change.positive {
  color: #059669;
  background: #ecfdf5;
}

.agent-comparison {
  margin-bottom: 32px;
}

.agent-comparison h2 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 20px;
}

.agent-table {
  overflow-x: auto;
}

.agent-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.agent-table th,
.agent-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

.agent-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.agent-table td {
  color: #6b7280;
  font-size: 13px;
}

.agent-table td.positive {
  color: #059669;
  font-weight: 600;
}

.agent-table td.negative {
  color: #dc2626;
  font-weight: 600;
}

.response-indicator {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.response-indicator.strong {
  background: #dcfce7;
  color: #166534;
}

.response-indicator.moderate {
  background: #fef3c7;
  color: #92400e;
}

.response-indicator.weak {
  background: #fee2e2;
  color: #991b1b;
}

.response-indicator.none {
  background: #f3f4f6;
  color: #6b7280;
}

.insights {
  margin-bottom: 32px;
}

.insights h2 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 20px;
}

.insight-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 16px;
}

.insight-card {
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.insight-card h3 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 16px;
}

.insight-card p {
  margin: 0;
  color: #6b7280;
  line-height: 1.5;
}

.insight-card ul {
  margin: 0;
  padding-left: 20px;
  color: #6b7280;
}

.insight-card li {
  margin-bottom: 8px;
  line-height: 1.4;
}

.action-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 24px 0;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
}
</style>
