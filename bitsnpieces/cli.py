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
        torfile = torrent.load(filepath)
        print()
        print(torfile)

        # print(math.ceil(torfile.info.files[0].length / torfile.info.piece_length))
        # print(len(torfile.info.pieces) // 20)