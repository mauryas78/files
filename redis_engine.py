import redis
import os 
from dotenv import load_dotenv

load_dotenv()
class RedisClient:
    def __init__(self, 
                host=os.getenv("HOST"), 
                port=int(os.getenv("PORT")),
                db=int(os.getenv("DB")),
                max_connections = int(os.getenv("MAX_CONNECTIONS")),
                user="",
                password=os.getenv("REDIS_PASSWORD")):
        creds_provider = redis.UsernamePasswordCredentialProvider("", password)
#  find out property for min connection and ideal number connection.
        self.redis_pool = redis.ConnectionPool(
            host=host, 
            port=port,
            db=db,
            credential_provider=creds_provider,
            max_connections=max_connections,
            connection_class=redis.SSLConnection,
            ssl_cert_reqs= 'none',
        )
 
 
    def get_redis_connection(self):
        """Get a Redis connection from the pool."""
        return redis.Redis(connection_pool=self.redis_pool)
 
    def get_value(self, key):
        """Retrieves a value from Redis."""
        redis_client = self.get_redis_connection()
        value = redis_client.get(key)
        if value:
            return value.decode('utf-8')
        else:
            return None
 
    def upsert_value(self, key, value):
        """Sets a key-value pair in Redis."""
        redis_client = self.get_redis_connection()
        redis_client.set(key, value)
 

