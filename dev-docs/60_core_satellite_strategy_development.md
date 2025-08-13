# CoreSatellite 投资策略开发计划

## 概述

本文档详细规划了在 QuantDB 框架基础上实现 CoreSatellite 投资策略的开发计划。该策略旨在通过分层仓位管理，在保护核心筹码的同时，通过卫星仓位的主动交易来放大收益。

### 核心目标
- 5年内实现16倍收益目标
- 保护核心筹码不丢失
- 在回调中通过做T增加收益
- 系统化风险控制

### 回测演示成果
已完成策略的可运行演示回测脚本，使用合成5年价格路径验证：
- **总收益**: ~2534% (演示数据)
- **最大回撤**: ~47% (需要风险承受能力评估)
- **策略验证**: Core(70%) + Satellite(30%) 分层管理有效
- **操作确认**: 3梯子建仓、2x/4x/8x分批减仓机制可行

## 技术架构设计

### 1. 策略框架结构

#### 命名规范
- **专项名称**: CoreSatellite (PascalCase)
- **技术命名**: core-satellite (kebab-case)
- **Python模块**: core_satellite (snake_case)
- **配置文件**: core-satellite.yml (kebab-case)

#### 目录结构
```
core/
├── strategies/
│   ├── core_satellite/                    # Python模块 (snake_case)
│   │   ├── __init__.py
│   │   ├── core_satellite_strategy.py     # 主策略类
│   │   ├── position_manager.py            # 仓位管理
│   │   ├── risk_manager.py                # 风险控制
│   │   ├── signal_generator.py            # 信号生成
│   │   ├── execution_engine.py            # 执行引擎
│   │   └── config/
│   │       ├── core-satellite-default.yml # 默认配置 (kebab-case)
│   │       └── core-satellite-prod.yml    # 生产配置
│   └── backtest/
│       ├── core_satellite_backtester.py   # 回测引擎
│       └── core_satellite_performance.py  # 绩效分析
├── data/
│   └── core-satellite/                    # 数据目录 (kebab-case)
│       ├── backtest-results/
│       ├── trade-logs/
│       └── performance-reports/
└── docs/
    └── core-satellite/                    # 文档目录 (kebab-case)
        ├── strategy-guide.md
        ├── api-reference.md
        └── examples/
```

#### 示例命名
```python
# 类名 (PascalCase)
class CoreSatelliteStrategy:
    pass

class CoreSatellitePositionManager:
    pass

# 函数名 (snake_case)
def calculate_core_satellite_allocation():
    pass

def execute_core_satellite_rebalance():
    pass

# 配置键名 (snake_case)
CORE_SATELLITE_CONFIG = {
    'core_allocation_ratio': 0.7,
    'satellite_allocation_ratio': 0.3,
    'max_single_risk_pct': 0.01
}

# 文件名示例
core_satellite_strategy.py
core_satellite_backtest_20241213.csv
core-satellite-config.yml
core-satellite-performance-report.html
```

### 2. 数据依赖
- 日线数据：价格、成交量、技术指标
- 分钟级数据：用于日内交易
- 基本面数据：用于Core仓位决策
- 市场数据：波动率、流动性指标

## 核心模块开发计划

### 模块1: 仓位分层管理 (Position Allocation)
**优先级**: 高
**预计工期**: 1周

#### 功能需求
- Core仓位：60-80%，长期持有
- Satellite仓位：20-40%，主动交易
- 动态仓位调整机制

#### 技术实现
```python
class CoreSatellitePositionManager:
    """CoreSatellite策略仓位管理器"""

    def __init__(self, core_ratio=0.7, satellite_ratio=0.3):
        self.core_ratio = core_ratio
        self.satellite_ratio = satellite_ratio
        self.strategy_name = "CoreSatellite"

    def allocate_core_satellite_positions(self, total_capital):
        """分配Core和Satellite仓位"""
        core_capital = total_capital * self.core_ratio
        satellite_capital = total_capital * self.satellite_ratio
        return {
            'core_allocation': core_capital,
            'satellite_allocation': satellite_capital,
            'strategy': 'core-satellite'
        }

    def rebalance_core_satellite(self, market_conditions):
        """CoreSatellite动态再平衡"""
        # 实现再平衡逻辑
        pass
```

### 模块2: 风险管理系统 (Risk Management)
**优先级**: 高
**预计工期**: 1.5周

#### 功能需求
- Kelly公式仓位计算
- ATR基础止损设置
- 波动率目标控制
- 单笔最大风险限制

#### 关键参数
- 单笔最大损失：账户净值的0.5%-2%
- 目标年化波动率：15%
- 日内交易损失上限：账户的1%-2%

### 模块3: 信号生成器 (Signal Generator)
**优先级**: 中
**预计工期**: 2周

#### Core仓位信号
- 基本面分析触发器
- 长期趋势确认
- 极端情况下的减仓信号

#### Satellite仓位信号
- 技术指标组合：MA21/50, RSI, ATR
- 量价配合确认
- 突破/回调识别

### 模块4: 执行引擎 (Execution Engine)
**优先级**: 中
**预计工期**: 2周

#### 功能需求
- 分批建仓/减仓
- VWAP/TWAP算法执行
- 滑点控制
- 交易量限制(%ADV)

### 模块5: 回测系统 (Backtesting)
**优先级**: 高
**预计工期**: 1.5周

#### 功能需求
- 历史数据回测
- 交易成本模拟
- 绩效指标计算
- 压力测试

## 开发路线图

### Sprint 1 (Week 1-2): 基础架构
- [ ] 创建策略框架结构
- [ ] 实现基础仓位管理
- [ ] 集成QuantDB数据接口
- [ ] 基础风险控制模块

### Sprint 2 (Week 3-4): 核心逻辑
- [ ] 完善风险管理系统
- [ ] 实现信号生成器
- [ ] 开发执行引擎基础功能
- [ ] 单元测试覆盖

### Sprint 3 (Week 5-6): 回测与优化
- [ ] 完整回测系统
- [ ] 参数优化框架
- [ ] 绩效分析工具
- [ ] 压力测试模块

### Sprint 4 (Week 7-8): 集成与测试
- [ ] 系统集成测试
- [ ] 实盘模拟测试
- [ ] 文档完善
- [ ] 部署准备

## 具体实现规则

### 建仓规则
```python
# CoreSatellite策略配置示例
CORE_SATELLITE_CONFIG = {
    'strategy_name': 'CoreSatellite',
    'strategy_version': '1.0.0',
    'core_allocation_ratio': 0.7,
    'satellite_allocation_ratio': 0.3,
    'max_single_risk_pct': 0.01,  # 1% of account
    'target_volatility_annual': 0.15,  # 15% annual
    'scale_out_levels': [2.0, 4.0, 8.0],  # 2x, 4x, 8x
    'scale_out_ratios': [0.25, 0.25, 0.25],  # 25% each
    'trailing_stop_atr_multiplier': 3.0,  # 3x ATR
    'config_file': 'core-satellite-default.yml'
}

# 配置文件示例: core-satellite-default.yml
"""
strategy:
  name: CoreSatellite
  version: 1.0.0

allocation:
  core_ratio: 0.7
  satellite_ratio: 0.3

risk_management:
  max_single_risk_pct: 0.01
  target_volatility_annual: 0.15
  trailing_stop_atr_multiplier: 3.0

execution:
  scale_out_levels: [2.0, 4.0, 8.0]
  scale_out_ratios: [0.25, 0.25, 0.25]
  max_adv_pct: 0.02
"""
```

### 加仓逻辑 (3梯子建仓)
1. **第1梯**: Satellite目标仓位的33% - 在MA21/50确认趋势且回调放量时建仓
2. **第2梯**: 价格从上次建仓点上涨≥12%且成交量配合时加仓33%
3. **第3梯**: 再上涨≥15%时加最后33%，完成Satellite满仓

### 减仓逻辑 (分段获利 + 跟踪止损)
- **2x收益**: 卖出25% Satellite仓位，锁定部分利润
- **4x收益**: 再卖出25%，累计已获利50%
- **8x收益**: 再卖出25%，累计已获利75%
- **剩余25%**: 使用跟踪止损保护
  - 20%回撤止损 OR 3×ATR下移止损
  - 保留上行"尾巴"收益的可能性

### 短线T操作 (卫星内部分配)
- 仅使用Satellite的30% (即总账户的9%) 进行日内交易
- 严格止损：单笔最大亏损0.2%账户，日累计亏损上限1%
- 超过损失阈值立即停止当日交易

## 测试计划

### 单元测试
- 各模块功能测试
- 边界条件测试
- 异常处理测试

### 集成测试
- 模块间协作测试
- 数据流测试
- 性能测试

### 回测验证
- 历史数据回测（5年+）
- 不同市场环境测试
- 参数敏感性分析
- **实际市场因素模拟**:
  - 交易费用和印花税
  - 买卖价差(Bid-Ask Spread)
  - 市场冲击和滑点
  - 流动性限制(%ADV)
  - 停牌和跳空缺口
  - 港股T+0规则限制

### 压力测试
- 30%下跌情景
- 跳空缺口情景
- 高波动率环境

## 风险控制机制

### 系统性风险控制
- **最大回撤预期**: 30-50% (基于回测结果调整)
- **回撤控制措施**:
  - Core仓位长期持有，不受短期波动影响
  - Satellite跟踪止损，及时止损保护利润
  - 分段获利，降低单次暴露风险
- 连续亏损停止交易机制
- 市场异常情况应急预案
- **风险承受能力评估**: 投资者需能承受47%+的最大回撤

### 操作风险控制
- 代码审查流程
- 自动化测试
- 监控告警系统

### 合规风险控制
- 交易规则遵循
- 监管要求满足
- 审计日志记录

## 成功指标

### 绩效指标
- **CAGR**: 目标年化收益率 (演示显示~70%年化)
- **总收益**: 5年目标16倍 (演示达到25倍+)
- **Sharpe比率**: >1.0 (考虑高波动性)
- **最大回撤**: 30-50% (需要强风险承受能力)
- **胜率**: >55% (平衡收益风险比)
- **收益风险比**: 盈亏比>2:1

### 技术指标
- 代码覆盖率：>90%
- 系统可用性：>99.9%
- 响应时间：<100ms

## 后续扩展

### 功能扩展
- 多资产支持
- 机器学习信号
- 情绪指标集成
- 宏观经济因子

### 技术扩展
- 实时流处理
- 分布式计算
- 云原生部署
- API服务化

## 回测演示经验教训

### 关键发现
1. **策略有效性**: Core+Satellite分层管理确实能在保护核心筹码的同时放大收益
2. **风险现实性**: 47%最大回撤提醒我们高收益伴随高风险，需要强心理承受能力
3. **操作纪律性**: 3梯子建仓和分段获利机制能有效控制风险暴露
4. **市场适应性**: 策略在长期上涨趋势中表现良好，需要测试震荡和下跌市场

### 实盘化考虑
1. **交易成本**: 回测需加入0.1-0.3%的交易费用和滑点
2. **流动性约束**: 大额交易需要分批执行，避免市场冲击
3. **心理因素**: 47%回撤期间的心理压力和执行纪律
4. **监管合规**: 港股交易规则、融资融券限制等

### 下一步行动
1. **真实数据回测**: 使用实际历史价格数据验证策略
2. **参数优化**: 调整风险参数以降低最大回撤
3. **压力测试**: 测试2008、2015、2020等极端市场环境
4. **实盘模拟**: 小资金量先行验证

## 策略使用指南

### 每日操作流程

#### 1. 数据更新 (收盘后)
```python
# 每日必做步骤
1. 更新当日行情数据 (OHLCV)
2. 计算技术指标 (MA21/50, ATR14, RSI14)
3. 更新波动率和风险指标
4. 运行策略引擎生成信号
```

#### 2. 信号生成与审核
- **自动执行**: 小额交易 (<总资产0.5% 且 <日均成交量1%)
- **人工审核**: 大额交易或Core仓位变动
- **必须人工批准**: 任何Core仓位卖出操作

#### 3. 执行与监控
- 优先使用限价单和算法单 (VWAP/TWAP)
- 控制单笔交易占日均成交量比例 (≤2% ADV)
- 实时监控日内累计损失 (上限1-2%)

### 盘中监控 (日内T操作)

#### 触发条件
- 突破30分钟高点 + 成交量放大
- 当日跌幅超过设定阈值的自动买入
- 仅使用Satellite的20-30%进行日内交易

#### 风险控制
- 日内累计亏损超过0.5%立即停止自动交易
- 优先限价单，避免市价单滑点
- 低流动性时段合并小单分批执行

### 每周维护流程

#### 定期检查 (建议周日)
1. **基本面复核**: 检查Core持仓公司新闻、公告、财报
2. **绩效分析**:
   - 周收益率和成交次数
   - 滑点情况和执行质量
   - 胜率和盈亏比统计
3. **参数调整**: 如周回撤异常，收紧日内规则

### 每月/季度/年度流程

#### 每月
- 回测上月策略参数 (使用6-12个月数据)
- 参数敏感性分析
- 策略稳定性评估

#### 每季度
- 深度压力测试 (大幅下跌、流动性枯竭场景)
- 风险指标全面评估
- 策略优化建议

#### 每年
- Core仓位基本面全面复审
- 税务整理和交易明细归档
- 策略年度绩效报告

### 决策规则表 ("如果→那么"快速决策)

#### 交易执行规则
- **如果**: 程序建议买入 且 单笔<0.5%总资产 且 <1%ADV → **那么**: 自动下限价单
- **如果**: 程序建议买入 但 现金不足 → **那么**: 从卫星现金池调配，不动Core
- **如果**: 程序建议卖Core → **那么**: 必须满足基本面触发器且人工确认
- **如果**: 日内累计亏损>1% → **那么**: 停止所有卫星自动交易
- **如果**: 股票停牌/异常公告 → **那么**: 立即告警，人工评估
- **如果**: 市场紧急事件 → **那么**: 停止自动下单，等待人工指示

#### Core仓位卖出触发器 (至少满足2个条件)
1. 公司基本面根本恶化 (造假、利润消失、管理层失信)
2. 面临退市风险或流动性极差
3. 股价长期下行(>12个月)且不可逆损失
4. 有更高概率的替代投资机会

### 风险控制与执行细节

#### 交易成本控制
- 回测必须包含: 手续费、印花税、买卖价差、滑点
- 实盘执行: 算法单分批、限价单优先
- 流动性管理: 单笔≤2% ADV，避免市场冲击

#### 止损机制
- **固定止损**: 应对跳空缺口
- **跟踪止损**: 保留上涨尾部收益
- **组合使用**: 根据市场情况灵活切换

#### 日志记录 (每笔交易必记录)
- 交易时间、价格、数量
- 信号来源和执行理由
- 是否人工批准
- 滑点和执行质量

### 监控仪表盘

#### 核心指标
- 组合净值曲线 (实时)
- 当日/7日/30日/365日收益率
- 历史最大回撤
- 当日未实现/已实现盈亏
- 持仓集中度 (最大持仓占比)
- 交易统计 (次数/滑点/胜率)

#### 自动报告
- **日报**: 净值、交易、告警 (邮件/微信/Slack)
- **周报**: 绩效分析、风险评估
- **月报**: 策略回顾、参数优化建议

### 自动化级别建议

#### 初期: 半自动化 (推荐)
- 程序生成信号 + 小单自动执行
- 大额/Core变动人工确认
- 保留异常情况人工干预能力

#### 成熟期: 渐进自动化
- 策略稳定6-12个月后
- 部分卫星完全自动化
- 保留人工审批阈值

### 应急预案

#### 三条必备规则
1. **单日亏损阈值**: 达到账户1-2%自动暂停交易
2. **停牌/重大公告**: 暂停该标的自动交易，标注待确认
3. **系统故障**: 任何错误或断连立即停止下单并告警

#### 典型交易日时间线
- **盘前/收盘后**: 运行策略引擎，生成委托单和风险报表
- **开盘前**: 检查新闻公告，批准/拒绝超大单
- **盘中**: 日内T自动监控，满足条件提交限价单
- **收盘后**: 全量回测，更新跟踪止损，记录日志，收取日报

---

**重要提醒**:
- 演示回测使用合成数据，实际结果可能差异很大
- 47%最大回撤需要投资者具备极强的风险承受能力
- 所有参数需要通过真实历史数据充分验证
- 实盘前必须进行小额资金测试
- 建议从半自动化开始，逐步提升自动化程度
