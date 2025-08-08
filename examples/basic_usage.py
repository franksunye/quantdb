import qdb

# 获取最近 30 天数据（自动缓存）
df = qdb.get_stock_data("000001", days=30)
print("Rows:", len(df))
print(df.head())

# 批量获取
data = qdb.get_multiple_stocks(["000001", "000002", "600000"], days=30)
print("Batch keys:", list(data.keys()))

