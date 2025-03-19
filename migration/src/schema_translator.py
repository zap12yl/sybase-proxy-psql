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
from psycopg3 import OperationalError, errors  # psycopg3 error imports
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError

logger = logging.getLogger("schema-translator")

class SchemaTranslator:
    TYPE_MAP = {
        'int': 'integer',
        'varchar': 'varchar(255)',  # Added length specification for varchar
        'char': 'char(255)',         # Added length specification for char
        'datetime': 'timestamp',
        'decimal': 'numeric',
        'money': 'numeric(19,4)',
        'text': 'text',
        'image': 'bytea',
        'bit': 'boolean',
        'datetime2': 'timestamp',   # Added datetime2 to timestamp mapping
        'smallint': 'smallint'      # Added smallint type support
    }

    def convert_schema(self, table_name: str, sybase_schema: list) -> str:
        try:
            columns = []
            for col in sybase_schema:
                col_name = col['Column_name']
                col_type = self._map_type(col['Type'])
                nullable = self._build_nullable(col['Nullable'])
                default = self._build_default(col['Default'])
                
                column_def = f"{col_name} {col_type} {nullable} {default}".strip()
                columns.append(column_def)
            
            pk = self._extract_primary_key(sybase_schema)
            logger.info(f"Generating CREATE TABLE for: {table_name}")
            return self._build_create_table(table_name, columns, pk)
        except Exception as e:
            logger.error(f"Schema conversion failed for {table_name}: {str(e)}")
            raise

    def _map_type(self, sybase_type: str) -> str:
        return self.TYPE_MAP.get(sybase_type.lower(), 'text')

    def _build_nullable(self, nullable: str) -> str:
        """Handles nullable column specification."""
        return 'NOT NULL' if nullable == 'NO' else 'NULL'

    def _build_default(self, default: str) -> str:
        """Handles default value clause."""
        return f"DEFAULT {default}" if default else ''

    def _extract_primary_key(self, schema: list) -> str:
        pk_cols = [col['Column_name'] for col in schema if col['Key'] == 1]
        return f"PRIMARY KEY ({', '.join(pk_cols)})" if pk_cols else ""

    def _build_create_table(self, name: str, columns: list, pk: str) -> str:
        ddl = f"CREATE TABLE IF NOT EXISTS {name} (\n  "
        ddl += ",\n  ".join(columns)
        if pk:
            ddl += f",\n  {pk}"
        ddl += "\n);"
        return ddl


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
        except errors.OperationalError as e:
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
        except errors.OperationalError as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseConnectionError(f"Database error: {str(e)}") from e
        except errors.DuplicateTable as e:
            logger.warning(f"Table already exists: {str(e)}")
        except errors.SyntaxError as e:
            logger.error(f"SQL syntax error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _migrate_schema(self):
        """Migrate schema from Sybase to PostgreSQL"""
        with pytds.connect(**self.sybase_config) as conn:
            tables = conn.execute_sql("SELECT name FROM sysobjects WHERE type='U'")
            for (table,) in tables:
                logger.info(f"Starting migration for table schema: {table}")
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
        except RetryError as e:
            logger.error(f"Migration failed after retrying: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise
        self._migrate_schema()
        self._migrate_data()
        self._migrate_stored_procs()
        return self.progress.as_dict()
