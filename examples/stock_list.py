import qdb

# 全量列表
all_stocks = qdb.get_stock_list()
print("Total:", len(all_stocks))

# 市场过滤（如有支持：'SHSE', 'SZSE', 'HKEX'）
sh = qdb.get_stock_list(market="SHSE")
print("SHSE:", len(sh))

