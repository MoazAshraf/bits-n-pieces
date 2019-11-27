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

def decode_big_endian(int_in_bytes: bytes) -> int:
    """decodes 4 Big-endian bytes to an int"""

    return struct.unpack('>H', int_in_bytes)[0]

def int_to_bytes(integer: int, endianness: str='big') -> bytes:
    """converts an integer into bytes with size depending on integer size"""

    n_bytes = (integer.bit_length() + 7) // 8
    return integer.to_bytes(n_bytes, endianness)

def bytes_to_int(string: bytes, endianness: str='big') -> int:
    """converts a byte string into an integer"""

    return int.from_bytes(bytes, endianness)

def bitlist_to_int(bitlist: list) -> int:
    """encodes bit list to int"""

    result = 0
    for bit in bitlist:
        result = (result << 1) | bit
    return result

def bitlist_to_bytes(bitlist: list) -> bytes:
    """encodes bit list to bytes"""

    return int_to_bytes(bitlist_to_int(list))

def byte_to_bitlist(b: bytes) -> list:
    """decodes a single byte to a bitlist"""

    bitlist = []
    integer = bytes_to_int(b)
    while integer // 2 != 0:
        bitlist += integer % 2
        integer //= 2
    bitlist.reverse()
    return bitlist

def bytes_to_bitlist(string: bytes) -> list:
    """decodes bytes to bitlist"""

    bitlist = []
    for b in string:
        bitlist += byte_to_bitlist(b)
    return bitlist

def generate_client_id() -> str:
    """
    Generates a random ID for a BitTorrent client, used as peer_id in tracker requests
    """
    
    return bytes(PEER_ID_PREFIX + ''.join(str(random.randint(0, 9)) for _ in range(12)), 'ascii')