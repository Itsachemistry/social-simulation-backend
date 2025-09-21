import { ref, reactive, computed } from 'vue'

export function useTimeRange() {
  // 时间范围状态
  const timeRange = reactive({
    start: null,
    end: null
  })

  // 更新时间范围
  const updateTimeRange = (newRange) => {
    if (newRange.start) {
      timeRange.start = newRange.start
    }
    if (newRange.end) {
      timeRange.end = newRange.end
    }
  }

  // 重置为默认时间范围
  const resetTimeRange = () => {
    const now = new Date()
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    
    timeRange.start = yesterday
    timeRange.end = now
  }

  // 格式化时间范围为字符串
  const formatTimeRange = computed(() => {
    if (!timeRange.start || !timeRange.end) return ''
    
    const formatDate = (date) => {
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    return `${formatDate(timeRange.start)} - ${formatDate(timeRange.end)}`
  })

  // 检查时间范围是否有效
  const isValidTimeRange = computed(() => {
    return timeRange.start && timeRange.end && timeRange.start <= timeRange.end
  })

  // 获取时间跨度（毫秒）
  const timeSpan = computed(() => {
    if (!isValidTimeRange.value) return 0
    return timeRange.end.getTime() - timeRange.start.getTime()
  })

  // 获取时间跨度（小时）
  const timeSpanHours = computed(() => {
    return Math.round(timeSpan.value / (1000 * 60 * 60))
  })

  // 获取时间跨度（天）
  const timeSpanDays = computed(() => {
    return Math.round(timeSpan.value / (1000 * 60 * 60 * 24))
  })

  return {
    timeRange,
    updateTimeRange,
    resetTimeRange,
    formatTimeRange,
    isValidTimeRange,
    timeSpan,
    timeSpanHours,
    timeSpanDays
  }
}
