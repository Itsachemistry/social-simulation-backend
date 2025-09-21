<template>
  <div id="post-list">
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中..
    </div>
    
    <div v-else-if="posts.length === 0" class="no-posts">
      暂无帖子数据
    </div>
    
    <div 
      v-else
      v-for="post in posts" 
      :key="post.id || post.mid"
      :class="['post-item', { 'agent-post': post.is_agent_generated }]"
    >
      <!-- 用户信息 -->
      <div class="user-info">
        <img 
          :src="post.avatar || DEFAULT_AVATAR" 
          :alt="post.author_id || post.uid"
          class="avatar"
          @error="handleImageError"
        >
        <span class="user-id">{{ post.author_id || post.uid }}</span>
        <!-- Agent标识 -->
        <span v-if="post.is_agent_generated" class="agent-badge">🤖 AI</span>
      </div>
      
      <!-- 帖子内容 -->
      <div class="post-content">
        {{ post.content || post.text }}
      </div>
      
      <!-- 时间和统计-->
      <div class="post-meta">
        <div class="post-time">
          {{ formatPostTime(post.timestamp || post.t) }}
        </div>
        <div class="post-actions-inline">
          <span class="action-icon" :title="`评论数 ${post.comments_count || 0}`">
            <i class="fas fa-comment"></i>
          </span>
          <span class="action-icon" :title="`转发数 ${post.reposts_count || 0}`">
            <i class="fas fa-retweet"></i>
          </span>
          <span class="action-icon" :title="`点赞数 ${post.attitudes_count || 0}`">
            <i class="fas fa-heart"></i>
          </span>
        </div>
      </div>
      
      <!-- 标签 -->
      <div v-if="post.tags && post.tags.length > 0" class="post-tags">
        <span 
          v-for="tag in post.tags" 
          :key="tag"
          class="tag"
          @click="$emit('tag-click', tag)"
        >
          #{{ tag }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useApi } from '../composables/useApiComplete'
import { useTimeRange } from '../composables/useApiComplete'

// Props
const props = defineProps({
  searchTag: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['tag-click'])

// 状态
const posts = ref([])
const { loading, error, getPosts } = useApi()
const { timeRange } = useTimeRange()

// 默认头像
const DEFAULT_AVATAR = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40NzcgMiAyIDYuNDc3IDIgMTJzNC40NzcgMTAgMTAgMTAgMTAtNC40NzcgMTAtMTBTMTcuNTIzIDIgMTIgMnptMCAyYzQuNDE4IDAgOCAzLjU4MiA4IDhzLTMuNTgyIDgtOCA4LTgtMy41ODItOC04IDMuNTgyLTggOC04eiIgZmlsbD0iIzk5OSIvPjwvc3ZnPg=="

// 获取帖子数据
const fetchPosts = async () => {
  try {
    console.log('正在获取帖子数据...', {
      startTime: timeRange.value.start,
      endTime: timeRange.value.end,
      tags: props.searchTag
    })
    
    const data = await getPosts(
      timeRange.value.start,
      timeRange.value.end,
      props.searchTag
    )
    
    console.log('获取到帖子数据', data)
    posts.value = data.posts || data || []
  } catch (err) {
    console.error('获取帖子数据失败:', err)
    posts.value = []
  }
}

// 处理图片加载错误
const handleImageError = (event) => {
  event.target.src = DEFAULT_AVATAR
}

// 格式化时间
const formatPostTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp)
  let hour = date.getHours()
  const minute = date.getMinutes().toString().padStart(2, '0')
  const ampm = hour >= 12 ? 'PM' : 'AM'
  hour = hour % 12
  if (hour === 0) hour = 12
  
  return `${hour}:${minute} ${ampm}`
}

// 监听时间范围变化
watch(timeRange, fetchPosts, { deep: true })

// 监听搜索标签变化
watch(() => props.searchTag, fetchPosts)

// 初始化
onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.loading, .no-posts {
  text-align: center;
  padding: 20px;
  color: #666;
}

/* Agent帖子样式 */
.agent-post {
  border-left: 4px solid #e53e3e !important;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%) !important;
  box-shadow: 0 2px 8px rgba(229, 62, 62, 0.1) !important;
}

.agent-badge {
  background: #e53e3e;
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: bold;
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.post-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  background: #e6f7ff;
  color: #1976d2;
  border: 1px solid #91d5ff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.tag:hover {
  background: #bae7ff;
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
</style>
