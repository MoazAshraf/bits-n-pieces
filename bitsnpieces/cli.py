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

        if len(sys.argv) > 2:
            download_directory = sys.argv[2]
        else:
            download_directory = "."
            
        client = TorrentClient(torfile, download_directory=download_directory, port=6889)
        await client.start()
        await client.disconnect()

def main():
    """
    Command line execution entry point.
    """

    print(f"Bits 'n' Pieces v{__version__}\n")
    asyncio.run(async_main())