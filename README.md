# QuantDB

*English | [中文版本](README.zh-CN.md)*

![Version](https://img.shields.io/badge/version-2.0.1-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![API](https://img.shields.io/badge/API-FastAPI-009688)
![Database](https://img.shields.io/badge/Database-SQLite-4169E1)
![Tests](https://img.shields.io/badge/Tests-259/259-success)
![Frontend](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![Cloud](https://img.shields.io/badge/Cloud-Ready-brightgreen)
![Performance](https://img.shields.io/badge/Cache-98.1%25_faster-brightgreen)
![Integration](https://img.shields.io/badge/Integration-Complete-success)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

High-performance stock data caching service based on AKShare data source, providing intelligent caching, RESTful API, and professional frontend interface.

**🚀 Cloud Deployment Ready!** Now provides complete cloud deployment solutions, including local development environment and Streamlit Cloud deployment version.

## 🎯 Core Value

- **🚀 Ultimate Performance**: Smart caching is **98.1%** faster than direct AKShare calls, response time ~18ms
- **☁️ Cloud Deployment**: Supports Streamlit Cloud deployment, one-click access to professional quantitative data platform
- **📊 Data Accuracy**: Based on official trading calendar, ensuring completeness and accuracy of stock data
- **🏢 Real Asset Information**: Display real company names (e.g., "SPDB") instead of technical codes (e.g., "Stock 600000")
- **💰 Financial Metrics Integration**: PE, PB, ROE and other key financial indicators from AKShare real-time data
- **⚡ Smart Caching**: Automatically identifies trading days, avoids invalid API calls, significantly improves efficiency
- **🔄 Real-time Monitoring**: Complete performance monitoring and data coverage tracking
- **📝 Unified Logging**: Completely unified logging system, eliminating dual logging inconsistencies
- **🧹 Clean Structure**: Agile development cleanup, 47% reduction in project files, easier maintenance
- **🛡️ Production Ready**: Complete error handling, 259 tests with 100% pass rate, comprehensive documentation system
- **📱 Professional Frontend**: Local and cloud dual versions, supporting multiple charts, performance monitoring, asset information display
- **🔧 Backend Integration**: Cloud version directly uses backend services, queries real database data

## ⚡ Performance Highlights

| Metric | Direct AKShare Call | QuantDB Cache | Performance Improvement |
|--------|-------------------|---------------|------------------------|
| **Response Time** | ~1000ms | ~18ms | **98.1%** ⬆️ |
| **Cache Hit** | N/A | 100% | **Perfect Cache** ✅ |
| **Trading Day Recognition** | Manual | Automatic | **Intelligent** 🧠 |

## 🚀 Quick Start

### Option 1: Cloud Access (Recommended)
Direct access to deployed Streamlit Cloud version:
- **Frontend Interface**: [QuantDB Cloud](https://quantdb.streamlit.app) (Coming Soon)
- **Complete Features**: Stock data query, asset information, cache monitoring, watchlist management

### Option 2: Local Deployment

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
