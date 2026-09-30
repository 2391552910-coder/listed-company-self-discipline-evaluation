<template>
  <div>
    <h2>大模型多维度评价</h2>
    <el-form :inline="true">
      <el-form-item label="股票代码"><el-input v-model="form.stock_code" style="width: 140px" /></el-form-item>
      <el-form-item label="年度"><el-input-number v-model="form.year" :min="2000" :max="2030" /></el-form-item>
      <el-form-item label="RAG 增强"><el-switch v-model="form.rag_enabled" /></el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="running" @click="onRun">生成评价</el-button>
        <el-button @click="onLoad">查看已有评价</el-button>
      </el-form-item>
    </el-form>

    <template v-if="result">
      <el-alert type="success" :closable="false" style="margin-bottom: 16px"
        :title="`模型：${result.evaluation.model_name}｜状态：${result.evaluation.status}｜综合得分：${result.evaluation.score ?? '-'}`" />
      <el-tabs>
        <el-tab-pane v-for="d in dims" :key="d.key" :label="d.name">
          <el-card>
            <p style="white-space: pre-wrap">{{ result.evaluation[d.field] || '该维度暂无评价' }}</p>
          </el-card>
        </el-tab-pane>
        <el-tab-pane label="总体摘要">
          <el-card><p style="white-space: pre-wrap">{{ result.evaluation.overall_summary }}</p></el-card>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { runEvaluation, getEvaluation } from '../api'

const form = reactive({ stock_code: '', year: 2025, rag_enabled: true })
const result = ref(null)
const running = ref(false)

const dims = [
  { key: 'D1', name: '信息披露质量', field: 'd1_evaluation' },
  { key: 'D2', name: '董事会治理有效性', field: 'd2_evaluation' },
  { key: 'D3', name: '内部控制与合规性', field: 'd3_evaluation' },
  { key: 'D4', name: '第三方声誉', field: 'd4_evaluation' },
]

async function onRun() {
  running.value = true
  try {
    await runEvaluation({ ...form })
    await onLoad()
  } finally {
    running.value = false
  }
}

async function onLoad() {
  const resp = await getEvaluation(form.stock_code, form.year)
  result.value = resp.data
}
</script>
