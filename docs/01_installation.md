# 安装指南

## 📦 从 PyPI 安装（推荐）

```bash
pip install quantdb
```

## 🔧 从源码安装

```bash
# 克隆仓库
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

## 📋 系统要求

- Python 3.8+
- 操作系统：Windows, macOS, Linux
- 内存：建议 4GB+
- 磁盘空间：至少 1GB（用于数据缓存）

## 🔍 验证安装

```python
import qdb

# 检查版本
print(qdb.__version__)

# 简单测试
data = qdb.stock_zh_a_hist("000001")
print(data.head())
```

## 🚨 常见问题

### 依赖冲突
如果遇到依赖冲突，建议使用虚拟环境：

```bash
python -m venv quantdb_env
source quantdb_env/bin/activate  # Linux/Mac
# 或
quantdb_env\Scripts\activate     # Windows

pip install quantdb
```

### 网络问题
如果下载速度慢，可以使用国内镜像：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple quantdb
```

## 📚 下一步

安装完成后，请查看：
- [快速开始](02_quickstart.md) - 5分钟上手指南
- [用户指南](03_user-guide.md) - 详细使用教程
- [API参考](04_api-reference.md) - 完整API文档
