<template>
  <div class="hurricane-config-dialog">
    <div class="dialog-overlay" @click="$emit('close')"></div>
    <div class="dialog-content">
      <div class="dialog-header">
        <h2>🌪️ 飓风消息配置</h2>
        <p class="dialog-subtitle">为对比仿真添加紧急广播事件</p>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="dialog-body">
        <!-- 仿真信息 -->
        <div class="simulation-info">
          <h3>原始仿真信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <label>仿真ID:</label>
              <span>{{ originalSimulation.id }}</span>
            </div>
            <div class="info-item">
              <label>总时间片:</label>
              <span>{{ timeSliceCount }} 个</span>
            </div>
            <div class="info-item">
              <label>仿真时长:</label>
              <span>{{ simulationDuration }}</span>
            </div>
          </div>
        </div>

        <!-- 快速输入模式 -->
        <div class="quick-input-section">
          <h3>🚀 快速添加飓风消息</h3>
          <p class="section-description">只需输入消息内容，系统将自动进行AI标注并保存到仿真数据</p>
          <div class="quick-input-form">
            <div class="input-row">
              <div class="input-group">
                <label>目标时间片:</label>
                <select v-model="quickMessage.targetTimeSlice">
                  <option
                    v-for="slice in timeSlices"
                    :key="slice.index"
                    :value="slice.index"
                  >
                    时间片 {{ slice.index }} ({{ slice.timeRange }})
                  </option>
                </select>
              </div>
            </div>
            <div class="input-row">
              <label>消息内容:</label>
              <textarea
                v-model="quickMessage.content"
                placeholder="输入飓风消息内容，例如：台风警报、地震预警、政府公告等..."
                rows="3"
                class="quick-message-input"
              ></textarea>
            </div>
            <div class="input-actions">
              <button 
                class="btn-primary btn-quick-add" 
                @click="addQuickMessage"
                :disabled="!quickMessage.content.trim() || quickLoading"
              >
                <span v-if="quickLoading">🔄 AI标注中...</span>
                <span v-else">🎯 快速添加</span>
              </button>
              <span class="quick-help">系统将自动进行情绪和立场标注</span>
            </div>
          </div>
        </div>

        <!-- 高级配置模式切换 -->
        <div class="mode-toggle">
          <button 
            class="btn-toggle" 
            @click="showAdvancedMode = !showAdvancedMode"
          >
            {{ showAdvancedMode ? '🔽 隐藏高级配置' : '🔧 显示高级配置' }}
          </button>
        </div>

        <!-- 高级配置（可展开/收起） -->
        <div v-if="showAdvancedMode" class="advanced-config">
          <h3>🔧 高级配置模式</h3>

        <!-- 时间片选择器 -->
        <div class="timeslice-selector">
          <h3>选择注入时间片</h3>
          <div class="timeslice-grid">
            <div
              v-for="slice in timeSlices"
              :key="slice.index"
              class="timeslice-item"
              :class="{ 
                selected: selectedTimeSlices.includes(slice.index),
                'has-hurricane': hurricaneMessages.some(h => h.target_time_slice === slice.index)
              }"
              @click="toggleTimeSlice(slice.index)"
            >
              <div class="slice-number">{{ slice.index }}</div>
              <div class="slice-info">
                <div class="slice-time">{{ slice.timeRange }}</div>
                <div class="slice-posts">{{ slice.postCount }} 帖子</div>
              </div>
              <div v-if="hurricaneMessages.some(h => h.target_time_slice === slice.index)" class="hurricane-indicator">🚨</div>
            </div>
          </div>
        </div>

        <!-- 飓风消息列表 -->
        <div class="hurricane-messages">
          <h3>飓风消息配置</h3>
          <div class="message-list">
            <div
              v-for="(message, index) in hurricaneMessages"
              :key="index"
              class="message-item"
            >
              <div class="message-header">
                <span class="message-title">消息 {{ index + 1 }}</span>
                <div class="message-actions">
                  <button class="btn-duplicate" @click="duplicateMessage(index)">复制</button>
                  <button class="btn-delete" @click="removeMessage(index)">删除</button>
                </div>
              </div>
              
              <div class="message-config">
                <div class="config-row">
                  <label>目标时间片:</label>
                  <select v-model="message.target_time_slice">
                    <option
                      v-for="slice in timeSlices"
                      :key="slice.index"
                      :value="slice.index"
                    >
                      时间片 {{ slice.index }} ({{ slice.timeRange }})
                    </option>
                  </select>
                </div>

                <div class="config-row">
                  <label>消息内容:</label>
                  <textarea
                    v-model="message.content"
                    placeholder="输入飓风消息内容..."
                    rows="3"
                  ></textarea>
                </div>

                <div class="config-row">
                  <div class="config-group">
                    <label>情绪影响:</label>
                    <input
                      type="range"
                      v-model="message.emotion_impact"
                      min="-1"
                      max="1"
                      step="0.1"
                    />
                    <span class="range-value">{{ message.emotion_impact }}</span>
                  </div>
                  <div class="config-group">
                    <label>立场影响:</label>
                    <input
                      type="range"
                      v-model="message.stance_impact"
                      min="-1"
                      max="1"
                      step="0.1"
                    />
                    <span class="range-value">{{ message.stance_impact }}</span>
                  </div>
                </div>

                <div class="config-row">
                  <div class="config-group">
                    <label>优先级:</label>
                    <input
                      type="number"
                      v-model="message.priority"
                      min="1"
                      max="999"
                    />
                  </div>
                  <div class="config-group">
                    <label>消息类型:</label>
                    <select v-model="message.message_type">
                      <option value="disaster">自然灾害</option>
                      <option value="government">政府公告</option>
                      <option value="emergency">紧急事件</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button class="btn-add-message" @click="addMessage">
            + 添加飓风消息
          </button>
        </div>

        </div> <!-- 结束高级配置 -->

        <!-- 预设模板 -->
        <div class="message-templates">
          <h3>快速模板</h3>
          <div class="template-grid">
            <div
              v-for="template in messageTemplates"
              :key="template.id"
              class="template-item"
              @click="applyTemplate(template)"
            >
              <div class="template-icon">{{ template.icon }}</div>
              <div class="template-info">
                <div class="template-name">{{ template.name }}</div>
                <div class="template-desc">{{ template.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <div class="config-summary">
          <span>已配置 {{ hurricaneMessages.length }} 条飓风消息</span>
          <span>涉及 {{ uniqueTimeSlices.length }} 个时间片</span>
        </div>
        <div class="footer-actions">
          <button class="btn-cancel" @click="$emit('close')">取消</button>
          <button class="btn-preview" @click="previewComparison">预览对比</button>
          <button 
            class="btn-confirm" 
            @click="startComparisonSimulation"
            :disabled="hurricaneMessages.length === 0"
          >
            开始对比仿真
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApiComplete.js'

// Props
const props = defineProps({
  originalSimulation: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits(['close', 'confirm'])

// Composables
const api = useApi()

// 响应式数据
const timeSlices = ref([])
const selectedTimeSlices = ref([])
const hurricaneMessages = ref([])
const loading = ref(false)
const showAdvancedMode = ref(false)
const quickLoading = ref(false)

// 快速输入消息
const quickMessage = ref({
  content: '',
  targetTimeSlice: 0
})

// 计算属性
const timeSliceCount = computed(() => timeSlices.value.length)
const simulationDuration = computed(() => {
  if (timeSlices.value.length === 0) return '未知'
  const first = timeSlices.value[0]
  const last = timeSlices.value[timeSlices.value.length - 1]
  return `${first.timeRange} - ${last.timeRange}`
})

const uniqueTimeSlices = computed(() => {
  return [...new Set(hurricaneMessages.value.map(m => m.target_time_slice))]
})

// 消息模板
const messageTemplates = ref([
  {
    id: 'typhoon',
    name: '台风警报',
    icon: '🌪️',
    description: '超强台风即将登陆',
    content: '🚨 紧急广播：超强台风即将于今晚登陆，请沿海地区所有居民立即撤离到安全地带！',
    emotion_impact: -0.8,
    stance_impact: 0.0,
    message_type: 'disaster'
  },
  {
    id: 'earthquake',
    name: '地震预警',
    icon: '🏗️',
    description: '地震预警系统启动',
    content: '⚠️ 地震预警：检测到强烈地震波，预计30秒后到达，请立即就近避险！',
    emotion_impact: -0.9,
    stance_impact: 0.0,
    message_type: 'disaster'
  },
  {
    id: 'government',
    name: '政府公告',
    icon: '📢',
    description: '官方重要通知',
    content: '📢 政府公告：根据最新疫情防控要求，即日起实施临时管控措施，请市民配合执行。',
    emotion_impact: -0.3,
    stance_impact: 0.3,
    message_type: 'government'
  },
  {
    id: 'evacuation',
    name: '紧急疏散',
    icon: '🚨',
    description: '紧急疏散通知',
    content: '🚨 紧急疏散：发现危险化学品泄漏，请xx区域居民立即疏散至安全地带！',
    emotion_impact: -0.7,
    stance_impact: 0.1,
    message_type: 'emergency'
  }
])

// 方法
const loadTimeSlices = async () => {
  try {
    loading.value = true
    const response = await api.getSimulationTimeSlices(props.originalSimulation.id)
    timeSlices.value = response.time_slices || []
  } catch (error) {
    console.error('加载时间片信息失败:', error)
    // 模拟数据作为回退
    timeSlices.value = Array.from({ length: 10 }, (_, i) => ({
      index: i,
      timeRange: `${String(i * 2).padStart(2, '0')}:00 - ${String(i * 2 + 2).padStart(2, '0')}:00`,
      postCount: Math.floor(Math.random() * 50) + 10
    }))
  } finally {
    loading.value = false
  }
}

const toggleTimeSlice = (sliceIndex) => {
  if (selectedTimeSlices.value.includes(sliceIndex)) {
    selectedTimeSlices.value = selectedTimeSlices.value.filter(s => s !== sliceIndex)
  } else {
    selectedTimeSlices.value.push(sliceIndex)
    // 自动为新选择的时间片添加默认消息
    if (!hurricaneMessages.value.some(m => m.target_time_slice === sliceIndex)) {
      addMessage(sliceIndex)
    }
  }
}

const addMessage = (targetSlice = null) => {
  const newMessage = {
    target_time_slice: targetSlice || (timeSlices.value[0]?.index ?? 0),
    content: '',
    emotion_impact: -0.5,
    stance_impact: 0.0,
    priority: 999,
    message_type: 'custom'
  }
  hurricaneMessages.value.push(newMessage)
}

// 快速添加消息（使用LLM自动标注）
const addQuickMessage = async () => {
  if (!quickMessage.value.content.trim()) {
    alert('请输入消息内容')
    return
  }

  try {
    quickLoading.value = true
    
    // 调用新的LLM标注API
    const response = await api.injectHurricaneMessageWithLLM(
      props.originalSimulation.id,
      quickMessage.value.content,
      quickMessage.value.targetTimeSlice
    )
    
    if (response.status === 'success') {
      // 显示成功消息
      alert(`✅ 飓风消息已成功添加到仿真数据！\n\n文件: ${response.json_file}\nAI标注结果: 情绪=${response.llm_annotation.emotion_score}, 立场=${response.llm_annotation.stance_score}`)
      
      // 清空输入框
      quickMessage.value.content = ''
      
      // 可选：关闭对话框或刷新数据
      // emit('close')
    } else {
      throw new Error(response.message || '添加失败')
    }
  } catch (error) {
    console.error('快速添加失败:', error)
    alert(`❌ 添加失败: ${error.message}`)
  } finally {
    quickLoading.value = false
  }
}

const removeMessage = (index) => {
  hurricaneMessages.value.splice(index, 1)
}

const duplicateMessage = (index) => {
  const original = hurricaneMessages.value[index]
  const duplicate = { ...original }
  hurricaneMessages.value.splice(index + 1, 0, duplicate)
}

const applyTemplate = (template) => {
  const targetSlice = selectedTimeSlices.value[0] || 0
  const newMessage = {
    target_time_slice: targetSlice,
    content: template.content,
    emotion_impact: template.emotion_impact,
    stance_impact: template.stance_impact,
    priority: 999,
    message_type: template.message_type
  }
  hurricaneMessages.value.push(newMessage)
}

const previewComparison = () => {
  // 显示预览对话框或者跳转到预览页面
  console.log('预览对比仿真配置:', {
    originalSimulation: props.originalSimulation,
    hurricaneMessages: hurricaneMessages.value
  })
}

const startComparisonSimulation = async () => {
  try {
    loading.value = true
    
    const hurricaneConfig = {
      name: `飓风对比_${new Date().toLocaleString()}`,
      hurricanes: hurricaneMessages.value,
      description: `基于仿真${props.originalSimulation.id}的飓风消息对比实验`
    }

    const response = await api.createComparisonSimulation(
      props.originalSimulation.id,
      hurricaneConfig
    )

    emit('confirm', {
      comparisonSimulationId: response.simulation_id,
      originalSimulationId: props.originalSimulation.id,
      hurricaneConfig: hurricaneConfig
    })

    // 显示成功消息
    api.showMessage('对比仿真已启动！', 'success')
    
  } catch (error) {
    console.error('启动对比仿真失败:', error)
    api.showMessage('启动对比仿真失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadTimeSlices()
})
</script>

<style scoped>
.hurricane-config-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
}

.dialog-content {
  position: relative;
  width: 90vw;
  max-width: 1200px;
  height: 90vh;
  background: white;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
}

.dialog-header h2 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 24px;
}

.dialog-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.simulation-info {
  margin-bottom: 32px;
}

.simulation-info h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 18px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-weight: 600;
  color: #6b7280;
  font-size: 12px;
  text-transform: uppercase;
}

.info-item span {
  color: #1f2937;
  font-size: 14px;
}

.timeslice-selector {
  margin-bottom: 32px;
}

.timeslice-selector h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 18px;
}

.timeslice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.timeslice-item {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.timeslice-item:hover {
  border-color: #3b82f6;
}

.timeslice-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.timeslice-item.has-hurricane {
  border-color: #f59e0b;
  background: #fef3c7;
}

.slice-number {
  font-weight: 700;
  font-size: 18px;
  color: #1f2937;
  text-align: center;
  margin-bottom: 8px;
}

.slice-info {
  text-align: center;
}

.slice-time {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 2px;
}

.slice-posts {
  font-size: 11px;
  color: #9ca3af;
}

.hurricane-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 12px;
}

.hurricane-messages {
  margin-bottom: 32px;
}

.hurricane-messages h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 18px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.message-title {
  font-weight: 600;
  color: #374151;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.btn-duplicate,
.btn-delete {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  font-size: 12px;
  cursor: pointer;
}

.btn-delete {
  color: #dc2626;
  border-color: #fca5a5;
}

.btn-delete:hover {
  background: #fef2f2;
}

.message-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.config-row:has(textarea) {
  grid-template-columns: 1fr;
}

.config-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.config-row input,
.config-row select,
.config-row textarea {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.config-row input[type="range"] {
  padding: 0;
}

.range-value {
  font-weight: 600;
  color: #374151;
  text-align: center;
  font-size: 12px;
}

.btn-add-message {
  width: 100%;
  padding: 12px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-message:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.message-templates h3 {
  margin: 0 0 16px 0;
  color: #374151;
  font-size: 18px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.template-icon {
  font-size: 24px;
  width: 40px;
  text-align: center;
}

.template-info {
  flex: 1;
}

.template-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.template-desc {
  font-size: 12px;
  color: #6b7280;
}

.dialog-footer {
  padding: 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  color: #6b7280;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel,
.btn-preview,
.btn-confirm {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: white;
  color: #6b7280;
}

.btn-cancel:hover {
  background: #f9fafb;
}

.btn-preview {
  background: white;
  color: #3b82f6;
  border-color: #3b82f6;
}

.btn-preview:hover {
  background: #eff6ff;
}

.btn-confirm {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-confirm:hover {
  background: #2563eb;
}

.btn-confirm:disabled {
  background: #d1d5db;
  border-color: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
}

/* 快速输入区域样式 */
.quick-input-section {
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
  border: 2px solid #4CAF50;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.quick-input-section h3 {
  color: #2E7D32;
  margin: 0 0 8px 0;
  font-size: 1.2em;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-description {
  color: #555;
  margin: 0 0 16px 0;
  font-size: 0.9em;
  line-height: 1.4;
}

.quick-input-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-group label {
  min-width: 80px;
  font-weight: 500;
  color: #333;
}

.input-group select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
}

.quick-message-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
  resize: vertical;
  min-height: 80px;
}

.quick-message-input:focus {
  outline: none;
  border-color: #2E7D32;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-quick-add {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-quick-add:hover:not(:disabled) {
  background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}

.btn-quick-add:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.quick-help {
  color: #666;
  font-size: 0.85em;
  font-style: italic;
}

/* 模式切换 */
.mode-toggle {
  text-align: center;
  margin: 20px 0;
}

.btn-toggle {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-toggle:hover {
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
}

.advanced-config {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.advanced-config h3 {
  margin: 0 0 16px 0;
  color: #1976D2;
  font-size: 1.1em;
}
</style>
