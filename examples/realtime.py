import qdb

# Real-time quotes
rt = qdb.get_realtime_data("000001")
print(rt)

# Batch real-time
batch = qdb.get_realtime_data_batch(["000001", "000002", "600000"])
print("Batch count:", len(batch))

