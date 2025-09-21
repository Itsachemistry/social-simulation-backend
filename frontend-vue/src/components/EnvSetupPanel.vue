<template>
  <div class="env-setup-panel">
    <h3>环境配置</h3>
    
    <div class="panel-content">
      <!-- 环境参数配置 -->
      <div class="env-config-section">
        <div class="control-group">
          <label>随机种子</label>
          <input 
            v-model.number="seedValue" 
            type="number" 
            placeholder="随机种子"
          />
        </div>
        
        <div class="control-group">
          <label>人口数量</label>
          <input 
            v-model.number="populationSize" 
            type="number" 
            placeholder="智能体数量"
          />
        </div>
        
        <div class="control-group">
          <label>环境参数</label>
          <textarea 
            v-model="environmentParams" 
            placeholder="JSON格式环境参数"
            rows="4"
          ></textarea>
        </div>
        
        <div class="control-group">
          <label>模拟时长</label>
          <input 
            v-model.number="simulationDuration" 
            type="number" 
            placeholder="模拟步数"
          />
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions-section">
        <button @click="saveEnvironment" class="save-btn" :disabled="loading">
          {{ loading ? '保存中...' : '保存配置' }}
        </button>
        <button @click="loadEnvironment" class="load-btn">
          加载配置
        </button>
        <button @click="resetEnvironment" class="reset-btn">
          重置配置
        </button>
      </div>
      
      <!-- 状态显示 -->
      <div v-if="error" class="error-message">
        错误: {{ error }}
      </div>
      
      <div v-if="environmentStatus" class="status-section">
        <h4>当前环境状态</h4>
        <pre>{{ JSON.stringify(environmentStatus, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApiComplete.js'

// 状态管理
const seedValue = ref(42)
const populationSize = ref(100)
const environmentParams = ref('{}')
const simulationDuration = ref(1000)
const environmentStatus = ref(null)

const { loading, error, getEnvironment, updateEnvironment } = useApi()

// 保存环境配置
const saveEnvironment = async () => {
  try {
    const params = JSON.parse(environmentParams.value)
    const config = {
      seed: seedValue.value,
      population_size: populationSize.value,
      duration: simulationDuration.value,
      ...params
    }
    
    await updateEnvironment(config)
    await loadEnvironment()
  } catch (err) {
    console.error('保存环境配置失败:', err)
  }
}

// 加载环境配置
const loadEnvironment = async () => {
  try {
    const data = await getEnvironment()
    environmentStatus.value = data
    
    if (data.seed !== undefined) seedValue.value = data.seed
    if (data.population_size !== undefined) populationSize.value = data.population_size
    if (data.duration !== undefined) simulationDuration.value = data.duration
  } catch (err) {
    console.error('加载环境配置失败:', err)
  }
}

// 重置环境配置
const resetEnvironment = () => {
  seedValue.value = 42
  populationSize.value = 100
  environmentParams.value = '{}'
  simulationDuration.value = 1000
  environmentStatus.value = null
}

// 初始化
onMounted(() => {
  loadEnvironment()
})
</script>

<style scoped>
.env-setup-panel {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.panel-content {
  max-width: 600px;
}

.env-config-section {
  margin-bottom: 20px;
}

.control-group {
  margin-bottom: 15px;
}

.control-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

.control-group input,
.control-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.control-group input:focus,
.control-group textarea:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.actions-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.actions-section button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

.save-btn {
  background: #4CAF50;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #45a049;
}

.save-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.load-btn {
  background: #2196F3;
  color: white;
}

.load-btn:hover {
  background: #1976D2;
}

.reset-btn {
  background: #f44336;
  color: white;
}

.reset-btn:hover {
  background: #d32f2f;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.status-section {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
}

.status-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.status-section pre {
  background: white;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  color: #666;
}
</style>
