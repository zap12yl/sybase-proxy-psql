import psycopg2
from psycopg2 import pool

class ConnectionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_pool()
        return cls._instance
    
    def _init_pool(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_DB"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD")
        )
    
    def get_conn(self):
        return self.pool.getconn()
    
    def put_conn(self, conn):
        self.pool.putconn(conn)
    
    def close_all(self):
        self.pool.closeall()