# QuantDB Changelog

## [2.3.0-dev] - 开发中

### 新增
- 实时数据API：完整的实时股票数据支持
- 财务数据API：财务摘要和指标数据支持
- 指数数据API：完整的指数历史/实时数据支持
- 股票列表API：完整的股票列表功能
- 智能缓存：高性能多功能数据访问策略

### 改进
- 测试覆盖率从39%提升到50% (+11个百分点)
- 新增37个核心测试，100%通过
- 完整国际化：版本显示和用户界面消息100%英文化
- 100%英文代码库：完全适配国际开发者社区

### 新增测试模块
- test_core_models.py - 13个核心模型测试
- test_validators.py - 15个验证器测试
- test_realtime_data_service.py - 9个实时数据服务测试
- test_realtime_api.py - 24个实时API测试
- test_package_quality.py - 质量保证测试套件

### 新增质量保证工具
- test_runner_v2.py - 下一代测试运行器
- package_quality_gate.py - Package质量门控脚本

### 测试质量指标改进
| 指标 | 升级前 | 升级后 | 改进 |
|------|--------|--------|------|
| 总覆盖率 | 39% | 50% | +11% |
| 核心模型覆盖 | 低 | 100% | 完全覆盖 |
| 验证器覆盖 | 14% | 94% | +80% |
| 实时服务覆盖 | 低 | 84% | 大幅提升 |

## [2.2.8] - UX Improvements + API Compatibility (2025-08-07)

### 🔧 User Experience
- API enhancement: `get_stock_data()` now supports positional arguments
  - New support: `qdb.get_stock_data('000001', '20240101', '20240131')`
  - Backward compatible: `qdb.get_stock_data('000001', start_date='20240101', end_date='20240131')`
  - Mixed call: `qdb.get_stock_data('000001', '20240101', end_date='20240131')`
- UX testing: complete acceptance test framework
- Docs update: README_PYPI.md and examples updated; added "Feature details" and index examples
- API exports: top-level export `get_index_data`/`get_index_realtime`/`get_index_list` in `qdb.__init__`

### 🧪 Quality
- 100% tests pass: 149 tests passed
- User journey tests: beginner to pro scenarios
- API compatibility: multiple calling signatures validated

### 📦 Release
- Repository updated to v2.2.8 (source code)
- PyPI: latest published is v2.2.7; v2.2.8 publication pending

## [2.2.7] - PyPI Release + Version Sync (2025-08-07)

### 🚀 PyPI
- Published: https://pypi.org/project/quantdb/2.2.7/
- Version sync across docs to v2.2.7
- Users can `pip install quantdb`
- Full feature set included

### 📚 Docs
- Main READMEs: README.md, README.zh-CN.md, README_PYPI.md
- Docs dir updated accordingly
- Release checklist updated as done

## [2.2.6] - Feature Completion + Docs Update (2025-08-07)

### 📚 Docs readiness for Python package release
- Unified versions to v2.2.6
- Full API docs and examples added
- Feature highlights updated (no more "Coming soon")

### 🎯 Feature set summary (v2.2.6)
- ✅ Realtime: get_realtime_data(), get_realtime_data_batch()
- ✅ Stock list: get_stock_list()
- ✅ Financials: get_financial_summary(), get_financial_indicators()
- ✅ Index data: history + realtime
- ✅ Unified caching
- ✅ 259 tests, production-ready

## [2.2.6] - i18n Finish + Realtime API (2025-08-06)

### 🌍 100% English user-facing messages
- Version string fixes: qdb.__version__ 2.2.4 → 2.2.6
- All user-visible messages translated to English
- Quality assurance: no functional regressions
- PyPI ready: v2.2.6

### 🚀 Realtime quotes
- AKShare integration for spot data with graceful fallback
- Smart TTL (5min during market hours, 60min off-hours)
- API endpoints for single and batch realtime quotes
- Python functions: qdb.get_realtime_data(), qdb.get_realtime_data_batch()
- Robust error handling and tests
- Performance: avg 82.6% speedup, up to 30.7x

### 📦 Files changed
- `qdb/__init__.py`: version
- `qdb/client.py`: English messages
- `qdb/simple_client.py`: English messages
- `cloud/streamlit_cloud/utils/session_manager.py`: English messages
- `core/models/realtime_data.py`: new
- `core/services/realtime_data_service.py`: new
- `api/routers/realtime.py`: new
- `tests/unit/test_realtime_api.py`: new
- `core/cache/akshare_adapter.py`: extended
- `qdb/client.py`, `qdb/simple_client.py`: realtime functions
- `core/models/__init__.py`, `core/models/asset.py`: relations updated
- `api/main.py`: routing integration

## [2.2.4] - Core i18n (2025-08-05)

- All comments translated to English (95%)
- Core services fully updated (models/services/cache)
- Config files updated
- 87 tests passed

### ✅ Fixed in v2.2.6
- Version display mismatch — fixed
- Chinese user messages — translated

## [2.2.3] - Naming & Import (2025-08-05)

- Added note "(import as 'qdb')"
- Expanded keywords for discoverability
- README sections clarified naming vs import
- Unified cloud URL: https://quantdb-cloud.streamlit.app

## [2.2.2] - Docs & URLs (2025-08-05)

- Unified cloud URL
- Chinese & English READMEs updated
- Version info synchronized

## [2.2.1] - PyPI Metadata & README (2025-08-05)

- English description improved
- Install command fixed: pip install qdb → pip install quantdb
- Naming unified
- Badges added

## [2.2.0] - PyPI Release (2025-08-05)

- PyPI: https://pypi.org/project/quantdb/
- Package name: quantdb
- Versions unified to v2.2.0
- Accurate author info
- CLI cleanup
- Build verified

## [2.1.1] - Multi-product Architecture (2025-08-04)

- Python package, API, Cloud app
- High code reuse (>90%)
- AKShare-compatible
- Standardized packaging

## [2.1.0] - Tech Debt Cleanup (2025-08-04)

- Unified versions
- Updated configs
- Branches synced
- Sprint planning established

## [2.0.1] - HK Market Support (2025-06-23)

- Auto-detect 5-digit HK symbols
- Full history support for HK market
- Mixed market support

## [2.0.0] - Internationalization (2025-06-24)

- 100% English UI
- Bilingual READMEs
- Standardized terminology
- Zero functional loss

---

More history: see Git history.

