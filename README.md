# 基于大模型的上市公司主体自律评价系统

硕士学位论文《基于大模型的上市公司主体自律评价系统的设计与实现》配套实现代码。
系统以 A 股上市公司年度报告和 CSMAR 结构化数据为输入，通过 **AHP-Transformer 混合赋权**计算主体自律指数，利用**大模型（DeepSeek）**对年报进行四维度自律信息抽取与多维度评价，并基于 **RAG（BGE-M3 + Milvus）**注入监管法规依据实现评价增强与证据溯源。

> 代码按功能模块与分层组织，不按照论文章节顺序排版。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue3 + Element Plus + ECharts + Vite |
| 控制层 | FastAPI（REST API） |
| 业务层 | Python 服务模块（LangChain 编排大模型与 RAG 流程） |
| 数据访问层 | SQLAlchemy Repository（DAO） |
| 结构化存储 | PostgreSQL |
| 向量检索 | Milvus（HNSW）+ BM25 双路混合检索 |
| 大模型 | DeepSeek（OpenAI 兼容接口） |
| 嵌入模型 | BGE-M3（sentence-transformers） |
| 年报解析 | MinerU（降级 pdfplumber） |

## 系统架构（前后端分离三层架构）

```
frontend/  Vue3 SPA
   │  /api/v1/**
   ▼
backend/app/api/v1/        控制层：参数校验、路由、统一响应
   ▼
backend/app/services/      业务层：指数计算、年报解析、LLM 评价、RAG 检索、报告生成
   ▼
backend/app/repositories/  数据访问层：SQLAlchemy CRUD
   ├─ PostgreSQL  公司/指标/指数/评价/证据/知识元数据
   └─ Milvus      监管知识向量（BGE-M3，1024 维，HNSW 索引）

backend/app/rag/           RAG 支撑：提示词模板、嵌入、向量库、混合检索器
```

## 核心流程

1. **数据导入**：CSMAR 四维度十二项指标 Excel/CSV 批量导入；年报 PDF 上传后经 MinerU 解析 → 章节识别 → 治理段落切分 → 维度标注。
2. **指数计算**：极差标准化 → AHP 主观权重（含一致性检验）+ Transformer 多头注意力客观权重 → 先验正则化融合 → 加权评分与 A/B/C/D 分级。
3. **大模型评价**：逐维度执行 事实抽取（LangChain PromptTemplate + DeepSeek）→ RAG 检索法规 → 结构化维度评价（JSON）→ 总体摘要。
4. **证据溯源**：评价引用的法规条款与处罚案例落库，支持按评价回溯具体依据与相似度。
5. **报告导出**：整合指数、四维评价、证据清单，导出 HTML / PDF 评价报告。

## 快速开始

### Docker 一键启动

```bash
cp backend/.env.example backend/.env   # 填入 DeepSeek API Key
docker compose up -d --build
```

- 前端：http://localhost:8080
- 后端接口文档（Swagger）：http://localhost:8000/docs

### 本地开发

```bash
# 1. 基础设施
docker compose up -d postgres milvus-etcd milvus-minio milvus

# 2. 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 配置数据库与 LLM_API_KEY
uvicorn app.main:app --reload --port 8000

# 3. 前端
cd ../frontend
npm install
npm run dev            # http://localhost:5173，已配置 /api 代理
```

## 目录说明

```
backend/app/
├── api/v1/         控制层路由（company / indicator / reports / evaluations / rag / reports-export）
├── services/       业务层（import / annual_report / index / llm / evaluation / rag / report）
├── repositories/   数据访问层（BaseRepository + 各表 Repository）
├── models/         SQLAlchemy ORM（对应 5.3.1 数据库设计）
├── schemas/        Pydantic 出入参模型
├── rag/            prompts（提示词模板）/ embeddings（BGE-M3）/ vector_store（Milvus）/ retriever（混合检索）
└── core/           数据库连接、全局异常
```

## 四维度十二项指标体系

| 维度 | 指标 |
| --- | --- |
| D1 信息披露质量 | 披露及时性、披露完整性、信息披露考评等级 |
| D2 董事会治理有效性 | 独立董事占比、董事会会议频次、专门委员会运作 |
| D3 内部控制与合规性 | 内控审计意见、违规处罚次数、内控缺陷整改率 |
| D4 第三方声誉 | ESG 评级、审计意见类型、媒体舆情得分 |

## 注意事项

- `.env` 中的 `LLM_API_KEY` 必填；未配置时评价接口返回业务异常提示。
- Milvus 首次写入向量时自动创建集合与 HNSW 索引。
- 首次计算指数前会自动初始化指标体系（幂等）。
