<template>
  <div class="single-panel">
    <h3>单帖深度分析</h3>
    
    <div class="panel-content">
      <!-- 帖子搜索 -->
      <div class="search-section">
        <div class="search-input-group">
          <input 
            v-model="searchQuery" 
            @keyup.enter="searchPost"
            type="text" 
            placeholder="输入帖子ID或关键词..."
          />
          <button @click="searchPost" :disabled="isLoading || !searchQuery.trim()">
            搜索
          </button>
        </div>
      </div>
      
      <!-- 帖子信息显示 -->
      <div class="post-info-section" v-if="selectedPost">
        <label>帖子信息：</label>
        <div class="post-info-card" :class="{ 'agent-post-card': selectedPost.is_agent_generated }">
          <div class="post-header">
            <div class="user-info">
              <span class="user-id">{{ selectedPost.user_id }}</span>
              <span class="post-time">{{ formatTime(selectedPost.timestamp) }}</span>
              <!-- Agent标识 -->
              <span v-if="selectedPost.is_agent_generated" class="agent-badge">🤖 AI仿真</span>
            </div>
            <div class="post-id">ID: {{ selectedPost.id }}</div>
          </div>
          
          <div class="post-content">
            {{ selectedPost.content || '无内容' }}
          </div>
          
          <div class="post-stats">
            <div class="stat-item">
              <span class="label">转发:</span>
              <span class="value">{{ selectedPost.repost_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">评论:</span>
              <span class="value">{{ selectedPost.comment_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">点赞:</span>
              <span class="value">{{ selectedPost.like_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 转播链分析-->
      <div class="repost-chain-section" v-if="repostChain.length > 0">
        <label>转播链分析({{ repostChain.length }} 个)</label>
        <div class="repost-chain-container">
          <div 
            v-for="(post, index) in repostChain.slice(0, 5)" 
            :key="post.id"
            class="repost-item"
            :class="{ 'is-root': index === 0 }"
          >
            <div class="repost-index">{{ index + 1 }}</div>
            <div class="repost-content">
              <div class="repost-user">{{ post.user_id }}</div>
              <div class="repost-text">{{ post.content ? post.content.substring(0, 80) + '...' : '转发' }}</div>
              <div class="repost-time">{{ formatTime(post.timestamp) }}</div>
            </div>
            <div class="repost-arrow" v-if="index < Math.min(4, repostChain.length - 1)">→</div>
          </div>
          
          <div v-if="repostChain.length > 5" class="more-reposts">
            还有 {{ repostChain.length - 5 }} 条转播..
          </div>
        </div>
      </div>
      
      <!-- 影响力分析-->
      <div class="influence-section" v-if="influenceData">
        <label>影响力分析：</label>
        <div class="influence-card">
          <div class="influence-item">
            <span class="label">传播深度:</span>
            <span class="value">{{ influenceData.depth || 0 }} 层</span>
          </div>
          <div class="influence-item">
            <span class="label">传播广度:</span>
            <span class="value">{{ influenceData.width || 0 }} 个分支</span>
          </div>
          <div class="influence-item">
            <span class="label">影响用户:</span>
            <span class="value">{{ influenceData.affected_users || 0 }} 人</span>
          </div>
          <div class="influence-item">
            <span class="label">影响力得分</span>
            <span class="value score">{{ influenceData.score ? influenceData.score.toFixed(2) : '0.00' }}</span>
          </div>
        </div>
      </div>
      
      <!-- 情感分析 -->
      <div class="sentiment-section" v-if="sentimentData">
        <label>情感分析结果</label>
        <div class="sentiment-card">
          <div class="sentiment-score">
            <div class="score-bar">
              <div 
                class="score-fill" 
                :class="getSentimentClass(sentimentData.polarity)"
                :style="{ width: Math.abs(sentimentData.polarity || 0) * 50 + '%' }"
              ></div>
            </div>
            <div class="score-label">
              {{ getSentimentLabel(sentimentData.polarity) }}
              ({{ sentimentData.polarity ? sentimentData.polarity.toFixed(2) : '0.00' }})
            </div>
          </div>
          
          <div class="sentiment-keywords" v-if="sentimentData.keywords">
            <div class="keywords-label">关键情感词：</div>
            <div class="keywords-list">
              <span 
                v-for="keyword in sentimentData.keywords.slice(0, 5)" 
                :key="keyword.word"
                class="keyword-tag"
                :class="keyword.sentiment"
              >
                {{ keyword.word }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="button-group">
        <button @click="analyzePost" :disabled="isLoading || !selectedPost">
          {{ isLoading ? '分析中..' : '深度分析' }}
        </button>
        <button @click="exportAnalysis" :disabled="!selectedPost">
          导出分析
        </button>
        <button @click="clearAnalysis">
          清除
        </button>
      </div>
      
      <div v-if="message" class="message" :class="messageType">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApiComplete.js'

const { fetchSinglePost, loading: isLoading } = useApi()

// 搜索和选择
const searchQuery = ref('')
const selectedPost = ref(null)

// 分析数据
const repostChain = ref([])
const influenceData = ref(null)
const sentimentData = ref(null)

// 消息显示
const message = ref('')
const messageType = ref('')

// 搜索帖子
const searchPost = async () => {
  if (!searchQuery.value.trim()) {
    showMessage('请输入搜索内容', 'error')
    return
  }
  
  try {
    const params = {
      query: searchQuery.value.trim()
    }
    
    const data = await fetchSinglePost(params)
    
    if (data && data.post) {
      selectedPost.value = data.post
      showMessage('帖子搜索成功', 'success')
      
      // 自动进行分析
      await analyzePost()
    } else {
      selectedPost.value = null
      clearAnalysisData()
      showMessage('未找到相关帖子', 'error')
    }
  } catch (error) {
    console.error('搜索帖子失败:', error)
    selectedPost.value = null
    clearAnalysisData()
    showMessage('搜索失败', 'error')
  }
}

// 分析帖子
const analyzePost = async () => {
  if (!selectedPost.value) {
    showMessage('请先选择一个帖子', 'error')
    return
  }
  
  try {
    const params = {
      post_id: selectedPost.value.id
    }
    
    // 这里可以调用多个分析API
    const analysisData = await fetchSinglePost({
      ...params,
      analysis_type: 'full'
    })
    
    if (analysisData) {
      // 处理转播链数据
      if (analysisData.repost_chain) {
        repostChain.value = analysisData.repost_chain
      }
      
      // 处理影响力数据
      if (analysisData.influence) {
        influenceData.value = analysisData.influence
      }
      
      // 处理情感数据
      if (analysisData.sentiment) {
        sentimentData.value = analysisData.sentiment
      }
      
      showMessage('帖子分析完成', 'success')
    } else {
      clearAnalysisData()
      showMessage('分析数据获取失败', 'error')
    }
  } catch (error) {
    console.error('帖子分析失败:', error)
    clearAnalysisData()
    showMessage('帖子分析失败', 'error')
  }
}

// 清除分析数据
const clearAnalysisData = () => {
  repostChain.value = []
  influenceData.value = null
  sentimentData.value = null
}

// 清除所有分析
const clearAnalysis = () => {
  selectedPost.value = null
  searchQuery.value = ''
  clearAnalysisData()
  showMessage('分析已清空', 'success')
}

// 导出分析结果
const exportAnalysis = () => {
  if (!selectedPost.value) {
    showMessage('没有可导出的分析数据', 'error')
    return
  }
  
  try {
    const analysisData = {
      post: selectedPost.value,
      repost_chain: repostChain.value,
      influence: influenceData.value,
      sentiment: sentimentData.value,
      analysis_time: new Date().toISOString()
    }
    
    const dataStr = JSON.stringify(analysisData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `post_analysis_${selectedPost.value.id}_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('分析结果已导出', 'success')
  } catch (error) {
    console.error('导出失败:', error)
    showMessage('导出失败', 'error')
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '未知时间'
  try {
    return new Date(timestamp).toLocaleString('zh-CN')
  } catch {
    return timestamp.toString()
  }
}

// 获取情感分类
const getSentimentClass = (polarity) => {
  if (polarity > 0.1) return 'positive'
  if (polarity < -0.1) return 'negative'
  return 'neutral'
}

// 获取情感标签
const getSentimentLabel = (polarity) => {
  if (polarity > 0.5) return '非常积极'
  if (polarity > 0.1) return '积极'
  if (polarity < -0.5) return '非常消极'
  if (polarity < -0.1) return '消极'
  return '中性'
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

// 暴露给父组件的方法
defineExpose({
  searchPostById: (postId) => {
    searchQuery.value = postId.toString()
    searchPost()
  },
  getSelectedPost: () => selectedPost.value,
  exportCurrentAnalysis: exportAnalysis
})
</script>

<style scoped>
.panel-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-section {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  background: #f9f9f9;
}

.search-input-group {
  display: flex;
  gap: 8px;
}

.search-input-group input {
  flex: 1;
  font-size: 12px;
  padding: 4px 8px;
  margin: 0;
}

.search-input-group button {
  flex-shrink: 0;
  font-size: 12px;
  padding: 4px 12px;
}

.post-info-section,
.repost-chain-section,
.influence-section,
.sentiment-section {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
}

.post-info-section label,
.repost-chain-section label,
.influence-section label,
.sentiment-section label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: bold;
}

.post-info-card {
  background: #f9f9f9;
  border-radius: 4px;
  padding: 8px;
}

/* Agent帖子卡片样式 */
.agent-post-card {
  background: linear-gradient(135deg, #fff5f5 0%, #f9f9f9 100%) !important;
  border: 2px solid #e53e3e !important;
  box-shadow: 0 2px 8px rgba(229, 62, 62, 0.15) !important;
}

.agent-badge {
  background: #e53e3e;
  color: white;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: bold;
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #eee;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-id {
  font-weight: bold;
  color: #333;
  font-size: 12px;
}

.post-time {
  font-size: 10px;
  color: #666;
}

.post-id {
  font-size: 10px;
  color: #999;
}

.post-content {
  margin: 6px 0;
  color: #333;
  font-size: 12px;
  line-height: 1.4;
  max-height: 60px;
  overflow-y: auto;
}

.post-stats {
  display: flex;
  gap: 12px;
  font-size: 10px;
}

.stat-item {
  display: flex;
  gap: 4px;
}

.stat-item .label {
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  color: #333;
}

.repost-chain-container {
  max-height: 200px;
  overflow-y: auto;
}

.repost-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px;
  margin-bottom: 4px;
  border-radius: 4px;
  background: #f9f9f9;
}

.repost-item.is-root {
  background: #e3f2fd;
  border: 1px solid #1976d2;
}

.repost-index {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1976d2;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
}

.repost-content {
  flex: 1;
  min-width: 0;
}

.repost-user {
  font-weight: bold;
  color: #333;
  font-size: 11px;
}

.repost-text {
  color: #666;
  font-size: 10px;
  margin: 2px 0;
  word-break: break-word;
}

.repost-time {
  color: #999;
  font-size: 9px;
}

.repost-arrow {
  flex-shrink: 0;
  color: #1976d2;
  font-size: 16px;
  font-weight: bold;
}

.more-reposts {
  text-align: center;
  color: #666;
  font-size: 11px;
  font-style: italic;
  padding: 8px;
}

.influence-card {
  background: #f9f9f9;
  border-radius: 4px;
  padding: 8px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.influence-item {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  padding: 2px 0;
}

.influence-item .label {
  color: #666;
}

.influence-item .value {
  font-weight: bold;
  color: #333;
}

.influence-item .value.score {
  color: #1976d2;
}

.sentiment-card {
  background: #f9f9f9;
  border-radius: 4px;
  padding: 8px;
}

.sentiment-score {
  margin-bottom: 8px;
}

.score-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}

.score-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.score-fill.positive {
  background: linear-gradient(90deg, #4caf50, #2e7d32);
}

.score-fill.negative {
  background: linear-gradient(90deg, #f44336, #c62828);
}

.score-fill.neutral {
  background: linear-gradient(90deg, #9e9e9e, #616161);
}

.score-label {
  font-size: 11px;
  color: #333;
  text-align: center;
}

.sentiment-keywords {
  border-top: 1px solid #eee;
  padding-top: 6px;
}

.keywords-label {
  font-size: 10px;
  color: #666;
  margin-bottom: 4px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword-tag {
  background: #e0e0e0;
  color: #333;
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 9px;
}

.keyword-tag.positive {
  background: #c8e6c9;
  color: #2e7d32;
}

.keyword-tag.negative {
  background: #ffcdd2;
  color: #c62828;
}

.button-group {
  display: flex;
  gap: 6px;
}

.button-group button {
  flex: 1;
  font-size: 11px;
  padding: 4px 8px;
}

.message {
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 11px;
  text-align: center;
}

.message.success {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #4caf50;
}

.message.error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #f44336;
}

h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
  border-bottom: 2px solid #1976d2;
  padding-bottom: 6px;
}

button:disabled {
  background: #ccc !important;
  cursor: not-allowed;
}
</style>
