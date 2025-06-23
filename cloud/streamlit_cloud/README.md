# QuantDB Cloud Edition

*English | [中文版本](README.zh-CN.md)*

**🌟 Cloud Version** | **📊 Stock Data Platform** | **⚡ Smart Caching** | **☁️ Anytime Access**

## 🎯 Project Overview

QuantDB Cloud Edition is a stock data query platform optimized for Streamlit Cloud, providing:

- 📈 **Stock Data Query**: Supports A-share historical data query and multi-dimensional chart display
- 📊 **Asset Information Display**: Real company names, financial metrics, market data
- ⚡ **Smart Caching**: SQLite database persistent caching with 98.1% performance improvement
- 🎨 **Professional Charts**: Interactive data visualization based on Plotly

## 🚀 Online Experience

**Deployment URL**: [Coming Soon]

## 💻 Local Development

```bash
# Clone repository
git clone https://github.com/franksunye/quantdb.git
cd quantdb

# Switch to cloud branch
git checkout streamlit-cloud-deployment

# Enter cloud application directory
cd cloud/streamlit_cloud

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

## 📋 Features

### Core Functions
- ✅ A-share stock data query (Shanghai and Shenzhen markets)
- ✅ Price trend charts and volume chart display
- ✅ Company basic information and financial metrics
- ✅ SQLite database persistent caching
- ✅ System status monitoring and performance testing
- ✅ Data export (CSV format)

### Technical Features
- ✅ **High-performance caching**: 98.1% faster than direct AKShare calls
- ✅ **Real asset information**: Display real company names instead of stock codes
- ✅ **Smart cache strategy**: Based on trading calendar, avoid invalid API calls
- ✅ **Complete error handling**: Comprehensive exception handling and user feedback
- ✅ **Professional interface**: Clean and intuitive user interface design
- ✅ **Multi-chart support**: Price trends, volume, performance comparison charts

## 🏗️ Architecture

### Core Architecture Migration
This version has completed migration to QuantDB core service architecture:

#### ✅ Completed Upgrades
- **Core Service Integration**: Uses unified `core/` modules
- **Code Reuse**: Shares business logic with other deployment modes
- **Architecture Consistency**: Follows project architecture evolution planning
- **Feature Preservation**: 100% retention of all original features

#### 🔧 Technical Improvements
- **Import Paths**: Migrated from `src/` to `core/`
- **Service Reuse**: Uses `core.services`, `core.models`, `core.cache`
- **Unified Configuration**: Compatible with multiple deployment path configurations
- **Code Cleanup**: Removed duplicate code while maintaining cloud-specific features

## 🚀 Deploy to Streamlit Cloud

### 1. Prepare GitHub Repository
```bash
# Ensure code is pushed to GitHub
git add .
git commit -m "feat: Streamlit Cloud deployment ready"
git push origin streamlit-cloud-deployment
```

### 2. Configure Streamlit Cloud
1. Visit https://share.streamlit.io/
2. Connect GitHub account
3. Select repository: `franksunye/quantdb`
4. Select branch: `streamlit-cloud-deployment`
5. Set main file path: `cloud/streamlit_cloud/app.py`
6. Click deploy

### 3. Verify Deployment
- Check all page functions work normally
- Verify SQLite database read/write
- Test stock data query functionality
- Confirm chart display is normal

## 🧪 Test Checklist

### Functional Testing
- [ ] Stock data query function works normally
- [ ] Asset information display is correct
- [ ] System status monitoring works
- [ ] Charts display correctly
- [ ] Database read/write is normal
- [ ] Cache mechanism is effective

### Performance Testing
- [ ] First query response time < 3 seconds
- [ ] Cache hit response time < 1 second
- [ ] Page load time < 5 seconds
- [ ] Memory usage is reasonable

## 📄 License

MIT License - see [LICENSE](../../LICENSE) file for details

## 🔗 Related Links

- **Main Project**: [QuantDB](../../README.md)
- **GitHub**: [https://github.com/franksunye/quantdb](https://github.com/franksunye/quantdb)
- **Documentation**: [Project Documentation](../../docs/)

---

⭐ If this project helps you, please give it a Star!
