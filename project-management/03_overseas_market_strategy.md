## QuantDB 海外市场策略与项目管理参考（Scrum / KISS / TDD）

### 目的与范围
- 目的：为 QuantDB 进入海外（非中国）市场提供一份精炼、可执行的项目管理参考，指导定位、路线图、度量与沟通。
- 范围：Python 包为主，兼顾 API 服务与云平台的延展；强调最小可行（MVP）与快速迭代。

### 产品当前价值（简述）
- 智能缓存层：SQLite 持久化缓存、增量更新、交易日历感知、毫秒级命中。
- 兼容接口：当前与 AKShare 兼容，一行接入，零配置。
- 形态：Python 包 + API 服务 + 云平台。

### 海外市场问题与机会
- 海外常见数据源：Yahoo、Polygon、IEX、Tiingo、Alpha Vantage、FRED 等。
- 现状痛点：多数客户端“默认不提供持久化缓存/增量/日历”，需要 requests-cache 或自管。
- 机会：将 QuantDB 的“数据层缓存 + 日历增量 + 统一 Schema”抽象为可插拔后端，形成“缓存中台 + 统一接口”。

### 定位与价值主张（针对海外）
- 定位：Universal market data caching layer for Python — plug-in backends, consistent schemas, smart incremental updates, calendar-aware, millisecond cache hits.
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

#### Sprint 1（1–2 周）：面向海外研究者的首个可用版本
- 目标：海外用户可用熟悉的数据源“一行代码享受缓存”。
- 范围：
  1) 后端抽象（DataSourceBackend 接口：fetch/normalize/supports/rate_limit）。
  2) Yahoo 后端（基于 yfinance 或 yahooquery 其一）。
  3) 交易日历接入（pandas_market_calendars）；无日历时降级策略。
  4) 统一 Schema（OHLCV + corporate actions，时区规范）。
  5) 缓存层与后端解耦；增量更新与批量/并发保留。
  6) 英文 README/文档与 US 示例；快速基准（首次 vs 二次命中）。
  7) TDD：后端契约测试、缓存命中/失效、日历增量与边界日期测试。
- 验收标准：
  - AAPL/TSLA/QQQ 无缓存与有缓存均能正确返回；二次查询毫秒级。
  - 支持 days/start_date/end_date；字段与时区一致。
  - 文档“跟着做即可跑通”；基准脚本可复现实验差异。

#### Sprint 2（1–2 周）：迈向企业与合规
- 目标：接入 1–2 个商业 API（Polygon/IEX/Tiingo 任选）。
- 范围：
  1) 商业后端 + token/env 管理（.env 方案）。
  2) 速率限制与重试策略；错误语义统一；配额保护。
  3) 统一公司行为与标识映射的规范补强。
  4) 基准脚本：Raw SDK vs QuantDB（首次拉取/二次命中/批量/增量）。
  5) 文档：授权与合规声明、费用与性能优化建议（命中率→省配额）。
- 验收标准：
  - 至少 1 个商业源端到端可用；缓存命中带来显著加速。
  - 后端切换无需改动业务代码；示例可复现。

### 优先级化 Backlog（可滚动维护）
1) 抽象后端接口（P0）
2) Yahoo 后端 MVP（P0）
3) 交易日历接入与降级（P0）
4) 统一 Schema（OHLCV/公司行为/时区）（P0）
5) 英文 README + US 示例 + 快速基准（P0）
6) 商业源后端（Polygon 或 IEX 或 Tiingo）（P1）
7) Token/速率限制/重试/错误语义统一（P1）
8) 标识映射（Ticker/ISIN/SEDOL）与公司行为一致性（P1）
9) DuckDB/Parquet 缓存后端可选（P2）
10) 指数/ETF/宏观数据与 FRED 后端（P2）

### TDD 策略（样例）
- 契约测试：对 DataSourceBackend 定义统一测试套件（fetch/normalize/分页/错误）。
- 缓存测试：首次拉取、命中、过期、失效与增量更新路径。
- 日历测试：交易/非交易日、跨时区、缺口填充。
- 回归测试：多后端的一致性/列名/时区/公司行为。

### 基准与度量（Success Metrics）
- 采用：PyPI 下载量、GitHub Stars、文档访问/示例复制率。
- 性能：缓存命中率、命中延迟分布、首次拉取与增量更新耗时。
- 覆盖：后端数量、市场与资产类型覆盖度；公司行为准确度。
- 稳定：错误率、重试成功率、速率限制触发率。

### 沟通与节奏（Scrum）
- Sprint：1–2 周；每日站会（15 分钟）同步阻塞与优先级。
- 产出：Sprint Backlog、可执行任务、演示/回顾与度量复盘。
- 文档：中文为主、英文对外；以最小示例与基准脚本为核心资产。

### 交付与发布（MVP 优先）
- 每个 Sprint 产出：
  - 可运行的 Python 包增量（不破坏 API）。
  - 更新 README/示例/基准脚本。
  - 小版本发版（PyPI）或预发布（rc）。
- 风险控制：优先不安装新依赖；若需则以最小变更合并并加测试。

### 决策与追踪（模板）
- 决策记录（Decision Log）：
  - 背景 → 选项 → 结论 → 影响（正/负）→ 评审时间点。
- 风险板（Risk Board）：
  - 描述 → 概率/影响 → 缓解措施 → Owner → 检查频率。

### 下一步（需确认）
- 首个商业后端优先选择（Polygon/IEX/Tiingo）？
- 是否需要我补充一次“竞争包事实核验”（PyPI 下载、缓存特性原文、近期变更）并更新本文件？

---

本文件作为项目管理参考，强调小步快跑、场景驱动与最小可行交付。所有条目可在 Sprint Planning 中细化为可估算的任务与测试用例。
