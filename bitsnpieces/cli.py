from collections import OrderedDict
import os
import sys
import math
import random
import asyncio
import argparse

from . import __version__
from .bencode.decoder import decode
from . import torrent
from .tracker import Tracker
from .client import TorrentClient
from .utils import generate_peer_id

async def start_download(filepath, path):
    # load the torrent file
    torfile = torrent.load(filepath)

    # start the client
    client = TorrentClient(torfile, download_directory=path, port=6889)
    await client.start()
    await client.disconnect()

def main():
    """
    Command line execution entry point.
    """

    default_path = os.path.join(os.getcwd(), 'downloads')

    parser = argparse.ArgumentParser(description=f"Bits 'n' Pieces v{__version__}\n")
    parser.add_argument('torrent', help="The metainfo file path (.torrent)")
    parser.add_argument('--path', help="The download directory path, defaults to './downloads'",
                        default=default_path)

    args = parser.parse_args()
    asyncio.run(start_download(args.torrent, args.path))