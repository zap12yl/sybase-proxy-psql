import psycopg2
import os

def init_database():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DB")
    )
    conn.autocommit = True
    
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE {os.getenv('PG_DB')}")
        cursor.execute(f"""
            CREATE USER {os.getenv('PG_USER')} 
            WITH PASSWORD '{os.getenv('PG_PASSWORD')}'
        """)
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE {os.getenv('PG_DB')} 
            TO {os.getenv('PG_USER')}
        """)

if __name__ == "__main__":
    init_database()
