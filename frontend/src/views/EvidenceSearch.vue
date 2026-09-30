<template>
  <div>
    <h2>法规检索与证据溯源</h2>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card title="监管知识入库">
          <el-form :model="kg" label-width="90px">
            <el-form-item label="类型">
              <el-select v-model="kg.doc_type">
                <el-option label="监管规则" value="regulation" />
                <el-option label="处罚案例" value="penalty" />
                <el-option label="历史公告" value="announcement" />
              </el-select>
            </el-form-item>
            <el-form-item label="标题"><el-input v-model="kg.title" /></el-form-item>
            <el-form-item label="发文机关"><el-input v-model="kg.source" /></el-form-item>
            <el-form-item label="正文"><el-input v-model="kg.content" type="textarea" :rows="6" /></el-form-item>
            <el-form-item><el-button type="primary" @click="onIngest">入库并向量化</el-button></el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card title="混合检索（向量 + BM25）">
          <el-input v-model="query" placeholder="输入检索问题，如：信息披露及时性监管要求" @keyup.enter="onSearch">
            <template #append><el-button @click="onSearch">检索</el-button></template>
          </el-input>
          <el-table :data="hits" style="margin-top: 12px" border>
            <el-table-column prop="title" label="标题" width="220" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="120" show-overflow-tooltip />
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column prop="score" label="相似度" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ingestKnowledge, searchKnowledge } from '../api'

const kg = reactive({ doc_type: 'regulation', title: '', source: '', publish_date: '', content: '' })
const query = ref('')
const hits = ref([])

async function onIngest() {
  await ingestKnowledge({ ...kg })
  ElMessage.success('入库成功')
  Object.assign(kg, { title: '', source: '', content: '' })
}

async function onSearch() {
  const resp = await searchKnowledge({ query: query.value, top_k: 8 })
  hits.value = resp.data || []
}
</script>
