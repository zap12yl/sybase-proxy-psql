# Marks this directory as a Python package
__version__ = "1.0.0"
__all__ = ['main', 'query_handler', 'connection_manager', 'protocol_handler', 'tds_handler', 'metrics','sybase_converter']

# Initialize logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize connection pool on package load
from .connection_manager import ConnectionManager
connection_pool = ConnectionManager()