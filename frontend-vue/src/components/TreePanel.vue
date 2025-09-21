<template>
  <div class="tree-panel">
    <h3>转播树分析</h3>
    
    <!-- 转播树说明 -->
    <div class="tree-description" style="margin-bottom: 15px; padding: 10px; background: #f0f8ff; border-radius: 5px; font-size: 12px; color: #666;">
      <!-- 数据源选择 -->
      <div class="data-source-section" style="margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 4px; border: 1px solid #ddd;">
        <label style="font-weight: bold; margin-bottom: 5px; display: block;">🎯 数据源选择：</label>
        <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
          <div style="display: flex; gap: 10px;">
            <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
              <input type="radio" v-model="dataSource" value="original" @change="onDataSourceChange" />
              <span>📊 仅原始数据</span>
            </label>
            <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
              <input type="radio" v-model="dataSource" value="merged" @change="onDataSourceChange" />
              <span>🤖 融合Agent仿真</span>
            </label>
          </div>
          <div v-if="dataSource === 'merged'" style="display: flex; align-items: center; gap: 5px;">
            <label style="font-size: 11px;">选择仿真文件:</label>
            <select v-model="selectedAgentFile" @change="onDataSourceChange" style="font-size: 11px; padding: 2px 4px;">
              <option value="">请选择...</option>
              <option v-for="file in agentFiles" :key="file.value" :value="file.value">
                {{ file.label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <p><strong>🌟 智能自适应径向转播树：</strong></p>
      <ul style="margin: 5px 0; padding-left: 20px;">
        <li>🔵 中心节点：信息扩散源头，深蓝色实心圆</li>
        <li>⭕ 普通节点：极简空心圆圈，淡蓝色描边</li>
        <li>� Agent帖子：AI仿真生成的帖子，鲜红色粗描边</li>
        <li>�🟢 补充根节点：来自pid=2的特殊根节点，绿色描边</li>
        <li>🟠 孤立根节点：独立的转发起点，橙色描边</li>
        <li>� 放射布局：从中心向外呈同心圆层次扩散</li>
        <li>🌊 汇聚扇形：多条连线先汇聚后散开，形成内凹扇形效果</li>
        <li>� 高亮节点：高转发数节点显示为橙红色描边</li>
        <li>📏 层级清晰：足够的层间距离，避免视觉混乱</li>
      </ul>
      <p><strong>🖱️ 交互操作：</strong>滚轮缩放，拖拽平移，点击选择节点（红色高亮）</p>
      <p><strong>⏰ 时间筛选：</strong>根据左侧时间选择器自动筛选指定时间范围内的转播数据</p>
      <button @click="loadTreeData" style="margin-top: 8px; padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">
        🔄 刷新转播树
      </button>
    </div>
    
    <div class="panel-content">
      <!-- 树状图画布-->
      <div class="tree-container">
        <canvas 
          ref="treeCanvas" 
          :width="canvasWidth" 
          :height="canvasHeight"
          @mousedown="onMouseDown"
          @mousemove="onMouseMove"
          @mouseup="onMouseUp"
          @wheel="onWheel"
          @click="onCanvasClick"
        ></canvas>
        
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载转播树中...</div>
        </div>
        
        <div v-if="!isLoading && !hasTreeData" class="no-data">
          暂无转播树数据
        </div>
      </div>
      
      <!-- 树状图信息-->
      <div class="tree-info-section" v-if="treeStats">
        <label>树状图统计：</label>
        <div class="tree-stats">
          <div class="stat-item">
            <span class="label">总节点数：</span>
            <span class="value">{{ treeStats.totalNodes }}</span>
          </div>
          <div class="stat-item">
            <span class="label">最大深度：</span>
            <span class="value">{{ treeStats.maxDepth }}</span>
          </div>
          <div class="stat-item">
            <span class="label">根节点数：</span>
            <span class="value">{{ treeStats.rootNodes }}</span>
          </div>
          <div class="stat-item">
            <span class="label">最大扇出：</span>
            <span class="value">{{ treeStats.maxFanout }}</span>
          </div>
          <div class="stat-item" v-if="treeStats.supplementaryRoots !== undefined">
            <span class="label">补充根节点：</span>
            <span class="value">{{ treeStats.supplementaryRoots }}</span>
          </div>
          <div class="stat-item" v-if="treeStats.isolatedRoots !== undefined">
            <span class="label">孤立根节点：</span>
            <span class="value">{{ treeStats.isolatedRoots }}</span>
          </div>
          <div class="stat-item" v-if="treeStats.totalEdges !== undefined">
            <span class="label">连接边数：</span>
            <span class="value">{{ treeStats.totalEdges }}</span>
          </div>
        </div>
      </div>
      
      <!-- 节点详情 -->
      <div class="node-details-section" v-if="selectedNode">
        <label>节点详情：</label>
        <div class="node-detail-card">
          <div class="detail-row">
            <span class="label">ID:</span>
            <span class="value">{{ selectedNode.id }}</span>
          </div>
          <div class="detail-row">
            <span class="label">用户:</span>
            <span class="value">{{ selectedNode.user_id || selectedNode.author_id || '未知' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">深度:</span>
            <span class="value">{{ selectedNode.depth || 0 }}</span>
          </div>
          <div class="detail-row">
            <span class="label">子节点:</span>
            <span class="value">{{ getChildrenCount(selectedNode.id) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">时间:</span>
            <span class="value">{{ formatTime(selectedNode.timestamp) }}</span>
          </div>
          <div class="detail-row" v-if="selectedNode.content">
            <span class="label">内容:</span>
            <span class="value content">{{ selectedNode.content.substring(0, 100) }}...</span>
          </div>
          <div class="detail-row" v-if="selectedNode.reposts_count !== undefined">
            <span class="label">转发数:</span>
            <span class="value">{{ selectedNode.reposts_count }}</span>
          </div>
        </div>
      </div>
      
      <!-- 控制区域 -->
      <div class="controls-section">
        <div class="zoom-controls">
          <label>缩放控制器</label>
          <div class="control-buttons">
            <button @click="zoomIn" :disabled="zoom >= maxZoom">放大</button>
            <button @click="zoomOut" :disabled="zoom <= minZoom">缩小</button>
            <button @click="resetView">重置视图</button>
            <button @click="fitToScreen">适应屏幕</button>
          </div>
        </div>
        
        <div class="display-options">
          <label>
            <input type="checkbox" v-model="showNodeLabels" @change="redrawTree">
            显示节点标签
          </label>
          <label>
            <input type="checkbox" v-model="showEdgeLabels" @change="redrawTree">
            显示边标签
          </label>
          <label>
            <input type="checkbox" v-model="colorByDepth" @change="redrawTree">
            按深度着色
          </label>
          <label>
            <input type="checkbox" v-model="performanceMode" @change="redrawTree">
            性能模式（大数据集推荐）
          </label>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="button-group">
        <button @click="loadTreeData" :disabled="isLoading">
          {{ isLoading ? '加载中..' : '刷新数据' }}
        </button>
        <button @click="exportTreeImage" :disabled="!hasTreeData">
          导出图片
        </button>
        <button @click="exportTreeData" :disabled="!hasTreeData">
          导出数据
        </button>
      </div>
      
      <div v-if="message" class="message" :class="messageType">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useApi } from '../composables/useApiComplete.js'
import { useTimeRange } from '../composables/useApiComplete.js'

const { getTree, getVisualizationOptions, loading: isLoading } = useApi()
const { timeRange } = useTimeRange()

// 数据源选择状态
const dataSource = ref('original')  // 'original' 或 'merged'
const selectedAgentFile = ref('')
const agentFiles = ref([])

// 画布引用
const treeCanvas = ref(null)

// 画布配置
const canvasWidth = ref(320)
const canvasHeight = ref(240)

// 树状图数据
const treeData = ref(null)
const treeStats = ref(null)
const selectedNode = ref(null)
const hasTreeData = ref(false)

// 视图控制
const zoom = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const minZoom = ref(0.1)
const maxZoom = ref(3)

// 显示选项
const showNodeLabels = ref(true)
const showEdgeLabels = ref(false)
const colorByDepth = ref(true)
const performanceMode = ref(false)  // 性能模式：简化渲染以提升大数据集性能

// 鼠标交互
const isDragging = ref(false)
const lastMouseX = ref(0)
const lastMouseY = ref(0)
const dragThrottle = ref(null)  // 拖拽节流控制

// 消息显示
const message = ref('')
const messageType = ref('')

// 节点布局缓存
const nodePositions = ref(new Map())

// 加载可视化配置选项
const loadVisualizationOptions = async () => {
  try {
    const options = await getVisualizationOptions()
    agentFiles.value = options.agent_posts_files || []
    console.log('可视化配置选项加载成功:', options)
  } catch (error) {
    console.error('加载可视化配置选项失败:', error)
    showMessage('加载配置选项失败', 'error')
  }
}

// 数据源变化处理
const onDataSourceChange = () => {
  console.log('数据源变化:', { dataSource: dataSource.value, selectedAgentFile: selectedAgentFile.value })
  
  // 如果切换到融合模式但没有选择文件，选择最新的文件
  if (dataSource.value === 'merged' && !selectedAgentFile.value && agentFiles.value.length > 0) {
    selectedAgentFile.value = agentFiles.value[0].value
  }
  
  // 自动重新加载数据
  loadTreeData()
}

// 加载树状图数据
const loadTreeData = async () => {
  try {
    const start = timeRange.value?.start || '2016-01-01T00:00:00'
    const end = timeRange.value?.end || '2016-12-31T23:59:59'
    
    console.log('转播树加载开始:', { 
      start, 
      end, 
      dataSource: dataSource.value, 
      agentFile: selectedAgentFile.value 
    })
    
    const data = await getTree(start, end, dataSource.value, selectedAgentFile.value)
    console.log('原始转播树数据:', data)
    
    // 处理后端返回的树形数据，转换为节点-边格式
    if (data && data.tree && data.tree.children && data.tree.children.length > 0) {
      console.log('转播树数据验证通过，开始处理...')
      console.log('根节点数量:', data.tree.children.length)
      console.log('第一个根节点:', data.tree.children[0])
      
      // 显示后端返回的元数据信息
      if (data.tree.meta) {
        console.log('转播树元数据:', data.tree.meta)
        showMessage(`加载成功: 共${data.tree.meta.total_nodes}个节点，最大深度${data.tree.meta.max_depth}层`, 'success')
      }
      
      const processedData = convertTreeToNodesEdges(data.tree)
      console.log('处理后的数据:', processedData)
      console.log('节点数量:', processedData.nodes.length)
      console.log('边数量:', processedData.edges.length)
      
      treeData.value = processedData
      calculateTreeStats(processedData)
      layoutNodesRadial(processedData)  // 使用自适应角度分配的放射状布局
      
      // 调试：输出前几个一级节点的子树大小和角度分配
      const firstLevelNodes = processedData.nodes.filter(n => n.depth === 1).slice(0, 5)
      console.log('🎯 前5个一级节点的子树分析:')
      firstLevelNodes.forEach(node => {
        const pos = nodePositions.value.get(node.id)
        const childrenCount = processedData.edges.filter(e => e.source === node.id).length
        if (pos) {
          console.log(`节点 ${node.id}: 直接子节点=${childrenCount}, 分配角度=${(pos.allocatedAngle * 180 / Math.PI).toFixed(1)}°`)
        }
      })
      
      redrawTree()
      hasTreeData.value = true
    } else {
      console.log('转播树数据验证失败:', {
        hasData: !!data,
        hasTree: !!(data && data.tree),
        hasChildren: !!(data && data.tree && data.tree.children),
        childrenLength: data && data.tree && data.tree.children ? data.tree.children.length : 0
      })
      treeData.value = null
      treeStats.value = null
      hasTreeData.value = false
      clearCanvas()
      showMessage('暂无转播树数据', 'error')
    }
  } catch (error) {
    console.error('加载转播树失败', error)
    treeData.value = null
    treeStats.value = null
    hasTreeData.value = false
    clearCanvas()
    showMessage('加载转播树失败: ' + error.message, 'error')
  }
}

// 将后端的树形数据转换为节点-边列表格式
const convertTreeToNodesEdges = (tree) => {
  const nodes = []
  const edges = []
  
  // 添加虚拟根节点（0号节点）
  const virtualRoot = {
    id: 'virtual_root',
    content: '转播树根节点',
    author_id: 'system',
    x: 0,
    y: 0,
    depth: 0,
    reposts_count: 0,
    attitudes_count: 0,
    comments_count: 0,
    isVirtual: true
  }
  nodes.push(virtualRoot)
  
  // 递归处理树结构
  const processNode = (node, depth = 1, parentId = 'virtual_root') => {
    // 添加当前节点
    const currentNode = {
      id: node.id,
      content: node.content || '',
      author_id: node.author_id || '',
      reposts_count: node.reposts_count || 0,
      attitudes_count: node.attitudes_count || 0,
      comments_count: node.comments_count || 0,
      timestamp: node.timestamp || 0,
      depth: depth,
      x: 0,  // 稍后在布局函数中设置
      y: 0,
      isVirtual: false,
      // 保留后端的节点类型信息
      is_supplementary_root: node.is_supplementary_root || false,
      is_isolated_root: node.is_isolated_root || false,
      is_agent_generated: node.is_agent_generated || false,  // 保留Agent生成标记
      direct_reposts: node.direct_reposts || 0
    }
    nodes.push(currentNode)
    
    // 添加边（从父节点到当前节点）
    if (parentId) {
      edges.push({
        source: parentId,
        target: node.id,
        from: parentId,
        to: node.id
      })
    }
    
    // 递归处理子节点
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => {
        processNode(child, depth + 1, node.id)
      })
    }
  }
  
  // 处理所有根节点（第一层节点）
  if (tree.children) {
    tree.children.forEach(rootNode => {
      processNode(rootNode, 1, 'virtual_root')
    })
  }
  
  return { nodes, edges }
}

// 计算树状图统计信息
const calculateTreeStats = (data) => {
  const nodes = data.nodes || []
  const edges = data.edges || []
  
  // 计算统计信息
  const depths = nodes.map(node => node.depth || 0)
  const fanouts = new Map()
  
  edges.forEach(edge => {
    const source = edge.source || edge.from
    fanouts.set(source, (fanouts.get(source) || 0) + 1)
  })
  
  // 计算不同类型的根节点
  const supplementaryRoots = nodes.filter(node => 
    node.depth === 1 && node.is_supplementary_root
  ).length
  
  const isolatedRoots = nodes.filter(node => 
    node.depth === 1 && node.is_isolated_root
  ).length
  
  treeStats.value = {
    totalNodes: nodes.length,
    maxDepth: Math.max(...depths, 0),
    rootNodes: nodes.filter(node => (node.depth || 0) === 1).length,  // 实际根节点数
    maxFanout: fanouts.size > 0 ? Math.max(...fanouts.values()) : 0,
    supplementaryRoots: supplementaryRoots,  // 补充根节点数(pid=2)
    isolatedRoots: isolatedRoots,            // 孤立根节点数
    totalEdges: edges.length                 // 总边数
  }
}

// 计算子树大小（递归计算每个节点的所有后代节点数量）
const calculateSubtreeSize = (nodeId, childrenMap, cache = new Map()) => {
  if (cache.has(nodeId)) {
    return cache.get(nodeId)
  }
  
  const children = childrenMap.get(nodeId) || []
  let size = 1 // 自身算1个节点
  
  children.forEach(childId => {
    size += calculateSubtreeSize(childId, childrenMap, cache)
  })
  
  cache.set(nodeId, size)
  return size
}

// 放射状布局节点位置 - 基于子树大小的自适应角度分配
const layoutNodesRadial = (data) => {
  const nodes = data.nodes || []
  const edges = data.edges || []
  
  // 构建树结构
  const nodeMap = new Map()
  const childrenMap = new Map()
  
  nodes.forEach(node => {
    nodeMap.set(node.id, node)
    childrenMap.set(node.id, [])
  })
  
  edges.forEach(edge => {
    const source = edge.source || edge.from
    const target = edge.target || edge.to
    if (childrenMap.has(source)) {
      childrenMap.get(source).push(target)
    }
  })
  
  // 计算每个节点的子树大小
  const subtreeSizes = new Map()
  nodes.forEach(node => {
    const size = calculateSubtreeSize(node.id, childrenMap)
    subtreeSizes.set(node.id, size)
  })
  
  const positions = new Map()
  const centerX = canvasWidth.value / 2
  const centerY = canvasHeight.value / 2
  
  // 虚拟根节点位于中心
  positions.set('virtual_root', { x: centerX, y: centerY })
  
  // 按深度分层处理
  const layers = new Map()
  nodes.forEach(node => {
    const depth = node.depth || 0
    if (!layers.has(depth)) {
      layers.set(depth, [])
    }
    layers.get(depth).push(node)
  })
  
  // 计算每层的半径
  const maxDepth = Math.max(...layers.keys(), 0)
  const minRadius = 70   // 第一层半径
  const radiusStep = 90  // 每层间距离增加
  
  // 为每层分配位置
  layers.forEach((layerNodes, depth) => {
    if (depth === 0) {
      // 跳过虚拟根节点
      return
    }
    
    const radius = minRadius + (depth - 1) * radiusStep
    
    if (depth === 1) {
      // 第一层：基于子树大小分配角度空间
      const totalSubtreeSize = layerNodes.reduce((sum, node) => sum + subtreeSizes.get(node.id), 0)
      
      let currentAngle = 0
      layerNodes.forEach(node => {
        const nodeSubtreeSize = subtreeSizes.get(node.id)
        // 根据子树大小分配角度比例
        const angleRatio = nodeSubtreeSize / totalSubtreeSize
        const allocatedAngle = angleRatio * 2 * Math.PI
        
        // 节点放在分配角度的中心位置
        const nodeAngle = currentAngle + allocatedAngle / 2
        const x = centerX + radius * Math.cos(nodeAngle)
        const y = centerY + radius * Math.sin(nodeAngle)
        
        positions.set(node.id, { 
          x, 
          y, 
          angle: nodeAngle,
          startAngle: currentAngle,
          endAngle: currentAngle + allocatedAngle,
          allocatedAngle: allocatedAngle
        })
        
        currentAngle += allocatedAngle
      })
    } else {
      // 后续层：在父节点分配的角度范围内分布
      layerNodes.forEach(node => {
        // 找到父节点
        const parentEdge = edges.find(edge => 
          (edge.target === node.id || edge.to === node.id)
        )
        
        if (parentEdge) {
          const parentId = parentEdge.source || parentEdge.from
          const parentPos = positions.get(parentId)
          
          if (parentPos && parentPos.allocatedAngle !== undefined) {
            // 获取同一父节点的所有子节点
            const siblings = childrenMap.get(parentId) || []
            const siblingIndex = siblings.indexOf(node.id)
            
            if (siblings.length === 1) {
              // 单个子节点：沿父节点方向延伸
              const childAngle = parentPos.angle
              const x = centerX + radius * Math.cos(childAngle)
              const y = centerY + radius * Math.sin(childAngle)
              positions.set(node.id, { 
                x, 
                y, 
                angle: childAngle,
                startAngle: parentPos.startAngle,
                endAngle: parentPos.endAngle,
                allocatedAngle: parentPos.allocatedAngle
              })
            } else {
              // 多个子节点：基于各自子树大小在父节点角度范围内分配
              const siblingsWithSizes = siblings.map(sibId => ({
                id: sibId,
                size: subtreeSizes.get(sibId) || 1
              }))
              
              const totalSiblingSize = siblingsWithSizes.reduce((sum, sib) => sum + sib.size, 0)
              
              // 计算当前节点在兄弟节点中的角度分配
              let childStartAngle = parentPos.startAngle
              for (let i = 0; i < siblingIndex; i++) {
                const siblingRatio = siblingsWithSizes[i].size / totalSiblingSize
                childStartAngle += siblingRatio * parentPos.allocatedAngle
              }
              
              const currentNodeRatio = (subtreeSizes.get(node.id) || 1) / totalSiblingSize
              const childAllocatedAngle = currentNodeRatio * parentPos.allocatedAngle
              const childAngle = childStartAngle + childAllocatedAngle / 2
              
              const x = centerX + radius * Math.cos(childAngle)
              const y = centerY + radius * Math.sin(childAngle)
              
              positions.set(node.id, { 
                x, 
                y, 
                angle: childAngle,
                startAngle: childStartAngle,
                endAngle: childStartAngle + childAllocatedAngle,
                allocatedAngle: childAllocatedAngle
              })
            }
          }
        }
      })
    }
  })
  
  nodePositions.value = positions
}

// 重绘树状图
const redrawTree = () => {
  if (!treeCanvas.value || !treeData.value) return
  
  const canvas = treeCanvas.value
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // 应用变换
  ctx.save()
  ctx.translate(offsetX.value, offsetY.value)
  ctx.scale(zoom.value, zoom.value)
  
  // 绘制边
  drawEdges(ctx)
  
  // 绘制节点
  drawNodes(ctx)
  
  ctx.restore()
}

// 绘制线 - 汇聚扇形效果：从父节点汇聚成一条线，然后向子节点散开
const drawEdges = (ctx) => {
  if (!treeData.value || !treeData.value.edges) return
  
  // 按源节点分组边，实现汇聚效果
  const edgesBySource = new Map()
  treeData.value.edges.forEach(edge => {
    const sourceId = edge.source || edge.from
    if (!edgesBySource.has(sourceId)) {
      edgesBySource.set(sourceId, [])
    }
    edgesBySource.get(sourceId).push(edge)
  })
  
  // 设置连线的基本样式
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  
  edgesBySource.forEach((edges, sourceId) => {
    const sourcePos = nodePositions.value.get(sourceId)
    if (!sourcePos || edges.length === 0) return
    
    const centerX = canvasWidth.value / 2
    const centerY = canvasHeight.value / 2
    
    if (edges.length === 1) {
      // 单条边：简单的贝塞尔曲线
      const edge = edges[0]
      const targetId = edge.target || edge.to
      const targetPos = nodePositions.value.get(targetId)
      
      if (targetPos) {
        ctx.globalAlpha = 0.3
        ctx.strokeStyle = '#9e9e9e'
        ctx.lineWidth = 1.0
        
        const cp1x = sourcePos.x + (targetPos.x - sourcePos.x) * 0.4
        const cp1y = sourcePos.y + (targetPos.y - sourcePos.y) * 0.4
        const cp2x = sourcePos.x + (targetPos.x - sourcePos.x) * 0.6
        const cp2y = sourcePos.y + (targetPos.y - sourcePos.y) * 0.6
        
        ctx.beginPath()
        ctx.moveTo(sourcePos.x, sourcePos.y)
        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, targetPos.x, targetPos.y)
        ctx.stroke()
        ctx.globalAlpha = 1.0
      }
    } else {
      // 多条边：汇聚扇形效果
      
      // 1. 计算汇聚点：在源节点和目标节点集群之间
      const targetPositions = edges.map(edge => {
        const targetId = edge.target || edge.to
        return nodePositions.value.get(targetId)
      }).filter(pos => pos)
      
      if (targetPositions.length === 0) return
      
      // 计算目标节点的中心位置
      const targetCenterX = targetPositions.reduce((sum, pos) => sum + pos.x, 0) / targetPositions.length
      const targetCenterY = targetPositions.reduce((sum, pos) => sum + pos.y, 0) / targetPositions.length
      
      // 汇聚点位于源节点向目标中心方向的60%处
      const convergenceRatio = 0.6
      const convergenceX = sourcePos.x + (targetCenterX - sourcePos.x) * convergenceRatio
      const convergenceY = sourcePos.y + (targetCenterY - sourcePos.y) * convergenceRatio
      
      edges.forEach((edge, index) => {
        const targetId = edge.target || edge.to
        const targetPos = nodePositions.value.get(targetId)
        
        if (targetPos) {
          ctx.globalAlpha = performanceMode.value ? 0.15 : 0.25
          ctx.strokeStyle = '#8e8e8e'
          ctx.lineWidth = performanceMode.value ? 0.5 : 0.8
          
          // 2. 绘制汇聚路径：从源节点到汇聚点的平滑曲线
          const midToConvergence = 0.7  // 到汇聚点的中间控制点位置
          const cp1x = sourcePos.x + (convergenceX - sourcePos.x) * midToConvergence
          const cp1y = sourcePos.y + (convergenceY - sourcePos.y) * midToConvergence
          
          // 3. 从汇聚点到目标节点的散开曲线
          // 散开控制点：在汇聚点和目标点之间，稍微向外偏移以产生扇形
          const spreadRatio = 0.3
          const spreadOffsetX = (targetPos.x - convergenceX) * spreadRatio
          const spreadOffsetY = (targetPos.y - convergenceY) * spreadRatio
          
          const cp2x = convergenceX + spreadOffsetX
          const cp2y = convergenceY + spreadOffsetY
          
          // 绘制整条路径：源点 -> 控制点1 -> 汇聚点 -> 控制点2 -> 目标点
          ctx.beginPath()
          ctx.moveTo(sourcePos.x, sourcePos.y)
          
          // 使用二次贝塞尔曲线创建内凹的扇形效果
          ctx.quadraticCurveTo(cp1x, cp1y, convergenceX, convergenceY)
          ctx.quadraticCurveTo(cp2x, cp2y, targetPos.x, targetPos.y)
          
          ctx.stroke()
          ctx.globalAlpha = 1.0
        }
      })
      
      // 可选：在汇聚点绘制一个小点来显示汇聚效果（调试用）
      if (false) { // 设为true可以看到汇聚点
        ctx.fillStyle = '#ff9800'
        ctx.globalAlpha = 0.6
        ctx.beginPath()
        ctx.arc(convergenceX, convergenceY, 2, 0, 2 * Math.PI)
        ctx.fill()
        ctx.globalAlpha = 1.0
      }
    }
  })
}

// 绘制节点 - 极简空心圆圈设计，区分不同类型的节点
const drawNodes = (ctx) => {
  if (!treeData.value || !treeData.value.nodes) return
  
  // 添加调试信息：统计Agent节点数量
  const agentNodes = treeData.value.nodes.filter(node => node.is_agent_generated)
  if (agentNodes.length > 0) {
    console.log(`🔴 发现 ${agentNodes.length} 个Agent生成节点:`, agentNodes.map(n => n.id))
  }
  
  treeData.value.nodes.forEach(node => {
    const pos = nodePositions.value.get(node.id)
    if (!pos) return
    
    // 虚拟根节点的特殊处理
    if (node.isVirtual) {
      const radius = 8
      
      // 绘制根节点 - 实心蓝色圆圈
      ctx.fillStyle = '#1976d2'
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI)
      ctx.fill()
      
      // 白色内圈
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, radius - 2, 0, 2 * Math.PI)
      ctx.fill()
      
      // 中心点
      ctx.fillStyle = '#1976d2'
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 2, 0, 2 * Math.PI)
      ctx.fill()
      
      return
    }
    
    // 普通节点 - 极简空心圆圈
    const baseRadius = 3  // 统一的小半径
    const isSelected = selectedNode.value && selectedNode.value.id === node.id
    const isHighlight = (node.reposts_count || 0) > 10  // 高转发数节点高亮
    
    // 根据节点类型确定半径、颜色和线宽
    let radius = baseRadius
    let strokeColor = '#64b5f6'  // 默认淡蓝色
    let lineWidth = 1
    
    if (isSelected) {
      strokeColor = '#f44336'  // 选中时红色
      lineWidth = 2
      radius = baseRadius + 1  // 选中节点稍大
    } else if (node.is_agent_generated) {
      strokeColor = '#e53e3e'  // Agent生成帖子 - 鲜红色
      lineWidth = 3  // 更粗的边框
      radius = baseRadius + 2  // Agent节点明显更大
      console.log(`🔴 绘制Agent节点 ${node.id}:`, { pos, radius, strokeColor, lineWidth })
    } else if (node.is_supplementary_root) {
      strokeColor = '#4caf50'  // 补充根节点 - 绿色
      lineWidth = 1.5
    } else if (node.is_isolated_root) {
      strokeColor = '#ff9800'  // 孤立根节点 - 橙色
      lineWidth = 1.5
    } else if (isHighlight) {
      strokeColor = '#ff5722'  // 高亮节点橙红色
      lineWidth = 1.5
    }
    
    // 绘制空心圆圈
    ctx.strokeStyle = strokeColor
    ctx.lineWidth = lineWidth
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI)
    ctx.stroke()
    
    // 选中节点或Agent节点添加内圈填充
    if (isSelected || node.is_agent_generated) {
      ctx.fillStyle = strokeColor
      ctx.globalAlpha = node.is_agent_generated ? 0.15 : 0.2  // Agent节点稍微透明一些
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI)
      ctx.fill()
      ctx.globalAlpha = 1.0
    }
  })
}

// 绘制箭头 - 简化版本，用于径向布局
const drawArrow = (ctx, from, to, color = '#999') => {
  // 在极简的径向布局中，我们不绘制箭头，保持清洁的视觉效果
  // 连线的方向性通过从中心向外的径向特征已经足够清晰
  return
}

// 清空画布
const clearCanvas = () => {
  if (treeCanvas.value) {
    const ctx = treeCanvas.value.getContext('2d')
    ctx.clearRect(0, 0, treeCanvas.value.width, treeCanvas.value.height)
    ctx.fillStyle = '#f9f9f9'
    ctx.fillRect(0, 0, treeCanvas.value.width, treeCanvas.value.height)
  }
}

// 鼠标事件处理
const onMouseDown = (event) => {
  isDragging.value = true
  lastMouseX.value = event.offsetX
  lastMouseY.value = event.offsetY
}

const onMouseMove = (event) => {
  if (isDragging.value) {
    const deltaX = event.offsetX - lastMouseX.value
    const deltaY = event.offsetY - lastMouseY.value
    
    offsetX.value += deltaX
    offsetY.value += deltaY
    
    lastMouseX.value = event.offsetX
    lastMouseY.value = event.offsetY
    
    // 使用节流来减少重绘频率，提升性能
    if (dragThrottle.value) {
      clearTimeout(dragThrottle.value)
    }
    dragThrottle.value = setTimeout(() => {
      redrawTree()
    }, 16) // 约60fps的刷新率
  }
}

const onMouseUp = () => {
  isDragging.value = false
  // 拖拽结束后立即重绘一次，确保最终状态正确
  if (dragThrottle.value) {
    clearTimeout(dragThrottle.value)
    dragThrottle.value = null
  }
  redrawTree()
}

const onWheel = (event) => {
  event.preventDefault()
  
  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
  const newZoom = Math.max(minZoom.value, Math.min(maxZoom.value, zoom.value * zoomFactor))
  
  if (newZoom !== zoom.value) {
    zoom.value = newZoom
    redrawTree()
  }
}

const onCanvasClick = (event) => {
  if (!treeData.value || !treeData.value.nodes) return
  
  const rect = treeCanvas.value.getBoundingClientRect()
  const x = (event.offsetX - offsetX.value) / zoom.value
  const y = (event.offsetY - offsetY.value) / zoom.value
  
  // 查找点击的节点
  let clickedNode = null
  let minDistance = Infinity
  
  treeData.value.nodes.forEach(node => {
    const pos = nodePositions.value.get(node.id)
    if (pos) {
      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2)
      const hitRadius = node.isVirtual ? 8 : 6  // 根节点稍大一些的点击区域
      if (distance < hitRadius && distance < minDistance) {
        minDistance = distance
        clickedNode = node
      }
    }
  })
  
  selectedNode.value = clickedNode
  redrawTree()
  
  // 如果选中了节点，显示详细信息
  if (clickedNode) {
    showMessage(`已选中节点: ${clickedNode.isVirtual ? '根节点' : clickedNode.id}`, 'success')
  }
}

// 缩放控制
const zoomIn = () => {
  zoom.value = Math.min(maxZoom.value, zoom.value * 1.2)
  redrawTree()
}

const zoomOut = () => {
  zoom.value = Math.max(minZoom.value, zoom.value / 1.2)
  redrawTree()
}

const resetView = () => {
  zoom.value = 1
  offsetX.value = 0
  offsetY.value = 0
  redrawTree()
}

const fitToScreen = () => {
  if (!treeData.value || !treeData.value.nodes) return
  
  // 计算边界
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity
  
  nodePositions.value.forEach(pos => {
    minX = Math.min(minX, pos.x)
    maxX = Math.max(maxX, pos.x)
    minY = Math.min(minY, pos.y)
    maxY = Math.max(maxY, pos.y)
  })
  
  if (minX !== Infinity) {
    const contentWidth = maxX - minX + 40
    const contentHeight = maxY - minY + 40
    
    const scaleX = canvasWidth.value / contentWidth
    const scaleY = canvasHeight.value / contentHeight
    zoom.value = Math.min(scaleX, scaleY, maxZoom.value)
    
    offsetX.value = (canvasWidth.value - contentWidth * zoom.value) / 2 - minX * zoom.value
    offsetY.value = (canvasHeight.value - contentHeight * zoom.value) / 2 - minY * zoom.value
    
    redrawTree()
  }
}

// 导出功能
const exportTreeImage = () => {
  if (!treeCanvas.value || !hasTreeData.value) return
  
  try {
    const canvas = treeCanvas.value
    const link = document.createElement('a')
    link.download = `repost_tree_${new Date().toISOString().split('T')[0]}.png`
    link.href = canvas.toDataURL()
    link.click()
    
    showMessage('转播树图片已导出', 'success')
  } catch (error) {
    console.error('导出图片失败:', error)
    showMessage('导出图片失败', 'error')
  }
}

const exportTreeData = () => {
  if (!treeData.value) return
  
  try {
    const dataStr = JSON.stringify(treeData.value, null, 2)
    const dataBlob = new Blob([dataStr], {type: 'application/json'})
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `repost_tree_data_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('转播树数据已导出', 'success')
  } catch (error) {
    console.error('导出数据失败:', error)
    showMessage('导出数据失败', 'error')
  }
}

// 获取节点的子节点数量
const getChildrenCount = (nodeId) => {
  if (!treeData.value || !treeData.value.edges) return 0
  return treeData.value.edges.filter(edge => edge.source === nodeId).length
}

// 时间格式化
const formatTime = (timestamp) => {
  if (!timestamp) return '未知'
  try {
    return new Date(timestamp).toLocaleString()
  } catch {
    return timestamp.toString()
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
    if (treeCanvas.value) {
      // 设置画布尺寸 - 为自适应径向布局提供足够空间
      const container = treeCanvas.value.parentElement
      canvasWidth.value = Math.max(900, container.clientWidth - 20)  // 增加宽度
      canvasHeight.value = Math.max(700, 700)  // 增加高度
      
      clearCanvas()
      
      // 先加载配置选项，再加载树数据
      loadVisualizationOptions().then(() => {
        loadTreeData()
      })
    }
  })
})

// 监听时间范围变化
watch(timeRange, () => {
  console.log('时间范围变化，重新加载转播树数据:', timeRange.value)
  loadTreeData()
}, { deep: true })

// 暴露给父组件的方法
defineExpose({
  refreshTree: loadTreeData,
  exportImage: exportTreeImage,
  exportData: exportTreeData,
  resetTreeView: resetView,
  fitTreeToScreen: fitToScreen
})
</script>

<style scoped>
.panel-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tree-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #fff;
  min-height: 260px;
}

canvas {
  border-radius: 4px;
  cursor: grab;
}

canvas:active {
  cursor: grabbing;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.tree-info-section,
.node-details-section {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
}

.tree-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 2px 0;
}

.stat-item .label {
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  color: #333;
}

.node-detail-card {
  background: #f9f9f9;
  border-radius: 4px;
  padding: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  padding: 2px 0;
  border-bottom: 1px solid #eee;
  font-size: 12px;
}

.detail-row:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.detail-row .label {
  font-weight: bold;
  color: #555;
  min-width: 40px;
}

.detail-row .value {
  color: #333;
  text-align: right;
  word-break: break-all;
}

.detail-row .value.content {
  text-align: left;
  max-width: 140px;
}

.controls-section {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  background: #f9f9f9;
}

.zoom-controls {
  margin-bottom: 8px;
}

.zoom-controls label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: bold;
}

.control-buttons {
  display: flex;
  gap: 4px;
}

.control-buttons button {
  flex: 1;
  padding: 4px 8px;
  font-size: 11px;
}

.display-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.display-options label {
  display: flex;
  align-items: center;
  font-size: 12px;
  cursor: pointer;
}

.display-options input[type="checkbox"] {
  margin-right: 6px;
  margin-bottom: 0;
}

.button-group {
  display: flex;
  gap: 6px;
}

.button-group button {
  flex: 1;
  font-size: 12px;
  padding: 6px 8px;
}

.no-data {
  color: #999;
  font-style: italic;
  text-align: center;
  padding: 40px 20px;
}

.message {
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
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
  font-size: 16px;
  color: #333;
  border-bottom: 2px solid #1976d2;
  padding-bottom: 6px;
}

button:disabled {
  background: #ccc !important;
  cursor: not-allowed;
}
</style>
