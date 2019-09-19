from .utils import generate_client_id
from .tracker import Tracker

class TorrentClient(object):
    """
    Abstracts the BitTorrent client for a single torrent.
    """
    
    def __init__(self, torfile, id=None, ip=None, port=None):
        self.torrent = torfile
        
        if id is None:
            id = generate_client_id()
        self.id = id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        self.uploaded = 0
        self.downloaded = 0

        # create a tracker
        self.tracker = Tracker(self.torrent)
    
    def start(self):
        """
        Starts downloading the torrent by making announce calls to the tracker and maintaining peer connections
        """
        
        # TODO
        pass