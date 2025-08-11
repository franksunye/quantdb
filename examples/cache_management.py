import qdb

stats = qdb.cache_stats()
print("Hit rate:", stats.get("hit_rate"))

qdb.set_cache_dir("./qdb_cache")
print("Cache dir set.")

# Clear cache (use with caution)
# qdb.clear_cache()
