from src.cache.redis_cache import get_redis_cache

cache = get_redis_cache()

if cache.is_connected():
    print("✅ Redis is connected!")
    
    # Test set/get
    cache.set("test_key", "Hello Redis!", ttl=60)
    value = cache.get("test_key")
    print(f"✅ Cached value: {value}")
    
    # Test query cache
    cache.cache_query_result("What is AI?", 5, {"answer": "Test answer"})
    result = cache.get_cached_query_result("What is AI?", 5)
    print(f"✅ Cached query result: {result}")
    
    print("\n🎉 Redis is working perfectly!")
else:
    print("❌ Redis not connected")