# 错误处理与日志记录指南

## 1. 概述

QuantDB 系统采用统一的错误处理和日志记录机制，确保系统运行稳定、可追踪和可维护。本文档详细说明了错误处理和日志记录的最佳实践和使用方法。

## 2. 错误处理机制

### 2.1 错误处理原则

QuantDB 系统的错误处理遵循以下原则：

1. **统一性**：使用统一的错误处理机制，确保错误响应格式一致
2. **明确性**：提供清晰的错误消息和错误代码，便于定位问题
3. **分层性**：根据错误类型和严重程度分层处理
4. **可追踪性**：记录详细的错误信息，包括堆栈跟踪
5. **用户友好**：向用户提供友好的错误消息，隐藏敏感的技术细节

### 2.2 错误类型

系统定义了以下主要错误类型：

| 错误类型 | 错误代码 | 描述 |
|---------|---------|------|
| 内部错误 | INTERNAL_ERROR | 系统内部错误 |
| 验证错误 | VALIDATION_ERROR | 输入验证失败 |
| 资源不存在 | NOT_FOUND | 请求的资源不存在 |
| 请求错误 | BAD_REQUEST | 请求格式或参数错误 |
| 数据不存在 | DATA_NOT_FOUND | 请求的数据不存在 |
| 数据获取错误 | DATA_FETCH_ERROR | 从外部源获取数据失败 |
| 数据处理错误 | DATA_PROCESSING_ERROR | 数据处理过程中出错 |
| 外部服务错误 | EXTERNAL_SERVICE_ERROR | 外部服务调用失败 |
| AKShare 错误 | AKSHARE_ERROR | AKShare 服务调用失败 |
| 数据库错误 | DATABASE_ERROR | 数据库操作失败 |
| 缓存错误 | CACHE_ERROR | 缓存操作失败 |
| MCP 处理错误 | MCP_PROCESSING_ERROR | MCP 协议处理失败 |

### 2.3 自定义异常类

系统定义了一系列自定义异常类，用于表示不同类型的错误：

```python
# 基础异常类
class QuantDBException(Exception):
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

# 数据不存在异常
class DataNotFoundException(QuantDBException):
    def __init__(
        self, 
        message: str = "Requested data not found", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

# 数据获取异常
class DataFetchException(QuantDBException):
    def __init__(
        self, 
        message: str = "Error fetching data from external source", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_FETCH_ERROR,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )
```

### 2.4 错误响应格式

系统返回的错误响应采用统一的 JSON 格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "status_code": 400,
    "details": {
      "field": "Additional error details"
    },
    "path": "/api/v1/resource",
    "timestamp": "2025-06-18T10:15:30.123456"
  }
}
```

### 2.5 使用示例

```python
# 抛出自定义异常
if not data:
    raise DataNotFoundException(
        message="Stock data not found",
        details={"symbol": symbol, "date_range": f"{start_date} to {end_date}"}
    )

# 捕获并处理异常
try:
    result = service.get_data(symbol, start_date, end_date)
    return result
except DataNotFoundException as e:
    logger.warning(f"Data not found: {e.message}")
    # 处理数据不存在的情况
except DataFetchException as e:
    logger.error(f"Error fetching data: {e.message}")
    # 处理数据获取失败的情况
except QuantDBException as e:
    logger.error(f"QuantDB error: {e.error_code} - {e.message}")
    # 处理其他 QuantDB 异常
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    # 处理未预期的异常
```

## 3. 日志记录机制

### 3.1 日志记录原则

QuantDB 系统的日志记录遵循以下原则：

1. **详细性**：记录足够详细的信息，便于问题定位和分析
2. **分级性**：根据日志级别分级记录，便于过滤和查看
3. **上下文关联**：使用上下文 ID 关联相关日志，便于追踪请求流程
4. **性能指标**：记录关键操作的性能指标，便于性能分析
5. **结构化**：使用结构化的日志格式，便于解析和分析

### 3.2 日志级别

系统使用以下日志级别：

| 级别 | 使用场景 |
|------|---------|
| DEBUG | 详细的调试信息，仅在开发环境使用 |
| INFO | 正常的操作信息，记录系统的正常运行状态 |
| WARNING | 潜在的问题或异常情况，但不影响系统正常运行 |
| ERROR | 错误信息，影响功能但不导致系统崩溃 |
| CRITICAL | 严重错误，可能导致系统崩溃或数据丢失 |

### 3.3 增强日志记录器

系统提供了增强的日志记录器 `EnhancedLogger`，支持以下功能：

1. **上下文跟踪**：使用上下文 ID 关联相关日志
2. **性能指标**：记录操作的执行时间和性能指标
3. **结构化数据**：记录结构化的数据对象
4. **日志轮转**：支持日志文件轮转，避免日志文件过大
5. **装饰器支持**：提供函数装饰器，自动记录函数调用和执行时间

### 3.4 使用示例

```python
# 创建增强日志记录器
logger = setup_enhanced_logger(
    name="my_module",
    level="INFO",
    detailed=True
)

# 开始上下文
context_id = logger.start_context(metadata={
    "request_id": request_id,
    "user_id": user_id
})

# 记录信息
logger.info("Processing request")

# 记录性能指标
start_time = time.time()
result = process_data()
duration = time.time() - start_time
logger.add_metric("processing_time", duration)

# 记录结构化数据
logger.log_data("result", result)

# 记录错误
try:
    validate_result(result)
except Exception as e:
    logger.error("Validation failed", exc_info=e)

# 结束上下文
logger.end_context()

# 使用装饰器自动记录函数调用
@log_function(level='info')
def process_request(request):
    # 函数执行前后会自动记录日志
    return process_data(request)
```

### 3.5 日志文件位置

系统日志文件存储在 `logs` 目录下，按模块名称分类：

- `logs/quantdb.log`：主日志文件
- `logs/api.log`：API 相关日志
- `logs/mcp.log`：MCP 协议相关日志
- `logs/cache.log`：缓存相关日志
- `logs/akshare.log`：AKShare 相关日志

## 4. 最佳实践

### 4.1 错误处理最佳实践

1. **使用自定义异常**：尽量使用自定义异常类，而不是通用的 Exception
2. **提供详细信息**：在异常中提供足够详细的信息，便于问题定位
3. **适当的错误级别**：根据错误的严重程度选择适当的日志级别
4. **捕获具体异常**：捕获具体的异常类型，而不是笼统的 Exception
5. **避免吞没异常**：不要捕获异常后不做任何处理
6. **用户友好消息**：向用户提供友好的错误消息，隐藏技术细节

### 4.2 日志记录最佳实践

1. **使用上下文**：使用上下文 ID 关联相关日志
2. **记录关键点**：在关键操作点记录日志，如请求开始、结束、状态变更等
3. **记录性能指标**：记录关键操作的执行时间和性能指标
4. **结构化数据**：使用 `log_data` 记录结构化数据，而不是直接拼接字符串
5. **避免过度日志**：避免记录过多的调试信息，特别是在生产环境
6. **敏感信息保护**：不要记录敏感信息，如密码、API 密钥等

## 5. 故障排查

### 5.1 常见错误及解决方法

| 错误代码 | 可能原因 | 解决方法 |
|---------|---------|---------|
| DATA_NOT_FOUND | 请求的数据不存在 | 检查数据源是否可用，数据是否已导入 |
| DATA_FETCH_ERROR | 从外部源获取数据失败 | 检查网络连接，外部 API 是否可用 |
| AKSHARE_ERROR | AKShare 服务调用失败 | 检查 AKShare 版本，网络连接，API 参数 |
| DATABASE_ERROR | 数据库操作失败 | 检查数据库连接，SQL 语句，数据库权限 |
| VALIDATION_ERROR | 输入验证失败 | 检查请求参数，确保符合 API 规范 |

### 5.2 日志分析技巧

1. **按上下文 ID 过滤**：使用上下文 ID 过滤相关日志，追踪完整请求流程
2. **按时间范围过滤**：使用时间范围过滤日志，定位特定时间段的问题
3. **按错误级别过滤**：使用错误级别过滤日志，关注严重问题
4. **性能分析**：分析性能指标，找出性能瓶颈
5. **模式识别**：识别日志中的模式，发现潜在问题

## 6. 总结

统一的错误处理和日志记录机制是系统稳定性和可维护性的关键。通过遵循本文档中的最佳实践，可以提高系统的可靠性、可追踪性和可维护性。
