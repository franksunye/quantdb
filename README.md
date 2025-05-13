# QuantDB: 面向Agent时代的开源金融智能中间件平台

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 项目概述

QuantDB是一个面向Agent时代的开源金融智能中间件平台，通过MCP（Model Context Protocol）协议标准化自然语言与金融数据之间的接口，支持AI原生、上下文感知、结构化响应的金融服务。

### 核心特点

- **智能数据中间层**：作为"数据蓄水池"模型，高效缓存热点数据，支持多Agent共享数据上下文
- **MCP协议支持**：将自然语言请求转化为结构化、可执行、上下文感知的任务协议
- **Agent生态对接**：支持与LangChain、OpenAI Plugin、AutoGPT等主流Agent平台集成
- **开放式数据服务**：整合多种金融数据源，提供统一的数据访问接口

### 核心转变

- 从**查询型API** → **交互式智能Agent接口**
- 从**静态数据管道** → **动态上下文增强数据服务**
- 从**服务消费者** → **Agent工具链提供者**

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```python
# 导入主模块
from src.main import main

# 运行股票数据更新
main(mode="update_stock", symbols=["000001", "600000"])

# 运行指数数据更新
main(mode="update_index", index_codes=["000300"])
```

### 命令行使用

```bash
# 下载股票数据
python -m src.main --mode stock --symbols 000001 600000

# 更新指数数据
python -m src.main --mode update_index --index_codes 000300

# 下载所有沪深股票信息
python -m src.main --mode all_stocks
```

## 项目结构

```
/
├── data/                          # 数据存储目录
│   ├── raw/                       # 原始数据
│   └── processed/                 # 处理过的数据
│
├── database/                      # 数据库相关文件
│   ├── schema.sql                 # 数据库初始化的SQL脚本
│   ├── migrations/                # 数据库迁移文件
│   └── stock_data.db              # SQLite数据库文件
│
├── docs/                          # 项目文档
│   ├── 00_vsion_and_roadmap.md    # 愿景与路线图
│   ├── 01_business_rules.md       # 业务规则参考
│   ├── 02_business_objects_design.md # 业务对象设计
│   ├── 03_system_architecture.md  # 系统架构概览
│   ├── 04_roadmap.md              # 开发路线图
│   ├── 05_testing_approach.md     # 测试策略简述
│   ├── 06_configuration_guide.md  # 配置指南
│   └── project_management/        # 项目管理文档
│
├── src/                           # 源代码目录
│   ├── domain/                    # 领域模型
│   │   ├── models/                # 业务模型
│   │   └── repositories/          # 数据仓库
│   ├── services/                  # 服务层
│   ├── config.py                  # 配置文件
│   ├── database.py                # 数据库操作
│   ├── downloader.py              # 数据下载
│   ├── indicators.py              # 指标计算
│   ├── logger.py                  # 日志记录
│   ├── main.py                    # 主程序入口
│   ├── processor.py               # 数据处理
│   ├── scheduler.py               # 任务调度
│   ├── signal_sender.py           # 信号发送
│   ├── signal_to_plan.py          # 信号转计划
│   └── updater.py                 # 数据更新
│
├── tests/                         # 测试目录
│
├── .gitignore                     # Git忽略文件
├── import_gen_plan.bat            # 导入计划批处理
├── requirements.txt               # 项目依赖
└── README.md                      # 项目说明
```

## 核心功能

- **数据获取与管理**：下载、存储和更新股票和指数数据
- **交易信号生成**：基于历史数据生成交易信号
- **交易计划管理**：将交易信号转换为交易计划并跟踪执行
- **绩效分析**：分析交易计划和策略的绩效
- **MCP协议支持**：支持自然语言到结构化查询的转换
- **Agent接口**：提供与各种Agent平台集成的接口

## 文档

详细文档请参阅[docs目录](./docs)：

- [愿景与路线图](./docs/00_vsion_and_roadmap.md)
- [业务规则参考](./docs/01_business_rules.md)
- [业务对象设计](./docs/02_business_objects_design.md)
- [系统架构概览](./docs/03_system_architecture.md)
- [开发路线图](./docs/04_roadmap.md)
- [测试策略简述](./docs/05_testing_approach.md)
- [配置指南](./docs/06_configuration_guide.md)

## 开发路线图

### 短期目标 (1-3个月)
- 实现智能缓存引擎
- 开发数据源整合网关
- 完善交易信号系统
- 增强交易计划管理

### 中期目标 (3-6个月)
- 开发MCP协议框架
- 实现API网关与服务层
- 构建策略管理系统
- 开发投资组合管理

### 长期目标 (6-12个月)
- 实现Agent生态对接
- 开发智能服务能力
- 构建智能数据中间层
- 支持系统扩展和集成

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式

Ye Sun - franksunye@hotmail.com

项目链接: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
