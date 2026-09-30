<template>
  <div>
    <h2>数据与年报导入</h2>
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card title="CSMAR 指标数据导入">
          <p>列要求：stock_code, indicator_code, year, raw_value（Excel 或 CSV）</p>
          <el-upload :auto-upload="false" :limit="1" :on-change="onIndicatorFile" :file-list="[]">
            <el-button type="primary">选择文件</el-button>
          </el-upload>
          <el-alert v-if="indicatorResult" :title="indicatorResult" type="success" style="margin-top: 12px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card title="年报 PDF 上传与解析">
          <el-form :inline="true">
            <el-form-item label="股票代码"><el-input v-model="reportForm.stock_code" /></el-form-item>
            <el-form-item label="年度"><el-input-number v-model="reportForm.year" :min="2000" :max="2030" /></el-form-item>
          </el-form>
          <el-upload :auto-upload="false" :limit="1" :on-change="onReportFile" :file-list="[]">
            <el-button type="primary">选择年报 PDF</el-button>
          </el-upload>
          <el-button type="success" style="margin-top: 12px" :disabled="!reportId" @click="onParse">
            触发 MinerU 解析
          </el-button>
          <el-alert v-if="parseResult" :title="parseResult" type="info" style="margin-top: 12px" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importIndicators, uploadReport, parseReport } from '../api'

const indicatorResult = ref('')
const reportForm = reactive({ stock_code: '', year: 2025 })
const reportFile = ref(null)
const reportId = ref(null)
const parseResult = ref('')

async function onIndicatorFile(file) {
  const fd = new FormData()
  fd.append('file', file.raw)
  const resp = await importIndicators(fd)
  const d = resp.data
  indicatorResult.value = `新增 ${d.inserted} 条，更新 ${d.updated} 条，跳过 ${d.skipped} 条`
}

function onReportFile(file) {
  reportFile.value = file.raw
  upload()
}

async function upload() {
  const fd = new FormData()
  fd.append('stock_code', reportForm.stock_code)
  fd.append('year', String(reportForm.year))
  fd.append('file', reportFile.value)
  const resp = await uploadReport(fd)
  reportId.value = resp.data.id
  ElMessage.success('年报上传成功')
}

async function onParse() {
  const resp = await parseReport(reportId.value)
  const d = resp.data
  parseResult.value = `解析状态：${d.status}，识别章节 ${d.chapters} 个，切分段落 ${d.chunks} 段`
}
</script>
