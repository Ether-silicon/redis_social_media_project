import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

try:
    redis_client.ping()
    print("✅ Connected to Redis")
except redis.ConnectionError:
    print("❌ Error connecting to Redis")

