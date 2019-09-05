from collections import OrderedDict
import sys

from . import __version__
from .bencode.decoder import decode

# TODO: command line execution entry point
def main():
    print(f"Bits 'n' Pieces v{__version__}")
    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        o = decode(f.read())
    
    # print all keys if dictionary
    if isinstance(o, OrderedDict):
        for key in o.keys():
            val = '...'
            if sys.getsizeof(o[key]) < 200:
                val = o[key]
            print(f"{key.decode('ascii')}: {val}")