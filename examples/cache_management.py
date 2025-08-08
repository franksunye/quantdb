import qdb

stats = qdb.cache_stats()
print("Hit rate:", stats.get("hit_rate"))

qdb.set_cache_dir("./qdb_cache")
print("Cache dir set.")

# 清除缓存（谨慎）
# qdb.clear_cache()

