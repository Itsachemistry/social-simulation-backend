<template>
  <div class="attitude-panel">
    <h4>群体情绪和立场分析</h4>
    
    <div class="attitude-description" style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666;">
      <p><strong>图表说明：</strong></p>
      <ul style="margin: 5px 0; padding-left: 20px;">
        <li>红色线条：情绪分析趋势（-1 表示负面，+1 表示正面）</li>
        <li>蓝色线条：立场分析趋势（-1 表示反对，+1 表示支持）</li>
        <li>横轴：时间轴（可选择按小时或按天聚合）</li>
        <li>纵轴：情绪/立场强度值（范围 -1 到 +1）</li>
      </ul>
      <p><strong>🖱️ 交互操作：</strong></p>
      <ul style="margin: 5px 0; padding-left: 20px;">
        <li><strong>滚轮缩放：</strong>普通滚轮=横向缩放，Shift+滚轮=纵向缩放</li>
        <li><strong>拖拽平移：</strong>按住左键拖拽移动图表视图</li>
        <li><strong>双击缩放：</strong>双击图表区域进行局部缩放</li>
        <li><strong>悬停提示：</strong>鼠标悬停查看具体数值</li>
      </ul>
    </div>
    
    <div class="attitude-controls">
      <div class="time-unit-selector">
        <select v-model="timeUnit" @change="updateChart">
          <option value="hour">按小时</option>
          <option value="day">按天</option>
        </select>
        <div class="range-control">
          <input 
            type="range" 
            v-model="timeRangeLocal" 
            :min="timeUnit === 'hour' ? 1 : 1" 
            :max="timeUnit === 'hour' ? 24 : 7" 
            @input="updateChart"
          >
          <span>{{ timeRangeLocal }}</span>
        </div>
      </div>
    </div>
    
    <div class="attitude-chart-container">
      <!-- 缩放控制 -->
      <div class="zoom-controls" style="margin-bottom: 10px; display: flex; align-items: center; gap: 15px;">
        <div>
          <label>水平缩放: </label>
          <input 
            type="range" 
            v-model="zoomLevel" 
            min="0.5" 
            max="3" 
            step="0.1" 
            @input="updateChart"
            style="width: 120px;"
          >
          <span>{{ zoomLevel }}x</span>
        </div>
        <div>
          <label>垂直缩放: </label>
          <input 
            type="range" 
            v-model="verticalZoom" 
            min="0.5" 
            max="2" 
            step="0.1" 
            @input="updateChart"
            style="width: 120px;"
          >
          <span>{{ verticalZoom }}x</span>
        </div>
        <div>
          <label>图表尺寸: </label>
          <select v-model="canvasSize" @change="resizeCanvas">
            <option value="small">小 (400x300)</option>
            <option value="medium">中 (500x350)</option>
            <option value="large">大 (600x400)</option>
            <option value="xlarge">超大 (700x450)</option>
          </select>
        </div>
        <button @click="resetZoom" style="padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa;">重置缩放</button>
      </div>
      
      <div class="canvas-wrapper" 
           style="overflow: auto; border: 1px solid #ddd; border-radius: 4px; position: relative;"
           @wheel="handleWheel"
           @mousedown="handleMouseDown"
           @mousemove="handleMouseMove"
           @mouseup="handleMouseUp"
           @mouseleave="handleMouseLeave">
        <canvas 
          ref="attitudeCanvas" 
          :width="canvasWidth * devicePixelRatio" 
          :height="canvasHeight * devicePixelRatio" 
          :style="{ 
            width: canvasWidth + 'px', 
            height: canvasHeight + 'px',
            display: 'block',
            cursor: isDragging ? 'grabbing' : 'grab'
          }"
          @dblclick="handleDoubleClick"
        ></canvas>
      </div>
      
      <div class="chart-legend" style="margin-top: 10px; display: flex; justify-content: center; gap: 20px;">
        <div style="display: flex; align-items: center;">
          <span style="display: inline-block; width: 12px; height: 3px; background: #e63946; margin-right: 5px;"></span>
          情绪分析
        </div>
        <div style="display: flex; align-items: center;">
          <span style="display: inline-block; width: 12px; height: 3px; background: #457b9d; margin-right: 5px;"></span>
          立场分析
        </div>
      </div>
    </div>
    
    <!-- 悬停提示 -->
    <div 
      v-if="tooltip.visible" 
      class="chart-tooltip" 
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div><strong>时间:</strong> {{ tooltip.time }}</div>
      <div><strong>情绪:</strong> {{ tooltip.emotion }}</div>
      <div><strong>立场:</strong> {{ tooltip.stance }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, nextTick } from 'vue'
import { useApi } from '../composables/useApiComplete'
import { useTimeRange } from '../composables/useApiComplete'

const attitudeCanvas = ref(null)
const timeUnit = ref('hour')
const timeRangeLocal = ref(1)
const attitudeData = ref(null)
const zoomLevel = ref(1)
const verticalZoom = ref(1)
const canvasSize = ref('medium')
const devicePixelRatio = window.devicePixelRatio || 1

// 拖拽和平移相关
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const panOffset = ref({ x: 0, y: 0 })
const lastPanOffset = ref({ x: 0, y: 0 })

// Canvas 尺寸配置
const canvasSizes = {
  small: { width: 400, height: 300 },
  medium: { width: 500, height: 350 },
  large: { width: 600, height: 400 },
  xlarge: { width: 700, height: 450 }
}

const canvasWidth = ref(canvasSizes.medium.width)
const canvasHeight = ref(canvasSizes.medium.height)

const { getAttitude } = useApi()
const { timeRange: globalTimeRange } = useTimeRange()

const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  time: '',
  emotion: '',
  stance: ''
})

// 调整画布尺寸
const resizeCanvas = () => {
  const size = canvasSizes[canvasSize.value]
  canvasWidth.value = size.width
  canvasHeight.value = size.height
  
  // 延时重绘，确保Canvas尺寸更新完成
  nextTick(() => {
    drawAttitudeChart()
  })
}

// 重置缩放
const resetZoom = () => {
  zoomLevel.value = 1
  verticalZoom.value = 1
  panOffset.value = { x: 0, y: 0 }
  lastPanOffset.value = { x: 0, y: 0 }
  updateChart()
}

// 鼠标滚轮缩放
const handleWheel = (event) => {
  event.preventDefault()
  const delta = event.deltaY > 0 ? 0.9 : 1.1
  
  if (event.shiftKey) {
    // Shift + 滚轮 = 垂直缩放
    verticalZoom.value = Math.max(0.5, Math.min(2, verticalZoom.value * delta))
  } else {
    // 普通滚轮 = 水平缩放
    zoomLevel.value = Math.max(0.5, Math.min(3, zoomLevel.value * delta))
  }
  
  updateChart()
}

// 双击重置某个区域的缩放
const handleDoubleClick = (event) => {
  const canvas = attitudeCanvas.value
  const rect = canvas.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const clickY = event.clientY - rect.top
  
  // 如果双击在图表区域内，进行局部缩放
  const margin = { top: 40, right: 40, bottom: 70, left: 70 }
  if (clickX > margin.left && clickX < canvasWidth.value - margin.right &&
      clickY > margin.top && clickY < canvasHeight.value - margin.bottom) {
    
    // 计算点击位置相对于图表的比例
    const relativeX = (clickX - margin.left) / (canvasWidth.value - margin.left - margin.right)
    
    // 缩放到该位置
    zoomLevel.value = zoomLevel.value === 1 ? 2 : 1
    
    // 调整平移以保持点击点居中
    if (zoomLevel.value > 1) {
      panOffset.value.x = -(relativeX - 0.5) * (canvasWidth.value - margin.left - margin.right) * (zoomLevel.value - 1)
    } else {
      panOffset.value.x = 0
    }
    
    updateChart()
  }
}

// 鼠标拖拽开始
const handleMouseDown = (event) => {
  if (event.button === 0) { // 左键
    isDragging.value = true
    dragStart.value = { x: event.clientX, y: event.clientY }
    lastPanOffset.value = { ...panOffset.value }
  }
}

// 鼠标拖拽移动
const handleMouseMove = (event) => {
  if (isDragging.value) {
    // 拖拽平移
    const deltaX = event.clientX - dragStart.value.x
    const deltaY = event.clientY - dragStart.value.y
    
    panOffset.value.x = lastPanOffset.value.x + deltaX
    panOffset.value.y = lastPanOffset.value.y + deltaY
    
    updateChart()
  } else {
    // 原有的工具提示逻辑
    handleMouseHover(event)
  }
}

// 鼠标拖拽结束
const handleMouseUp = () => {
  isDragging.value = false
}

// 鼠标离开画布
const handleMouseLeave = () => {
  isDragging.value = false
  hideTooltip()
}

// 处理鼠标悬停（原有的工具提示功能）
const handleMouseHover = (event) => {
  if (!attitudeData.value) return
  
  const canvas = attitudeCanvas.value
  const rect = canvas.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  
  const margin = { top: 40, right: 40, bottom: 70, left: 70 }
  const chartWidth = (canvasWidth.value - margin.left - margin.right) * zoomLevel.value
  
  const relativeX = mouseX - margin.left - panOffset.value.x
  
  if (relativeX >= 0 && relativeX <= chartWidth) {
    const dataSource = timeUnit.value === 'hour' ? attitudeData.value.hourly_data : attitudeData.value.daily_data
    
    if (dataSource && dataSource.length > 0) {
      const index = Math.round((relativeX / chartWidth) * (dataSource.length - 1))
      
      if (index >= 0 && index < dataSource.length) {
        const point = dataSource[index]
        const date = new Date(point.timestamp || point.date)
        const timeStr = timeUnit.value === 'hour'
          ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
          : date.toLocaleDateString('zh-CN')
        
        tooltip.visible = true
        tooltip.x = event.clientX + 10
        tooltip.y = event.clientY - 10
        tooltip.time = timeStr
        tooltip.emotion = point.emotion.toFixed(3)
        tooltip.stance = point.stance.toFixed(3)
      }
    }
  } else {
    tooltip.visible = false
  }
}

// 获取态度分析数据
const fetchAttitudeData = async () => {
  try {
    const start = globalTimeRange.value?.start || '2016-01-01T00:00:00'
    const end = globalTimeRange.value?.end || '2016-12-31T23:59:59'
    
    const data = await getAttitude(start, end, timeUnit.value, timeRangeLocal.value)
    attitudeData.value = data
    
    console.log('态度分析数据:', data)
    drawAttitudeChart()
  } catch (error) {
    console.error('获取态度分析数据失败', error)
    // 显示错误信息
    const canvas = attitudeCanvas.value
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = 'red'
      ctx.font = '14px Arial'
      ctx.fillText(`加载失败: ${error.message}`, 10, 30)
    }
  }
}

// 绘制态度分析图表
const drawAttitudeChart = () => {
  const canvas = attitudeCanvas.value
  if (!canvas || !attitudeData.value) return
  
  const ctx = canvas.getContext('2d')
  const { width, height } = canvas
  
  // 设置高DPI显示
  ctx.scale(devicePixelRatio, devicePixelRatio)
  
  const displayWidth = canvasWidth.value
  const displayHeight = canvasHeight.value
  
  ctx.clearRect(0, 0, displayWidth, displayHeight)
  
  // 设置画布背景
  ctx.fillStyle = '#f8f9fa'
  ctx.fillRect(0, 0, displayWidth, displayHeight)
  
  const margin = { top: 40, right: 40, bottom: 70, left: 70 }
  const chartWidth = (displayWidth - margin.left - margin.right) * zoomLevel.value
  const chartHeight = (displayHeight - margin.top - margin.bottom) * verticalZoom.value
  
  // 绘制网格线 - 增加更多网格线用于高精度显示
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 0.5
  
  // 横向网格线 (Y轴刻度) - 增加到10条
  const yTicks = 10
  for (let i = 0; i <= yTicks; i++) {
    const y = margin.top + (i / yTicks) * Math.min(chartHeight, displayHeight - margin.top - margin.bottom) + panOffset.value.y
    if (y >= margin.top && y <= displayHeight - margin.bottom) {
      ctx.beginPath()
      ctx.moveTo(margin.left, y)
      ctx.lineTo(margin.left + Math.min(chartWidth, displayWidth - margin.left - margin.right), y)
      ctx.stroke()
      
      // Y轴标签 (-1 到 1) - 更精确的标签
      if (i % 2 === 0) { // 只显示偶数标签避免拥挤
        ctx.fillStyle = '#666'
        ctx.font = '12px Arial'
        ctx.textAlign = 'right'
        const value = (1 - (i / yTicks) * 2).toFixed(1)
        ctx.fillText(value, margin.left - 10, y + 4)
      }
    }
  }
  
  // 选择数据源
  const dataSource = timeUnit.value === 'hour' ? attitudeData.value.hourly_data : attitudeData.value.daily_data
  
  if (dataSource && dataSource.length > 1) {
    // 纵向网格线 (X轴刻度) - 根据缩放级别调整网格密度
    const maxXTicks = Math.min(20, dataSource.length)
    const xTicks = Math.max(5, Math.floor(maxXTicks * zoomLevel.value))
    
    for (let i = 0; i < xTicks; i++) {
      const index = Math.floor(i * (dataSource.length - 1) / (xTicks - 1))
      const x = margin.left + (index / (dataSource.length - 1)) * chartWidth
      
      if (x >= margin.left && x <= margin.left + chartWidth) {
        ctx.beginPath()
        ctx.moveTo(x, margin.top)
        ctx.lineTo(x, margin.top + chartHeight)
        ctx.stroke()
        
        // X轴时间标签 - 增大字体
        const timeData = dataSource[index]
        const date = new Date(timeData.timestamp || timeData.date)
        const timeStr = timeUnit.value === 'hour' 
          ? date.getHours() + ':00'
          : (date.getMonth() + 1) + '/' + date.getDate()
        
        ctx.fillStyle = '#666'
        ctx.font = '12px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(timeStr, x, displayHeight - margin.bottom + 25)
      }
    }
  }
  
  // 绘制坐标轴 - 增加轴线宽度
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 2
  
  // X轴
  ctx.beginPath()
  ctx.moveTo(margin.left, margin.top + chartHeight)
  ctx.lineTo(margin.left + chartWidth, margin.top + chartHeight)
  ctx.stroke()
  
  // Y轴
  ctx.beginPath()
  ctx.moveTo(margin.left, margin.top)
  ctx.lineTo(margin.left, margin.top + chartHeight)
  ctx.stroke()
  
  // 坐标轴标签 - 增大字体
  ctx.fillStyle = '#333'
  ctx.font = 'bold 14px Arial'
  ctx.textAlign = 'center'
  ctx.fillText('时间', displayWidth / 2, displayHeight - 10)
  
  ctx.save()
  ctx.translate(25, displayHeight / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillText('情绪/立场值', 0, 0)
  ctx.restore()
  
  // 绘制数据线条 - 增加线条宽度和抗锯齿
  if (dataSource && dataSource.length > 0) {
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    
    // 情绪线条 (红色) - 更粗的线条
    ctx.strokeStyle = '#e63946'
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.beginPath()
    dataSource.forEach((point, i) => {
      const x = margin.left + (i / (dataSource.length - 1)) * chartWidth + panOffset.value.x
      const y = margin.top + chartHeight / 2 - (point.emotion * chartHeight / 2) + panOffset.value.y
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()
    
    // 立场线条 (蓝色) - 更粗的线条
    ctx.strokeStyle = '#457b9d'
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.beginPath()
    dataSource.forEach((point, i) => {
      const x = margin.left + (i / (dataSource.length - 1)) * chartWidth + panOffset.value.x
      const y = margin.top + chartHeight / 2 - (point.stance * chartHeight / 2) + panOffset.value.y
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()
    
    // 绘制数据点 - 增大点的尺寸
    const pointRadius = 5
    dataSource.forEach((point, i) => {
      const x = margin.left + (i / (dataSource.length - 1)) * chartWidth + panOffset.value.x
      
      // 情绪点 (红色) - 添加描边
      const emotionY = margin.top + chartHeight / 2 - (point.emotion * chartHeight / 2) + panOffset.value.y
      ctx.fillStyle = '#e63946'
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(x, emotionY, pointRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      
      // 立场点 (蓝色) - 添加描边
      const stanceY = margin.top + chartHeight / 2 - (point.stance * chartHeight / 2) + panOffset.value.y
      ctx.fillStyle = '#457b9d'
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(x, stanceY, pointRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
    })
  }
}

// 隐藏提示
const hideTooltip = () => {
  tooltip.visible = false
}

// 更新图表
const updateChart = () => {
  // 调整时间范围的值
  if (timeUnit.value === 'hour') {
    if (timeRangeLocal.value > 24) timeRangeLocal.value = 24
  } else {
    if (timeRangeLocal.value > 7) timeRangeLocal.value = 7
  }
  
  fetchAttitudeData()
}

// 监听时间范围变化
watch(globalTimeRange, () => {
  fetchAttitudeData()
}, { deep: true })

onMounted(() => {
  fetchAttitudeData()
})
</script>

<style scoped>
.attitude-panel {
  padding: 20px;
  background: white;
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.attitude-panel h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
}

.attitude-controls {
  margin-bottom: 15px;
}

.time-unit-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}

.time-unit-selector select {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.range-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-control input[type="range"] {
  width: 100px;
}

.range-control span {
  min-width: 20px;
  text-align: center;
  font-weight: bold;
}

.attitude-chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.attitude-chart-container canvas {
  max-width: 100%;
  height: auto;
  cursor: crosshair;
}

.canvas-wrapper {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.zoom-controls {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.zoom-controls label {
  font-weight: 500;
  color: #495057;
}

.zoom-controls input[type="range"] {
  margin: 0 8px;
}

.zoom-controls select {
  padding: 4px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
}

.zoom-controls button:hover {
  background: #e9ecef !important;
  border-color: #adb5bd !important;
}

.chart-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.chart-tooltip div {
  margin-bottom: 4px;
}

.chart-tooltip div:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .attitude-panel {
    padding: 15px;
  }
  
  .time-unit-selector {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .chart-legend {
    flex-direction: column !important;
    gap: 10px !important;
  }
}
</style>
