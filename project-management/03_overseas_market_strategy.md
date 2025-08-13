## QuantDB 海外市场策略与项目管理参考（Agent-first / Scrum / KISS / TDD）

### 目的与范围
- 目的：为 QuantDB 进入海外（非中国）市场提供一份精炼、可执行的项目管理参考，指导定位、路线图、度量与沟通。
- 范围：Python 包为主，兼顾 API 服务与云平台的延展；强调最小可行（MVP）与快速迭代；**特别强调面向 AI Agent 的工具化接口（Agent-first）**。

### Agent-first 假设与设计原则
- **工具化**：以"简单、可组合、无副作用/幂等"的工具函数为核心能力单元（stateless 优先）。
- **严格 JSON**：严格 JSON Schema 输入/输出；稳定字段与类型，不返回 HTML/富文本。
- **小负载**：默认分页/时间窗裁剪；支持字段选择；上限控制（便于 token/成本与上下文）。
- **可预测**：确定性/可复现；错误语义稳定，机器易处理（error_code、retry_after）。
- **速率与重试**：内置 429/Retry-After 语义；幂等键（Idempotency-Key）；指数退避。
- **观测**：请求 ID、结构化日志、可选推理链标注；指标可聚合（成功率/延迟/错误）。
- **安全**：API Key/OAuth Token、作用域最小化（只读）；令牌不落盘/短时凭证。
- **隐私**：不回显秘密；脱敏错误；避免大批量原始敏感数据外泄。
- **经济性**：高命中缓存、增量同步；文档引导节省配额与 token。
- **互操作**：优先提供 OpenAPI + MCP Server；提供 LangChain Tool/LlamaIndex 简单适配。

### 产品当前价值（简述）
- 智能缓存层：SQLite 持久化缓存、增量更新、交易日历感知、毫秒级命中。
- 兼容接口：当前与 AKShare 兼容，一行接入，零配置。
- 形态：Python 包 + API 服务 + 云平台。

### 海外市场问题与机会（Agent 视角）
- 海外常见数据源：Yahoo、Polygon、IEX、Tiingo、Alpha Vantage、FRED 等。
- 现状痛点：多数客户端“默认不提供持久化缓存/增量/日历”，需要 requests-cache 或自管。
- 机会：将 QuantDB 的“数据层缓存 + 日历增量 + 统一 Schema”抽象为可插拔后端，形成“缓存中台 + 统一接口”。
### Agent 生态与集成标准
- **MCP（Model Context Protocol）**：提供轻量 MCP Server，暴露 tools：get_prices、get_calendar、resolve_identifier、cache_stats 等；支持 JSON schema、流式/分页。
- **OpenAPI + HTTP API**：提供最小 OpenAPI 3 规范；鉴权以 Bearer；返回标准错误格式；429/Retry-After。
- **OpenAI/Anthropic 工具调用**：以 JSON Schema 工具描述为准；函数参数简洁且显式 required/enum。
- **LangChain/LlamaIndex**：提供 Python 适配器（Tool/QueryEngine）；Vercel AI SDK/Node 客户端示例。
- **文档优先**：一页示例"Agent 工具调用最短路径"，含 E2E 样例与失败/重试/速率边界。

### 定位与价值主张（针对海外 + Agent）
- 定位：Universal market data caching layer for Python & AI Agents — plug-in backends, consistent schemas, smart incremental updates, calendar-aware, millisecond cache hits, **Agent-ready tools**.
- 关键价值：
  - 可插拔数据后端（Yahoo/Polygon/IEX/Tiingo/FRED/AKShare）。
  - 统一字段/时区/公司行为（复权、拆分、分红）的标准化。
  - 本地持久化缓存（SQLite/DuckDB/Parquet 可扩展），增量同步与离线复用。
  - 交易日历感知、批量/并发优化、速率限制与重试的生产默认。
  - Jupyter 友好，零配置，一键切换后端。

### 竞争环境（速览）
- 开源/免费：yfinance、yahooquery、pandas-datareader、nasdaq-data-link、alpha_vantage、tiingo（官方包）、fredapi、yahoo_fin 等。
- 商业 SDK：polygon、finnhub、IEX Cloud、tiingo 官方客户端（通常不内建持久化缓存）。
- 辅助：requests-cache、pandas_market_calendars 等。
- 差异点：QuantDB 将“持久化缓存 + 交易日历 + 统一接口 + 增量更新”开箱即用整合，这是稀缺能力。

### 风险与差距
- 数据后端广度：当前偏向 AKShare；需快速覆盖海外主流源。
- 证券标识与公司行为：Ticker/ISIN/SEDOL 映射、时区、复权/分红/拆分一致性。
- 合规：对抓取型源给出免责声明与替代（商业源）；对商业 API 提供 token 管理与速率保护。
- 英文文档与示例：覆盖 US/EU 股票、ETF、指数、宏观数据，提供可复现基准脚本。

### 两个短 Sprint 的最小化路线图（MVP 优先）

#### Sprint 1（1–2 周）：Agent 可用最小版本
- 目标：海外用户可用熟悉的数据源“一行代码享受缓存”。
- 范围：
  1) 后端抽象（DataSourceBackend 接口：fetch/normalize/supports/rate_limit）。
  2) Yahoo 后端（基于 yfinance 或 yahooquery 其一）。
  3) 交易日历接入（pandas_market_calendars）；无日历时降级策略。
  4) 统一 Schema（OHLCV + corporate actions，时区规范）。
  5) 缓存层与后端解耦；增量更新与批量/并发保留。
  6) **最小 HTTP API + OpenAPI**（只读：prices、calendar、health、cache）。
  7) **最小 MCP Server**（同等能力的只读工具）。
  8) **LangChain Tool 适配**与 1 个 E2E 示例（AAPL 日线）。
  9) 英文 README/Agent 集成快速上手；基准（首次 vs 二次命中）。
  10) TDD：后端契约、缓存命中/失效、日历增量、**工具 JSON schema 校验**。
- 验收标准：
  - AAPL/TSLA/QQQ 无缓存与有缓存均能正确返回；二次查询毫秒级。
  - 支持 days/start_date/end_date；字段与时区一致。
  - **工具调用成功率≥99%，二次命中毫秒级；错误可机读、可重试**。
  - 文档“跟着做即可跑通”；基准脚本可复现实验差异。

#### Sprint 2（1–2 周）：企业与合规（Agent 增强）
- 目标：接入 1–2 个商业 API（Polygon/IEX/Tiingo 任选）；**Agent 调用稳定性与观测能力**。
- 范围：
  1) 商业后端 + token/env 管理（.env 方案）。
  2) Token/速率限制/重试策略与统一错误语义（429/Retry-After/Idempotency-Key）。
  3) 统一公司行为与标识映射（Ticker/ISIN/SEDOL）规范补强。
  4) **Langfuse/OTel 观测埋点**（成功率、延迟、错误分布、429）。
  5) **Evals/回归**：Raw SDK vs QuantDB 工具调用（首次/二次/批量/增量）。
  6) 文档：授权与合规声明、费用与性能优化建议。
- 验收标准：
  - ≥1 商业源端到端；**工具化调用稳定加速且配额节省显著**。
  - 后端切换无需改动业务代码；示例可复现。

### 优先级化 Backlog（Agent-first 重排）
**P0（工具化与稳定性）**
1) OpenAPI + 最小 HTTP API（只读）
2) MCP Server（同等只读工具）
3) LangChain Tool 适配与 E2E 示例
4) 抽象后端接口 + Yahoo 后端 MVP
5) 交易日历接入与降级
6) 统一 Schema（OHLCV/公司行为/时区）
7) 英文 README + Agent 快速上手 + 基准
8) 工具 JSON Schema/错误契约/幂等与速率测试

**P1（商业源与观测）**
9) 商业源后端（Polygon/IEX/Tiingo）
10) Token/速率限制/重试/错误语义统一（429/Retry-After/Idempotency-Key）
11) 观测与指标（Langfuse/OTel）
12) 标识映射与公司行为一致性

**P2（数据面扩展）**
13) DuckDB/Parquet 缓存后端可选
14) 指数/ETF/宏观（含 FRED）与更多源

### TDD 策略（Agent 增强）
- 契约测试：DataSourceBackend + **工具 JSON Schema 校验**。
- 缓存：首次/命中/过期/失效/增量/批量并发。
- 日历：交易/非交易、跨时区、缺口填充。
- **工具 E2E**：OpenAPI/MCP/LangChain 调用；幂等、429/重试、分页。
- 回归：多后端一致性/列名/时区/公司行为。

### 基准与度量（Agent-first）
- **采用/触达**：PyPI 下载、GitHub Stars、文档访问/示例复制率、工具清单曝光（MCP/OpenAPI）。
- **稳定性**：工具调用成功率、JSON 解析错误率、超时率、429 触发率与重试成功率。
- **性能**：P50/P95 延迟、缓存命中率、首次拉取/增量耗时、响应负载大小分布。
- **覆盖**：后端数量、资产类型覆盖、公司行为准确度、Agent 框架适配数。
### 安全与合规（Agent）
- **鉴权**：Bearer/OAuth（只读最小作用域）；短期令牌；密钥不回显。
- **访问控制**：速率/配额/配对域名（CORS/Referer 控制用于 Web 场景）。
- **错误**：脱敏；不泄露内部栈信息；统一错误代码。
- **数据**：遵守各数据源许可；为抓取型源提供免责声明与商业源替代。

### 沟通与节奏（Scrum）
- Sprint：1–2 周；每日站会（15 分钟）同步阻塞与优先级。
- 产出：Sprint Backlog、可执行任务、演示/回顾与度量复盘。
- 文档：中文为主、英文对外；以最小示例与基准脚本为核心资产。

### 交付与发布（Agent-first MVP）
- 每个 Sprint 产出：
  - 包/API/MCP 之一的可运行增量 + 文档/基准/观测面板更新。
  - 演示面向"Agent 调用路径"的端到端成功。
  - 小版本发版（PyPI）或预发布（rc）。
- 风险控制：首选最小改动与可回滚；如需引入依赖，保持小步验证。

### 决策与追踪（模板）
- 决策记录（Decision Log）：
  - 背景 → 选项 → 结论 → 影响（正/负）→ 评审时间点。
- 风险板（Risk Board）：
  - 描述 → 概率/影响 → 缓解措施 → Owner → 检查频率。

### 下一步（需确认）
- Agent 框架优先级：MCP、OpenAPI（Assistants/Tool Use）、LangChain/LlamaIndex/Vercel AI SDK 的优先顺序？
- 首个商业后端选择（Polygon/IEX/Tiingo）？
- 是否需要我补充一次“竞争包事实核验”（PyPI 下载、缓存特性原文、近期变更）并更新本文件？
- 是否需要我补充"Agent 框架对接清单与示例代码"小册并纳入仓库？

---

本文件作为项目管理参考，强调小步快跑、场景驱动与最小可行交付。所有条目可在 Sprint Planning 中细化为可估算的任务与测试用例。
