# 配置指南

## 1. 系统配置概述

QuantDB系统的配置主要通过`src/config.py`文件进行管理。该文件包含系统运行所需的各种参数和设置，包括数据库路径、API密钥、日志设置等。本指南将详细说明各配置项的用途和最佳实践。

## 2. 基础配置

### 2.1 数据库配置

数据库配置决定了系统数据的存储位置和访问方式。

```python
# 数据库路径
DATABASE_PATH = 'database/stock_data.db'

# 数据库连接超时设置（秒）
DATABASE_TIMEOUT = 30

# 数据库连接池大小
DATABASE_POOL_SIZE = 5
```

**最佳实践**:
- 使用相对路径指定数据库位置，便于项目迁移
- 根据系统性能和并发需求调整连接池大小
- 定期备份数据库文件，防止数据丢失

### 2.2 日志配置

日志配置控制系统日志的记录级别、格式和存储位置。

```python
# 日志级别
LOG_LEVEL = 'INFO'  # 可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日志文件路径
LOG_FILE = 'logs/quantdb.log'

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 日志轮转设置
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
```

**最佳实践**:
- 开发环境使用DEBUG级别，生产环境使用INFO或WARNING级别
- 启用日志轮转，防止日志文件过大
- 定期检查和清理日志文件

### 2.3 数据下载配置

数据下载配置控制从外部数据源获取数据的行为。

```python
# 数据源设置
DATA_SOURCE = 'akshare'  # 可选值: akshare, tushare, baostock

# API密钥（如果需要）
API_KEY = 'your_api_key_here'

# 下载重试设置
DOWNLOAD_RETRY_COUNT = 3
DOWNLOAD_RETRY_DELAY = 5  # 秒

# 下载超时设置
DOWNLOAD_TIMEOUT = 30  # 秒

# 并发下载设置
MAX_CONCURRENT_DOWNLOADS = 5
```

**最佳实践**:
- 不要在代码中硬编码API密钥，使用环境变量或配置文件
- 根据网络条件调整重试和超时设置
- 控制并发下载数量，避免触发API限制

## 3. 高级配置

### 3.1 交易信号配置

交易信号配置控制信号生成和处理的行为。

```python
# 信号阈值设置
SIGNAL_STRENGTH_THRESHOLD = 0.7  # 信号强度阈值
SIGNAL_CONFIRMATION_PERIOD = 3   # 信号确认周期（天）

# 信号发送设置
SIGNAL_WEBHOOK_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key_here'
SIGNAL_BATCH_SIZE = 10  # 批量发送信号的数量
```

**最佳实践**:
- 根据回测结果调整信号阈值和确认周期
- 使用安全方式存储Webhook URL
- 控制信号发送频率，避免信息过载

### 3.2 交易计划配置

交易计划配置控制计划生成和管理的行为。

```python
# 计划生成设置
DEFAULT_PLAN_STATUS = 'PENDING'
DEFAULT_SLIP_ENTRY = 0.001  # 默认入场滑点
DEFAULT_SLIP_EXIT = 0.001   # 默认出场滑点
DEFAULT_COMM_ENTRY = 0.0003  # 默认入场佣金率
DEFAULT_COMM_EXIT = 0.0003   # 默认出场佣金率
DEFAULT_FEE = 0.0001         # 默认费用率
```

**最佳实践**:
- 根据实际交易条件调整滑点和佣金设置
- 定期检查和更新默认值，确保与实际情况一致

### 3.3 绩效分析配置

绩效分析配置控制绩效计算和报告生成的行为。

```python
# 绩效计算设置
PERFORMANCE_WINDOW_DAYS = 30  # 绩效计算窗口（天）
BENCHMARK_INDEX = '000300'    # 基准指数

# 图表生成设置
CHART_DPI = 300
CHART_FIGSIZE = (12, 8)
CHART_STYLE = 'seaborn'
```

**最佳实践**:
- 根据分析需求调整绩效计算窗口
- 选择合适的基准指数进行比较
- 根据显示需求调整图表设置

## 4. 环境特定配置

### 4.1 开发环境配置

开发环境配置专注于便于开发和调试。

```python
# 开发环境特定设置
DEBUG_MODE = True
USE_MOCK_DATA = True
PROFILE_PERFORMANCE = True
```

**最佳实践**:
- 启用调试模式，获取详细的错误信息
- 使用模拟数据进行快速测试
- 启用性能分析，识别性能瓶颈

### 4.2 生产环境配置

生产环境配置专注于系统稳定性和性能。

```python
# 生产环境特定设置
DEBUG_MODE = False
USE_MOCK_DATA = False
PROFILE_PERFORMANCE = False
ERROR_NOTIFICATION_EMAIL = 'admin@example.com'
```

**最佳实践**:
- 禁用调试模式，减少信息泄露风险
- 使用真实数据进行操作
- 配置错误通知，及时发现和处理问题

## 5. 配置管理最佳实践

### 5.1 配置文件分离

将配置分离为基础配置和环境特定配置，便于管理不同环境的设置。

```python
# config.py
import os
from config_base import *

# 根据环境加载特定配置
env = os.environ.get('QUANTDB_ENV', 'development')
if env == 'production':
    from config_production import *
elif env == 'testing':
    from config_testing import *
else:
    from config_development import *
```

### 5.2 敏感信息保护

使用环境变量或专用配置文件存储敏感信息，避免将其提交到版本控制系统。

```python
# 从环境变量获取敏感信息
API_KEY = os.environ.get('QUANTDB_API_KEY', '')
SIGNAL_WEBHOOK_URL = os.environ.get('QUANTDB_WEBHOOK_URL', '')
```

### 5.3 配置验证

在系统启动时验证配置的有效性，确保所有必要的配置项都已正确设置。

```python
def validate_config():
    """验证配置的有效性"""
    required_configs = ['DATABASE_PATH', 'LOG_FILE', 'API_KEY']
    for config in required_configs:
        if not globals().get(config):
            raise ValueError(f"缺少必要的配置项: {config}")
    
    # 验证路径是否存在
    if not os.path.exists(os.path.dirname(DATABASE_PATH)):
        raise ValueError(f"数据库目录不存在: {os.path.dirname(DATABASE_PATH)}")
    
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        raise ValueError(f"日志目录不存在: {os.path.dirname(LOG_FILE)}")
```

### 5.4 配置文档化

为每个配置项提供清晰的文档，说明其用途、可选值和默认值。

```python
# 数据库路径
# 指定SQLite数据库文件的位置
# 默认值: 'database/stock_data.db'
DATABASE_PATH = 'database/stock_data.db'
```
