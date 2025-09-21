<template>
  <div id="container">
    <!-- 左侧边栏 -->
    <SideBar />
    
    <!-- 主区域 -->
    <main id="main">
      <!-- 时间线区域 -->
      <div id="timeline-bar">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
          <span id="timeline-label">时间线:</span>
          <canvas id="timeline" width="600" height="100"></canvas>
        </div>
        <div id="timeline-controls">
          <button class="red">开始</button>
          <button class="blue">暂停</button>
          <button class="gray">重置</button>
          <button class="darkgray">快进</button>
        </div>
      </div>
      
      <!-- 功能面板选择器 -->
      <div id="function-checkbox">
        <label>
          <input type="checkbox" v-model="panels.simulation">
          仿真配置
        </label>
        <label>
          <input type="checkbox" v-model="panels.agent">
          智能体管理
        </label>
        <label>
          <input type="checkbox" v-model="panels.histogram">
          数据分布
        </label>
        <label>
          <input type="checkbox" v-model="panels.attitude">
          态度分析 (Canvas)
        </label>
        <label>
          <input type="checkbox" v-model="panels.attitudeVega">
          态度分析 (Vega-Lite)
        </label>
        <label>
          <input type="checkbox" v-model="panels.wordcloud">
          词云分析
        </label>
        <label>
          <input type="checkbox" v-model="panels.tree">
          转播树
        </label>
        <label>
          <input type="checkbox" v-model="panels.single">
          单帖分析
        </label>
        <label>
          <input type="checkbox" v-model="panels.officialStatement">
          �️ 官方声明干预
        </label>
      </div>
      
      <!-- 功能面板 -->
      <div id="function-panels">
        <SimulationPanel v-if="panels.simulation" />
        <AgentPanel v-if="panels.agent" />
        <HistogramPanel v-if="panels.histogram" />
        <AttitudePanel v-if="panels.attitude" />
        <AttitudePanelVega v-if="panels.attitudeVega" />
        <WordcloudPanel v-if="panels.wordcloud" />
        <TreePanel v-if="panels.tree" />
        <SinglePanel v-if="panels.single" />
        <OfficialStatementDemo v-if="panels.officialStatement" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import SideBar from './components/SideBar.vue'
import SimulationPanel from './components/SimulationPanel.vue'
import AgentPanel from './components/AgentPanel.vue'
import HistogramPanel from './components/HistogramPanel.vue'
import AttitudePanel from './components/AttitudePanel.vue'
import AttitudePanelVega from './components/AttitudePanelVega.vue'
import WordcloudPanel from './components/WordcloudPanel.vue'
import TreePanel from './components/TreePanel.vue'
import SinglePanel from './components/SinglePanel.vue'
import OfficialStatementDemo from './views/OfficialStatementDemo.vue'

// 面板显示控制
const panels = reactive({
  simulation: false,
  agent: false,
  histogram: false,
  attitude: false,
  attitudeVega: true, // 默认显示 Vega-Lite 版本
  wordcloud: false,
  tree: true, // 默认显示转播树
  single: false,
  hurricane: false,
  officialStatement: false
})
</script>
