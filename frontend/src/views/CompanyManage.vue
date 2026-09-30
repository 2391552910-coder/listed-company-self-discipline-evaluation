<template>
  <div>
    <h2>公司管理</h2>
    <el-form :inline="true" :model="form">
      <el-form-item label="股票代码"><el-input v-model="form.stock_code" /></el-form-item>
      <el-form-item label="股票简称"><el-input v-model="form.stock_name" /></el-form-item>
      <el-form-item label="行业"><el-input v-model="form.industry" /></el-form-item>
      <el-form-item><el-button type="primary" @click="onCreate">新增公司</el-button></el-form-item>
    </el-form>
    <el-table :data="table.items" border>
      <el-table-column prop="stock_code" label="股票代码" width="120" />
      <el-table-column prop="stock_name" label="股票简称" />
      <el-table-column prop="industry" label="所属行业" />
      <el-table-column prop="market" label="板块" width="80" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCompany, listCompanies } from '../api'
import request from '../api/request'

const form = reactive({ stock_code: '', stock_name: '', industry: '', market: 'SH' })
const table = reactive({ items: [] })

async function load() {
  const resp = await listCompanies({ size: 200 })
  table.items = resp.data.items || []
}

async function onCreate() {
  await createCompany({ ...form })
  ElMessage.success('创建成功')
  Object.assign(form, { stock_code: '', stock_name: '', industry: '' })
  load()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除 ${row.stock_name}？`, '提示', { type: 'warning' })
  await request.delete(`/companies/${row.stock_code}`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
