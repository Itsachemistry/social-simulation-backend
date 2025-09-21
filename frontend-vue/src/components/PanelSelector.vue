<template>
  <div id="function-checkbox">
    <label v-for="panel in panels" :key="panel.value">
      <input 
        type="checkbox" 
        :id="panel.value" 
        :value="panel.value"
        :checked="selectedPanels.includes(panel.value)"
        @change="handlePanelChange(panel.value, $event.target.checked)"
      />
      {{ panel.label }}
    </label>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  selectedPanels: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['panel-change'])

const panels = ref([
  { value: 'agent-setup', label: 'agent' },
  { value: 'simulation', label: 'simulation' },
  { value: 'histogram', label: 'histogram' },
  { value: 'attitude', label: 'attitude' },
  { value: 'wordcloud', label: 'word cloud' },
  { value: 'tree', label: 'tree' },
  { value: 'single', label: 'single' }
])

const handlePanelChange = (panelValue, isChecked) => {
  let newSelectedPanels = [...props.selectedPanels]
  
  if (isChecked) {
    if (!newSelectedPanels.includes(panelValue)) {
      newSelectedPanels.push(panelValue)
    }
  } else {
    newSelectedPanels = newSelectedPanels.filter(panel => panel !== panelValue)
  }
  
  emit('panel-change', newSelectedPanels)
}
</script>

<style scoped>
#function-checkbox {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

#function-checkbox label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
}

#function-checkbox input[type="checkbox"] {
  margin: 0;
}

#function-checkbox label:hover {
  color: #1976d2;
}
</style>
