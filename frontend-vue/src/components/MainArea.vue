<template>
  <div id="main">
    <!-- 时间轴区域-->
    <TimelineArea 
      :timeline="timeline"
      @timeline-action="$emit('timeline-action', $event)"
    />
    
    <!-- 功能面板控制 -->
    <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">
      Checkbox Group
    </div>
    <PanelSelector 
      :selected-panels="selectedPanels"
      @panel-change="$emit('panel-change', $event)"
    />
    
    <!-- 功能面板容器 -->
    <div id="function-panels">
      <component 
        v-for="panel in activePanels"
        :key="panel"
        :is="getPanelComponent(panel)"
        class="panel-component"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TimelineArea from './TimelineArea.vue'
import PanelSelector from './PanelSelector.vue'
import AgentPanel from './AgentPanel.vue'
import SimulationPanel from './SimulationPanel.vue'
import HistogramPanel from './HistogramPanel.vue'
import AttitudePanel from './AttitudePanel.vue'
import WordcloudPanel from './WordcloudPanel.vue'
import TreePanel from './TreePanel.vue'
import SinglePanel from './SinglePanel.vue'

// Props
const props = defineProps({
  timeline: {
    type: Array,
    default: () => []
  },
  selectedPanels: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['panel-change', 'timeline-action'])

// 计算当前激活的面板（最后个）
const activePanels = computed(() => {
  return props.selectedPanels.slice(0, 3)
})

// 获取面板组件
const getPanelComponent = (panel) => {
  const componentMap = {
    'agent-setup': AgentPanel,
    'simulation': SimulationPanel,
    'histogram': HistogramPanel,
    'attitude': AttitudePanel,
    'wordcloud': WordcloudPanel,
    'tree': TreePanel,
    'single': SinglePanel
  }
  return componentMap[panel]
}
</script>

<style scoped>
.panel-component {
  flex: 0 0 calc(33.333% - 11px);
  width: calc(33.333% - 11px);
  height: 100%;
  min-width: 0;
}
</style>
