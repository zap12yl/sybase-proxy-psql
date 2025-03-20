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
from tenacity import retry, stop_after_attempt, wait_fixed

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

# Set up the logging format
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

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
            logger.debug(f"Attempting to connect to PostgreSQL with config: {self.pg_config}")
            conn = psycopg3.connect(**self.pg_config)
            conn.close()
            logger.info("Successfully connected to PostgreSQL.")
        except OperationalError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise DatabaseNotAvailableError("Target database unavailable") from e

    def _execute_pg(self, query: str):
        """Execute PostgreSQL query with connection check"""
        try:
            self._check_database_available()
            logger.debug(f"Executing PostgreSQL query: {query}")
            with psycopg3.connect(**self.pg_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                conn.commit()
            logger.info("PostgreSQL query executed successfully.")
        except OperationalError as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseConnectionError(f"Database error: {str(e)}") from e

    def full_migration(self):
        """Full migration logic"""
        try:
            logger.info("Migration process started.")
            self._check_database_available()
            # Rest of migration logic
            self._migrate_schema()
            self._migrate_data()
            self._migrate_stored_procs()
            logger.info(f"Migration completed successfully.")
        except DatabaseNotAvailableError as e:
            logger.critical("Migration aborted: Target database unavailable")
            raise
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise
        return self.progress.as_dict()

    def _migrate_schema(self):
        """Migrate schema from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            logger.debug(f"Fetching table names from Sybase...")
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                logger.debug(f"Migrating schema for table {table}...")
                schema = conn.execute_sql(f"sp_help {table}")
                pg_ddl = self.translator.convert_schema(table, schema)
                self._execute_pg(pg_ddl)
                self.progress.tables_migrated += 1
                logger.info(f"Schema for table {table} migrated successfully.")

    def _migrate_data(self):
        """Migrate data from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            logger.debug(f"Fetching table names from Sybase for data migration...")
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                logger.debug(f"Migrating data for table {table}...")
                self.data_mover.migrate_table(table, self.sybase_config, self.pg_config)
                row_count = conn.execute_sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                self.progress.rows_migrated += row_count
                logger.info(f"Data for table {table} migrated successfully with {row_count} rows.")

    def _migrate_stored_procs(self):
        """Migrate stored procedures from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            logger.debug(f"Fetching stored procedures from Sybase...")
            procs = conn.execute_sql("SELECT name FROM sysobjects WHERE type='P'")
            for (proc,) in procs:
                logger.debug(f"Converting stored procedure {proc}...")
                definition = conn.execute_sql(f"EXEC sp_helptext '{proc}'")
                pg_func = self.sp_converter.convert(proc, definition)
                self._execute_pg(pg_func)
                self.progress.sprocs_converted += 1
                logger.info(f"Stored procedure {proc} converted successfully.")

    def _execute_pg(self, query: str):
        """Execute PostgreSQL query"""
        with psycopg3.connect(**self.pg_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
            conn.commit()
            logger.debug(f"Executed PostgreSQL query: {query}")
