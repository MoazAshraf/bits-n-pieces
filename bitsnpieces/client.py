import math
import asyncio

from .utils import generate_peer_id
from .tracker import Tracker
from .peer import Peer


class TorrentClient(object):
    """
    Abstracts the client for a single torrent
    """
    
    def __init__(self, torrent, peer_id: bytes=None, ip=None, port=None):
        # set parameters
        self.torrent = torrent
        
        if peer_id is None:
            peer_id = generate_peer_id()
        self.peer_id = peer_id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        # create piece manager
        self.piece_manager = PieceManager(self.torrent)
        
        # create a tracker
        self.tracker = Tracker(self.torrent)

        # client connected peers list
        self.peers = []
    
    async def start(self):
        """
        Starts downloading the torrent by making announce calls to the tracker and maintaining peer connections
        """
        
        # make the first (started) announce request to the tracker
        tracker_response = await self.tracker.announce(self.peer_id, self.port,
            self.piece_manager.uploaded, self.piece_manager.downloaded, 'started')

        # connect to each peer and start communications
        # for i in range(len(tracker_response.peers)):
        for i in range(1):
            peer = Peer(self, self.torrent, **tracker_response.peers[i])
            
            # TODO: account for failure of connection
            await peer.connect()
            self.peers.append(peer)
        
        # wait for all peers to finish their communication tasks
        comm_tasks = []
        for peer in self.peers:
            comm_tasks.append(peer.communication_task)

        print(comm_tasks)        
        await asyncio.gather(*comm_tasks)
        await self.close()

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

    def __init__(self, torrent):
        # set parameters
        self.torrent = torrent
        self.uploaded = 0
        self.downloaded = 0

        self.initialize_pieces()
        
    
    def initialize_pieces(self):
        """
        Initialize piece list
        """
        
        num_pieces = self.torrent.info.num_pieces
        piece_length = self.torrent.info.piece_length
        last_piece_length = self.torrent.info.total_length - (num_pieces - 1) * piece_length
        
        self.pieces = [Piece(index, piece_length) for index in range(num_pieces - 1)]
        self.pieces.append(Piece(num_pieces - 1, last_piece_length))


class Piece(object):
    """
    Stores piece status and data until it is complete.
    """

    # typical block size in bytes
    BLOCK_LENGTH = 16384

    def __init__(self, index, length):
        # set parameters
        self.index = index
        self.length = length

        # status (can be "missing", "downloading" or "complete")
        self.status = "missing"

        # initialize blocks
        num_blocks = math.ceil(length / Piece.BLOCK_LENGTH)
        last_block_length = length - (num_blocks - 1) * Piece.BLOCK_LENGTH

        self.blocks = [Block(block_index, Piece.BLOCK_LENGTH) for block_index in range(num_blocks - 1)]
        self.blocks.append(Block(num_blocks - 1, last_block_length))


class Block(object):
    """
    Stores block status and data.
    """

    def __init__(self, index, length):
        # set parameters
        self.index = index
        self.length = length

        # status (can be "missing", "requested" or "complete")
        self.status = "missing"
        self.data = None