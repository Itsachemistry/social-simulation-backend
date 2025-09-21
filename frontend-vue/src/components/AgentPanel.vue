<template>
  <div class="agent-panel">
    <div class="agent-controls">
      <div class="agent-list-header">
        <span>智能体列表</span>
        <div>
          <button class="create-agent-btn blue" @click="createNewAgent">新建</button>
        </div>
      </div>
      <div class="agent-list">
        <div 
          v-for="agent in agents" 
          :key="agent.agent_id"
          class="agent-item"
          :class="{ active: selectedAgent?.agent_id === agent.agent_id }"
          @click="selectAgent(agent)"
        >
          <div class="agent-info">
            <div class="agent-id">{{ agent.agent_id }}</div>
            <div class="agent-role">{{ getRoleLabel(agent.role_type) }}</div>
            <div class="agent-stats">
              活跃度: {{ (agent.activity_level * 100).toFixed(0) }}% | 
              情感: {{ agent.current_emotion?.toFixed(2) || '0.00' }}
            </div>
          </div>
          <div class="agent-actions">
            <button class="edit-btn" @click.stop="selectAgent(agent)">编辑</button>
            <button class="delete-btn" @click.stop="deleteAgent(agent.agent_id)">删除</button>
          </div>
        </div>
        <div v-if="agents.length === 0" class="no-agents">
          暂无智能体，点击"新建"创建第一个智能体
        </div>
      </div>
    </div>
    
    <div class="agent-editor">
      <div v-if="!selectedAgent && !isCreating" class="editor-placeholder">
        请在左侧新建或选择一个智能体进行编辑。
      </div>
      
      <div v-else class="editor-form">
        <h4>{{ isCreating ? '新建智能体' : `编辑: ${selectedAgent.agent_id}` }}</h4>
        
        <div class="form-group">
          <label>智能体ID:</label>
          <input 
            type="text" 
            v-model="editingAgent.agent_id" 
            :readonly="!isCreating"
            placeholder="请输入唯一标识符"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>角色类型:</label>
          <select v-model="editingAgent.role_type" class="form-select">
            <option value="ordinary_user">普通用户</option>
            <option value="opinion_leader">意见领袖</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>态度坚定度:</label>
          <input 
            type="number" 
            step="0.01" 
            min="0" 
            max="1" 
            v-model.number="editingAgent.attitude_firmness"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>意见屏蔽度:</label>
          <input 
            type="number" 
            step="0.01" 
            min="0" 
            max="1" 
            v-model.number="editingAgent.opinion_blocking"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>活跃度:</label>
          <input 
            type="number" 
            step="0.01" 
            min="0" 
            max="1" 
            v-model.number="editingAgent.activity_level"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>初始情感:</label>
          <input 
            type="number" 
            step="0.01" 
            min="-1" 
            max="1" 
            v-model.number="editingAgent.initial_emotion"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>初始立场:</label>
          <input 
            type="number" 
            step="0.01" 
            min="-1" 
            max="1" 
            v-model.number="editingAgent.initial_stance"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>初始确信度:</label>
          <input 
            type="number" 
            step="0.01" 
            min="0" 
            max="1" 
            v-model.number="editingAgent.initial_confidence"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>当前情感:</label>
          <input 
            type="number" 
            step="0.01" 
            min="-1" 
            max="1" 
            v-model.number="editingAgent.current_emotion"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>当前立场:</label>
          <input 
            type="number" 
            step="0.01" 
            min="-1" 
            max="1" 
            v-model.number="editingAgent.current_stance"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>当前确信度:</label>
          <input 
            type="number" 
            step="0.01" 
            min="0" 
            max="1" 
            v-model.number="editingAgent.current_confidence"
            class="form-input"
          />
        </div>
        
        <div class="button-group">
          <button class="save-btn blue" @click="saveAgent">
            {{ isCreating ? '新建' : '保存' }}
          </button>
          <button class="cancel-btn gray" @click="cancelEdit">
            {{ isCreating ? '清空' : '取消' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useApi } from '../composables/useApiComplete'

const selectedAgent = ref(null)
const agents = ref([])
const isCreating = ref(false)
const editingAgent = reactive({})

const { getAgents, addAgent, updateAgent, deleteAgent: deleteAgentApi } = useApi()

// 获取智能体数据
const fetchAgents = async () => {
  try {
    const data = await getAgents()
    agents.value = data.agents || []
    console.log('智能体数据:', agents.value)
  } catch (error) {
    console.error('获取智能体数据失败', error)
    agents.value = []
  }
}

// 获取角色标签
const getRoleLabel = (roleType) => {
  const labels = {
    'ordinary_user': '普通用户',
    'opinion_leader': '意见领袖'
  }
  return labels[roleType] || '未知'
}

// 选择智能体
const selectAgent = (agent) => {
  selectedAgent.value = agent
  isCreating.value = false
  
  // 复制数据到编辑表单
  Object.assign(editingAgent, {
    agent_id: agent.agent_id,
    role_type: agent.role_type,
    attitude_firmness: agent.attitude_firmness,
    opinion_blocking: agent.opinion_blocking,
    activity_level: agent.activity_level,
    initial_emotion: agent.initial_emotion,
    initial_stance: agent.initial_stance,
    initial_confidence: agent.initial_confidence,
    current_emotion: agent.current_emotion,
    current_stance: agent.current_stance,
    current_confidence: agent.current_confidence
  })
}

// 创建新智能体
const createNewAgent = () => {
  isCreating.value = true
  selectedAgent.value = null
  
  // 重置编辑表单为默认值
  Object.assign(editingAgent, {
    agent_id: '',
    role_type: 'ordinary_user',
    attitude_firmness: 0.5,
    opinion_blocking: 0.3,
    activity_level: 0.7,
    initial_emotion: 0.0,
    initial_stance: 0.0,
    initial_confidence: 0.5,
    current_emotion: 0.0,
    current_stance: 0.0,
    current_confidence: 0.5
  })
}

// 保存智能体
const saveAgent = async () => {
  try {
    if (!editingAgent.agent_id.trim()) {
      alert('请输入智能体ID')
      return
    }
    
    if (isCreating.value) {
      // 检查ID是否已存在
      if (agents.value.some(a => a.agent_id === editingAgent.agent_id)) {
        alert('智能体ID已存在，请使用其他ID')
        return
      }
      
      await addAgent(editingAgent)
      console.log('智能体创建成功')
      isCreating.value = false
    } else {
      await updateAgent(editingAgent.agent_id, editingAgent)
      console.log('智能体更新成功')
    }
    
    // 刷新列表
    await fetchAgents()
    
    // 如果是编辑模式，保持选中状态
    if (!isCreating.value) {
      const updatedAgent = agents.value.find(a => a.agent_id === editingAgent.agent_id)
      if (updatedAgent) {
        selectedAgent.value = updatedAgent
      }
    }
  } catch (error) {
    console.error('保存智能体失败', error)
    alert('保存失败，请检查网络连接和输入数据')
  }
}

// 取消编辑
const cancelEdit = () => {
  if (isCreating.value) {
    // 清空表单
    Object.keys(editingAgent).forEach(key => {
      delete editingAgent[key]
    })
    isCreating.value = false
  } else {
    // 恢复到原始状态
    selectedAgent.value = null
  }
}

// 删除智能体
const deleteAgent = async (agentId) => {
  if (!confirm(`确定要删除智能体 "${agentId}" 吗？此操作不可撤销。`)) {
    return
  }
  
  try {
    await deleteAgentApi(agentId)
    console.log('智能体删除成功')
    
    // 如果删除的是当前选中的智能体，清除选中状态
    if (selectedAgent.value?.agent_id === agentId) {
      selectedAgent.value = null
      isCreating.value = false
    }
    
    // 刷新列表
    await fetchAgents()
  } catch (error) {
    console.error('删除智能体失败', error)
    alert('删除失败，请检查网络连接')
  }
}

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.agent-panel {
  display: flex;
  height: 100%;
  gap: 20px;
}

.agent-controls {
  width: 300px;
  border-right: 1px solid #ddd;
  padding-right: 20px;
}

.agent-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.agent-list-header span {
  font-weight: bold;
  font-size: 16px;
}

.create-agent-btn {
  background: #1976d2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.create-agent-btn:hover {
  background: #1565c0;
}

.agent-list {
  max-height: 400px;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.agent-item:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.agent-item.active {
  background: #e3f2fd;
  border-color: #1976d2;
}

.agent-info {
  flex: 1;
}

.agent-id {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.agent-role {
  color: #666;
  font-size: 12px;
  margin-bottom: 4px;
}

.agent-stats {
  color: #888;
  font-size: 11px;
}

.agent-actions {
  display: flex;
  gap: 5px;
}

.edit-btn, .delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}

.edit-btn {
  background: #4caf50;
  color: white;
}

.edit-btn:hover {
  background: #45a049;
}

.delete-btn {
  background: #f44336;
  color: white;
}

.delete-btn:hover {
  background: #d32f2f;
}

.no-agents {
  text-align: center;
  color: #666;
  padding: 40px 20px;
  font-style: italic;
}

.agent-editor {
  flex: 1;
  padding-left: 20px;
}

.editor-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #666;
  font-style: italic;
  background: #f9f9f9;
  border-radius: 4px;
}

.editor-form {
  background: white;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.editor-form h4 {
  margin: 0 0 20px 0;
  color: #333;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-input, .form-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1);
}

.form-input[readonly] {
  background: #f5f5f5;
  color: #666;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.save-btn {
  background: #1976d2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.save-btn:hover {
  background: #1565c0;
}

.cancel-btn {
  background: #9e9e9e;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: #757575;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-panel {
    flex-direction: column;
    height: auto;
  }
  
  .agent-controls {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ddd;
    padding-right: 0;
    padding-bottom: 20px;
    margin-bottom: 20px;
  }
  
  .agent-editor {
    padding-left: 0;
  }
}
</style>
