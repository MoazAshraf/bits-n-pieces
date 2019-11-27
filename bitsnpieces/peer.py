import struct
import asyncio
from .utils import bitlist_to_bytes, bytes_to_bitlist


class PeerError(Exception):
    pass

class Peer(object):
    """
    Represents a TCP connection to a peer and its last updated state,
    responsible for sending and receiving messages from peer
    """
    
    CHUNK_SIZE = 10240

    def __init__(self, client_id, torrent, ip, port, peer_id=None):
        # parameters
        self.client_id = client_id
        self.torrent = torrent
        self.ip = ip
        self.port = port
        self.peer_id = peer_id
        
        # peer state
        self.is_connected = False
        self.am_chocking = False
        self.am_interested = False
        self.peer_chocking = False
        self.peer_interested = False

        # connection streams
        self.reader = None
        self.writer = None
        self.buffer = b""
        self.buffer_iterator = PeerBufferIterator(self.buffer)

        self.communication_task = None
    
    async def connect(self):
        """
        Opens a TCP connection to this peer and performs a handshake
        """

        # connect
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        except ConnectionRefusedError:
            raise ConnectionError

        # initialize buffer
        self.buffer = b""

        # get torrent info hash
        info_hash = self.torrent.info.get_sha1()

        # send handshake
        handshake = Handshake(info_hash, self.client_id)
        await self.send(handshake)
        
        # receive and decode handshake
        data = await self.read()
        response_handshake = Handshake.decode(data)
        if response_handshake:
            # store peer ID
            self.peer_id = response_handshake.peer_id
            print(f"Received {response_handshake} from {self.peer_id}")
            
            # validate handshake
            if response_handshake.info_hash != info_hash:
                raise PeerError("torrent hash and handshake response hash are not the same")

            msg_len = len(response_handshake)
            self.buffer = data[msg_len:]
            self.buffer_iterator = PeerBufferIterator(self.buffer)

            # start communication
            self.is_connected = True
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

        data = await self.reader.read(Peer.CHUNK_SIZE)
        return data

    async def send(self, message):
        """
        Sends a message to this peer
        """

        # TODO: use logging instead
        print(f"Sent {message} to {self.peer_id}")
        
        if not isinstance(message, PeerMessage):
            raise TypeError(f"Peer.send() requires a PeerMessage object, a {type(message).__name__} "
                            "object was given instead.")
        
        # encode and send the message
        data = message.encode()
        await self.write(data)
    
    def consume(self, message):
        """
        Consumes a peer message and changes peer status
        """

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
            # TODO: let client piece manager handle this
            pass
        elif isinstance(message, Have):
            # TODO: let client piece manager handle this
            pass
        elif isinstance(message, Request):
            # TODO
            pass
        elif isinstance(message, Piece):
            # TODO: let client piece manager handle this
            pass
        elif isinstance(message, Cancel):
            # TODO
            pass
    
    async def start_communication(self):
        """
        Start sending communications with peer (after handshake)
        """

        while self.is_connected:
            self.buffer_iterator.buffer = self.buffer
            async for message in self.buffer_iterator:
                # TODO: use logging instead
                print(type(message))
                print(f"Received {message} from {self.peer_id}")

                # consume message and change client and peer status
                self.consume(message)
            
            self.buffer = self.buffer_iterator.buffer

    async def disconnect(self):
        """
        Closes the connection to this peer.
        """

        self.writer.close()
        await self.writer.wait_closed()
        self.is_connected = False
    
    def __str__(self) -> str:
        s = f"[{self.ip}:{self.port}"
        if not self.peer_id is None:
            s += f"({self.peer_id})"
        s += ']'
        return s

    def __repr__(self) -> str:
        return str(self)


class PeerBufferIterator(object):
    """
    Decodes peer messages in a buffer
    """
    
    def __init__(self, buffer):
        self.buffer = buffer
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        # TODO: deal with bad data (timeout or buffer size limit)
        if not self.buffer:
            raise StopAsyncIteration
        else:
            # read and decode next message in buffer
            msg_len = struct.unpack('>I', self.buffer[0:4])[0]
            
            decoded = None
            if msg_len == 0:
                decoded = KeepAlive()
            else:
                data = self.buffer[:msg_len]
                msg_id = struct.unpack('>b', data[4:5])[0]
                
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
                
            if decoded is None:
                raise StopAsyncIteration
            else:
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
        return f"Handshake(protocol_id: {self.protocol_id}, reserved: {self.reserved_bytes}, hash: {self.info_hash}, peer_id: {self.peer_id})"

    def __repr__(self) -> str:
        return str(self)


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

    def __init__(self, bitfield: bytes):
        self.bitfield = bitfield
    
    def encode(self) -> bytes:
        """
        Encodes this message to bytes.
        """

        return struct.pack('>Ib', 1 + len(self.bitfield), BitField.ID) + self.bitfield

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the data into an instance of a bitfield message. If not a valid message, None is returned.
        """

        try:
            msg_id = struct.unpack('>b', data[4:5])[0]
            if msg_id == cls.ID:
                bitfield = data[5:]
                return cls(bitfield)
        except:
            pass
        return None

    def __str__(self) -> str:
        return f"BitField({self.bitfield})"

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
        return f"Piece(index: {self.index}, begin: {self.begin}, block: {self.block})"

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