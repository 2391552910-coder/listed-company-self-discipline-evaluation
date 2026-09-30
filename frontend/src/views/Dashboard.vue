<template>
  <div>
    <h2>总览看板</h2>
    <el-row :gutter="16">
      <el-col :span="6"><el-card><div class="stat">{{ stats.companyCount }}</div><div>覆盖公司</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="stat">{{ stats.levelA }}</div><div>A 级（自律优秀）</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="stat">{{ stats.levelCD }}</div><div>C/D 级（重点关注）</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="stat">{{ stats.avgScore }}</div><div>平均指数得分</div></el-card></el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12"><el-card title="四维度平均得分"><div ref="radar" style="height: 360px"></div></el-card></el-col>
      <el-col :span="12"><el-card title="等级分布"><div ref="pie" style="height: 360px"></div></el-card></el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { listCompanies } from '../api'

const radar = ref(null)
const pie = ref(null)
const stats = reactive({ companyCount: 0, levelA: 0, levelCD: 0, avgScore: '-' })

onMounted(async () => {
  const resp = await listCompanies({ size: 200 })
  const items = resp.data.items || []
  stats.companyCount = items.length
  // 演示数据：实际由指数计算结果驱动
  const radarChart = echarts.init(radar.value)
  radarChart.setOption({
    radar: {
      indicator: [
        { name: '信息披露质量', max: 100 },
        { name: '董事会治理', max: 100 },
        { name: '内控合规', max: 100 },
        { name: '第三方声誉', max: 100 },
      ],
    },
    series: [{ type: 'radar', data: [{ value: [82, 76, 88, 71], name: '四维度平均得分' }] }],
  })
  const pieChart = echarts.init(pie.value)
  pieChart.setOption({
    series: [{
      type: 'pie',
      data: [
        { value: 30, name: 'A 级' }, { value: 45, name: 'B 级' },
        { value: 18, name: 'C 级' }, { value: 7, name: 'D 级' },
      ],
    }],
  })
})
</script>

<style scoped>
.stat { font-size: 32px; font-weight: bold; color: #409eff; }
</style>
