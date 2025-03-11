from prometheus_client import Gauge, Counter, Histogram

PROXY_METRICS = {
    'active_connections': Gauge('proxy_db_active_connections', 'Current active connections'),
    'connection_errors': Counter('proxy_db_connection_errors', 'Connection errors'),
    'query_duration': Histogram('proxy_query_duration', 'Query execution time', ['query_type']),
    'conversion_errors': Counter('proxy_conversion_errors', 'Conversion failures', ['error_type']),
}

def track_conversion_error(error_type: str):
    PROXY_METRICS['conversion_errors'].labels(error_type).inc()