<template>
  <div>
    <h2>主体自律指数</h2>
    <el-form :inline="true">
      <el-form-item label="年度">
        <el-input-number v-model="year" :min="2000" :max="2030" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="computing" @click="onCompute">AHP-Transformer 混合赋权计算</el-button>
      </el-form-item>
      <el-form-item label="查看公司">
        <el-input v-model="queryCode" placeholder="股票代码" style="width: 140px" />
        <el-button @click="onQuery">查询</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="indexData" style="margin-top: 16px">
      <template #header>
        <span>{{ queryCode }} {{ year }} 年度：{{ indexData.score }} 分（{{ indexData.level }} 级）</span>
      </template>
      <div ref="bar" style="height: 340px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import * as echarts from 'echarts'
import { computeIndex, getIndex } from '../api'

const year = ref(2025)
const queryCode = ref('')
const indexData = ref(null)
const bar = ref(null)
const computing = ref(false)

async function onCompute() {
  computing.value = true
  try {
    await computeIndex(year.value, null)
  } finally {
    computing.value = false
  }
}

async function onQuery() {
  const resp = await getIndex(queryCode.value, year.value)
  indexData.value = resp.data
  if (!resp.data) return
  await nextTick()
  const chart = echarts.init(bar.value)
  chart.setOption({
    xAxis: { type: 'category', data: ['信息披露质量', '董事会治理', '内控合规', '第三方声誉'] },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'bar', data: [resp.data.d1_score, resp.data.d2_score, resp.data.d3_score, resp.data.d4_score] }],
  })
}
</script>
