# 常见问题

## 🔧 安装和配置

### Q: 安装时遇到依赖冲突怎么办？
**A:** 建议使用虚拟环境隔离依赖：
```bash
python -m venv quantdb_env
source quantdb_env/bin/activate  # Linux/Mac
pip install quantdb
```

### Q: 如何更新到最新版本？
**A:** 使用 pip 更新：
```bash
pip install --upgrade quantdb
```

### Q: 支持哪些 Python 版本？
**A:** 支持 Python 3.8 及以上版本。推荐使用 Python 3.9+ 以获得最佳性能。

## 📊 数据获取

### Q: 为什么有时候数据不是最新的？
**A:** 这是因为缓存机制。你可以：
- 清理缓存：`qdb.clear_cache()`
- 调整缓存过期时间：`qdb.set_cache_expire(300)`  # 5分钟
- 临时禁用缓存：`qdb.disable_cache()`

### Q: 如何获取更多历史数据？
**A:** 使用日期参数：
```python
data = qdb.stock_zh_a_hist(
    symbol="000001",
    start_date="20200101",  # 更早的开始日期
    end_date="20241231"
)
```

### Q: 支持哪些股票市场？
**A:** 目前主要支持：
- A股市场（沪深两市）
- 港股市场
- 美股市场（部分接口）

## ⚡ 性能优化

### Q: 如何提高数据获取速度？
**A:** 几个优化建议：
1. 启用缓存（默认已启用）
2. 批量获取数据时使用合理的间隔
3. 预热常用股票的缓存
4. 定期清理过期缓存

### Q: 缓存文件占用空间太大怎么办？
**A:** 可以：
- 定期清理：`qdb.clear_cache()`
- 设置较短的过期时间：`qdb.set_cache_expire(1800)`  # 30分钟
- 手动删除数据库文件（位于 `./database/stock_data.db`）

### Q: 如何查看缓存使用情况？
**A:** 使用统计功能：
```python
stats = qdb.get_cache_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
print(f"缓存大小: {stats['cache_size']} 条记录")
```

## 🐛 错误处理

### Q: 遇到网络错误怎么办？
**A:** 检查：
1. 网络连接是否正常
2. 是否被防火墙阻止
3. 数据源服务是否可用
4. 尝试使用代理或VPN

### Q: 数据格式不正确怎么办？
**A:** 可能的原因：
- 股票代码错误（检查格式，如 "000001" 而不是 "1"）
- 日期格式错误（使用 "YYYYMMDD" 格式）
- 数据源临时变更（等待修复或联系维护者）

### Q: 程序运行很慢怎么办？
**A:** 排查步骤：
1. 检查是否首次运行（需要下载数据）
2. 确认缓存是否启用
3. 检查网络连接速度
4. 考虑减少数据获取的时间范围

## 🔄 数据更新

### Q: 如何确保获取最新数据？
**A:** 
```python
# 方法1：清理特定股票缓存
qdb.clear_cache(symbol="000001")

# 方法2：设置短期缓存
qdb.set_cache_expire(60)  # 1分钟过期

# 方法3：临时禁用缓存
qdb.disable_cache()
data = qdb.stock_zh_a_hist("000001")
qdb.enable_cache()
```

### Q: 数据更新频率是多少？
**A:** 取决于数据源：
- 实时行情：通常延迟15分钟
- 日线数据：每日收盘后更新
- 财务数据：季度更新

## 🛠️ 开发集成

### Q: 如何在生产环境中使用？
**A:** 建议：
1. 使用专用的数据库路径
2. 设置合理的缓存策略
3. 实现错误重试机制
4. 监控缓存使用情况

### Q: 可以与其他数据源结合使用吗？
**A:** 可以，QuantDB 主要是 AKShare 的缓存层，你可以：
- 结合使用多个数据源
- 实现数据验证和清洗
- 构建自己的数据管道

### Q: 如何贡献代码或报告问题？
**A:** 
- GitHub Issues: https://github.com/franksunye/quantdb/issues
- 提交 Pull Request
- 参与社区讨论

## 📚 更多帮助

如果以上答案没有解决你的问题：

1. 查看 [用户指南](03_user-guide.md) 获取详细使用说明
2. 查看 [API参考](04_api-reference.md) 了解所有可用接口
3. 查看 [示例代码](05_examples.md) 学习最佳实践
4. 在 GitHub 上提交 Issue 获取帮助

## 🔗 相关链接

- [项目主页](https://github.com/franksunye/quantdb)
- [PyPI 页面](https://pypi.org/project/quantdb/)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [社区讨论](community/)
