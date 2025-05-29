# 🛠️ QuantDB 工具集

项目开发和运维工具集合。

## 📁 目录结构

```
tools/
├── README.md                    # 工具集说明
├── monitoring/                  # 系统监控工具
│   ├── water_pool_monitor.py    # 蓄水池状态监控
│   └── system_performance_monitor.py  # 系统性能监控
└── performance/                 # 性能分析工具 🆕
    └── cache_performance_report.py  # 缓存性能报告
```

## 🎯 工具分类

### 📊 系统监控工具 (`monitoring/`)

#### `water_pool_monitor.py`
**用途**: 监控QuantDB蓄水池核心状态
```bash
python tools/monitoring/water_pool_monitor.py
```

**监控指标**:
- 数据库缓存状态 (股票数量、记录数)
- 数据覆盖情况 (时间跨度、数据分布)
- 系统健康度评估
- 核心价值指标验证

#### `system_performance_monitor.py`
**用途**: 系统性能全面监控和基准测试
```bash
python tools/monitoring/system_performance_monitor.py
```

**监控功能**:
- 端到端性能基准测试
- 缓存命中率和性能提升验证
- AKShare调用减少效果监控
- 智能数据获取策略验证

### ⚡ 性能分析工具 (`performance/`)

#### `cache_performance_report.py`
**用途**: 生成详细的缓存性能分析报告
```bash
python tools/performance/cache_performance_report.py
```

**分析功能**:
- 缓存性能对比分析 (QuantDB vs AKShare)
- 响应时间统计和趋势分析
- 价值场景验证报告
- 性能提升量化展示

## 🚀 使用场景

### 开发阶段
- 验证缓存机制是否正常工作
- 监控数据积累和覆盖情况
- 性能基准测试和优化

### 运维阶段
- 定期检查系统健康状态
- 监控核心价值指标
- 性能趋势分析和告警

### 价值验证
- 向用户展示系统核心价值
- 量化缓存效果和成本节省
- 验证智能数据获取策略

## 📝 工具开发规范

### 命名规范
- 监控工具: `*_monitor.py`
- 运维工具: `ops_*.py`
- 分析工具: `analyze_*.py`
- 管理工具: `manage_*.py`

### 代码规范
- 每个工具都应该有清晰的文档说明
- 提供使用示例和预期输出
- 包含错误处理和用户友好的提示
- 支持命令行参数 (如果需要)

## 🔮 未来扩展

计划添加的工具类型:
- **数据管理**: 数据导入/导出、清理工具
- **性能分析**: 详细的性能分析和报告工具
- **运维监控**: 生产环境监控和告警工具
- **开发辅助**: 代码生成、测试数据生成等
