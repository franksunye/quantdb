# QuantDB API 文档

QuantDB API 是一个用于访问和管理金融数据的RESTful API。它提供了一系列端点，用于获取股票和指数数据、管理资产、查询价格历史以及使用自然语言进行市场数据查询。

## 文档目录

- [API路由文档](api_routes.md) - 详细的API路由和参数说明
- [API使用示例](api_examples.md) - 常见API使用场景的示例

## API概述

QuantDB API 使用标准的HTTP方法和JSON格式进行通信。所有API端点都使用统一的前缀：`/api/v1`。

### 主要功能

1. **资产管理** - 管理股票、指数等金融资产
2. **价格数据** - 获取资产的历史价格数据
3. **数据导入** - 从外部数据源导入数据
4. **缓存管理** - 管理和监控缓存系统
5. **历史数据** - 获取股票的历史数据
6. **MCP查询** - 使用自然语言查询市场数据

### 认证

当前版本的API不需要认证。未来版本可能会添加API密钥或OAuth2认证。

### 速率限制

当前版本的API没有实施速率限制。未来版本可能会添加速率限制以防止滥用。

### 错误处理

所有API端点在发生错误时都会返回标准的错误响应，包含HTTP状态码和详细的错误信息。

## 快速开始

### 安装依赖

```bash
pip install requests
```

### 基本使用

```python
import requests

# 基础URL
base_url = "http://localhost:8000"

# 获取API信息
response = requests.get(base_url)
print(response.json())

# 获取资产列表
response = requests.get(f"{base_url}/api/v1/assets/")
print(response.json())

# 获取特定股票的历史数据
response = requests.get(
    f"{base_url}/api/v1/historical/stock/000001",
    params={"start_date": "20230101", "end_date": "20230131"}
)
print(response.json())
```

## API版本历史

### v0.1.0 (当前版本)

- 初始版本
- 基本的资产和价格数据管理
- AKShare数据导入
- 缓存系统
- MCP查询

## 未来计划

- 添加用户认证
- 实施速率限制
- 添加更多数据源
- 支持更多资产类型
- 提供WebSocket实时数据流
- 添加批量操作端点

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请参阅项目的GitHub仓库了解更多信息。

## 许可证

QuantDB API 使用 MIT 许可证。
