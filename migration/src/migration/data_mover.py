import pytds
import psycopg3
from tqdm import tqdm
import logging
from psycopg3 import Pool

# Set up logging
logger = logging.getLogger("data-mover")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)

class DataMover:
    BATCH_SIZE = 1000
    COMMIT_BATCH_COUNT = 10  # Number of batches after which to commit in bulk (optimization)

    def __init__(self, pg_config: dict):
        # Using psycopg3 connection pooling
        self.pg_config = pg_config
        self.pg_pool = Pool(max_size=10, **self.pg_config)  # Connection pool with a max size of 10

    def migrate_table(self, table_name: str, sybase_config: dict):
        try:
            with pytds.connect(**sybase_config) as syb_conn:
                with syb_conn.cursor() as syb_cursor:
                    # Get total row count from Sybase
                    syb_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_rows = syb_cursor.fetchone()[0]

                    # Start migrating data
                    syb_cursor.execute(f"SELECT * FROM {table_name}")
                    self._copy_data(syb_cursor, table_name, total_rows)
        except (OperationalError, InterfaceError) as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error during migration: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"General error during migration for {table_name}: {str(e)}")
            raise

    def _copy_data(self, syb_cursor, table_name: str, total: int):
        try:
            with self.pg_pool.connection() as pg_conn:  # Using pooled connection
                with pg_conn.cursor() as pg_cursor, tqdm(
                    total=total,
                    desc=f"Migrating {table_name}",
                    unit="rows"
                ) as pbar:
                    cols = [desc[0] for desc in syb_cursor.description]
                    placeholders = ",".join(["%s"] * len(cols))
                    insert_sql = f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({placeholders})"

                    batch_count = 0  # Track number of batches migrated

                    while True:
                        # Fetch a batch of data
                        batch = syb_cursor.fetchmany(self.BATCH_SIZE)
                        if not batch:
                            break

                        # Perform batch insert using psycopg3
                        pg_cursor.executemany(insert_sql, batch)
                        batch_count += 1

                        # Commit in bulk after every COMMIT_BATCH_COUNT
                        if batch_count >= self.COMMIT_BATCH_COUNT:
                            pg_conn.commit()  # Commit the transaction after the specified number of batches
                            batch_count = 0  # Reset batch counter

                        pbar.update(len(batch))

                    # Final commit for any remaining batches
                    if batch_count > 0:
                        pg_conn.commit()

        except (OperationalError, InterfaceError) as e:
            logger.error(f"Error during database operation: {str(e)}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error during data copying: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"General error during data migration: {str(e)}")
            raise
