import qdb

# 实时行情
rt = qdb.get_realtime_data("000001")
print(rt)

# 批量实时
batch = qdb.get_realtime_data_batch(["000001", "000002", "600000"])
print("Batch count:", len(batch))

