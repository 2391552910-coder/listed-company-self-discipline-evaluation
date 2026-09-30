<template>
  <div>
    <h2>评价报告导出</h2>
    <el-form :inline="true">
      <el-form-item label="股票代码"><el-input v-model="form.stock_code" style="width: 140px" /></el-form-item>
      <el-form-item label="年度"><el-input-number v-model="form.year" :min="2000" :max="2030" /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onPreview">预览报告</el-button>
        <el-button type="success" @click="onExportPdf">导出 PDF</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="report" style="margin-top: 16px">
      <template #header>
        <span>{{ report.company.stock_name }}（{{ report.company.stock_code }}）{{ report.year }} 年度主体自律评价报告</span>
      </template>
      <h3>主体自律指数</h3>
      <p v-if="report.index_result">
        综合得分 {{ report.index_result.score }} 分，等级 {{ report.index_result.level }}
      </p>
      <p v-else>该年度尚未计算自律指数</p>
      <h3>多维度评价</h3>
      <p style="white-space: pre-wrap">{{ report.evaluation?.overall_summary || '暂无评价' }}</p>
      <h3>证据溯源</h3>
      <ul>
        <li v-for="ev in evidenceList" :key="ev.id">
          【{{ ev.dimension_code }}】《{{ ev.regulation_title }}》（{{ ev.regulation_source }}）
        </li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { previewReport, exportPdfUrl } from '../api'

const form = reactive({ stock_code: '', year: 2025 })
const report = ref(null)

const evidenceList = computed(() => {
  const grouped = report.value?.evidence_by_dim || {}
  return Object.values(grouped).flat()
})

async function onPreview() {
  const resp = await previewReport({ ...form })
  report.value = resp.data
}

async function onExportPdf() {
  const resp = await fetch(exportPdfUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...form }),
  })
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${form.stock_code}_${form.year}_自律评价报告.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
