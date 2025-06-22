# Streamlit Cloud 部署问题修复指南

## 问题描述
Streamlit Cloud部署时出现 "No module named 'fastapi'" 错误，但本地运行正常。

## 根本原因
1. **依赖差异**: Streamlit Cloud环境缺少FastAPI相关依赖
2. **模块导入**: 应用试图导入core模块，但core模块依赖FastAPI
3. **路径问题**: Streamlit Cloud的文件结构可能与本地不同

## 解决方案

### 1. 确保正确的requirements.txt
确保 `cloud/streamlit_cloud/requirements.txt` 包含所有必要依赖：

```txt
# QuantDB Streamlit Cloud Edition - Dependencies
streamlit>=1.28.0
pandas>=1.3.0
numpy>=1.20.0
akshare>=1.0.0
sqlalchemy>=1.4.0
requests>=2.26.0
plotly>=5.15.0
python-dateutil>=2.8.0
pydantic>=1.8.0
python-dotenv>=0.19.0

# FastAPI相关依赖（core模块需要）
fastapi>=0.68.0
uvicorn>=0.15.0
httpx>=0.18.0
tenacity>=9.1.0

# 可选增强功能
streamlit-option-menu>=0.3.6
```

### 2. Streamlit Cloud 配置
在Streamlit Cloud中设置：

- **Repository**: `https://github.com/franksunye/quantdb`
- **Branch**: `streamlit-cloud-deployment`
- **Main file path**: `cloud/streamlit_cloud/app.py`
- **Requirements file**: `cloud/streamlit_cloud/requirements.txt`

### 3. 环境变量（如果需要）
在Streamlit Cloud的Secrets中添加：

```toml
[general]
DATABASE_URL = "sqlite:///database/stock_data.db"
ENVIRONMENT = "production"
```

### 4. 验证部署
部署后检查：

1. **依赖安装**: 查看部署日志确认所有依赖正确安装
2. **文件结构**: 确认database目录和文件存在
3. **错误日志**: 查看具体的错误信息

## 应急方案

如果问题持续，可以：

1. **简化依赖**: 移除不必要的FastAPI依赖
2. **使用本地模块**: 完全避免导入core模块
3. **分步部署**: 先部署基础功能，再逐步添加复杂功能

## 测试步骤

### 本地测试
```bash
cd cloud/streamlit_cloud
pip install -r requirements.txt
streamlit run app.py
```

### 云端验证
1. 推送代码到GitHub
2. 在Streamlit Cloud中重新部署
3. 检查启动日志
4. 测试基本功能

## 联系支持

如果问题仍然存在：
1. 检查Streamlit Cloud的部署日志
2. 确认GitHub仓库的文件结构
3. 验证requirements.txt的内容
4. 考虑使用Streamlit Community论坛寻求帮助
