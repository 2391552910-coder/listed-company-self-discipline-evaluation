import request from './request'

// 公司管理
export const createCompany = (data) => request.post('/companies', data)
export const listCompanies = (params) => request.get('/companies', { params })
export const getCompany = (code) => request.get(`/companies/${code}`)

// 数据导入
export const importIndicators = (formData) =>
  request.post('/indicators/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

// 年报解析
export const uploadReport = (formData) =>
  request.post('/reports/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const parseReport = (id) => request.post(`/reports/parse/${id}`)
export const listChunks = (id) => request.get(`/reports/chunks/${id}`)

// 指数计算
export const computeIndex = (year, matrix) => request.post('/indicators/index/compute', matrix, { params: { year } })
export const getIndex = (code, year) => request.get(`/indicators/index/${code}/${year}`)

// 大模型评价
export const runEvaluation = (data) => request.post('/evaluations/run', data)
export const getEvaluation = (code, year) => request.get(`/evaluations/${code}/${year}`)

// RAG
export const ingestKnowledge = (data) => request.post('/rag/knowledge', data)
export const searchKnowledge = (data) => request.post('/rag/search', data)

// 报告
export const previewReport = (data) => request.post('/reports-export/preview', data)
export const exportPdfUrl = () => '/api/v1/reports-export/export/pdf'
