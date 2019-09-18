## Encoding to B-encoded data
from collections import OrderedDict
from collections.abc import Iterable


class EncodeError(Exception):
    pass

def encode(obj, str_encoding=None) -> bytes:
    """encodes a python object into a B-encoded byte string"""
    
    if isinstance(obj, int):
        return encode_int(obj)
    elif isinstance(obj, bytes) or isinstance(obj, str):
        return encode_str(obj, str_encoding=str_encoding)
    elif isinstance(obj, dict):
        return encode_dict(obj, str_encoding=str_encoding)
    elif isinstance(obj, Iterable):
        return encode_list(obj, str_encoding=str_encoding)
    else:
        raise EncodeError(f"cannot encode object of type {type(obj).__name__}")

def encode_int(integer: int) -> bytes:
    """encodes a python integer into a B-encoded byte string"""
    
    if not isinstance(integer, int):
        raise EncodeError(f"encode_int cannot encode object of type {type(integer).__name__}")
    return b'i' + bytes(str(integer), "ascii") + b'e'

def encode_str(string, str_encoding=None) -> bytes:
    """encodes a python bytes object into a B-encoded byte string"""
    
    byte_string = string
    if isinstance(byte_string, str):
        if str_encoding is None:
            raise EncodeError("cannot encode str objects, str_encoding undefined")
        else:
            byte_string = bytes(string, str_encoding)
    elif not isinstance(byte_string, bytes):
        raise EncodeError(f"cannot encode object of type {type(string).__name__} as Bencode string")

    return bytes(str(len(byte_string)), "ascii") + b':' + byte_string

def encode_list(ls: list, str_encoding=None) -> bytes:
    """encodes a python list into a B-encoded byte string"""
    
    return b'l' + b''.join(encode(item, str_encoding) for item in ls) + b'e'

def encode_dict(dictionary: dict, str_encoding=None) -> bytes:
    """encodes a python dict object into a B-encoded byte string"""
    
    # encode values, convert all keys to bytes
    bytekey_dict = {}
    for key in dictionary:
        byte_key = key
        if isinstance(key, str):
            if str_encoding is None:
                raise EncodeError("cannot encode str objects, str_encoding undefined")
            else:
                byte_key = bytes(key, str_encoding)
        elif not isinstance(key, bytes):
            raise EncodeError("dictionary key must be a valid string or bytes object")
        bytekey_dict[byte_key] = encode(dictionary[key], str_encoding)

    # sort dictionary by byte keys and encode keys
    encoded_dict = OrderedDict((encode_str(key), bytekey_dict[key]) for key in sorted(bytekey_dict.keys()))

    # concatenate encoded keys and values
    encoded = b''.join(key + encoded_dict[key] for key in encoded_dict)
    
    # return encoded dictionary
    return b'd' + encoded + b'e'