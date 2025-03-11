import struct
import logging

logger = logging.getLogger("tds-protocol")

class TDSProtocolHandler:
    def parse_query(self, data: bytes) -> str:
        try:
            header = struct.unpack('>BBH', data[:4])
            if header[0] == 0x03:  # SQL Batch
                return data[8:].decode('utf-16le').strip()
            return ""
        except Exception as e:
            logger.error(f"Protocol error: {str(e)}")
            raise

    def build_response(self, result) -> bytes:
        if isinstance(result, list):
            response = str(result).encode()
        else:
            response = str(result).encode()
        
        header = struct.pack('>BBHII', 
            0x04,  # Packet type
            0x01,  # Status
            len(response) + 8,
            0,  # SPID
            0   # Packet number
        )
        return header + response
