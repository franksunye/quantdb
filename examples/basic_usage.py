import qdb

# Get recent 30 days data (auto-cached)
df = qdb.get_stock_data("000001", days=30)
print("Rows:", len(df))
print(df.head())

# Batch retrieval
data = qdb.get_multiple_stocks(["000001", "000002", "600000"], days=30)
print("Batch keys:", list(data.keys()))
