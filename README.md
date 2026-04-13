<<<<<<< HEAD
# 基于 LangChain 的生产级 RAG 系统

这是一个可直接扩展的生产化 RAG 服务骨架，核心能力包括：

- `FastAPI` 提供查询与写入接口
- `LangChain` 负责检索与生成链路
- `PGVector(Postgres)` 负责向量存储
- `Redis` 负责查询结果缓存
- 结构化日志、健康检查、环境配置、Docker 部署
- 返回可追踪引用，避免“只给答案不告诉来源”

## 目录结构

```text
src/app
├── config.py
├── logging.py
├── main.py
├── schemas.py
└── rag
    ├── chunker.py
    ├── loaders.py
    ├── prompts.py
    ├── service.py
    └── vectorstore.py
```

## 为什么这个骨架更接近生产

- 配置集中管理：通过环境变量切换模型、数据库、缓存和检索参数
- 检索与生成解耦：`RAGService` 可替换为混合检索、重排、多路召回
- 可观测性：JSON 日志 + `/healthz`
- 可扩展性：可继续接入 LangSmith、鉴权、限流、异步任务队列
- 可部署性：提供 `Dockerfile` 和 `docker-compose.yml`

## 快速启动

1. 复制配置

```bash
cp .env.example .env
```

2. 填入 `.env` 中的 `OPENAI_API_KEY`

3. 启动依赖与 API

```bash
docker compose up --build
```

4. 检查服务

```bash
curl http://localhost:8000/healthz
```

## 写入知识库

```bash
curl -X POST http://localhost:8000/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "source": "employee-handbook",
        "text": "员工试用期为 3 个月，期间可以提前 3 天提出离职。",
        "metadata": {"department": "hr", "lang": "zh"}
      },
      {
        "source": "security-policy",
        "text": "所有生产数据库访问必须通过堡垒机，并开启审计日志。",
        "metadata": {"department": "security", "lang": "zh"}
      }
    ]
  }'
```

也支持导入本机上的 `txt/pdf`：

```bash
curl -X POST http://localhost:8000/v1/ingest/file \
  -H "Content-Type: application/json" \
  -d '{
    "paths": ["/data/handbook.pdf", "/data/runbook.txt"],
    "metadata": {"tenant_id": "default", "lang": "zh"}
  }'
```

## 查询

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "生产数据库如何访问？",
    "filter": {"department": "security"}
  }'
```

返回示例：

```json
{
  "answer": "生产数据库访问必须通过堡垒机，并开启审计日志。",
  "citations": [
    {
      "source": "security-policy",
      "chunk_id": "xxx",
      "score": 0.92,
      "metadata": {
        "source": "security-policy",
        "department": "security",
        "lang": "zh",
        "chunk_id": "xxx"
      },
      "preview": "所有生产数据库访问必须通过堡垒机，并开启审计日志。"
    }
  ],
  "cached": false
}
```

## 下一步建议

如果你要把这个系统真正用于生产，建议继续补这几层：

- 接入 `JWT/API Key` 鉴权
- 增加 `Celery / Arq / Dramatiq` 做异步索引
- 增加 `reranker` 提升召回质量
- 增加 `tenant_id` 元数据做多租户隔离
- 增加 `S3 / OSS + 文档解析流水线`
- 接入 `LangSmith` 和 APM

## 本地开发

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```
=======
# RAG_langchain
>>>>>>> ee41ea27cc674f6b8fa37c206168bb60509fc47a
