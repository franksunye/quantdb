# QuantDB

*English | [中文版本](README.zh-CN.md)*

![Version](https://img.shields.io/badge/version-2.2.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python Package](https://img.shields.io/badge/PyPI-quantdb-blue)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-259/259-success)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![Cloud](https://img.shields.io/badge/Cloud-Ready-brightgreen)
![Performance](https://img.shields.io/badge/Cache-90%25_faster-brightgreen)
![Integration](https://img.shields.io/badge/Integration-Complete-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

**Intelligent caching wrapper for AKShare with 90%+ performance boost** - Complete stock data ecosystem with smart SQLite caching for Chinese financial markets.

**🎉 NOW AVAILABLE ON PyPI!**
[![PyPI version](https://badge.fury.io/py/quantdb.svg)](https://pypi.org/project/quantdb/)
[![Downloads](https://pepy.tech/badge/quantdb)](https://pepy.tech/project/quantdb)

```bash
pip install quantdb  # One command, instant 90%+ speed boost!
```

**Three product formats**: Python Package, API Service, and Cloud Platform for different user needs.

## 🎯 Product Matrix

### 📦 **QuantDB Python Package** - For Developers
```bash
pip install quantdb
```
```python
import qdb  # Import as qdb for API consistency
df = qdb.get_stock_data("000001", days=30)  # 90%+ faster than AKShare!
```
**Perfect for**: Quantitative researchers, Python developers, data scientists

### 🚀 **API Service** - For Enterprises
```bash
curl "https://your-api.com/api/v1/stocks/000001/data?days=30"
```
**Perfect for**: Enterprise teams, multi-user applications, production systems

### ☁️ **Cloud Platform** - For Individual Investors
Visit: [QuantDB Cloud Platform](https://quantdb-cloud.streamlit.app)
**Perfect for**: Individual investors, data analysis, visualization

## ✨ Core Features

- **🚀 90%+ Performance Boost**: Smart SQLite caching, millisecond response time
- **📦 Multiple Product Forms**: Python package, API service, cloud platform
- **🔄 Full AKShare Compatibility**: Same API interface, seamless replacement
- **💾 Local Caching**: Offline available, intelligent incremental updates
- **📅 Trading Calendar Integration**: Smart data fetching based on real trading days
- **🛠️ Zero Configuration**: pip install and ready to use
- **☁️ Cloud Deployment Ready**: Supports Railway, Render, Alibaba Cloud, etc.
- **🧠 Intelligent Updates**: Automatic missing data detection and fetching

## ⚡ Performance Highlights

| Metric | Direct AKShare Call | QuantDB Package | Performance Improvement |
|--------|-------------------|-------------|------------------------|
| **Response Time** | ~1000ms | ~10ms | **99%** ⬆️ |
| **Cache Hit** | N/A | 90%+ | **Smart Cache** ✅ |
| **Trading Day Recognition** | Manual | Automatic | **Intelligent** 🧠 |
| **Installation** | Complex setup | `pip install quantdb` | **One Command** 🚀 |

## 🚀 Quick Start

### Option 1: Python Package (Recommended)
```bash
# Install
pip install quantdb

# Use immediately
python -c "
import qdb
df = qdb.get_stock_data('000001', days=30)
print(f'Got {len(df)} records with 90%+ speed boost!')
"
```

### Option 2: Cloud Platform Access
Direct access to deployed Streamlit Cloud version:
- **Frontend Interface**: [QuantDB Cloud](https://quantdb-cloud.streamlit.app)
- **Complete Features**: Stock data query, asset information, cache monitoring, watchlist management

### Option 3: Local API Service

#### 1. Installation and Setup

```bash
# Clone repository
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/scripts/init_db.py
```

#### 2. Start Services

**Method 1: One-click Start (Recommended)**
```bash
# Enter frontend directory and run startup script
cd quantdb_frontend
python start.py
# Script will automatically start backend API and frontend interface
```

**Method 2: Manual Start**
```bash
# 1. Start backend API (in project root)
python src/api/main.py

# 2. Start frontend interface (in new terminal)
cd quantdb_frontend
streamlit run app.py

# Access URLs
# Frontend Interface: http://localhost:8501
# API Documentation: http://localhost:8000/docs
```

**Method 3: Cloud Version Local Run**
```bash
# Run Streamlit Cloud version (integrated backend services)
cd cloud/streamlit_cloud
streamlit run app.py
# Access URL: http://localhost:8501
```

### 3. Using API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get stock data (auto-cached, displays real company names)
curl "http://localhost:8000/api/v1/historical/stock/600000?start_date=20240101&end_date=20240131"

# Get asset information (includes financial metrics)
curl "http://localhost:8000/api/v1/assets/symbol/600000"

# View cache status
curl http://localhost:8000/api/v1/cache/status
```

### 4. Run Tests

```bash
# Run backend tests
python scripts/test_runner.py --all

# Run frontend tests
cd quantdb_frontend
python run_tests.py

# Run performance tests
python scripts/test_runner.py --performance
```

## 🏗️ Architecture Overview

QuantDB adopts modern microservice architecture with the following core components:

- **🔧 Core Services**: Unified business logic layer supporting multiple deployment modes
- **📡 FastAPI Backend**: High-performance REST API service
- **📱 Streamlit Frontend**: Interactive data analysis interface
- **☁️ Cloud Deployment**: Cloud deployment version supporting Streamlit Cloud
- **🧪 Comprehensive Testing**: Complete test suite covering unit, integration, API, E2E tests
- **📊 Smart Caching**: Intelligent caching system based on trading calendar

For detailed architecture design, please refer to [System Architecture Documentation](./docs/10_ARCHITECTURE.md).

## 🔧 Technology Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Streamlit + Plotly + Pandas
- **Data Source**: AKShare (Official Stock Data)
- **Caching**: Smart database caching + trading calendar
- **Testing**: pytest + unittest (259 tests, 100% pass rate)
- **Monitoring**: Real-time performance monitoring and data tracking
- **Logging**: Unified logging system with completely consistent recording
- **Integration**: Complete frontend-backend integration solution

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📋 Project Status](./docs/00_BACKLOG.md) | Current progress and priorities |
| [📅 Changelog](./docs/01_CHANGELOG.md) | Version history and changes |
| [🏗️ System Architecture](./docs/10_ARCHITECTURE.md) | Architecture design and components |
| [🗄️ Database Architecture](./docs/11_DATABASE_ARCHITECTURE.md) | Database design and models |
| [📊 API Documentation](./docs/20_API.md) | Complete API usage guide |
| [🛠️ Development Guide](./docs/30_DEVELOPMENT.md) | Development environment and workflow |
| [🧪 Testing Guide](./docs/31_TESTING.md) | Test execution and writing |

## 🎯 Project Status

**Current Version**: v2.0.1 (Complete Hong Kong Stock Support)
**Next Version**: v2.1.0 (Enhanced Monitoring and Analysis Features)
**MVP Score**: 10/10 (Core features complete, cloud deployment ready)
**Test Coverage**: 259/259 passed (100%) - 222 backend + 37 frontend
**Data Quality**: ⭐⭐⭐⭐⭐ (5/5) - Real company names and financial metrics
**Frontend Experience**: ⭐⭐⭐⭐⭐ (5/5) - Professional quantitative data platform interface
**Integration Status**: ✅ Complete frontend-backend integration, cloud deployment ready
**Production Ready**: ⭐⭐⭐⭐⭐ (5/5) - Cloud deployment version complete
**Cloud Deployment**: ✅ Streamlit Cloud version, directly using backend services

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **API Documentation**: http://localhost:8000/docs (access after starting service)
- **Project Maintainer**: frank

---

⭐ If this project helps you, please give it a Star!
