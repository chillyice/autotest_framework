<template>
  <div class="section-block">
    <div class="section-head" :style="{ borderLeftColor: color }">
      <span :style="{ color, fontWeight: 600 }">{{ title }}</span>
      <span class="text-muted" style="margin-left:8px;font-size:12px">{{ list.length }} 步</span>
    </div>
    <draggable
      :list="list"
      :group="{ name: 'aw', pull: true, put: true }"
      item-key="key"
      :animation="150"
      @end="onEnd"
      @add="onEnd"
      @remove="onEnd"
    >
      <template #item="{ element, index }">
        <div
          class="step-item"
          :class="{ active: element.id === selectedId }"
          @click="$emit('select', element)"
        >
          <el-tag size="small" type="info">{{ index + 1 }}</el-tag>
          <span class="step-name">{{ element.name || element.action_word_detail?.name || '(未命名)' }}</span>
          <div class="step-actions">
            <el-icon :title="element.enabled ? '禁用' : '启用'" @click.stop="$emit('toggle', element)">
              <CircleCheck v-if="element.enabled" /><CircleClose v-else />
            </el-icon>
            <el-icon title="删除" @click.stop="$emit('remove', element)"><Delete /></el-icon>
          </div>
        </div>
      </template>
      <template #footer>
        <div v-if="!list.length" class="section-empty">拖 AW 到这里</div>
      </template>
    </draggable>
  </div>
</template>

<script setup lang="ts">
import draggable from 'vuedraggable'
import type { TestCaseStep } from '@/api'

defineProps<{
  title: string
  color: string
  list: TestCaseStep[]
  selectedId?: number
}>()

const emit = defineEmits<{
  (e: 'select', step: TestCaseStep): void
  (e: 'remove', step: TestCaseStep): void
  (e: 'toggle', step: TestCaseStep): void
  (e: 'change'): void
}>()

function onEnd() { emit('change') }
</script>

<style scoped>
.section-block { border: 1px solid #ebeef5; border-radius: 4px; min-height: 100px; background: #fff; }
.section-head { padding: 8px 12px; border-left: 4px solid #409eff; background: #fafafa; border-radius: 4px 4px 0 0; }
.step-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid #ebeef5; border-radius: 4px; margin: 6px 0; cursor: pointer; background: #fff; }
.step-item.active { border-color: #409eff; background: #ecf5ff; }
.step-item:hover { border-color: #c6e2ff; }
.step-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.step-actions { display: flex; gap: 6px; }
.step-actions .el-icon { cursor: pointer; color: #909399; }
.step-actions .el-icon:hover { color: #409eff; }
.section-empty { padding: 16px; text-align: center; color: #c0c4cc; font-size: 12px; border: 1px dashed #dcdfe6; border-radius: 4px; margin: 6px 0; }
</style>
