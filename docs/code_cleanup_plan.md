# QuantDB 代码整理和精简计划

## 文档信息
**文档类型**: 代码整理计划  
**文档编号**: quantdb-CLEANUP-001  
**版本**: 1.0.0  
**创建日期**: 2025-01-27  
**最后更新**: 2025-01-27  
**状态**: 执行计划  
**负责人**: frank  

---

## 1. 整理目标

### 1.1 主要目标
- **减少代码冗余**: 移除重复和过时的文件
- **明确架构方向**: 统一技术架构，移除实验性代码
- **提高可维护性**: 简化项目结构，提高代码质量
- **聚焦核心功能**: 移除与核心平台目标不符的功能

### 1.2 预期收益
- 减少项目复杂度 30-40%
- 提高开发效率 20-30%
- 降低维护成本 40-50%
- 改善新开发者上手体验

---

## 2. 代码整理清单

### 2.1 重复文件处理

#### 数据库模块整理
```
操作: 移除旧版数据库模块
文件: src/database.py
原因: 已被 src/api/database.py (SQLAlchemy版本) 替代
影响: 需要更新所有引用此模块的代码
```

#### 主程序入口重命名
```
操作: 重命名以明确用途
文件: src/main.py -> src/cli_main.py
原因: 与 src/api/main.py 功能不同，避免混淆
影响: 更新文档和脚本中的引用
```

#### AKShare适配器统一
```
操作: 采用简化版作为主版本
保留: src/cache/akshare_adapter_simplified.py -> src/cache/akshare_adapter.py
移除: src/cache/akshare_adapter.py (旧版)
原因: 简化版架构更清晰，性能更好
影响: 更新所有相关导入和配置
```

#### API路由整理
```
操作: 合并历史数据路由
保留: src/api/routes/historical_data_simplified.py -> src/api/routes/historical_data.py
移除: src/api/routes/historical_data.py (旧版)
原因: 新版本功能更完善，架构更合理
影响: 更新路由注册和测试
```

### 2.2 特定功能文件处理

#### 移动到工具目录
创建 `tools/` 目录，移动以下文件：
```
src/calculate_ma_above_ratio.py -> tools/analysis/ma_ratio_calculator.py
src/entry_window_performance_analysis.py -> tools/analysis/entry_window_analyzer.py
src/trade_plan_performance_analysis.py -> tools/analysis/trade_plan_analyzer.py
```

#### 移动到示例目录
创建 `examples/` 目录，移动以下文件：
```
src/generate_trade_logs.py -> examples/trading/trade_log_generator.py
src/import_optimization_results.py -> examples/trading/optimization_importer.py
src/import_trade_signals.py -> examples/trading/signal_importer.py
src/signal_sender.py -> examples/trading/signal_sender.py
src/signal_to_plan.py -> examples/trading/signal_to_plan.py
src/update_trade_logs.py -> examples/trading/trade_log_updater.py
src/update_trade_plan_metrics.py -> examples/trading/plan_metrics_updater.py
```

#### 完全移除的文件
以下文件功能重复或已过时：
```
src/update_assets.py (功能已集成到服务层)
src/processor.py (功能不明确，未被使用)
src/scheduler.py (功能不明确，未被使用)
src/trace_logger.py (功能重复，已有logger模块)
```

### 2.3 测试脚本整理

#### 统一测试管理
创建统一的测试管理脚本：
```
新建: scripts/test_runner.py
移除: run_test.py, run_tests.py, run_specific_tests.py, run_e2e_tests.py, run_coverage.py
```

#### 测试脚本功能整合
```python
# scripts/test_runner.py 功能规划
- 单元测试运行
- 集成测试运行  
- 端到端测试运行
- 覆盖率测试
- 性能测试
- 测试报告生成
```

### 2.4 缓存系统整理

#### 移除复杂缓存组件
```
移除: src/cache/cache_engine.py
移除: src/cache/freshness_tracker.py  
移除: src/cache/data_injector.py
移除: src/cache/preloader.py
原因: 简化架构已证明更有效
```

#### 保留核心缓存组件
```
保留: src/services/database_cache.py
保留: src/services/stock_data_service.py
原因: 这些是新架构的核心组件
```

---

## 3. 目录结构重组

### 3.1 新的项目结构
```
quantdb/
├── src/                          # 核心源代码
│   ├── api/                      # API层
│   ├── services/                 # 服务层
│   ├── cache/                    # 缓存层（简化）
│   ├── mcp/                      # MCP协议
│   ├── scripts/                  # 核心脚本
│   ├── config.py                 # 配置
│   ├── logger.py                 # 日志
│   ├── cli_main.py              # 命令行工具
│   └── indicators.py            # 技术指标（核心功能）
├── tools/                        # 分析工具
│   └── analysis/                 # 数据分析工具
├── examples/                     # 使用示例
│   └── trading/                  # 交易相关示例
├── scripts/                      # 项目管理脚本
│   ├── test_runner.py           # 统一测试管理
│   ├── setup_dev_env.py         # 开发环境设置
│   └── fix_deprecation_warnings.py
├── tests/                        # 测试代码
├── docs/                         # 项目文档
└── database/                     # 数据库文件
```

### 3.2 domain目录处理
```
当前状态: src/domain/ 目录存在但为空
处理方案: 移除空的domain目录，或明确其用途
建议: 如果计划实现DDD架构，保留并完善；否则移除
```

---

## 4. 执行步骤

### 4.1 第一阶段：安全备份和准备
1. **创建备份分支**
   ```bash
   git checkout -b backup-before-cleanup
   git push origin backup-before-cleanup
   ```

2. **创建新目录结构**
   ```bash
   mkdir -p tools/analysis
   mkdir -p examples/trading
   mkdir -p scripts
   ```

3. **运行测试确保当前状态稳定**
   ```bash
   python run_specific_tests.py
   ```

### 4.2 第二阶段：文件移动和重命名
1. **移动分析工具**
   ```bash
   mv src/calculate_ma_above_ratio.py tools/analysis/ma_ratio_calculator.py
   mv src/entry_window_performance_analysis.py tools/analysis/entry_window_analyzer.py
   mv src/trade_plan_performance_analysis.py tools/analysis/trade_plan_analyzer.py
   ```

2. **移动交易示例**
   ```bash
   mv src/generate_trade_logs.py examples/trading/trade_log_generator.py
   mv src/import_optimization_results.py examples/trading/optimization_importer.py
   # ... 其他文件
   ```

3. **重命名主程序**
   ```bash
   mv src/main.py src/cli_main.py
   ```

### 4.3 第三阶段：移除冗余文件
1. **移除旧版数据库模块**
   ```bash
   rm src/database.py
   ```

2. **移除复杂缓存组件**
   ```bash
   rm src/cache/cache_engine.py
   rm src/cache/freshness_tracker.py
   rm src/cache/data_injector.py
   rm src/cache/preloader.py
   ```

3. **移除过时文件**
   ```bash
   rm src/update_assets.py
   rm src/processor.py
   rm src/scheduler.py
   rm src/trace_logger.py
   ```

### 4.4 第四阶段：统一AKShare适配器
1. **备份当前版本**
   ```bash
   cp src/cache/akshare_adapter.py src/cache/akshare_adapter_complex.py.bak
   ```

2. **替换为简化版**
   ```bash
   mv src/cache/akshare_adapter_simplified.py src/cache/akshare_adapter.py
   ```

3. **更新所有导入引用**

### 4.5 第五阶段：整理API路由
1. **备份旧版路由**
   ```bash
   cp src/api/routes/historical_data.py src/api/routes/historical_data_old.py.bak
   ```

2. **替换为新版路由**
   ```bash
   mv src/api/routes/historical_data_simplified.py src/api/routes/historical_data.py
   ```

### 4.6 第六阶段：创建统一测试脚本
1. **创建新的测试管理器**
   ```bash
   # 创建 scripts/test_runner.py
   ```

2. **移除旧测试脚本**
   ```bash
   rm run_test.py run_tests.py run_specific_tests.py run_e2e_tests.py run_coverage.py
   ```

### 4.7 第七阶段：更新引用和配置
1. **更新导入语句**
2. **更新配置文件**
3. **更新文档引用**
4. **更新测试文件**

### 4.8 第八阶段：验证和测试
1. **运行完整测试套件**
2. **验证API功能**
3. **检查文档链接**
4. **性能对比测试**

---

## 5. 风险控制

### 5.1 回滚计划
- 保留备份分支 `backup-before-cleanup`
- 每个阶段完成后创建检查点
- 关键文件保留 `.bak` 备份

### 5.2 测试策略
- 每个阶段完成后运行测试
- 重点测试受影响的功能模块
- 保持API兼容性

### 5.3 文档更新
- 同步更新README.md
- 更新架构文档
- 更新API文档
- 更新开发指南

---

## 6. 预期结果

### 6.1 文件数量变化
- **移除文件**: ~15个
- **移动文件**: ~10个  
- **重命名文件**: ~5个
- **新增文件**: ~3个

### 6.2 代码行数变化
- **预计减少**: 2000-3000行代码
- **核心代码**: 保持不变
- **测试代码**: 略有减少

### 6.3 项目复杂度
- **目录层级**: 减少1-2层
- **依赖关系**: 简化30%
- **维护成本**: 降低40%

---

## 7. 后续维护

### 7.1 代码质量保持
- 建立代码审查机制
- 定期进行代码质量检查
- 避免重复代码的引入

### 7.2 架构演进
- 明确架构决策文档
- 建立变更评估流程
- 保持架构一致性

---

## 8. 执行时间表

| 阶段 | 预计时间 | 主要任务 |
|------|---------|---------|
| 第1阶段 | 0.5天 | 备份和准备 |
| 第2阶段 | 1天 | 文件移动和重命名 |
| 第3阶段 | 0.5天 | 移除冗余文件 |
| 第4阶段 | 1天 | 统一适配器 |
| 第5阶段 | 0.5天 | 整理路由 |
| 第6阶段 | 1天 | 统一测试脚本 |
| 第7阶段 | 1天 | 更新引用 |
| 第8阶段 | 1天 | 验证测试 |
| **总计** | **6天** | **完整整理** |

---

**计划制定时间**: 2025-01-27  
**计划执行开始**: 待确认  
**预期完成时间**: 执行开始后6个工作日
