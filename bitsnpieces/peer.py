import struct
import asyncio
from bitstring import BitArray


class PeerError(Exception):
    pass

class Peer(object):
    """
    Represents a TCP connection to a peer and its last updated state,
    responsible for sending and receiving messages from peer
    """
    
    CHUNK_SIZE = 10240
    CONNECT_TIMEOUT = 60
    READ_TIMEOUT = 3
    REQUEST_DELAY_AFTER_BLOCK = 0.1
    REQUEST_DELAY_NO_BLOCK = 3

    def __init__(self, client, torrent, ip, port, peer_id=None):
        # parameters
        self.client = client
        self.torrent = torrent
        self.ip = ip
        self.port = port
        self.peer_id = peer_id
        
        # peer state
        self.is_connected = False
        self.am_choking = False
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.pieces_bitarray = BitArray(self.torrent.info.num_pieces)
        self.pieces_downloading = []

        # connection streams
        self.reader = None
        self.writer = None
        self.buffer = b""

        self.communication_task = None
    
    async def connect(self):
        """
        Opens a TCP connection to this peer and performs a handshake
        """

        # connect
        while not self.is_connected:
            try:
                self.reader, self.writer = await asyncio.wait_for(asyncio.open_connection(self.ip, self.port),
                    Peer.CONNECT_TIMEOUT)
                self.is_connected = True
            except:
                continue

        # initialize buffer
        self.buffer = b""

        # perform a handshake
        handshake_success = await self.handshake()
        if handshake_success:
            print(f"Connected to and handshaked peer {self}")
            self.communication_task = asyncio.create_task(self.start_communication())

    async def write(self, data) -> bytes:
        """
        Writes data to this peer.
        """

        self.writer.write(data)
        await self.writer.drain()
    
    async def read(self) -> bytes:
        """
        Reads data from this peer.
        """

        try:
            data = await asyncio.wait_for(self.reader.read(Peer.CHUNK_SIZE), Peer.READ_TIMEOUT)
        except:
            return ""
        return data

    async def send(self, message):
        """
        Sends a message to this peer
        """

        # TODO: use logging instead
        # print(f"Sent {message} to {self}")
        
        if not isinstance(message, PeerMessage):
            raise TypeError(f"Peer.send() requires a PeerMessage object, a {type(message).__name__} "
                            "object was given instead.")
        
        # encode and send the message
        data = message.encode()
        await self.write(data)
    
    async def handshake(self):
        """
        Send a handshake then receive and decode the response and return the message length
        """

        # get torrent info hash
        info_hash = self.torrent.info.get_sha1()

        # send handshake
        try:
            handshake = Handshake(info_hash, self.client.peer_id)
            await self.send(handshake)
            
            # receive and decode handshake
            response_handshake = None
            while response_handshake is None:
                # TODO: timeout or stop when buffer exceeds certain length
                data = await self.read()
                if data:
                    self.buffer += data
                    pstrlen = struct.unpack('>b', data[0:1])[0]
                    if len(data) >= 49+pstrlen:
                        response_handshake = Handshake.decode(data[:49+pstrlen])

            # store peer ID
            self.peer_id = response_handshake.peer_id
            # print(f"Received {response_handshake} from {self}")
            
            # validate handshake
            if response_handshake.info_hash != info_hash:
                raise PeerError("torrent hash and handshake response hash are not the same")

            msg_len = len(response_handshake)
            self.buffer = self.buffer[msg_len:]
            return True
        except (ConnectionRefusedError, ConnectionResetError):
            await self.disconnect()
        
        return False

    async def start_communication(self):
        """
        Start sending and receiving messages to and from peer (after handshake)
        """

        try:
            # send an interested message
            await self.send(Interested())
            self.am_interested = True

            await asyncio.gather(self.start_receiving(), self.start_sending())
        except ConnectionResetError:
            # TODO: send a cancel for the currently requested block
            await self.disconnect()

    async def start_receiving(self):
        """
        Start receiving messages from peer (after handshake and interested)
        """

        while self.is_connected:
            # print("Receiving?")
            stream_iterator = PeerStreamIterator(self.reader, self.buffer)

            async for message in stream_iterator:
                # TODO: use logging instead
                # print(f"Received {message} from {self}")

                # consume message and change client and peer status
                if isinstance(message, KeepAlive):
                    # TODO: make a timeout for inactive connections and break the timeout here
                    pass
                elif isinstance(message, Choke):
                    self.peer_choking = True
                elif isinstance(message, Unchoke):
                    self.peer_choking = False
                elif isinstance(message, Interested):
                    self.peer_interested = True
                elif isinstance(message, NotInterested):
                    self.peer_interested = False
                elif isinstance(message, BitField):
                    self.pieces_bitarray = message.bitfield[:len(self.pieces_bitarray)]
                elif isinstance(message, Have):
                    self.pieces_bitarray[message.piece_index] = True
                elif isinstance(message, Request):
                    # TODO
                    pass
                elif isinstance(message, Piece):
                    # save the block in the piece manager
                    await self.client.piece_manager.download_block(self, message)

                    # make the next block request
                    await asyncio.sleep(Peer.REQUEST_DELAY_AFTER_BLOCK)
                    request_message = self.client.piece_manager.get_next_request(self)
                    if request_message is not None:
                        await self.send(request_message)
                elif isinstance(message, Cancel):
                    # TODO
                    pass
            self.buffer = stream_iterator.buffer
        
    async def start_sending(self):
        """
        Start sending messages to and from peer (after handshake and interested)
        """

        while self.is_connected:
            await asyncio.sleep(Peer.REQUEST_DELAY_NO_BLOCK)
            # print("Sending?")
            if not self.peer_choking:
                # make block requests
                request_message = self.client.piece_manager.get_next_request(self)
                if request_message is not None:
                    await self.send(request_message)

    async def disconnect(self):
        """
        Closes the connection to this peer.
        """

        self.writer.close()
        await self.writer.wait_closed()
        self.is_connected = False
        
        if self in self.client.peers:
            self.client.peers.remove(self)
        
        print(f"Disconnected from {self}")
    
    def __str__(self) -> str:
        s = f"[{self.ip}:{self.port}"
        if not self.peer_id is None:
            s += f"({self.peer_id})"
        s += ']'
        return s

    def __repr__(self) -> str:
        return str(self)


class PeerStreamIterator(object):
    """
    Decodes peer messages coming from a stream reader
    """
    
    def __init__(self, reader, buffer):
        self.reader = reader
        self.buffer = buffer
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        message = self.decode()
        if message:
            return message

        while True:
            # TODO: use try and except, read() may fail with connection errors
            data = await asyncio.wait_for(self.reader.read(Peer.CHUNK_SIZE), Peer.READ_TIMEOUT)
            if data:
                self.buffer += data
                message = self.decode()
                if message:
                    return message
            else:
                break
        raise StopAsyncIteration
    
    def decode(self):
        """
        Decodes the next message in buffer
        """

        buf_len = len(self.buffer)
        if buf_len < 4:
            return None
    
        decoded = None
        msg_len = struct.unpack('>I', self.buffer[0:4])[0]
        
        if msg_len == 0:
            decoded = KeepAlive()
        else:
            if buf_len < 4 + msg_len:
                return None
            data = self.buffer[:4+msg_len]
            msg_id = struct.unpack('>b', data[4:5])[0]
            
            decoded = None
            if msg_id == Choke.ID:
                decoded = Choke()
            elif msg_id == Unchoke.ID:
                decoded = Unchoke()
            elif msg_id == Interested.ID:
                decoded = Interested()
            elif msg_id == NotInterested.ID:
                decoded = NotInterested()
            elif msg_id == Have.ID:
                decoded = Have.decode(data)
            elif msg_id == BitField.ID:
                decoded = BitField.decode(data)
            elif msg_id == Request.ID:
                decoded = Request.decode(data)
            elif msg_id == Piece.ID:
                decoded = Piece.decode(data)
            elif msg_id == Cancel.ID:
                decoded = Cancel.decode(data)
        
        self.buffer = self.buffer[4+msg_len:]
        return decoded


class PeerMessage(object):
    """
    An abstract class meant that represents a message to be sent to or received from a peer.
    """

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """
        
        pass

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of the implementing type.
        """

        pass

    def __len__(self):
        return len(self.encode())


class Handshake(PeerMessage):
    def __init__(self, info_hash: bytes, peer_id: bytes, reserved_bytes: bytes=b'\0'*8,
            protocol_id: bytes=b'BitTorrent protocol'):

        self.pstrlen: int = len(protocol_id)
        self.protocol_id: bytes = protocol_id
        self.reserved_bytes: bytes = reserved_bytes
        self.info_hash: bytes = info_hash
        self.peer_id: bytes = peer_id

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return bytes([self.pstrlen]) + self.protocol_id + self.reserved_bytes + self.info_hash + self.peer_id
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a handshake message. If not a valid message, None is returned.
        """

        try:
            pstrlen = struct.unpack('>b', data[0:1])[0]
            protocol_id = data[1:1+pstrlen]
            reserved = data[1+pstrlen:pstrlen+9]
            info_hash = data[pstrlen+9:pstrlen+29]
            peer_id = data[pstrlen+29:]

            return cls(info_hash, peer_id, reserved, protocol_id)
        except:
            pass
        return None

    def __str__(self) -> str:
        # return f"Handshake(protocol_id: {self.protocol_id}, reserved: {self.reserved_bytes}, hash: {self.info_hash}, peer_id: {self.peer_id})"
        return f"Handshake"

    def __repr__(self) -> str:
        pass


class KeepAlive(PeerMessage):
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>I', 0)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a keep-alive message. If not a valid message, None is returned.
        """

        return cls()

    def __str__(self) -> str:
        return f"KeepAlive"

    def __repr__(self) -> str:
        return str(self)


class Choke(PeerMessage):
    ID = 0

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1, Choke.ID)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a choke message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                return cls()
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Choke"

    def __repr__(self) -> str:
        return str(self)


class Unchoke(PeerMessage):
    ID = 1

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1, Unchoke.ID)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of an unchoke message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                return cls()
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Unchoke"

    def __repr__(self) -> str:
        return str(self)

class Interested(PeerMessage):
    ID = 2

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1, Interested.ID)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of an interested message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                return cls()
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Interested"

    def __repr__(self) -> str:
        return str(self)


class NotInterested(PeerMessage):
    ID = 3

    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1, NotInterested.ID)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a not-interested message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                return cls()
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"NotInterested"

    def __repr__(self) -> str:
        return str(self)


class Have(PeerMessage):
    ID = 4

    def __init__(self, piece_index):
        self.piece_index = piece_index
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>IbI', 5, Have.ID, self.piece_index)
    
    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a have message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                piece_index = struct.unpack('>I', data[5:])[0]
                return cls(piece_index)
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Have(piece index: {self.piece_index})"

    def __repr__(self) -> str:
        return str(self)


class BitField(PeerMessage):
    ID = 5

    def __init__(self, bitfield: BitArray):
        self.bitfield = BitArray(bitfield.tobytes())
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1 + len(self.bitfield) // 8, BitField.ID) + self.bitfield.tobytes()

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a bitfield message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                bitfield = data[5:]
                bitfield = BitArray(bitfield)
                return cls(bitfield)
        except:
            pass
        return None

    def __str__(self) -> str:
        return "BitField"
        # return f"BitField({self.bitfield})"

    def __repr__(self) -> str:
        return str(self)


class Request(PeerMessage):
    ID = 6

    def __init__(self, index, begin, length):
        self.index = index
        self.begin = begin
        self.length = length
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>IbIII', 13, Request.ID, self.index, self.begin, self.length)

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a request message. If not a valid message, None is returned.
        """
        
        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                index, begin, length = struct.unpack('>III', data[5:])
                return cls(index, begin, length)
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Request(index: {self.index}, begin: {self.begin}, length: {self.length})"

    def __repr__(self) -> str:
        return str(self)


class Piece(PeerMessage):
    # sends a block (not a full piece)
    ID = 7

    def __init__(self, index, begin, block):
        self.index = index
        self.begin = begin
        self.block = block
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>IbII', 9 + len(self.block), Piece.ID, self.index, self.begin) + self.block

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a piece message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                index, begin = struct.unpack('>II', data[5:13])
                block = data[13:]
                return cls(index, begin, block)
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Piece(index: {self.index}, begin: {self.begin})"
        # return f"Piece(index: {self.index}, begin: {self.begin}, block: {self.block})"

    def __repr__(self) -> str:
        return str(self)


class Cancel(PeerMessage):
    ID = 8

    def __init__(self, index, begin, length):
        self.index = index
        self.begin = begin
        self.length = length
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>IbIII', 13, Cancel.ID, self.index, self.begin, self.length)

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a cancel message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                index, begin, length = struct.unpack('>III', data[5:])
                return cls(index, begin, length)
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"Cancel(index: {self.index}, begin: {self.begin}, length: {self.length})"

    def __repr__(self) -> str:
        return str(self)