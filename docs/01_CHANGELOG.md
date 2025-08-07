# QuantDB 更新日志

## [2.2.6] - 国际化收尾+实时API完成 (2025-08-06)

### 🎯 Sprint 4.1&4.3 完成 - 100%国际化+实时数据API达成
- **版本显示修复**: 修复qdb.__version__从2.2.4到2.2.6，与PyPI包版本保持一致
- **用户界面完全英文化**: 完成所有剩余中文消息翻译
  - 状态消息: "运行中" → "Running"
  - 缓存消息: "已清除所有缓存" → "Cache cleared"
  - 配置消息: "日志级别已设置为" → "Log level set to"
  - 初始化消息: "QDB已初始化，缓存目录" → "QDB initialized, cache directory"
  - 模式消息: "使用QDB简化模式" → "Using QDB simplified mode"
- **质量保证**: 功能完整性验证，所有用户可见文本100%英文
- **PyPI就绪**: 准备发布v2.2.6，完整国际化版本

### 🚀 Sprint 4.3 完成 - 实时行情数据API
- **AKShare集成**: 实现stock_zh_a_spot接口包装，支持降级机制
- **智能缓存**: SQLite-based缓存，交易时间5分钟TTL，非交易时间60分钟TTL
- **API端点**: GET /api/v1/realtime/stock/{symbol} 单股票实时数据
- **批量API**: POST /api/v1/batch/realtime 批量实时数据查询
- **Python包集成**: qdb.get_realtime_data() 和 qdb.get_realtime_data_batch()
- **错误处理**: 完整的错误处理和降级机制，包含模拟数据支持
- **质量保证**: 全面的单元测试和功能验证
- **性能验证**: 量化性能测试，平均82.6%性能提升，最高30.7倍加速比

### 📦 修改文件
**国际化相关**:
- `qdb/__init__.py`: 版本号更新
- `qdb/client.py`: 用户消息英文化
- `qdb/simple_client.py`: 简化客户端消息英文化
- `cloud/streamlit_cloud/utils/session_manager.py`: 云平台消息英文化

**实时API相关**:
- `core/models/realtime_data.py`: 实时数据模型 (NEW)
- `core/services/realtime_data_service.py`: 实时数据服务 (NEW)
- `api/routers/realtime.py`: 实时数据API路由 (NEW)
- `tests/unit/test_realtime_api.py`: 实时API测试 (NEW)
- `core/cache/akshare_adapter.py`: 扩展实时数据支持
- `qdb/client.py`, `qdb/simple_client.py`: 实时数据函数集成
- `core/models/__init__.py`, `core/models/asset.py`: 模型关系更新
- `api/main.py`: 路由集成

## [2.2.4] - 核心代码国际化完成 (2025-08-05)

### 🌍 重大里程碑 - 100%英文代码库 (95%完成)
- **完整国际化**: 所有中文注释翻译为英文
- **核心服务层**: core/models/, core/services/, core/cache/ 全部英文化
- **配置文件**: MANIFEST.in, setup.py 完全英文化
- **测试验证**: 87个测试通过，无功能回归
- **全球就绪**: 包现已完全适配国际开发者社区

### ✅ 已解决问题 (v2.2.6已修复)
- ~~**版本显示**: PyPI包显示版本不一致~~ → ✅ 已修复
- ~~**用户消息**: 部分日志和状态消息仍为中文~~ → ✅ 已完成英文化

## [2.2.3] - 包名和导入说明完善 (2025-08-05)

### 📚 文档和用户体验优化
- **包描述优化**: 添加"(import as 'qdb')"说明
- **关键词扩展**: 添加qdb和quantdb关键词便于搜索
- **README专门章节**: 详细解释包名vs导入名的区别
- **业界案例对比**: 类似scikit-learn→sklearn的做法
- **欢迎信息优化**: 包含完整使用指南和命名说明
- **云服务地址修复**: 统一为https://quantdb-cloud.streamlit.app

## [2.2.2] - 云服务地址和README内容修复 (2025-08-05)

### 🔗 地址和内容修复
- **云服务地址统一**: 修复为正确的quantdb-cloud.streamlit.app
- **中文README优化**: 更新包名、安装命令、添加PyPI徽章
- **英文README修复**: 确保所有链接和命令正确
- **版本信息同步**: 中英文README内容保持一致

## [2.2.1] - PyPI包描述和README优化 (2025-08-05)

### 📝 PyPI显示优化
- **包描述英文化**: 改为专业英文描述
- **安装命令修正**: pip install qdb → pip install quantdb
- **包名统一**: 所有QDB引用改为QuantDB
- **PyPI徽章添加**: 版本、下载统计等专业展示

## [2.2.0] - PyPI正式发布成功 (2025-08-05)

### 🎉 里程碑1.5完成 - Python包全球发布
- **PyPI发布成功**: https://pypi.org/project/quantdb/
- **包名优化**: 解决qdb冲突，使用quantdb
- **版本统一**: 所有配置文件版本号统一到v2.2.0
- **作者信息规范**: 更新为GitHub真实信息
- **CLI优化**: 移除未实现的CLI入口点
- **包构建验证**: wheel和源码包构建成功
- **功能测试**: 安装和基本功能验证通过

## [2.1.1] - 多产品架构完成版本 (2025-08-04)

### 🎉 重大里程碑 - 产品矩阵完成
- **多产品架构**: 一套代码，多个技术产品
- **Python包开发**: 90%+性能提升的智能缓存包
- **API服务**: 企业级高性能API
- **云平台**: Streamlit Cloud部署版本
- **代码复用率>90%**: 统一核心业务逻辑
- **完全兼容AKShare**: 保持相同API接口
- **标准化开发**: 符合Python包发布规范
- **文档完善**: 多产品文档体系和版本管理

## [2.1.0] - 技术债务清理版本 (2025-08-04)

### 🔧 技术债务清理完成
- **版本统一**: 所有组件版本号统一
- **配置更新**: 覆盖率配置适配新架构
- **分支同步**: main和develop分支完全同步
- **敏捷规范**: 建立Sprint迭代计划

## [2.0.1] - 港股支持和质量提升 (2025-06-23)

### 🇭🇰 港股支持功能完整实现
- **港股代码识别**: 自动识别5位港股代码
- **港股数据获取**: 完整支持港股历史数据查询
- **混合市场支持**: A股和港股统一处理
- **测试通过率**: 提升到90%+

## [2.0.0] - 国际化完成版本 (2025-06-24)

### 🌍 国际化支持全面完成
- **系统界面100%英文化**: 所有页面完全英文化
- **双语文档支持**: README.md英文版，README.zh-CN.md中文版
- **专业术语标准化**: PE/PB/ROE、Market Cap等金融术语
- **功能完整性保证**: 国际化过程中零功能损失

---

*更多历史版本记录请查看Git提交历史*
