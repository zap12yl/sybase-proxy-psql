import pytds
import psycopg3
from tqdm import tqdm
from psycopg3.extras import execute_batch
import logging

logger = logging.getLogger("data-mover")

class DataMover:
    BATCH_SIZE = 1000

    def migrate_table(self, table_name: str, sybase_config: dict, pg_config: dict):
        try:
            with pytds.connect(**sybase_config) as syb_conn:
                with syb_conn.cursor() as syb_cursor:
                    syb_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_rows = syb_cursor.fetchone()[0]
                    
                    syb_cursor.execute(f"SELECT * FROM {table_name}")
                    self._copy_data(syb_cursor, table_name, pg_config, total_rows)
        except Exception as e:
            logger.error(f"Data migration failed for {table_name}: {str(e)}")
            raise

    def _copy_data(self, syb_cursor, table_name: str, pg_config: dict, total: int):
        with psycopg3.connect(**pg_config) as pg_conn:
            with pg_conn.cursor() as pg_cursor, tqdm(
                total=total, 
                desc=f"Migrating {table_name}",
                unit="rows"
            ) as pbar:
                
                cols = [desc[0] for desc in syb_cursor.description]
                placeholders = ",".join(["%s"] * len(cols))
                insert_sql = f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({placeholders})"
                
                while True:
                    batch = syb_cursor.fetchmany(self.BATCH_SIZE)
                    if not batch:
                        break
                    
                    execute_batch(pg_cursor, insert_sql, batch)
                    pg_conn.commit()
                    pbar.update(len(batch))
