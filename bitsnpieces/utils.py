import struct
import random


PEER_ID_PREFIX = '-BP0001-'

def get_str_prop(dictionary: dict, key: bytes) -> str:
    """returns a string property from a dictionary or None if non-existent"""

    prop = dictionary.get(key)
    if prop is not None:
        return prop.decode('utf-8')
    return None

def ip_from_bytes(binary_ip: bytes) -> str:
    """converts IP bytes into a dotted format string"""

    return '.'.join(str(int(byte)) for byte in binary_ip)

def decode_port(port: bytes) -> int:
    """decodes Big-endian port to an int"""

    return struct.unpack('>H', port)[0]

def generate_client_id() -> str:
    """
    Generates a random ID for a BitTorrent client, used as peer_id in tracker requests
    """
    
    return PEER_ID_PREFIX + ''.join(str(random.randint(0, 9)) for _ in range(12))