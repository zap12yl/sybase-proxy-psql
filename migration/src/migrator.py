import os
import time
import pytds
from tqdm import tqdm
from typing import Dict
from schema_translator import SchemaTranslator
from data_mover import DataMover
from sp_converter import SPConverter
import logging
import psycopg3
from psycopg3 import OperationalError
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

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
            conn = psycopg3.connect(**self.pg_config)
            conn.close()
        except OperationalError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise DatabaseNotAvailableError("Target database unavailable") from e

    def _execute_pg(self, query: str, params: tuple = ()):
        """Execute PostgreSQL query with parameterization"""
        try:
            self._check_database_available()
            with psycopg3.connect(**self.pg_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                conn.commit()
        except OperationalError as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseConnectionError(f"Database error: {str(e)}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _migrate_schema(self):
        """Migrate schema from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                logger.info(f"Starting migration for table schema: {table}")
                # Safely parameterize the table name
                schema = conn.execute_sql("sp_help ?", (table,))
                pg_ddl = self.translator.convert_schema(table, schema)
                self._execute_pg(pg_ddl)
                self.progress.tables_migrated += 1
                logger.info(f"Successfully migrated schema for table: {table} (Total migrated: {self.progress.tables_migrated})")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _migrate_data(self):
        """Migrate data from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                logger.info(f"Starting data migration for table: {table}")
                self.data_mover.migrate_table(table, self.sybase_config, self.pg_config)
                # Parameterizing the row count query to avoid SQL injection
                row_count = conn.execute_sql("SELECT COUNT(*) FROM ?", (table,)).fetchone()[0]
                self.progress.rows_migrated += row_count
                logger.info(f"Successfully migrated {row_count} rows for table: {table} (Total rows migrated: {self.progress.rows_migrated})")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _migrate_stored_procs(self):
        """Migrate stored procedures from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            procs = conn.execute_sql("SELECT name FROM sysobjects WHERE type='P'")
            for (proc,) in procs:
                logger.info(f"Starting stored procedure migration for: {proc}")
                definition = conn.execute_sql("EXEC sp_helptext ?", (proc,))
                pg_func = self.sp_converter.convert(proc, definition)
                self._execute_pg(pg_func)
                self.progress.sprocs_converted += 1
                logger.info(f"Successfully migrated stored procedure: {proc} (Total procedures converted: {self.progress.sprocs_converted})")

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
