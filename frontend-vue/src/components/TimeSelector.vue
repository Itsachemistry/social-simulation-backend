<template>
  <div id="time-selector-wrapper">
    <div id="time-selector">
      <input 
        ref="startTimeInput"
        type="text" 
        id="start-time" 
        readonly
        :value="formattedStartTime"
      >
      <input 
        ref="endTimeInput"
        type="text" 
        id="end-time" 
        readonly
        :value="formattedEndTime"
      >
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import flatpickr from 'flatpickr'
import { Chinese } from 'flatpickr/dist/l10n/zh.js'

// Props
const props = defineProps({
  startTime: {
    type: Date,
    default: () => new Date(Date.now() - 24 * 60 * 60 * 1000)
  },
  endTime: {
    type: Date,
    default: () => new Date()
  }
})

// Emits
const emit = defineEmits(['time-change'])

// Refs
const startTimeInput = ref(null)
const endTimeInput = ref(null)

// 内部状态
const currentStartTime = ref(props.startTime)
const currentEndTime = ref(props.endTime)

// 计算属性
const formattedStartTime = computed(() => {
  return currentStartTime.value?.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }) || ''
})

const formattedEndTime = computed(() => {
  return currentEndTime.value?.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit', 
    hour: '2-digit',
    minute: '2-digit'
  }) || ''
})

// flatpickr 实例
let startTimePicker = null
let endTimePicker = null

// 通用配置
const commonConfig = {
  locale: Chinese,
  dateFormat: 'Y-m-d H:i',
  enableTime: true,
  time_24hr: true,
  minuteIncrement: 1,
  allowInput: false,
  clickOpens: true,
  // 禁用导航箭头，移除大箭头元素
  prevArrow: '',
  nextArrow: ''
}

// 发射时间变化事件
const emitTimeChange = () => {
  emit('time-change', {
    start: currentStartTime.value,
    end: currentEndTime.value
  })
}

onMounted(() => {
  // 初始化开始时间选择器
  startTimePicker = flatpickr(startTimeInput.value, {
    ...commonConfig,
    defaultDate: currentStartTime.value,
    maxDate: currentEndTime.value,
    onChange: (selectedDates) => {
      if (selectedDates.length > 0) {
        currentStartTime.value = selectedDates[0]
        if (endTimePicker) {
          endTimePicker.set('minDate', selectedDates[0])
        }
        emitTimeChange()
      }
    }
  })

  // 初始化结束时间选择器 
  endTimePicker = flatpickr(endTimeInput.value, {
    ...commonConfig,
    defaultDate: currentEndTime.value,
    minDate: currentStartTime.value,
    onChange: (selectedDates) => {
      if (selectedDates.length > 0) {
        currentEndTime.value = selectedDates[0]
        if (startTimePicker) {
          startTimePicker.set('maxDate', selectedDates[0])
        }
        emitTimeChange()
      }
    }
  })
})
</script>
