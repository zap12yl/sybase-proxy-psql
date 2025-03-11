import os
import time
import pytds
from tqdm import tqdm
from typing import Dict
from schema_translator import SchemaTranslator
from data_mover import DataMover
from sp_converter import SPConverter
import logging
import psycopg2
from psycopg2 import OperationalError
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass

class DatabaseNotAvailableError(Exception):
    """Custom exception for target database unavailability"""
    pass

class MigrationProgress:
    def __init__(self):
        self.tables_migrated = 0
        self.rows_migrated = 0
        self.sprocs_converted = 0
        self.start_time = time.time()
    
    def as_dict(self) -> Dict:
        return {
            "tables": self.tables_migrated,
            "rows": self.rows_migrated,
            "sprocs": self.sprocs_converted,
            "duration": time.time() - self.start_time
        }

class DatabaseMigrator:
    def __init__(self):
        self.sybase_config = {
            "server": os.getenv("SYBASE_HOST"),
            "database": os.getenv("SYBASE_DB"),
            "user": os.getenv("SYBASE_USER"),
            "password": os.getenv("SYBASE_PASSWORD")
        }
        self.pg_config = {
            "host": os.getenv("PG_HOST"),
            "database": os.getenv("PG_DB"),
            "user": os.getenv("PG_USER"),
            "password": os.getenv("PG_PASSWORD")
        }
        self.progress = MigrationProgress()
        self.translator = SchemaTranslator()
        self.data_mover = DataMover()
        self.sp_converter = SPConverter()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _check_database_available(self):
        """Check if PostgreSQL database is reachable"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            conn.close()
        except OperationalError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise DatabaseNotAvailableError("Target database unavailable") from e

    def _execute_pg(self, query: str):
        """Execute PostgreSQL query with connection check"""
        try:
            self._check_database_available()
            with psycopg2.connect(**self.pg_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                conn.commit()
        except OperationalError as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseConnectionError(f"Database error: {str(e)}") from e

    def full_migration(self):
        try:
            self._check_database_available()
            # Rest of migration logic
        except DatabaseNotAvailableError as e:
            logger.critical("Migration aborted: Target database unavailable")
            raise
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise
        self._migrate_schema()
        self._migrate_data()
        self._migrate_stored_procs()
        return self.progress.as_dict()
    
    def _migrate_schema(self):
        with pytds.connect(**self.sybase_config) as conn:
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                schema = conn.execute_sql(f"sp_help {table}")
                pg_ddl = self.translator.convert_schema(table, schema)
                self._execute_pg(pg_ddl)
                self.progress.tables_migrated += 1

    def _migrate_data(self):
        with pytds.connect(**self.sybase_config) as conn:
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                self.data_mover.migrate_table(table, self.sybase_config, self.pg_config)
                row_count = conn.execute_sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                self.progress.rows_migrated += row_count

    def _migrate_stored_procs(self):
        with pytds.connect(**self.sybase_config) as conn:
            procs = conn.execute_sql("SELECT name FROM sysobjects WHERE type='P'")
            for (proc,) in procs:
                definition = conn.execute_sql(f"EXEC sp_helptext '{proc}'")
                pg_func = self.sp_converter.convert(proc, definition)
                self._execute_pg(pg_func)
                self.progress.sprocs_converted += 1

    def _execute_pg(self, query: str):
        with psycopg2.connect(**self.pg_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
            conn.commit()
