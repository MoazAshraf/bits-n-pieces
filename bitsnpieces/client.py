import math
import time
import asyncio
import os.path

from .utils import generate_peer_id, sha1
from .tracker import Tracker
from .peer import Peer, Request


class TorrentClient(object):
    """
    Abstracts the client for a single torrent
    """
    
    def __init__(self, torrent, download_directory: str="test/downloads",
            peer_id: bytes=None, ip=None, port=None):
        # set parameters
        self.torrent = torrent
        self.download_directory = download_directory
        
        if peer_id is None:
            peer_id = generate_peer_id()
        self.peer_id = peer_id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        # create piece manager
        self.piece_manager = PieceManager(self.torrent, self.download_directory)
        
        # create a tracker
        self.tracker = Tracker(self.torrent)

        # client connected peers list
        self.peers = []
    
    async def start(self):
        """
        Starts downloading the torrent by making announce calls to the tracker and maintaining peer connections
        """
        
        # make periodic tracker announcements and update peer list
        await self.start_tracker_announces()
    
    async def start_tracker_announces(self):
        """
        Start sending announces to tracker and updating the peer list
        """

        tracker_response = None
        event = 'started'

        while not self.piece_manager.is_complete:
            # make tracker announce request and get response
            try:
                tracker_response = await self.tracker.announce(self.peer_id, self.port,
                    self.piece_manager.uploaded, self.piece_manager.downloaded, event)
            except ConnectionError:
                print("Tracker announce failed")
                continue
            
            print(f"Announce to tracker {self.torrent.announce}, next request in {tracker_response.interval} seconds")

            # update the peer list
            asyncio.create_task(self.update_peer_list(tracker_response))

            # wait until you can send another request
            await asyncio.sleep(tracker_response.interval)

            if event == 'started':
                event = ""
    
    async def update_peer_list(self, tracker_response):
        # disconnect any peer not in the response
        disconnected_peers = []
        for my_peer in self.peers:
            still_connected = False
            for new_peer in tracker_response.peers:
                if my_peer.ip == new_peer['ip'] and my_peer.port == new_peer['port']:
                    still_connected = True
                    break
            if not still_connected:
                disconnected_peers.append(my_peer)
        
        for peer in disconnected_peers:
            await peer.disconnect()

        # connect to any new peers and update the peer list
        connected_peers = []
        for new_peer in tracker_response.peers:
            connected = False
            for my_peer in self.peers:
                if my_peer.ip == new_peer['ip'] and my_peer.port == new_peer['port']:
                    connected = True
            if connected:
                connected_peers.append(my_peer)
            else:
                # connect to the new peer
                peer_obj = Peer(self, self.torrent, **new_peer)
                try:
                    await peer_obj.connect()
                    connected_peers.append(peer_obj)
                except ConnectionError:
                    pass
        self.peers = connected_peers

    async def disconnect(self):
        """
        Close connections to the tracker and any peers
        """

        for peer in self.peers:
            await peer.disconnect()
        self.peers = []
        await self.tracker.close()
        self.is_connected = False


class PieceManager(object):
    """
    Manages pieces for a single client
    """

    def __init__(self, torrent, download_directory):
        # set parameters
        self.torrent = torrent
        self.download_directory = download_directory
        self.uploaded = 0
        self.downloaded = 0
        self.is_complete = False

        # download metrics
        self.latest_download_sizes = []
        self.latest_download_times = []
        self.num_complete_pieces = 0

        # initialize
        self.initialize_pieces()
        self.data_writer = DataWriter(self.torrent, self.download_directory)
        
    def initialize_pieces(self):
        """
        Initialize piece list
        """
        
        num_pieces = self.torrent.info.num_pieces
        piece_length = self.torrent.info.piece_length
        last_piece_length = self.torrent.info.total_length - (num_pieces - 1) * piece_length
        
        self.pieces = [Piece(self, index, piece_length) for index in range(num_pieces - 1)]
        self.pieces.append(Piece(self, num_pieces - 1, last_piece_length))
    
    def get_next_request(self, peer):
        """
        Returns next request message for this peer.
        Returns None if no requests available (all pieces the peer has have been requested).
        """

        for index, peer_has_piece in enumerate(peer.pieces_bitarray):
            if peer_has_piece and not self.pieces[index].is_complete and peer not in self.pieces[index].requested_from:
                return self.pieces[index].get_next_request(peer)
        return None
    
    async def download_block(self, peer, message):
        """
        Called when a a "Piece" message is received from a peer. Saves block and will write piece to disk
        if a piece is complete.
        """

        piece = self.pieces[message.index]
        if not piece.is_complete:
            block_size = await piece.download_block(peer, message)

            # check if piece is complete
            if piece.is_complete:
                self.num_complete_pieces += 1
            if self.num_complete_pieces == self.torrent.info.num_pieces:
                self.is_complete = True
            
            # update download metrics
            self.downloaded += block_size
            self.latest_download_sizes.append(block_size)
            self.latest_download_times.append(time.time())
            if len(self.latest_download_sizes) > 10:
                self.latest_download_sizes.pop(0)
                self.latest_download_times.pop(0)
            
            download_percentage = self.downloaded * 100 / self.torrent.info.total_length
            if len(self.latest_download_sizes) <= 1:
                download_speed = 0
                time_left = float('inf')
            else:
                total_downloaded = sum(self.latest_download_sizes)
                total_time = self.latest_download_times[-1] - self.latest_download_times[0]
                download_speed = total_downloaded / total_time
                time_left = (self.torrent.info.total_length - self.downloaded) / download_speed
            print(f"Downloaded {block_size} bytes, downloaded: {download_percentage:0.2f}%, "
                f"download speed: {download_speed:0.2f} B/s, time left: {time_left:0.2f}s")

    
    def write_piece(self, piece, data):
        """
        Write the piece's data to disk
        """

        self.data_writer.write_piece(piece, data)


class Piece(object):
    """
    Stores piece status and data until it is complete.
    """

    # typical block size in bytes
    BLOCK_LENGTH = 16384

    def __init__(self, piece_manager, index, length):
        # set parameters
        self.piece_manager = piece_manager
        self.torrent = piece_manager.torrent
        self.index = index
        self.length = length

        self.is_complete = False

        # list of peers this whole piece has been requested from
        self.requested_from = []

        # initialize blocks
        self.num_blocks = math.ceil(length / Piece.BLOCK_LENGTH)
        last_block_length = length - (self.num_blocks - 1) * Piece.BLOCK_LENGTH

        self.blocks = [Block(self.index, block_index, Piece.BLOCK_LENGTH) for block_index in range(self.num_blocks - 1)]
        self.blocks.append(Block(self.index, self.num_blocks - 1, last_block_length))

    def get_next_request(self, peer):
        """
        Returns next request message for this peer.
        Returns None if no requests available (all blocks of this piece have been requested).
        """

        for block in self.blocks:
            if not block.is_complete and peer not in block.requested_from:
                block.requested_from.append(peer)
                if all(peer in b.requested_from for b in self.blocks):
                    self.requested_from.append(peer)
                return block.request()
        return None
    
    async def download_block(self, peer, message):
        """
        Called when a a "Piece" message is received from a peer. Saves block and will write piece to disk
        if the piece is complete. Also updates the piece status. Returns size of data downloaded.
        """

        block_index = message.begin // Piece.BLOCK_LENGTH
        if not self.blocks[block_index].is_complete:
            await self.blocks[block_index].download(message.block)
            
            print(f"Block {block_index+1}/{self.num_blocks} of Piece {self.index+1} is downloaded")
            
            if all(block.is_complete for block in self.blocks):
                data = b""
                for b in self.blocks:
                    data += b.data
                
                piece_data_hash = sha1(data)
                piece_hash_in_torrent = self.torrent.info.get_piece_hash(self.index)
                if piece_data_hash == piece_hash_in_torrent:
                    self.piece_manager.write_piece(self, data)
                    self.is_complete = True
                    print(f"Piece {self.index+1}/{self.piece_manager.torrent.info.num_pieces} is verified and written to disk")
            
            return len(message.block)
        return 0


class Block(object):
    """
    Stores block status and data.
    """

    def __init__(self, piece_index, block_index, length):
        # set parameters
        self.piece_index = piece_index
        self.block_index = block_index
        self.length = length

        self.data = None
        self.is_complete = False

        # list of peers this block has been requested from
        self.requested_from = []

    
    def request(self):
        """
        Returns a request message for this block.
        """

        return Request(self.piece_index, self.block_index * Piece.BLOCK_LENGTH, self.length)
    
    async def download(self, data):
        """
        Called when a a "Piece" message is received from a peer. Saves block and changes its state.
        """

        self.data = data
        self.is_complete = True


class DataWriter(object):
    """
    Writes a single torrent's data to disk
    """

    MAX_TEMP_FILE_SIZE = 2 ** 27   # in bytes
    
    def __init__(self, torrent, download_directory):
        # parameters
        self.torrent = torrent
        self.download_directory = download_directory
        self.temp_base_path = os.path.join(download_directory, torrent.info.files[0].path + ".tmp.")

        # typical temp file size
        self.piece_length = self.torrent.info.piece_length
        max_temp_file_size = DataWriter.MAX_TEMP_FILE_SIZE // self.piece_length * self.piece_length
        self.temp_file_size = min(max_temp_file_size, self.torrent.info.total_length)

        # number of temp files
        self.num_temp_files = math.ceil(self.torrent.info.total_length / self.temp_file_size)
        self.last_temp_file_size = self.torrent.info.total_length - (self.num_temp_files - 1) * self.temp_file_size

        # info on download and temp files
        self.download_filepaths = [os.path.join(download_directory, f_info.path) for f_info in self.torrent.info.files]
        self.temp_files = []
        
    def write_piece(self, piece, data):
        """
        Writes a piece to the appropriate file at the correct position
        """

        # TODO: raise an error
        # if len(data) != piece.length:

        # figure out which temp file to write the piece to
        global_data_position = piece.index * self.piece_length
        temp_file_index = global_data_position // self.temp_file_size

        # create the temp file if necessary
        if len(self.temp_files) <= temp_file_index:
            self.temp_files += [None] * (temp_file_index - len(self.temp_files) + 1)
        if self.temp_files[temp_file_index] is None:
            temp_file_path = self.temp_base_path + str(temp_file_index)
            if temp_file_index == self.num_temp_files - 1:
                temp_file_size = self.last_temp_file_size
            else:
                temp_file_size = self.temp_file_size
            temp_file = TempFile(temp_file_index, temp_file_path, temp_file_size)
            self.temp_files[temp_file_index] = temp_file

        # write the piece to the file and update its state
        data_position_in_temp_file = global_data_position - temp_file_index * self.temp_file_size
        temp_file = self.temp_files[temp_file_index]
        
        # TODO: raise error
        # if data_position_in_temp_file + len(data) > temp_file.size:

        temp_file.write_data(data_position_in_temp_file, data)

        # if temp file is complete, write its data to the actual download files and remove it
        if temp_file.written == temp_file.size:
            self.write_to_download_files(temp_file)
            temp_file.delete()

    def write_to_download_file(self, filepath, position, data):
        """
        Writes the data at the specified position
        """

        # TODO: change this to appending one part of the temp data after another

        if not os.path.isfile(filepath):
            with open(filepath, 'wb') as f:
                pass

        # read the current content to memory
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        file_length = len(file_content)
        data_length = len(data)
        
        # update the content with the new data
        if position < file_length:
            file_content = file_content[:position] + data + file_content[position+data_length:]
        else:
            file_content = file_content + b'\x00' * (position - file_length) + data
        
        # write the updated content to disk
        with open(filepath, 'wb') as f:
            f.write(file_content)

    def write_to_download_files(self, temp_file):
        """
        Writes a temp file to actual download files
        """

        temp_file_content = temp_file.read()

        # figure out which download files contain the data in this temp file
        data_begin = temp_file.index * self.temp_file_size  # start position in all temp data
        data_end = data_begin + temp_file.size              # end position + 1 in all temp data

        file_length_sum = 0
        # for each download file
        for file_index, file_info in enumerate(self.torrent.info.files):
            file_begin = file_length_sum
            file_end = file_begin + file_info.length

            if file_begin >= data_begin and file_begin <= data_end:
                part_begin_in_data = file_begin - data_begin
                part_begin_in_file = 0
            else:
                part_begin_in_data = 0
                part_begin_in_file = data_begin - file_begin

            if file_end >= data_begin and file_end <= data_end:
                part_end_in_data = file_end - data_begin
                # part_end_in_file = file_end - file_begin
            else:
                part_end_in_data = data_end - data_begin
                # part_end_in_file = data_end - file_begin

            # write the data
            self.write_to_download_file(self.download_filepaths[file_index], part_begin_in_file,
                temp_file_content[part_begin_in_data:part_end_in_data])
            
            file_length_sum += file_info.length


class TempFile(object):
    """
    Represents a single download file
    """
    
    def __init__(self, index, filepath, size):
        # parameters
        self.index = index
        self.filepath = filepath
        self.size = size

        # create the file
        with open(self.filepath, 'wb') as f:
            pass

        # length of written bytes
        self.written = 0

    def write_data(self, position, data):
        """
        Writes the data at the specified position
        """

        # read the current content to memory
        file_content = self.read()
        
        file_length = len(file_content)
        data_length = len(data)
        
        # update the content with the new data
        if position < file_length:
            file_content = file_content[:position] + data + file_content[position+data_length:]
        else:
            file_content = file_content + b'\x00' * (position - file_length) + data
        
        # write the updated content to disk
        with open(self.filepath, 'wb') as f:
            f.write(file_content)
        
        self.written += data_length

    def read(self):
        # read the current content to memory
        with open(self.filepath, 'rb') as f:
            file_content = f.read()
        return file_content

    def delete(self):
        # TODO: delete the file
        pass