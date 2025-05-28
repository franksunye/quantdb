# 测试指南

## 1. 概述

QuantDB 系统采用全面的测试策略，确保系统的稳定性、可靠性和性能。本文档详细说明了测试的类型、组织结构、运行方法和最佳实践。

## 2. 测试类型

QuantDB 系统包含以下类型的测试：

### 2.1 单元测试

单元测试用于测试系统的最小可测试单元，通常是一个函数或方法。单元测试应该是独立的，不依赖于外部系统或数据库。

单元测试位于 `tests/unit` 目录下，按照被测试的模块组织。

### 2.2 集成测试

集成测试用于测试多个组件的交互，确保它们能够正确地协同工作。集成测试可能依赖于外部系统或数据库。

集成测试位于 `tests/integration` 目录下，按照被测试的功能组织。

### 2.3 端到端测试

端到端测试用于测试整个系统的功能，从用户界面到数据库。端到端测试模拟用户的实际使用场景。

端到端测试位于 `tests/e2e` 目录下，按照被测试的功能组织。

### 2.4 性能测试

性能测试用于测试系统的性能，包括响应时间、吞吐量和资源使用情况。性能测试可以帮助识别系统的瓶颈。

性能测试位于 `tests/performance` 目录下，按照被测试的功能组织。

## 3. 测试组织结构

测试目录结构如下：

```
tests/
├── unit/                  # 单元测试
│   ├── test_api_routes.py
│   ├── test_enhanced_logger.py
│   ├── test_error_handling.py
│   └── ...
├── integration/           # 集成测试
│   ├── test_error_handling_integration.py
│   ├── test_logging_integration.py
│   └── ...
├── e2e/                   # 端到端测试
│   ├── test_api_e2e.py
│   ├── test_mcp_e2e.py
│   └── ...
├── performance/           # 性能测试
│   ├── test_api_performance.py
│   ├── test_cache_performance.py
│   └── ...
├── conftest.py            # 测试配置和共享夹具
└── README.md              # 测试说明
```

## 4. 运行测试

### 4.1 运行所有测试

使用以下命令运行所有测试：

```bash
python -m pytest
```

### 4.2 运行特定类型的测试

使用以下命令运行特定类型的测试：

```bash
# 运行单元测试
python -m pytest tests/unit

# 运行集成测试
python -m pytest tests/integration

# 运行端到端测试
python -m pytest tests/e2e

# 运行性能测试
python -m pytest tests/performance
```

### 4.3 运行特定的测试文件

使用以下命令运行特定的测试文件：

```bash
python -m pytest tests/unit/test_api_routes.py
```

### 4.4 运行特定的测试函数

使用以下命令运行特定的测试函数：

```bash
python -m pytest tests/unit/test_api_routes.py::TestAPIRoutes::test_health_endpoint
```

### 4.5 运行带有覆盖率报告的测试

使用以下命令运行带有覆盖率报告的测试：

```bash
# 运行所有测试并生成覆盖率报告
python run_tests_with_coverage.py --html --open

# 运行特定类型的测试并生成覆盖率报告
python run_tests_with_coverage.py --html --open --tests tests/unit

# 运行特定的测试文件并生成覆盖率报告
python run_tests_with_coverage.py --html --open --tests tests/unit/test_api_routes.py
```

## 5. 测试覆盖率

测试覆盖率是衡量测试质量的重要指标，它表示代码被测试的比例。QuantDB 系统使用 `coverage.py` 工具来生成测试覆盖率报告。

### 5.1 覆盖率报告

使用以下命令生成覆盖率报告：

```bash
# 运行测试并收集覆盖率数据
coverage run -m pytest

# 生成覆盖率报告
coverage report

# 生成 HTML 覆盖率报告
coverage html

# 生成 XML 覆盖率报告
coverage xml
```

HTML 覆盖率报告将生成在 `coverage_html_report` 目录下，可以在浏览器中打开 `coverage_html_report/index.html` 文件查看。

### 5.2 覆盖率配置

覆盖率配置文件 `.coveragerc` 定义了覆盖率报告的配置，包括要包含和排除的文件、要排除的行等。

```ini
[run]
source = src
omit =
    src/config.py
    src/logger.py
    # 其他要排除的文件

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    # 其他要排除的行

[html]
directory = coverage_html_report
title = QuantDB Coverage Report
```

## 6. 测试最佳实践

### 6.1 单元测试最佳实践

1. **测试一个单元**：每个测试应该只测试一个函数或方法。
2. **独立性**：测试应该是独立的，不依赖于其他测试的结果。
3. **模拟外部依赖**：使用 `unittest.mock` 模块模拟外部依赖，如数据库、API 等。
4. **测试边界条件**：测试函数的边界条件，如空输入、最大值、最小值等。
5. **测试异常**：测试函数在异常情况下的行为。

### 6.2 集成测试最佳实践

1. **测试组件交互**：测试多个组件的交互，确保它们能够正确地协同工作。
2. **使用测试数据库**：使用测试数据库而不是生产数据库。
3. **清理测试数据**：测试完成后清理测试数据，避免影响其他测试。
4. **测试事务**：测试数据库事务，确保数据的一致性。

### 6.3 端到端测试最佳实践

1. **模拟用户行为**：测试应该模拟用户的实际使用场景。
2. **测试关键流程**：测试系统的关键流程，如数据获取、处理和展示。
3. **验证结果**：验证测试结果是否符合预期。
4. **测试错误处理**：测试系统在错误情况下的行为。

### 6.4 性能测试最佳实践

1. **设置基准**：设置性能基准，用于比较性能变化。
2. **测试不同负载**：测试系统在不同负载下的性能。
3. **监控资源使用**：监控系统的资源使用情况，如 CPU、内存等。
4. **识别瓶颈**：识别系统的性能瓶颈，并进行优化。

## 7. 持续集成

QuantDB 系统使用持续集成 (CI) 来自动运行测试，确保代码的质量。CI 系统会在每次代码提交时运行测试，并生成测试报告。

### 7.1 CI 配置

CI 配置文件定义了 CI 系统的配置，包括要运行的测试、环境设置等。

### 7.2 CI 流程

1. 开发者提交代码到代码库。
2. CI 系统检测到代码变更，触发构建。
3. CI 系统设置测试环境，包括安装依赖、配置数据库等。
4. CI 系统运行测试，包括单元测试、集成测试、端到端测试和性能测试。
5. CI 系统生成测试报告，包括测试结果和覆盖率报告。
6. CI 系统通知开发者测试结果。

## 8. 故障排查

### 8.1 常见问题及解决方法

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 测试失败 | 代码错误 | 检查代码，修复错误 |
| 测试超时 | 性能问题 | 优化代码，提高性能 |
| 测试不稳定 | 依赖外部系统 | 模拟外部依赖，使测试更稳定 |
| 覆盖率低 | 测试不完整 | 添加更多测试，提高覆盖率 |

### 8.2 调试测试

使用以下命令调试测试：

```bash
# 使用 -v 参数显示详细信息
python -m pytest -v

# 使用 -s 参数显示 print 输出
python -m pytest -s

# 使用 --pdb 参数在测试失败时进入调试器
python -m pytest --pdb

# 使用 -xvs 参数在第一个测试失败时停止
python -m pytest -xvs
```

## 9. 总结

全面的测试策略是确保系统质量的关键。通过遵循本文档中的最佳实践，可以提高系统的可靠性、稳定性和性能。
