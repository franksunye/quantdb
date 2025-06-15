# QuantDB Frontend 部署指南

**版本**: v1.0.0-mvp | **更新**: 2025-06-15

## 🚀 快速部署

### 方法1: 一键启动 (推荐)

```bash
# 进入前端目录
cd quantdb_frontend

# 运行启动脚本 (自动处理依赖和后端启动)
python start.py
```

### 方法2: 手动启动

```bash
# 1. 启动后端API (在QuantDB根目录)
cd ..
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 2. 安装前端依赖 (在quantdb_frontend目录)
cd quantdb_frontend
pip install -r requirements.txt

# 3. 启动前端应用
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 📋 环境要求

### 系统要求
- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python版本**: 3.8+
- **内存**: 最低2GB，推荐4GB+
- **磁盘空间**: 最低1GB可用空间

### Python依赖
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
requests>=2.31.0
python-dateutil>=2.8.0
```

## 🔧 配置选项

### 环境变量
```bash
# API服务地址 (默认: http://localhost:8000)
export QUANTDB_API_URL=http://localhost:8000

# API请求超时时间 (默认: 30秒)
export API_TIMEOUT=30
```

### 配置文件
编辑 `utils/config.py` 可以修改以下配置：
- API基础URL
- 默认查询天数
- 图表样式和颜色
- 错误消息文本

## 🌐 网络部署

### 本地网络访问
```bash
# 启动时指定地址，允许局域网访问
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### 云端部署 (Streamlit Cloud)

1. **准备代码**
   ```bash
   # 确保代码已推送到GitHub
   git add .
   git commit -m "Add frontend application"
   git push origin main
   ```

2. **部署到Streamlit Cloud**
   - 访问 https://share.streamlit.io/
   - 连接GitHub仓库
   - 选择 `quantdb_frontend/app.py` 作为主文件
   - 配置环境变量 `QUANTDB_API_URL`

3. **配置后端API**
   - 确保后端API可以从外网访问
   - 更新CORS设置允许Streamlit Cloud域名

### Docker部署

1. **创建Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
   ```

2. **构建和运行**
   ```bash
   # 构建镜像
   docker build -t quantdb-frontend .
   
   # 运行容器
   docker run -p 8501:8501 -e QUANTDB_API_URL=http://host.docker.internal:8000 quantdb-frontend
   ```

## 🔒 安全配置

### 生产环境安全
```python
# 在config.py中配置
ALLOWED_ORIGINS = ["https://yourdomain.com"]
API_KEY_REQUIRED = True
HTTPS_ONLY = True
```

### API安全
- 配置API Key认证
- 启用HTTPS
- 设置请求频率限制
- 配置CORS白名单

## 📊 性能优化

### 缓存配置
```python
# 在页面中使用缓存
@st.cache_data(ttl=300)  # 5分钟缓存
def get_stock_data_cached(symbol, start_date, end_date):
    return api_client.get_stock_data(symbol, start_date, end_date)
```

### 资源优化
- 启用Streamlit的内置缓存
- 优化图表渲染性能
- 使用懒加载大数据集
- 压缩静态资源

## 🔍 故障排除

### 常见问题

**1. 前端无法连接后端API**
```bash
# 检查后端是否运行
curl http://localhost:8000/api/v1/health

# 检查防火墙设置
# Windows: 允许Python通过防火墙
# Linux: sudo ufw allow 8000
```

**2. 依赖安装失败**
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**3. Streamlit启动失败**
```bash
# 检查端口是否被占用
netstat -an | grep 8501

# 使用不同端口
streamlit run app.py --server.port 8502
```

**4. 图表不显示**
- 检查浏览器JavaScript是否启用
- 清除浏览器缓存
- 尝试不同浏览器

### 日志调试
```bash
# 启用详细日志
streamlit run app.py --logger.level debug

# 查看错误日志
tail -f ~/.streamlit/logs/streamlit.log
```

## 📈 监控和维护

### 健康检查
```python
# 添加健康检查端点
def health_check():
    try:
        # 检查API连接
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

### 性能监控
- 监控页面加载时间
- 跟踪API响应时间
- 监控内存使用情况
- 记录用户访问日志

### 定期维护
- 更新依赖包版本
- 清理缓存数据
- 备份用户配置
- 检查安全更新

## 🔗 相关链接

- **Streamlit文档**: https://docs.streamlit.io/
- **Plotly文档**: https://plotly.com/python/
- **QuantDB后端**: ../README.md
- **API文档**: http://localhost:8000/docs

## 📞 技术支持

如果遇到部署问题，请：

1. 检查本文档的故障排除部分
2. 查看GitHub Issues: https://github.com/franksunye/quantdb/issues
3. 提交新的Issue并提供详细的错误信息

---

⚡ 快速开始: `python start.py`
