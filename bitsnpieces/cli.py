from collections import OrderedDict
import sys
import math
import random

from . import __version__
from .bencode.decoder import decode
from . import torrent
from .tracker import Tracker
from .client import TorrentClient
from .utils import generate_client_id

def main():
    """
    Command line execution entry point.
    """

    print(f"Bits 'n' Pieces v{__version__}\n")

    if len(sys.argv) > 1:
        # load the torrent file
        filepath = sys.argv[1]
        torfile = torrent.load(filepath)
        
        # announce a 'started' event to the tracker
        tracker = Tracker(torfile)
        peer_id = generate_client_id()
        print(tracker.announce(peer_id, 6889, 0, 0, "started"))