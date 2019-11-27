from .utils import generate_client_id
from .tracker import Tracker
from .peer import Peer


class TorrentClient(object):
    """
    Abstracts the client for a single torrent
    """
    
    def __init__(self, torrent, client_id: bytes=None, ip=None, port=None):
        # set parameters
        self.torrent = torrent
        
        if client_id is None:
            client_id = generate_client_id()
        self.client_id = client_id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        # create piece manager
        self.piece_manager = PieceManager()
        
        # create a tracker
        self.tracker = Tracker(self.torrent)

        # client connected peers list
        self.peers = []
    
    async def start(self):
        """
        Starts downloading the torrent by making announce calls to the tracker and maintaining peer connections
        """
        
        # make the first (started) announce request to the tracker
        tracker_response = await self.tracker.announce(self.client_id, self.port,
            self.piece_manager.uploaded, self.piece_manager.downloaded, 'started')

        # connect to each peer and start communications
        # for i in range(len(tracker_response.peers)):
        for i in range(1):
            peer = Peer(self.client_id, self.torrent, **tracker_response.peers[i])
            
            # TODO: account for failure of connection
            await peer.connect()
            self.peers.append(peer)

    async def close(self):
        """
        Close connections to the tracker and any peers
        """

        for peer in self.peers:
            await peer.disconnect()
        self.peers = []
        await self.tracker.close()


class PieceManager(object):
    """
    Manages pieces for a single client
    """

    def __init__(self):
        # set parameters
        self.uploaded = 0
        self.downloaded = 0