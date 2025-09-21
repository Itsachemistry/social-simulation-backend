<template>
  <div class="attitude-panel-vega">
    <h4>群体情绪和立场分析 (Vega-Lite)</h4>
    
    <div class="attitude-description" style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666;">
      <p><strong>高质量矢量可视化图表说明：</strong></p>
      <ul style="margin: 5px 0; padding-left: 20px;">
        <li>🔴 红色区域：情绪分析趋势（-1 表示负面，+1 表示正面）</li>
        <li>🔵 蓝色区域：立场分析趋势（-1 表示反对，+1 表示支持）</li>
        <li>📊 SVG矢量图形：无限缩放不失真</li>
      </ul>
      <p><strong>🖱️ 交互操作指南：</strong></p>
      <ul style="margin: 5px 0; padding-left: 20px;">
        <li><strong>平移+缩放模式：</strong>鼠标滚轮缩放，拖拽平移，双击重置</li>
        <li><strong>区域选择模式：</strong>拖拽选择时间区域，选中区域高亮显示</li>
        <li><strong>时间区间模式：</strong>拖拽创建时间刷选区域</li>
        <li><strong>重置视图：</strong>点击"重置视图"按钮恢复原始缩放</li>
      </ul>
    </div>
    
    <div class="vega-controls">
      <div class="control-group">
        <label>时间单位:</label>
        <select v-model="timeUnit" @change="updateVisualization">
          <option value="hour">按小时</option>
          <option value="day">按天</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>图表主题:</label>
        <select v-model="theme" @change="updateVisualization">
          <option value="excel">Excel风格</option>
          <option value="ggplot2">ggplot2风格</option>
          <option value="quartz">Quartz风格</option>
          <option value="vox">Vox风格</option>
          <option value="dark">深色主题</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>图表尺寸:</label>
        <select v-model="chartSize" @change="updateVisualization">
          <option value="small">小 (400x300)</option>
          <option value="medium">中 (500x350)</option>
          <option value="large">大 (600x400)</option>
          <option value="xlarge">超大 (700x450)</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>显示样式:</label>
        <select v-model="visualStyle" @change="updateVisualization">
          <option value="line">线条图</option>
          <option value="area">面积图</option>
          <option value="both">线条+面积</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>交互模式:</label>
        <select v-model="interactionMode" @change="updateVisualization">
          <option value="pan-zoom">平移+缩放</option>
          <option value="brush">区域选择</option>
          <option value="interval">时间区间</option>
        </select>
      </div>
      
      <button @click="exportChart" class="export-btn">导出SVG</button>
      <button @click="resetView" class="reset-btn">重置视图</button>
    </div>
    
    <!-- Vega-Lite 图表容器 -->
    <div class="vega-chart-container">
      <div 
        ref="vegaContainer" 
        class="vega-chart"
        style="width: 100%; min-height: 300px; border: 1px solid #e0e0e0; border-radius: 8px; background: white;"
      ></div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-indicator">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <!-- 错误信息 -->
    <div v-if="error" class="error-message">
      <p>❌ {{ error }}</p>
      <button @click="retryLoad">重试</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useApi, useTimeRange } from '../composables/useApiComplete'
import vegaEmbed from 'vega-embed'

// 响应式状态
const vegaContainer = ref(null)
const attitudeData = ref(null)
const timeUnit = ref('hour')
const theme = ref('excel')
const chartSize = ref('medium')
const visualStyle = ref('both')
const interactionMode = ref('pan-zoom')
const loading = ref(false)
const error = ref(null)
let vegaView = null

// API 和时间范围
const { getAttitude } = useApi()
const { timeRange: globalTimeRange } = useTimeRange()

// 图表尺寸配置
const chartSizes = {
  small: { width: 400, height: 300 },
  medium: { width: 500, height: 350 },
  large: { width: 600, height: 400 },
  xlarge: { width: 700, height: 450 }
}

// 获取态度分析数据
const fetchAttitudeData = async () => {
  loading.value = true
  error.value = null
  
  try {
    const start = globalTimeRange.value?.start || '2016-01-01T00:00:00'
    const end = globalTimeRange.value?.end || '2016-12-31T23:59:59'
    
    const data = await getAttitude(start, end, timeUnit.value, 24)
    attitudeData.value = data
    
    console.log('Vega态度分析数据:', data)
    await renderVegaChart()
  } catch (err) {
    console.error('获取态度分析数据失败', err)
    error.value = err.message || '加载数据失败'
  } finally {
    loading.value = false
  }
}

// 获取交互参数
const getInteractionParams = () => {
  if (interactionMode.value === 'pan-zoom') {
    // 简化为基础交互，不使用复杂的域绑定
    return []
  } else if (interactionMode.value === 'brush') {
    return [
      {
        name: "brush_selection",
        select: {
          type: "interval",
          encodings: ["x"],
          mark: {fill: "rgba(0, 123, 255, 0.2)", stroke: "#007bff"}
        }
      }
    ]
  } else if (interactionMode.value === 'interval') {
    return [
      {
        name: "interval_selection",
        select: {
          type: "interval",
          encodings: ["x"],
          mark: {fill: "rgba(255, 193, 7, 0.3)", stroke: "#ffc107"}
        }
      }
    ]
  }
  return []
}

// 获取编码配置
const getEncodingConfig = () => {
  const baseEncoding = {
    x: {
      field: "time",
      type: "temporal",
      title: "时间",
      axis: {
        format: timeUnit.value === 'hour' ? "%H:%M" : "%m/%d",
        tickCount: 10,
        labelAngle: -45
      }
    },
    y: {
      field: "value",
      type: "quantitative",
      title: "情绪/立场值",
      scale: { domain: [-1, 1] },
      axis: { grid: true }
    },
    color: {
      field: "type",
      type: "nominal",
      scale: {
        domain: ["emotion", "stance"],
        range: ["#e63946", "#457b9d"]
      },
      legend: {
        title: "指标类型",
        values: ["emotion", "stance"],
        labelExpr: "datum.value === 'emotion' ? '情绪分析' : '立场分析'"
      }
    },
    tooltip: [
      { field: "time", type: "temporal", title: "时间", format: "%Y-%m-%d %H:%M" },
      { field: "category", type: "nominal", title: "类型" },
      { field: "value", type: "quantitative", title: "数值", format: ".3f" }
    ]
  }

  // 根据交互模式添加额外的编码
  if (interactionMode.value === 'brush') {
    baseEncoding.opacity = {
      condition: { param: 'brush_selection', value: 1.0 },
      value: 0.3
    }
  } else if (interactionMode.value === 'interval') {
    baseEncoding.opacity = {
      condition: { param: 'interval_selection', value: 1.0 },
      value: 0.3
    }
  }

  return baseEncoding
}

// 构建 Vega-Lite 规范
const buildVegaSpec = () => {
  if (!attitudeData.value) return null
  
  const dataSource = timeUnit.value === 'hour' ? attitudeData.value.hourly_data : attitudeData.value.daily_data
  
  if (!dataSource || dataSource.length === 0) {
    throw new Error('没有可用的数据')
  }
  
  // 转换数据格式为 Vega-Lite 需要的长格式
  const vegaData = []
  dataSource.forEach(point => {
    const timestamp = point.timestamp || point.date
    vegaData.push({
      time: timestamp,
      type: 'emotion',
      value: point.emotion,
      label: '情绪分析'
    })
    vegaData.push({
      time: timestamp,
      type: 'stance', 
      value: point.stance,
      label: '立场分析'
    })
  })
  
  const size = chartSizes[chartSize.value]
  
  // 基础规范
  const spec = {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json",
    title: {
      text: "群体情绪和立场趋势分析 (可交互)",
      fontSize: 16,
      anchor: "start",
      font: "Arial, sans-serif"
    },
    width: size.width,
    height: size.height,
    data: { values: vegaData },
    transform: [
      {
        calculate: "datum.type === 'emotion' ? '情绪分析' : '立场分析'",
        as: "category"
      }
    ],
    // 添加交互选择
    params: getInteractionParams()
  }
  
  // 根据可视化样式构建不同的图层
  const encoding = getEncodingConfig()
  
  if (visualStyle.value === 'line') {
    spec.mark = {
      type: "line",
      point: true,
      strokeWidth: 3,
      pointSize: 60
    }
    spec.encoding = encoding
  } else if (visualStyle.value === 'area') {
    spec.mark = {
      type: "area",
      opacity: 0.7,
      line: true,
      strokeWidth: 2
    }
    spec.encoding = encoding
  } else { // both
    spec.layer = [
      {
        mark: {
          type: "area",
          opacity: 0.3,
        },
        encoding: {
          ...encoding,
          // 去除 tooltip，避免在面积图层重复
          tooltip: undefined
        }
      },
      {
        mark: {
          type: "line",
          strokeWidth: 3,
          point: { size: 60 }
        },
        encoding: encoding
      }
    ]
  }
  
  return spec
}

// 渲染 Vega-Lite 图表
const renderVegaChart = async () => {
  if (!vegaContainer.value) return
  
  try {
    const spec = buildVegaSpec()
    if (!spec) return
    
    // 清除之前的图表
    if (vegaView) {
      vegaView.finalize()
    }
    
    // 根据交互模式设置不同的配置
    const vegaConfig = {
      theme: theme.value,
      actions: {
        export: true,
        source: true,
        compiled: false,
        editor: false
      },
      scaleFactor: 2,
      downloadFileName: `attitude_analysis_${new Date().getTime()}`
    }
    
    // 为平移缩放模式添加原生缩放支持
    if (interactionMode.value === 'pan-zoom') {
      vegaConfig.config = {
        view: {
          continuousWidth: chartSizes[chartSize.value].width,
          continuousHeight: chartSizes[chartSize.value].height
        }
      }
    }
    
    // 渲染新图表
    const result = await vegaEmbed(vegaContainer.value, spec, vegaConfig)
    
    vegaView = result.view
    
    // 为平移缩放模式添加鼠标事件监听
    if (interactionMode.value === 'pan-zoom') {
      vegaView.addEventListener('wheel', (event, item) => {
        // 阻止默认滚动行为
        event.preventDefault()
        
        // 获取当前缩放状态
        const currentDomain = vegaView.scale('x').domain()
        const range = currentDomain[1] - currentDomain[0]
        const center = currentDomain[0] + range / 2
        
        // 计算新的缩放范围
        const zoomFactor = event.deltaY > 0 ? 1.1 : 0.9
        const newRange = range * zoomFactor
        const newDomain = [center - newRange / 2, center + newRange / 2]
        
        // 应用新的域
        vegaView.signal('width', chartSizes[chartSize.value].width)
        vegaView.runAsync()
      })
    }
    
    console.log('Vega-Lite 图表渲染完成')
  } catch (err) {
    console.error('渲染 Vega-Lite 图表失败:', err)
    error.value = '图表渲染失败: ' + err.message
  }
}

// 更新可视化
const updateVisualization = async () => {
  await nextTick()
  await renderVegaChart()
}

// 重置视图
const resetView = () => {
  if (vegaView) {
    // 重置选择参数
    if (interactionMode.value === 'brush') {
      vegaView.signal('brush_selection', null)
    } else if (interactionMode.value === 'interval') {
      vegaView.signal('interval_selection', null)
    }
    vegaView.runAsync()
  }
}

// 导出图表
const exportChart = () => {
  if (vegaView) {
    vegaView.toSVG().then(svg => {
      const blob = new Blob([svg], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `attitude_analysis_${new Date().getTime()}.svg`
      a.click()
      URL.revokeObjectURL(url)
    }).catch(err => {
      console.error('导出失败:', err)
      alert('导出失败: ' + err.message)
    })
  }
}

// 重试加载
const retryLoad = () => {
  fetchAttitudeData()
}

// 监听时间范围变化
watch(globalTimeRange, () => {
  fetchAttitudeData()
}, { deep: true })

// 组件挂载时加载数据
onMounted(() => {
  fetchAttitudeData()
})
</script>

<style scoped>
.attitude-panel-vega {
  padding: 20px;
  background: white;
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.attitude-panel-vega h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.vega-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-weight: 500;
  color: #495057;
  min-width: 70px;
}

.control-group select {
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
  font-size: 14px;
}

.export-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.export-btn:hover {
  background: #0056b3;
}

.reset-btn {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  margin-left: 8px;
}

.reset-btn:hover {
  background: #1e7e34;
}

.vega-chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

.vega-chart {
  flex: 1;
  overflow: auto;
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  text-align: center;
  color: #dc3545;
  padding: 20px;
  background: #f8d7da;
  border-radius: 4px;
  margin: 20px 0;
}

.error-message button {
  margin-top: 10px;
  padding: 6px 12px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.error-message button:hover {
  background: #c82333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .attitude-panel-vega {
    padding: 15px;
  }
  
  .vega-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-group {
    justify-content: space-between;
  }
}

/* Vega-Lite 图表样式覆盖 */
:deep(.vega-embed) {
  padding: 10px;
}

:deep(.vega-embed .vega-actions) {
  top: 10px;
  right: 10px;
}

:deep(.vega-embed .vega-actions a) {
  margin-left: 5px;
  padding: 4px 8px;
  background: rgba(0, 123, 255, 0.1);
  border-radius: 3px;
  text-decoration: none;
  font-size: 12px;
}

:deep(.vega-embed .vega-actions a:hover) {
  background: rgba(0, 123, 255, 0.2);
}
</style>
