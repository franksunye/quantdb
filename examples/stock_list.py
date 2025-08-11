import qdb

# Full stock list
all_stocks = qdb.get_stock_list()
print("Total:", len(all_stocks))

# Market filtering (if supported: 'SHSE', 'SZSE', 'HKEX')
sh = qdb.get_stock_list(market="SHSE")
print("SHSE:", len(sh))

