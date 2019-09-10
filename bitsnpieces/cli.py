from collections import OrderedDict
import sys
import math

from . import __version__
from .bencode.decoder import decode
from . import torrent

# TODO: command line execution entry point
def main():
    print(f"Bits 'n' Pieces v{__version__}")
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        t = torrent.load(filepath)
        print()
        print(t)

        print(math.ceil(t.info.files[0].length / t.info.piece_length))
        print(len(t.info.pieces) // 20)