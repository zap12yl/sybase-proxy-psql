import os
import psycopg2
from psycopg2 import pool
from prometheus_client import Gauge

class ConnectionManager:
    _instance = None

    def __init__(self):
        self.metrics = {
            'active': Gauge('db_connections_active', 'Active connections'),
            'waiting': Gauge('db_connections_waiting', 'Pending connection requests'),
            'usage': Histogram('db_connection_usage', 'Connection hold time')
        }

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=int(os.getenv("PG_MIN_CONN", 5)),
                maxconn=int(os.getenv("PG_MAX_CONN", 20)),
                host=os.getenv("PG_HOST"),
                database=os.getenv("PG_DB"),
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD")
            )
        return cls._instance
        

    def get_conn(self):
        start = time.time()
        conn = self.pool.getconn()
        self.metrics['active'].inc()
        self.metrics['usage'].observe(time.time() - start)
        return conn

    def put_conn(self, conn):
        self.pool.putconn(conn)
        self.metrics['active'].dec()

    def close_all(self):
        self.pool.closeall()
