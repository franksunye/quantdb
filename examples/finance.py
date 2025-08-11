import qdb

summary = qdb.get_financial_summary("000001")
print("Summary keys:", list(summary.keys()))

ind = qdb.get_financial_indicators("000001")
print("Indicators keys:", list(ind.keys()))
