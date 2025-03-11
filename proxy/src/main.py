import os
import socket
import logging
from protocol_handler import TDSProtocolHandler
from connection_manager import ConnectionManager
from query_handler import QueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-main")

class ProxyServer:
    def __init__(self):
        self.host = os.getenv("PROXY_HOST", "0.0.0.0")
        self.port = int(os.getenv("PROXY_PORT", 5000))
        self.protocol = TDSProtocolHandler()
        self.connections = ConnectionManager()
        self.query_handler = QueryHandler()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(int(os.getenv("MAX_CONNECTIONS", 100)))
            logger.info(f"Sybase proxy listening on {self.host}:{self.port}")
            
            while True:
                conn, addr = s.accept()
                logger.info(f"New connection from {addr}")
                self.handle_connection(conn)

    def handle_connection(self, conn):
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                
                query = self.protocol.parse_query(data)
                translated = self.query_handler.translate(query)
                result = self.execute_query(translated)
                response = self.protocol.build_response(result)
                conn.send(response)
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
        finally:
            conn.close()

    def execute_query(self, query):
        pg_conn = self.connections.get_conn()
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    return cursor.fetchall()
                pg_conn.commit()
                return cursor.rowcount
        finally:
            self.connections.put_conn(pg_conn)

if __name__ == "__main__":
    ProxyServer().start()
