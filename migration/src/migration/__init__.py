# Marks this directory as a Python package
__version__ = "1.0.0"
__all__ = ['migrator', 'schema_translator', 'data_mover', 'sp_converter']

# Common initialization
import logging
import os

# Set logging level from environment variable, defaulting to INFO
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

logger = logging.getLogger("migration")
logger.setLevel(log_level)

# Stream handler for console output
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Optionally, add file handler for persistent logging
file_handler = logging.FileHandler('migration.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Import core components
from .migrator import DatabaseMigrator, DatabaseConnectionError, DatabaseNotAvailableError
from .schema_translator import SchemaTranslator
from .data_mover import DataMover
from .sp_converter import SPConverter

# You can now access the components using:
# - migration.DatabaseMigrator
# - migration.SchemaTranslator
# - migration.DataMover
# - migration.SPConverter
