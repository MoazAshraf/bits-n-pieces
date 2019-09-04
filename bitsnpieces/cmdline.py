from . import __version__
from . import bencode
import sys
from collections import OrderedDict

# TODO: command line execution entry point
def main():
    print(f"Bits 'n' Pieces v{__version__}")
    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        o = bencode.decode(f.read())
    
    # print all keys if dictionary
    if isinstance(o, OrderedDict):
        for key in o.keys():
            val = '...'
            if sys.getsizeof(o[key]) < 200:
                val = o[key]
            print(f"{key.decode('ascii')}: {val}")