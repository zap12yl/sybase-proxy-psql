# Import core components
from migrator import DatabaseMigrator, DatabaseConnectionError, DatabaseNotAvailableError
from schema_translator import SchemaTranslator
from data_mover import DataMover
from sp_converter import SPConverter

# Marks this directory as a Python package
__version__ = "1.0.0"
__all__ = ['migrator', 'schema_translator', 'data_mover', 'sp_converter']

# Common initialization
import logging
logger = logging.getLogger("migration")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)

