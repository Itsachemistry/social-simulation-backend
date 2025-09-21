<template>
  <div class="modal-overlay" v-if="show" @click="handleOverlayClick">
    <div class="config-dialog" @click.stop>
      <div class="dialog-header">
        <h2>🏛️ 官方声明配置</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="dialog-content">
        <!-- 基本信息 -->
        <div class="section">
          <h3>基本信息</h3>
          <div class="form-group">
            <label>目标仿真:</label>
            <div class="simulation-info">
              <span class="simulation-name">{{ simulationInfo.name || `仿真 ${simulationInfo.id?.substring(0, 8)}` }}</span>
              <span class="simulation-status">{{ simulationInfo.status }}</span>
            </div>
          </div>
        </div>

        <!-- 声明内容配置 -->
        <div class="section">
          <h3>声明内容</h3>
          
          <div class="form-group">
            <label>声明内容 <span class="required">*</span></label>
            <div class="textarea-container">
              <textarea 
                v-model="config.content"
                placeholder="请输入官方声明内容，例如：
【官方澄清】经核实，网传相关信息不属实，特此澄清...
【通知公告】根据最新情况，现发布以下重要信息...
【辟谣声明】针对网络传言，经调查核实情况如下..."
                rows="6"
                class="statement-textarea"
                :class="{ error: errors.content }"
              ></textarea>
              <div class="char-count" :class="{ warning: config.content.length > 500 }">
                {{ config.content.length }}/500 字符
              </div>
            </div>
            <div v-if="errors.content" class="error-text">{{ errors.content }}</div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>声明类型 <span class="required">*</span></label>
              <select v-model="config.statement_type" :class="{ error: errors.statement_type }">
                <option 
                  v-for="type in statementTypes" 
                  :key="type.id" 
                  :value="type.id"
                >
                  {{ type.name }} - {{ type.description }}
                </option>
              </select>
              <div v-if="errors.statement_type" class="error-text">{{ errors.statement_type }}</div>
            </div>

            <div class="form-group">
              <label>权威级别 <span class="required">*</span></label>
              <select v-model="config.authority_level" :class="{ error: errors.authority_level }">
                <option 
                  v-for="level in authorityLevels" 
                  :key="level.id" 
                  :value="level.id"
                >
                  {{ level.name }} - {{ level.description }}
                </option>
              </select>
              <div v-if="errors.authority_level" class="error-text">{{ errors.authority_level }}</div>
            </div>
          </div>
        </div>

        <!-- 时机配置 -->
        <div class="section">
          <h3>发布时机</h3>
          
          <div class="form-group">
            <label>目标时间片 <span class="required">*</span></label>
            <div class="time-slice-selector">
              <select v-model="config.target_time_slice" :class="{ error: errors.target_time_slice }">
                <option
                  v-for="slice in timeSlices"
                  :key="slice.index"
                  :value="slice.index"
                >
                  时间片 {{ slice.index + 1 }} ({{ slice.timeRange }})
                </option>
              </select>
              <div class="time-slice-info">
                <span v-if="selectedTimeSlice">
                  预计发布时间: {{ selectedTimeSlice.timeRange }}
                </span>
              </div>
            </div>
            <div v-if="errors.target_time_slice" class="error-text">{{ errors.target_time_slice }}</div>
          </div>
        </div>

        <!-- 预期效果 -->
        <div class="section">
          <h3>预期效果预览</h3>
          <div class="effect-preview">
            <div class="effect-grid">
              <div class="effect-item">
                <div class="effect-label">声明类型:</div>
                <div class="effect-value">{{ selectedStatementType?.name || '未选择' }}</div>
              </div>
              <div class="effect-item">
                <div class="effect-label">权威级别:</div>
                <div class="effect-value">{{ selectedAuthorityLevel?.name || '未选择' }}</div>
              </div>
              <div class="effect-item">
                <div class="effect-label">情绪影响:</div>
                <div class="effect-value">{{ selectedStatementType?.emotion_effect || 'N/A' }}</div>
              </div>
              <div class="effect-item">
                <div class="effect-label">立场影响:</div>
                <div class="effect-value">{{ selectedStatementType?.stance_effect || 'N/A' }}</div>
              </div>
              <div class="effect-item">
                <div class="effect-label">影响强度:</div>
                <div class="effect-value">{{ selectedAuthorityLevel ? `${selectedAuthorityLevel.influence_multiplier * 100}%` : 'N/A' }}</div>
              </div>
              <div class="effect-item">
                <div class="effect-label">影响范围:</div>
                <div class="effect-value">{{ selectedAuthorityLevel?.coverage || 'N/A' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 高级选项 -->
        <div class="section">
          <div class="section-header" @click="toggleAdvanced">
            <h3>高级选项</h3>
            <span class="toggle-icon" :class="{ expanded: showAdvanced }">▼</span>
          </div>
          
          <div v-if="showAdvanced" class="advanced-options">
            <div class="form-group">
              <label>自定义标签:</label>
              <input 
                v-model="config.custom_tags"
                type="text" 
                placeholder="可选：为此次官方声明添加自定义标签，用逗号分隔"
                class="custom-input"
              />
            </div>

            <div class="form-group">
              <label>备注说明:</label>
              <textarea 
                v-model="config.notes"
                placeholder="可选：添加内部备注或说明"
                rows="3"
                class="notes-textarea"
              ></textarea>
            </div>

            <div class="checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="config.enable_tracking">
                <span class="checkmark"></span>
                启用详细效果跟踪
              </label>
              <p class="checkbox-desc">开启后将记录声明发布前后的详细Agent状态变化</p>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <div class="validation-summary">
          <div v-if="hasErrors" class="validation-errors">
            <span class="error-icon">⚠️</span>
            请检查并修正标红的必填项
          </div>
          <div v-else-if="isValid" class="validation-success">
            <span class="success-icon">✅</span>
            配置完成，可以启动仿真
          </div>
        </div>
        
        <div class="footer-actions">
          <button @click="$emit('close')" class="btn-cancel">
            取消
          </button>
          <button @click="saveConfig" :disabled="!isValid || saving" class="btn-save">
            <span v-if="saving">保存中...</span>
            <span v-else>保存并启动</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, defineProps, defineEmits } from 'vue'

// Props 和 Emits
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  simulationInfo: {
    type: Object,
    default: () => ({})
  },
  timeSlices: {
    type: Array,
    default: () => []
  },
  statementTypes: {
    type: Array,
    default: () => []
  },
  authorityLevels: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

// 响应式数据
const showAdvanced = ref(false)
const saving = ref(false)

// 配置数据
const config = reactive({
  content: '',
  statement_type: 'clarification',
  authority_level: 'high',
  target_time_slice: 0,
  custom_tags: '',
  notes: '',
  enable_tracking: true
})

// 错误状态
const errors = reactive({
  content: '',
  statement_type: '',
  authority_level: '',
  target_time_slice: ''
})

// 计算属性
const selectedStatementType = computed(() => {
  return props.statementTypes.find(t => t.id === config.statement_type)
})

const selectedAuthorityLevel = computed(() => {
  return props.authorityLevels.find(l => l.id === config.authority_level)
})

const selectedTimeSlice = computed(() => {
  return props.timeSlices.find(s => s.index === config.target_time_slice)
})

const hasErrors = computed(() => {
  return Object.values(errors).some(error => error !== '')
})

const isValid = computed(() => {
  return config.content.trim().length >= 10 && 
         config.statement_type && 
         config.authority_level && 
         config.target_time_slice !== undefined &&
         !hasErrors.value
})

// 监听器
watch(() => config.content, (newContent) => {
  if (newContent.trim().length < 10) {
    errors.content = '声明内容至少需要10个字符'
  } else if (newContent.length > 500) {
    errors.content = '声明内容不能超过500个字符'
  } else {
    errors.content = ''
  }
})

watch(() => config.statement_type, (newType) => {
  if (!newType) {
    errors.statement_type = '请选择声明类型'
  } else {
    errors.statement_type = ''
  }
})

watch(() => config.authority_level, (newLevel) => {
  if (!newLevel) {
    errors.authority_level = '请选择权威级别'
  } else {
    errors.authority_level = ''
  }
})

watch(() => config.target_time_slice, (newSlice) => {
  if (newSlice === undefined || newSlice === null) {
    errors.target_time_slice = '请选择目标时间片'
  } else {
    errors.target_time_slice = ''
  }
})

// 方法
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value
}

const handleOverlayClick = () => {
  emit('close')
}

const saveConfig = async () => {
  if (!isValid.value) return
  
  saving.value = true
  try {
    // 准备配置数据
    const configData = {
      ...config,
      custom_tags: config.custom_tags ? config.custom_tags.split(',').map(tag => tag.trim()) : []
    }
    
    emit('save', configData)
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    saving.value = false
  }
}

// 重置配置
const resetConfig = () => {
  config.content = ''
  config.statement_type = 'clarification'
  config.authority_level = 'high'
  config.target_time_slice = 0
  config.custom_tags = ''
  config.notes = ''
  config.enable_tracking = true
  
  Object.keys(errors).forEach(key => {
    errors[key] = ''
  })
}

// 监听 show 属性变化，重置配置
watch(() => props.show, (newShow) => {
  if (newShow) {
    resetConfig()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.config-dialog {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.dialog-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h2 {
  margin: 0;
  font-size: 1.5em;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 2em;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
}

.section {
  margin-bottom: 30px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 25px;
}

.section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section h3 {
  color: #333;
  margin: 0 0 20px 0;
  font-size: 1.2em;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: color 0.2s;
}

.section-header:hover {
  color: #667eea;
}

.toggle-icon {
  transition: transform 0.3s;
  color: #667eea;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.simulation-info {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f8f9ff;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.simulation-name {
  font-weight: 600;
  color: #333;
}

.simulation-status {
  background: #e8f5e8;
  color: #2e7d32;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 500;
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

.required {
  color: #e74c3c;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.textarea-container {
  position: relative;
}

.statement-textarea {
  width: 100%;
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.2s;
}

.statement-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.statement-textarea.error {
  border-color: #e74c3c;
}

.char-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  background: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  color: #666;
}

.char-count.warning {
  color: #e74c3c;
  font-weight: 600;
}

select, .custom-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s;
}

select:focus, .custom-input:focus {
  outline: none;
  border-color: #667eea;
}

select.error, .custom-input.error {
  border-color: #e74c3c;
}

.time-slice-selector .time-slice-info {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f8ff;
  border-radius: 6px;
  font-size: 0.9em;
  color: #667eea;
}

.notes-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
  resize: vertical;
  font-family: inherit;
}

.notes-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.error-text {
  color: #e74c3c;
  font-size: 0.85em;
  margin-top: 5px;
  font-weight: 500;
}

/* 效果预览 */
.effect-preview {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f8ff 100%);
  border: 2px solid #667eea;
  border-radius: 12px;
  padding: 20px;
}

.effect-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.effect-item {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border-left: 4px solid #667eea;
}

.effect-label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 4px;
}

.effect-value {
  font-weight: 600;
  color: #667eea;
}

/* 高级选项 */
.advanced-options {
  margin-top: 20px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
}

.checkbox-group {
  margin-top: 15px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
  color: #333;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 10px;
  width: 18px;
  height: 18px;
}

.checkbox-desc {
  margin: 5px 0 0 28px;
  font-size: 0.85em;
  color: #666;
  line-height: 1.4;
}

/* 对话框底部 */
.dialog-footer {
  background: #fafafa;
  padding: 20px 30px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.validation-summary {
  flex: 1;
}

.validation-errors {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e74c3c;
  font-weight: 500;
}

.validation-success {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #27ae60;
  font-weight: 500;
}

.footer-actions {
  display: flex;
  gap: 15px;
}

.btn-cancel, .btn-save {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-cancel {
  background: white;
  color: #666;
  border: 2px solid #ddd;
}

.btn-cancel:hover {
  background: #f5f5f5;
  border-color: #bbb;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  min-width: 120px;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .config-dialog {
    width: 95%;
    max-height: 95vh;
  }

  .dialog-content {
    padding: 20px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .effect-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }

  .footer-actions {
    justify-content: stretch;
  }

  .btn-cancel, .btn-save {
    flex: 1;
  }
}
</style>
