from collections import OrderedDict
import sys
import math
import random
import asyncio

from . import __version__
from .bencode.decoder import decode
from . import torrent
from .tracker import Tracker
from .client import TorrentClient
from .utils import generate_peer_id

async def async_main():
    if len(sys.argv) > 1:
        # load the torrent file
        filepath = sys.argv[1]
        torfile = torrent.load(filepath)
        # print(torfile.info.piece_length)
        # print(torfile.info.files[0].length/torfile.info.piece_length)

        client = TorrentClient(torfile, port=6889)
        await client.start()
        # await client.close()

def main():
    """
    Command line execution entry point.
    """

    print(f"Bits 'n' Pieces v{__version__}\n")
    asyncio.run(async_main())