<template>
  <div id="sidebar">
    <!-- 时间选择器-->
    <TimeSelector />
    
    <!-- 主题内容 -->
    <div id="topic-content">
      <div class="section-title topic-title">主题内容</div>
      <div class="topic-placeholder">
        {{ topicContent }}
      </div>
    </div>
    
    <!-- 帖文内容 -->
    <div class="section-title post-title">帖文内容</div>
    <PostList :search-tag="searchTag" />
    
    <!-- 搜索框-->
    <div id="search-bar">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="搜索帖子内容..."
        @keyup.enter="handleSearch"
      />
      <button id="search-btn" @click="handleSearch">搜索</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TimeSelector from './TimeSelector.vue'
import PostList from './PostList.vue'
import { useApi } from '../composables/useApiComplete'

const searchQuery = ref('')
const searchTag = ref('')
const topicContent = ref('')
const { getTopicSummary } = useApi()

// 获取主题内容
const fetchTopicContent = async () => {
  try {
    const data = await getTopicSummary()
    topicContent.value = data.summary || data.content || '点击时间范围加载主题数据'
  } catch (error) {
    console.error('获取主题内容失败:', error)
    topicContent.value = '加载主题内容失败'
  }
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    console.log('搜索:', searchQuery.value)
    searchTag.value = searchQuery.value.trim()
  }
}

onMounted(() => {
  fetchTopicContent()
})
</script>

<style scoped>
#topic-content {
  min-height: 12vh;
  margin-bottom: 10px;
  box-sizing: border-box;
}

.topic-placeholder {
  padding: 20px;
  text-align: center;
  color: #999;
  font-style: italic;
  border: 1px dashed #ddd;
  border-radius: 4px;
  margin-top: 8px;
}

#search-bar {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

#search-bar input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

#search-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

#search-btn:hover {
  background: #1565c0;
}
</style>
