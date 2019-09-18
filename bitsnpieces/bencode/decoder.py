## Decoding B-encoded data
from collections import OrderedDict


# tokens
TOK_INT = ord('i')      # start of int values
TOK_LIST = ord('l')     # start of lists
TOK_DICT = ord('d')     # start of dicts
TOK_END = ord('e')      # end of ints and lists
TOK_STR_SEP = ord(':')  # delimits string length from string data


class DecodeError(Exception):
    pass

def is_digit(byte: int) -> bool:
    return byte >= ord('0') and byte <= ord('9')

def decode_int(bs: bytes, retlen: bool=False) -> int:
    """decodes a B-encoded integer"""

    if bs[0] != TOK_INT:
        raise DecodeError(f"invalid literal '{chr(bs[0])}', int must start with 'i'")
    end = 1
    if bs[1] == ord('-'):
        end += 1
    while is_digit(bs[end]):
        end += 1
    
    if bs[end] != TOK_END:
        raise DecodeError(f"invalid literal '{chr(bs[end])}', int must end with 'e'")
    
    # validity checking
    if end == 1:
        # empty int invalid
        raise DecodeError(f"int cannot be an empty byte string")
    elif end > 2:
        if bs[1] == ord('0'):
            # leading zeros invalid
            raise DecodeError(f"int cannot have leading zeros")
        elif bs[1:3] == b'-0':
            # negative zero invalid
            raise DecodeError(f"int cannot start with '-0'")
    
    # uncaught validity errors
    try:
        decoded = int(bs[1:end])
    except ValueError:
        raise DecodeError(f"invalid int {bs.decode('ascii')}")

    if retlen:
        # length of original B-encoded byte string
        bencode_len = end + 1
        return decoded, bencode_len
    
    return decoded

def decode_str(bs: bytes, retlen: bool=False) -> bytes:
    """decodes a B-encoded string"""

    if not is_digit(bs[0]):
        raise DecodeError(f"invalid literal '{chr(bs[0])}', string must start with an int length")
    len_end = 1
    while is_digit(bs[len_end]):
        len_end += 1
    if bs[len_end] != TOK_STR_SEP:
        raise DecodeError(f"invalid literal '{chr(bs[len_end])}', string length must end with ':'")
    
    length = int(bs[0:len_end])

    start = len_end + 1
    end = start + length

    if end > len(bs):
        # string length discrepancy
        raise DecodeError(f"string ends before specified length")

    decoded = bs[start:end]

    if retlen:
        # length of original B-encoded byte string
        bencode_len = end
        return decoded, bencode_len

    return decoded

def decode_list(bs: bytes, retlen: bool=False) -> list:
    """decodes a B-encoded list"""

    if bs[0] != TOK_LIST:
        raise DecodeError(f"invalid literal '{chr(bs[0])}', list must start with 'l'")
    end = 1
    decoded = []
    
    while bs[end] != TOK_END:
        decoded_val, bencode_len = decode(bs[end:], retlen=True)
        decoded.append(decoded_val)
        end += bencode_len
        if end >= len(bs):
            raise DecodeError(f"invalid last character '{chr(bs[-1])}', list must end with 'e'")

    if retlen:
        # length of original B-encoded byte string
        bencode_len = end + 1
        return decoded, bencode_len

    return decoded

def decode_dict(bs: bytes, retlen: bool=False) -> OrderedDict:
    """decodes a B-encoded dictionary to and OrderedDict"""
    
    if bs[0] != TOK_DICT:
        raise DecodeError(f"invalid literal '{chr(bs[0])}', dictionary must start with 'd'")
    end = 1
    decoded = OrderedDict()
    while bs[end] != TOK_END:
        try:
            key, bencode_key_len = decode_str(bs[end:], retlen=True)
        except DecodeError:
            raise DecodeError(f"dictionary key must be a valid B-encoded string")
        if key in decoded:
            raise DecodeError(f"duplicate key '{key.decode('ascii')}' in dictionary")
        end += bencode_key_len
        if bs[end] == TOK_END:
            raise DecodeError(f"missing dictionary value, dictionary ends after key '{key}'")
        value, bencode_val_len = decode(bs[end:], retlen=True)
        decoded[key] = value
        end += bencode_val_len
        if end >= len(bs):
            raise DecodeError(f"invalid last character '{chr(bs[-1])}', dictionary must end with 'e'")

    if retlen:
        # length of original B-encoded byte string
        bencode_len = end + 1
        return decoded, bencode_len

    return decoded

def decode(bs: bytes, retlen: bool=False):
    """decodes a B-encoded byte string to a python object"""

    if bs[0] == TOK_INT:
        return decode_int(bs, retlen)
    elif is_digit(bs[0]):
        return decode_str(bs, retlen)
    elif bs[0] == TOK_LIST:
        return decode_list(bs, retlen)
    elif bs[0] == TOK_DICT:
        return decode_dict(bs, retlen)
    else:
        raise DecodeError(f"invalid literal '{chr(bs[0])}'")