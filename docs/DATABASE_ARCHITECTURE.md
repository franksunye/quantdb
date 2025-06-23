# QuantDB 数据库架构统一文档

## 📊 架构概述

QuantDB 现在使用**统一数据库架构**，所有组件共享同一个 SQLite 数据库文件。

### 🎯 统一原则

- **单一数据源**: 所有数据存储在 `database/stock_data.db`
- **配置统一**: 所有组件通过配置文件指向同一数据库
- **路径标准化**: 使用项目根目录作为基准路径

## 📁 目录结构

```
quantdb/
├── database/                          # 统一数据库目录
│   ├── stock_data.db                 # 主数据库文件 ⭐
│   ├── schema.sql                    # 数据库架构定义
│   ├── stock_data.db.backup          # 自动备份
│   └── test_db.db                    # 测试数据库
├── core/                             # 核心服务层
│   └── utils/config.py               # 核心配置 → database/
├── cloud/streamlit_cloud/            # 云端应用
│   ├── src/config.py                 # 云端配置 → database/
│   └── app.py                        # 主应用 → database/
└── scripts/
    └── unify_database.py             # 数据库统一工具
```

## 🔧 配置系统

### 核心配置 (`core/utils/config.py`)

```python
# 统一数据库路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = os.path.join(BASE_DIR, 'database/stock_data.db')

def get_database_url():
    # 多路径回退机制
    possible_paths = [
        DATABASE_PATH,  # 标准路径
        os.path.join(BASE_DIR, 'database', 'stock_data.db'),
        # ... 其他回退路径
    ]
```

### 云端配置 (`cloud/streamlit_cloud/src/config.py`)

```python
# 指向项目根目录数据库
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATABASE_PATH = os.path.join(BASE_DIR, 'database/stock_data.db')
```

## 📋 数据库表结构

### 核心表

1. **assets** - 资产信息表
   - 存储股票基本信息
   - 支持A股和港股

2. **daily_stock_data** - 日线数据表
   - OHLC价格数据
   - 成交量和成交额

3. **intraday_stock_data** - 分钟线数据表
   - 高频交易数据

4. **request_logs** - 请求日志表
   - API调用记录
   - 性能监控

5. **data_coverage** - 数据覆盖表
   - 数据完整性跟踪

6. **system_metrics** - 系统指标表
   - 系统性能数据

## 🔄 统一过程

### 历史问题

在统一之前，项目存在**双数据库架构**：

```
❌ 旧架构 (已解决)
├── database/stock_data.db              # 核心服务数据库
└── cloud/streamlit_cloud/database/     # 云端独立数据库
    ├── stock_data.db
    └── stock_data.db.backup
```

### 统一解决方案

1. **数据合并**: 将云端数据库的完整数据合并到根目录
2. **配置更新**: 修改所有配置文件指向统一数据库
3. **路径重构**: 更新应用代码使用统一路径
4. **清理冗余**: 删除云端数据库目录

### 统一工具

使用 `scripts/unify_database.py` 执行统一：

```bash
python scripts/unify_database.py
```

功能：
- 自动检测数据库状态
- 智能合并数据
- 创建安全备份
- 清理冗余文件

## 🚀 使用指南

### 开发环境

```bash
# 1. 确认数据库路径
python -c "from core.utils.config import DATABASE_URL; print(DATABASE_URL)"

# 2. 启动API服务
python -m uvicorn api.main:app --reload

# 3. 启动云端应用
cd cloud/streamlit_cloud
streamlit run app.py
```

### 数据库操作

```python
# 核心服务中
from core.database import get_db
from core.models import Asset

db_session = next(get_db())
assets = db_session.query(Asset).all()

# 云端应用中
import sqlite3
conn = sqlite3.connect('../../database/stock_data.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM assets")
```

## 🔍 验证统一

### 检查配置

```bash
# 检查核心配置
python -c "from core.utils.config import DATABASE_URL; print('Core:', DATABASE_URL)"

# 检查云端配置
cd cloud/streamlit_cloud
python -c "import sys; sys.path.append('src'); from config import get_database_url; print('Cloud:', get_database_url())"
```

### 检查数据一致性

```bash
# 统一数据库状态
python -c "
import sqlite3
conn = sqlite3.connect('database/stock_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM assets')
print(f'Assets: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM daily_stock_data')
print(f'Data: {cursor.fetchone()[0]}')
conn.close()
"
```

## 📈 优势

### 统一后的优势

1. **数据一致性**: 所有组件访问相同数据
2. **简化维护**: 单一数据库文件管理
3. **性能优化**: 避免数据同步开销
4. **部署简化**: 统一的部署配置
5. **备份简单**: 单文件备份策略

### 配置灵活性

- **环境变量支持**: `DATABASE_URL` 环境变量覆盖
- **多路径回退**: 自动寻找可用数据库文件
- **云端兼容**: 支持不同部署环境

## 🛠️ 维护指南

### 备份策略

```bash
# 自动备份 (统一工具会创建)
database/stock_data.backup_YYYYMMDD_HHMMSS

# 手动备份
cp database/stock_data.db database/stock_data.backup_manual
```

### 故障恢复

```bash
# 从备份恢复
cp database/stock_data.backup_before_merge database/stock_data.db

# 重新统一
python scripts/unify_database.py
```

### 数据库迁移

```bash
# 导出数据
sqlite3 database/stock_data.db .dump > backup.sql

# 导入数据
sqlite3 new_database.db < backup.sql
```

## 📝 最佳实践

1. **定期备份**: 重要操作前创建备份
2. **配置验证**: 部署前验证数据库路径
3. **性能监控**: 监控数据库大小和查询性能
4. **版本控制**: 不要将数据库文件提交到Git
5. **环境隔离**: 开发/测试/生产使用不同数据库

## 🔗 相关文档

- [开发指南](30_DEVELOPMENT.md)
- [部署指南](40_DEPLOYMENT.md)
- [API文档](50_API.md)
- [故障排除](60_TROUBLESHOOTING.md)
