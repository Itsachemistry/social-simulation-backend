<template>
  <div class="histogram-panel">
    <h3>数据分布直方图</h3>
    
    <div class="panel-content">
      <!-- 直方图控制 -->
      <div class="controls-section">
        <div class="control-group">
          <label>数据类型：</label>
          <select v-model="dataType" @change="generateHistogram">
            <option value="post_time">发帖时间分布</option>
            <option value="user_activity">用户活跃度</option>
            <option value="sentiment">情感分布</option>
            <option value="influence">影响力分析</option>
          </select>
        </div>
        
        <div class="control-group">
          <label>时间粒度：</label>
          <select v-model="timeGranularity" @change="generateHistogram" v-if="dataType === 'post_time'">
            <option value="hour">小时</option>
            <option value="day">天</option>
            <option value="week">周</option>
            <option value="month">月</option>
          </select>
          
          <input 
            v-else
            v-model.number="binCount" 
            type="number" 
            min="5" 
            max="50" 
            placeholder="区间数量"
            @change="generateHistogram"
          />
        </div>
        
        <div class="control-group">
          <button @click="generateHistogram" :disabled="isLoading">
            {{ isLoading ? '生成中...' : '重新生成' }}
          </button>
          <button @click="exportData" :disabled="!histogramData.length">
            导出数据
          </button>
        </div>
      </div>

      <!-- 直方图显示区域 -->
      <div class="histogram-section">
        <div id="histogram-container" v-if="histogramData.length">
          <canvas ref="histogramCanvas"></canvas>
        </div>
        <div v-else class="no-data">
          暂无数据
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section" v-if="histogramStats">
        <div class="stats-header">
          <label>统计信息：</label>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="label">总数：</span>
            <span class="value">{{ histogramStats.total }}</span>
          </div>
          <div class="stat-item">
            <span class="label">平均值：</span>
            <span class="value">{{ histogramStats.average }}</span>
          </div>
          <div class="stat-item">
            <span class="label">最大值：</span>
            <span class="value">{{ histogramStats.max }}</span>
          </div>
          <div class="stat-item">
            <span class="label">最小值：</span>
            <span class="value">{{ histogramStats.min }}</span>
          </div>
          <div class="stat-item">
            <span class="label">标准差：</span>
            <span class="value">{{ histogramStats.stdDev }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useApiComplete } from '../composables/useApiComplete'
import Chart from 'chart.js/auto'

const { getHistogram, isLoading, showMessage } = useApiComplete()

// 响应式数据
const dataType = ref('post_time')
const timeGranularity = ref('hour')
const binCount = ref(20)
const histogramData = ref([])
const histogramStats = ref(null)
const histogramCanvas = ref(null)
let chartInstance = null

// 处理后端返回的posts数据，生成直方图数据
const processHistogramData = (posts) => {
  if (!posts || posts.length === 0) {
    return { data: [], stats: null }
  }

  let data = []
  let values = []

  if (dataType.value === 'post_time') {
    // 时间分布直方图
    const timeGroups = {}
    const granularity = timeGranularity.value

    posts.forEach(post => {
      const timestamp = post.t || post.timestamp
      if (!timestamp) return

      const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp)
      let key = ''

      if (granularity === 'hour') {
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:00`
      } else if (granularity === 'day') {
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      } else if (granularity === 'month') {
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      }

      timeGroups[key] = (timeGroups[key] || 0) + 1
    })

    data = Object.entries(timeGroups)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([label, value]) => ({ label, value }))
    
    values = data.map(item => item.value)
  } else {
    // 其他类型的分布
    data = Array.from({ length: binCount.value }, (_, i) => ({
      label: `区间 ${i + 1}`,
      value: Math.floor(Math.random() * 50) // 临时数据
    }))
    values = data.map(item => item.value)
  }

  // 计算统计信息
  const total = values.reduce((sum, val) => sum + val, 0)
  const average = total / values.length || 0
  const max = Math.max(...values) || 0
  const min = Math.min(...values) || 0
  const variance = values.reduce((sum, val) => sum + Math.pow(val - average, 2), 0) / values.length
  const stdDev = Math.sqrt(variance)

  const stats = {
    total,
    average: parseFloat(average.toFixed(2)),
    max,
    min,
    stdDev: parseFloat(stdDev.toFixed(2))
  }

  return { data, stats }
}

// 生成直方图
const generateHistogram = async () => {
  try {
    const params = {
      type: dataType.value,
      bins: dataType.value === 'post_time' ? timeGranularity.value : binCount.value
    }
    
    const response = await getHistogram(params)
    if (response && response.posts && response.posts.length > 0) {
      // 处理从后端返回的posts数据，生成直方图数据
      const processedData = processHistogramData(response.posts)
      histogramData.value = processedData.data
      histogramStats.value = processedData.stats
      
      // 等待DOM更新后绘制图表
      await nextTick()
      drawHistogram()
      
      showMessage('直方图生成成功', 'success')
    } else {
      histogramData.value = []
      histogramStats.value = null
      showMessage('暂无数据生成直方图', 'error')
    }
  } catch (error) {
    console.error('生成直方图失败:', error)
    histogramData.value = []
    histogramStats.value = null
    showMessage('生成直方图失败', 'error')
  }
}

// 绘制直方图
const drawHistogram = () => {
  if (!histogramCanvas.value || !histogramData.value.length) return

  // 销毁之前的图表实例
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = histogramCanvas.value.getContext('2d')
  
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: histogramData.value.map(item => item.label),
      datasets: [{
        label: getDataTypeLabel(),
        data: histogramData.value.map(item => item.value),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '频次'
          }
        },
        x: {
          title: {
            display: true,
            text: getXAxisLabel()
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: `${getDataTypeLabel()} - 分布直方图`
        },
        legend: {
          display: false
        }
      }
    }
  })
}

// 获取数据类型标签
const getDataTypeLabel = () => {
  const labels = {
    'post_time': '发帖时间',
    'user_activity': '用户活跃度',
    'sentiment': '情感分布',
    'influence': '影响力分析'
  }
  return labels[dataType.value] || '数据分布'
}

// 获取X轴标签
const getXAxisLabel = () => {
  if (dataType.value === 'post_time') {
    const labels = {
      'hour': '小时',
      'day': '天',
      'week': '周',
      'month': '月'
    }
    return labels[timeGranularity.value] || '时间'
  }
  return '数值区间'
}

// 导出数据
const exportData = () => {
  if (!histogramData.value.length) return

  const dataToExport = {
    type: dataType.value,
    granularity: dataType.value === 'post_time' ? timeGranularity.value : binCount.value,
    data: histogramData.value,
    stats: histogramStats.value,
    generatedAt: new Date().toISOString()
  }

  const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
    type: 'application/json'
  })
  
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `histogram_${dataType.value}_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  showMessage('数据导出成功', 'success')
}

// 组件挂载时生成默认直方图
onMounted(() => {
  generateHistogram()
})

// 组件卸载时清理图表实例
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.histogram-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.histogram-panel h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.controls-section {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  color: #555;
  white-space: nowrap;
}

.control-group select,
.control-group input {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.control-group button {
  padding: 8px 16px;
  border: 1px solid #007bff;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.control-group button:hover:not(:disabled) {
  background: #0056b3;
  border-color: #0056b3;
}

.control-group button:disabled {
  background: #6c757d;
  border-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.histogram-section {
  flex: 1;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background: #fff;
}

#histogram-container {
  width: 100%;
  height: 400px;
  padding: 20px;
}

#histogram-container canvas {
  width: 100% !important;
  height: 100% !important;
}

.no-data {
  color: #6c757d;
  font-size: 16px;
  text-align: center;
}

.stats-section {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.stats-header {
  margin-bottom: 10px;
}

.stats-header label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.stat-item .label {
  font-size: 13px;
  color: #666;
}

.stat-item .value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

@media (max-width: 768px) {
  .controls-section {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .control-group {
    flex-direction: column;
    align-items: stretch;
    gap: 5px;
  }
  
  .control-group select,
  .control-group input,
  .control-group button {
    min-width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
