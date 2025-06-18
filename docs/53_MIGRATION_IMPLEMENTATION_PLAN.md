# QuantDB 架构迁移实施方案

**目标**: 从当前结构迁移到多模式部署架构 | **时间**: 2-3周 | **策略**: 渐进式重构

## 🎯 迁移策略

### 核心原则
1. **向后兼容**: 确保现有功能在迁移过程中正常工作
2. **渐进式重构**: 分阶段进行，每个阶段都可以独立验证
3. **最小风险**: 保持主分支稳定，在新分支进行重构
4. **功能优先**: 优先保证核心功能，再优化架构

## 📋 第一阶段：Streamlit Cloud快速部署 (3-5天)

### 目标
在不改变现有架构的前提下，快速实现Streamlit Cloud部署

### 实施步骤

#### 1.1 创建云端部署分支
```bash
# 基于当前分支创建云端部署版本
git checkout -b cloud-deployment-v1
mkdir -p cloud/streamlit_cloud
```

#### 1.2 创建单体应用结构
```
cloud/streamlit_cloud/
├── app.py                          # 主应用入口
├── pages/                          # 页面文件
│   ├── 1_📈_股票数据查询.py
│   ├── 2_📊_资产信息.py
│   └── 3_⚡_系统状态.py
├── src/                           # 复制现有src目录
│   ├── services/                  # 业务服务
│   ├── cache/                     # 缓存层
│   ├── api/                       # API模型和工具
│   └── config.py                  # 配置文件
├── database/                      # 复制数据库文件
│   ├── stock_data.db
│   └── schema.sql
├── requirements.txt               # 整合依赖
├── .streamlit/
│   └── config.toml
└── README.md
```

#### 1.3 核心代码适配
```python
# cloud/streamlit_cloud/app.py
import streamlit as st
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 直接导入现有服务
from services.stock_data_service import StockDataService
from services.asset_info_service import AssetInfoService
from services.database_cache import DatabaseCache

# 初始化服务
@st.cache_resource
def init_services():
    """初始化服务实例"""
    return {
        'stock_service': StockDataService(),
        'asset_service': AssetInfoService(),
        'cache_service': DatabaseCache()
    }

def main():
    st.set_page_config(
        page_title="QuantDB - 量化数据平台",
        page_icon="📊",
        layout="wide"
    )
    
    services = init_services()
    
    # 主页面内容
    st.title("📊 QuantDB - 量化数据平台")
    # ... 其他页面内容
```

#### 1.4 页面实现
```python
# cloud/streamlit_cloud/pages/1_📈_股票数据查询.py
import streamlit as st
import sys
from pathlib import Path

# 路径设置
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from services.stock_data_service import StockDataService

def main():
    st.title("📈 股票数据查询")
    
    # 初始化服务
    stock_service = StockDataService()
    
    # 用户输入
    col1, col2, col3 = st.columns(3)
    with col1:
        symbol = st.text_input("股票代码", placeholder="例如: 600000")
    with col2:
        start_date = st.date_input("开始日期")
    with col3:
        end_date = st.date_input("结束日期")
    
    if st.button("查询数据"):
        if symbol:
            # 直接调用现有服务
            result = stock_service.get_historical_data(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if result:
                # 显示结果
                st.success(f"获取到 {len(result)} 条数据")
                st.dataframe(result)
            else:
                st.error("获取数据失败")

if __name__ == "__main__":
    main()
```

#### 1.5 依赖整合
```txt
# cloud/streamlit_cloud/requirements.txt
# 核心框架
streamlit>=1.28.0

# 现有项目依赖
pandas>=1.3.0
numpy>=1.20.0
akshare>=1.0.0
sqlalchemy>=1.4.0
plotly>=5.15.0
requests>=2.26.0
python-dateutil>=2.8.0

# FastAPI相关（用于模型定义）
pydantic>=1.8.0
```

### 1.6 快速验证
```bash
cd cloud/streamlit_cloud
pip install -r requirements.txt
streamlit run app.py
```

## 📋 第二阶段：架构重构准备 (1周)

### 目标
在保持功能正常的前提下，重新组织代码结构

### 实施步骤

#### 2.1 创建新架构分支
```bash
git checkout -b architecture-v2
```

#### 2.2 创建核心业务层
```bash
mkdir -p core/{models,services,database,cache,utils}
```

#### 2.3 代码迁移映射

| 现有位置 | 新位置 | 说明 |
|----------|--------|------|
| `src/api/models.py` | `core/models/` | 数据模型 |
| `src/services/` | `core/services/` | 业务服务 |
| `src/cache/` | `core/cache/` | 缓存层 |
| `src/api/database.py` | `core/database/connection.py` | 数据库连接 |
| `src/config.py` | `core/config.py` | 配置管理 |

#### 2.4 逐步迁移脚本
```python
# scripts/migrate_to_core.py
import shutil
from pathlib import Path

def migrate_code():
    """代码迁移脚本"""
    migrations = [
        ("src/api/models.py", "core/models/"),
        ("src/services/", "core/services/"),
        ("src/cache/", "core/cache/"),
        ("src/config.py", "core/config.py")
    ]
    
    for source, target in migrations:
        source_path = Path(source)
        target_path = Path(target)
        
        if source_path.exists():
            if source_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
            else:
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            
            print(f"Migrated {source} -> {target}")

if __name__ == "__main__":
    migrate_code()
```

## 📋 第三阶段：多服务架构实现 (1-2周)

### 目标
实现API、Admin、WebApp三个独立服务

### 实施步骤

#### 3.1 API服务独立化
```python
# api/main.py
from fastapi import FastAPI
import sys
from pathlib import Path

# 添加core目录到路径
core_dir = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_dir))

from services.stock_data_service import StockDataService
from services.asset_info_service import AssetInfoService

app = FastAPI(title="QuantDB API")

# 初始化服务
stock_service = StockDataService()
asset_service = AssetInfoService()

@app.get("/api/v1/stocks/{symbol}")
async def get_stock_data(symbol: str, start_date: str, end_date: str):
    """获取股票数据"""
    result = stock_service.get_historical_data(symbol, start_date, end_date)
    return {"data": result}

@app.get("/api/v1/assets/{symbol}")
async def get_asset_info(symbol: str):
    """获取资产信息"""
    result = asset_service.get_asset_info(symbol)
    return {"data": result}
```

#### 3.2 管理后台开发
```python
# admin/app.py
import streamlit as st
import sys
from pathlib import Path

# 添加core目录到路径
core_dir = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_dir))

from services.stock_data_service import StockDataService
from database.connection import get_db_session

st.set_page_config(
    page_title="QuantDB 管理后台",
    page_icon="👨‍💼",
    layout="wide"
)

def main():
    st.title("👨‍💼 QuantDB 管理后台")
    
    # 管理功能
    tab1, tab2, tab3 = st.tabs(["数据概览", "数据管理", "系统监控"])
    
    with tab1:
        # 数据统计
        db = get_db_session()
        # 显示数据库统计信息
        
    with tab2:
        # 数据管理功能
        # 批量导入、删除、更新等
        
    with tab3:
        # 系统监控
        # 性能指标、缓存状态等

if __name__ == "__main__":
    main()
```

#### 3.3 SaaS应用开发
```python
# webapp/app.py
import streamlit as st
import requests
from pathlib import Path

# 配置API地址
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="QuantDB - 股票数据平台",
    page_icon="🌐",
    layout="wide"
)

def call_api(endpoint: str, params: dict = None):
    """调用API服务"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        return response.json()
    except Exception as e:
        st.error(f"API调用失败: {e}")
        return None

def main():
    st.title("🌐 QuantDB - 股票数据平台")
    
    # 用户界面
    symbol = st.text_input("股票代码")
    if st.button("查询"):
        if symbol:
            # 调用API服务
            result = call_api(f"stocks/{symbol}", {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            })
            
            if result:
                st.success("查询成功")
                st.json(result)

if __name__ == "__main__":
    main()
```

## 🚀 部署配置

### Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  quantdb-api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database
      - ./core:/app/core
    environment:
      - DATABASE_URL=sqlite:///database/stock_data.db

  quantdb-admin:
    build: ./admin
    ports:
      - "8501:8501"
    volumes:
      - ./database:/app/database
      - ./core:/app/core
    depends_on:
      - quantdb-api

  quantdb-webapp:
    build: ./webapp
    ports:
      - "8502:8502"
    environment:
      - API_BASE_URL=http://quantdb-api:8000/api/v1
    depends_on:
      - quantdb-api

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - quantdb-api
      - quantdb-admin
      - quantdb-webapp
```

## 📊 迁移验证清单

### 功能验证
- [ ] 股票数据查询功能正常
- [ ] 资产信息展示正确
- [ ] 缓存机制工作正常
- [ ] 图表显示无误
- [ ] 数据库读写正常

### 性能验证
- [ ] API响应时间 < 2秒
- [ ] 页面加载时间 < 5秒
- [ ] 缓存命中率 > 80%
- [ ] 内存使用合理

### 部署验证
- [ ] 本地开发环境正常
- [ ] Docker容器启动成功
- [ ] Streamlit Cloud部署成功
- [ ] 多服务协同工作正常

## 🎯 成功标准

1. **功能完整性**: 所有现有功能在新架构下正常工作
2. **性能保持**: 性能指标不低于现有水平
3. **部署灵活性**: 支持多种部署模式
4. **代码质量**: 代码结构清晰，易于维护
5. **文档完善**: 每个服务都有完整的使用文档

这个迁移方案既满足了你的即时需求（Streamlit Cloud部署），又为未来的架构演进奠定了基础。你觉得这个实施计划如何？需要我详细说明某个阶段吗？
