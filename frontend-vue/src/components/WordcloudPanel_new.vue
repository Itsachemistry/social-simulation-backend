<template>
  <div class="wordcloud-panel">
    <h3>词云分析 ✨</h3>
    
    <div class="panel-content">
      <!-- 词云控制区域 -->
      <div class="controls-section">
        <div class="control-group">
          <label>词云类型：</label>
          <select v-model="wordcloudType" @change="generateWordcloud">
            <option value="content">内容词云</option>
            <option value="hashtag">话题标签</option>
            <option value="user">用户提及</option>
            <option value="sentiment">情感词汇</option>
          </select>
        </div>
        
        <div class="control-group">
          <label>最大词数：</label>
          <input 
            v-model.number="maxWords" 
            type="number" 
            min="10" 
            max="100" 
            @change="generateWordcloud"
          />
        </div>
        
        <div class="control-group">
          <label>最小频次：</label>
          <input 
            v-model.number="minFrequency" 
            type="number" 
            min="1" 
            max="10" 
            @change="generateWordcloud"
          />
        </div>
      </div>
      
      <!-- 词云画布 -->
      <div class="wordcloud-container">
        <div class="canvas-wrapper">
          <canvas 
            ref="wordcloudCanvas" 
            :width="canvasWidth" 
            :height="canvasHeight"
            @click="onWordClick"
          ></canvas>
          
          <div v-if="isLoading" class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">生成词云中...</div>
          </div>
          
          <div v-if="!isLoading && !hasWordcloudData" class="no-data">
            <div class="no-data-icon">📊</div>
            <div class="no-data-text">暂无词云数据</div>
            <div class="no-data-hint">请调整时间范围或降低最小频次</div>
          </div>
        </div>
        
        <!-- 词云信息显示 -->
        <div class="wordcloud-info" v-if="hasWordcloudData">
          <div class="info-item">
            <span class="info-label">词汇总数</span>
            <span class="info-value">{{ wordStats.length }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">类型</span>
            <span class="info-value">{{ getTypeLabel(wordcloudType) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最高频次</span>
            <span class="info-value">{{ maxFrequency }}</span>
          </div>
        </div>
      </div>
      
      <!-- 词频统计 -->
      <div class="word-stats-section" v-if="wordStats.length > 0">
        <label>📈 词频统计 (前10)：</label>
        <div class="word-stats-list">
          <div 
            v-for="(word, index) in wordStats.slice(0, 10)" 
            :key="word.text"
            class="word-stat-item"
            :class="{ highlighted: highlightedWord === word.text }"
            @mouseenter="highlightWord(word.text)"
            @mouseleave="clearHighlight"
          >
            <span class="rank">{{ index + 1 }}</span>
            <span class="word">{{ word.text }}</span>
            <span class="frequency">{{ word.frequency }}</span>
            <div class="frequency-bar">
              <div 
                class="frequency-fill" 
                :style="{ width: (word.frequency / maxFrequency * 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="button-group">
        <button @click="generateWordcloud" :disabled="isLoading">
          {{ isLoading ? '生成中...' : '🔄 重新生成' }}
        </button>
        <button @click="exportWordcloud" :disabled="!hasWordcloudData">
          📷 导出图片
        </button>
        <button @click="exportWordData" :disabled="!wordStats.length">
          📊 导出数据
        </button>
      </div>
      
      <div v-if="message" class="message" :class="messageType">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useApi } from '../composables/useApiComplete.js'
import { useTimeRange } from '../composables/useApiComplete.js'

const { fetchWordcloud, loading: isLoading } = useApi()
const { timeRange } = useTimeRange()

// 画布引用
const wordcloudCanvas = ref(null)

// 词云配置
const wordcloudType = ref('content')
const maxWords = ref(50)
const minFrequency = ref(2)
const canvasWidth = ref(500)
const canvasHeight = ref(350)

// 词云数据
const wordStats = ref([])
const highlightedWord = ref('')
const hasWordcloudData = ref(false)

// 消息显示
const message = ref('')
const messageType = ref('')

// 计算最大频次用于进度条
const maxFrequency = computed(() => {
  return wordStats.value.length > 0 ? Math.max(...wordStats.value.map(w => w.frequency)) : 1
})

// 获取类型标签
const getTypeLabel = (type) => {
  const labels = {
    content: '内容词云',
    hashtag: '话题标签', 
    user: '用户提及',
    sentiment: '情感词汇'
  }
  return labels[type] || type
}

// 生成词云
const generateWordcloud = async () => {
  if (!wordcloudCanvas.value) return
  
  try {
    const params = {
      type: wordcloudType.value,
      max_words: maxWords.value,
      min_frequency: minFrequency.value,
      start_time: timeRange.value.start,
      end_time: timeRange.value.end
    }
    
    const data = await fetchWordcloud(params)
    
    if (data && data.words && data.words.length > 0) {
      wordStats.value = data.words.map(word => ({
        text: word.text || word.word,
        frequency: word.frequency || word.count || 1,
        size: word.size || 16
      }))
      
      await renderWordcloud(wordStats.value)
      hasWordcloudData.value = true
      showMessage('词云生成成功！', 'success')
    } else {
      wordStats.value = []
      hasWordcloudData.value = false
      clearCanvas()
      showMessage('暂无数据生成词云', 'error')
    }
  } catch (error) {
    console.error('生成词云失败:', error)
    wordStats.value = []
    hasWordcloudData.value = false
    clearCanvas()
    showMessage('生成词云失败', 'error')
  }
}

// 渲染词云到画布 - 改进的紧凑算法
const renderWordcloud = async (words) => {
  const canvas = wordcloudCanvas.value
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 设置渐变背景
  const gradient = ctx.createRadialGradient(canvas.width/2, canvas.height/2, 0, canvas.width/2, canvas.height/2, Math.max(canvas.width, canvas.height)/2)
  gradient.addColorStop(0, '#ffffff')
  gradient.addColorStop(1, '#f8f9fa')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  if (!words || words.length === 0) return
  
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const placedWords = []
  
  // 按频次排序，重要词汇优先放置
  const sortedWords = [...words].sort((a, b) => b.frequency - a.frequency)
  
  sortedWords.forEach((word, index) => {
    // 动态计算字体大小
    const maxFreq = sortedWords[0].frequency
    const minFreq = sortedWords[sortedWords.length - 1].frequency
    const freqRatio = (word.frequency - minFreq) / (maxFreq - minFreq || 1)
    const fontSize = Math.max(14, Math.min(42, 14 + freqRatio * 28))
    
    ctx.font = `bold ${fontSize}px 'Microsoft YaHei', Arial, sans-serif`
    
    // 计算文本尺寸
    const metrics = ctx.measureText(word.text)
    const textWidth = metrics.width
    const textHeight = fontSize * 0.8
    
    // 丰富的颜色方案
    const colorSchemes = [
      { h: 210, s: 70, l: 50 }, // 蓝色系
      { h: 340, s: 70, l: 50 }, // 红色系
      { h: 120, s: 60, l: 45 }, // 绿色系
      { h: 45, s: 75, l: 50 },  // 橙色系
      { h: 270, s: 65, l: 55 }, // 紫色系
      { h: 180, s: 60, l: 45 }, // 青色系
    ]
    const scheme = colorSchemes[index % colorSchemes.length]
    const lightness = scheme.l + (freqRatio * 15 - 7.5)
    const color = `hsl(${scheme.h}, ${scheme.s}%, ${Math.max(30, Math.min(70, lightness))}%)`
    
    // 改进的位置查找算法 - 多层搜索
    let bestPosition = null
    let minDistance = Infinity
    
    const searchLayers = [
      { radius: 0, step: 1 },      // 中心点
      { radius: 20, step: 8 },     // 内层
      { radius: 50, step: 12 },    // 中层
      { radius: 80, step: 16 },    // 外层
      { radius: 120, step: 20 },   // 最外层
    ]
    
    for (const layer of searchLayers) {
      if (bestPosition) break
      
      const angleStep = (Math.PI * 2) / layer.step
      for (let i = 0; i < layer.step; i++) {
        const angle = i * angleStep
        const x = centerX + layer.radius * Math.cos(angle) - textWidth / 2
        const y = centerY + layer.radius * Math.sin(angle)
        
        // 检查边界
        if (x < 5 || x + textWidth > canvas.width - 5 || 
            y - textHeight < 5 || y > canvas.height - 5) {
          continue
        }
        
        // 精确的碰撞检测
        let hasCollision = false
        for (const placed of placedWords) {
          const padding = 3 // 紧凑间距
          if (x < placed.x + placed.width + padding && 
              x + textWidth > placed.x - padding &&
              y > placed.y - placed.height - padding && 
              y - textHeight < placed.y + padding) {
            hasCollision = true
            break
          }
        }
        
        if (!hasCollision) {
          const distanceFromCenter = Math.sqrt((x + textWidth/2 - centerX)**2 + (y - textHeight/2 - centerY)**2)
          if (distanceFromCenter < minDistance) {
            minDistance = distanceFromCenter
            bestPosition = { x, y }
          }
        }
      }
    }
    
    // 绘制文字
    if (bestPosition) {
      const { x, y } = bestPosition
      
      // 添加阴影效果
      ctx.shadowColor = 'rgba(0, 0, 0, 0.1)'
      ctx.shadowBlur = 2
      ctx.shadowOffsetX = 1
      ctx.shadowOffsetY = 1
      
      ctx.fillStyle = color
      ctx.fillText(word.text, x, y)
      
      // 重置阴影
      ctx.shadowColor = 'transparent'
      ctx.shadowBlur = 0
      ctx.shadowOffsetX = 0
      ctx.shadowOffsetY = 0
      
      // 记录位置
      placedWords.push({
        x: x,
        y: y,
        width: textWidth,
        height: textHeight,
        word: word.text,
        fontSize: fontSize
      })
    }
  })
  
  // 装饰边框
  ctx.strokeStyle = '#e9ecef'
  ctx.lineWidth = 2
  ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2)
}

// 清空画布
const clearCanvas = () => {
  if (wordcloudCanvas.value) {
    const ctx = wordcloudCanvas.value.getContext('2d')
    ctx.clearRect(0, 0, wordcloudCanvas.value.width, wordcloudCanvas.value.height)
    
    // 设置空白状态背景
    const gradient = ctx.createLinearGradient(0, 0, wordcloudCanvas.value.width, wordcloudCanvas.value.height)
    gradient.addColorStop(0, '#f8f9fa')
    gradient.addColorStop(1, '#e9ecef')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, wordcloudCanvas.value.width, wordcloudCanvas.value.height)
  }
}

// 词云点击事件
const onWordClick = (event) => {
  console.log('点击词云区域')
}

// 高亮词汇
const highlightWord = (word) => {
  highlightedWord.value = word
}

// 清除高亮
const clearHighlight = () => {
  highlightedWord.value = ''
}

// 导出词云图片
const exportWordcloud = () => {
  if (!wordcloudCanvas.value || !hasWordcloudData.value) return
  
  try {
    const canvas = wordcloudCanvas.value
    const link = document.createElement('a')
    link.download = `wordcloud_${wordcloudType.value}_${new Date().toISOString().split('T')[0]}.png`
    link.href = canvas.toDataURL()
    link.click()
    
    showMessage('词云图片已导出 📷', 'success')
  } catch (error) {
    console.error('导出图片失败:', error)
    showMessage('导出图片失败', 'error')
  }
}

// 导出词频数据
const exportWordData = () => {
  if (!wordStats.value.length) return
  
  try {
    const dataStr = JSON.stringify(wordStats.value, null, 2)
    const dataBlob = new Blob([dataStr], {type: 'application/json'})
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `wordcloud_data_${wordcloudType.value}_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('词频数据已导出 📊', 'success')
  } catch (error) {
    console.error('导出数据失败:', error)
    showMessage('导出数据失败', 'error')
  }
}

// 显示消息
const showMessage = (text, type) => {
  message.value = text
  messageType.value = type
  
  setTimeout(() => {
    message.value = ''
    messageType.value = ''
  }, 3000)
}

// 组件挂载时初始化
onMounted(() => {
  nextTick(() => {
    if (wordcloudCanvas.value) {
      // 自适应画布尺寸
      const container = wordcloudCanvas.value.parentElement.parentElement
      const containerWidth = container.clientWidth - 40
      canvasWidth.value = Math.max(450, Math.min(600, containerWidth))
      canvasHeight.value = Math.max(300, canvasWidth.value * 0.7)
      
      clearCanvas()
      generateWordcloud()
    }
  })
})

// 暴露给父组件的方法
defineExpose({
  refreshWordcloud: generateWordcloud,
  exportImage: exportWordcloud,
  exportData: exportWordData
})
</script>

<style scoped>
.wordcloud-panel {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.wordcloud-panel h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 2px solid #1976d2;
  padding-bottom: 8px;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.controls-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  padding: 16px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  min-width: 80px;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin: 0;
}

.control-group select,
.control-group input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.control-group select:focus,
.control-group input:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.wordcloud-container {
  position: relative;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: white;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.canvas-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 350px;
  padding: 20px;
}

canvas {
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

canvas:hover {
  transform: scale(1.02);
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  backdrop-filter: blur(2px);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1976d2;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 12px;
  color: #666;
  font-size: 16px;
  font-weight: 500;
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #9e9e9e;
  text-align: center;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.no-data-text {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 6px;
}

.no-data-hint {
  font-size: 14px;
  color: #bdbdbd;
}

.wordcloud-info {
  display: flex;
  justify-content: space-around;
  padding: 12px 20px;
  background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.info-value {
  font-size: 16px;
  color: #495057;
  font-weight: 600;
}

.word-stats-section {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.word-stats-section label {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: block;
}

.word-stats-list {
  max-height: 240px;
  overflow-y: auto;
  border-radius: 6px;
}

.word-stat-item {
  display: grid;
  grid-template-columns: 30px 1fr 60px;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
  cursor: pointer;
}

.word-stat-item:hover,
.word-stat-item.highlighted {
  background: #e3f2fd;
  border-color: #1976d2;
  transform: translateX(2px);
}

.rank {
  font-size: 12px;
  color: #9e9e9e;
  font-weight: 600;
  text-align: center;
}

.word {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.frequency {
  font-size: 12px;
  color: #666;
  font-weight: 600;
  text-align: right;
}

.frequency-bar {
  grid-column: 1 / -1;
  height: 3px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.frequency-fill {
  height: 100%;
  background: linear-gradient(90deg, #1976d2, #42a5f5);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.button-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button-group button {
  flex: 1;
  min-width: 120px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: none;
}

.button-group button:first-child {
  background: linear-gradient(135deg, #1976d2, #1565c0);
  color: white;
}

.button-group button:first-child:hover:not(:disabled) {
  background: linear-gradient(135deg, #1565c0, #0d47a1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.button-group button:not(:first-child) {
  background: linear-gradient(135deg, #757575, #616161);
  color: white;
}

.button-group button:not(:first-child):hover:not(:disabled) {
  background: linear-gradient(135deg, #616161, #424242);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(97, 97, 97, 0.3);
}

.button-group button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.message {
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  animation: slideIn 0.3s ease;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .wordcloud-panel {
    padding: 15px;
  }
  
  .controls-section {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .button-group button {
    min-width: auto;
  }
  
  .wordcloud-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .info-item {
    flex-direction: row;
    justify-content: space-between;
  }
}

/* 滚动条样式 */
.word-stats-list::-webkit-scrollbar {
  width: 6px;
}

.word-stats-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.word-stats-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.word-stats-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
