import unittest
from unittest import TestCase
import struct
import random
from bitstring import BitArray

from bitsnpieces import peer
from bitsnpieces.client import generate_peer_id


class TestDecodePeerMessages(TestCase):
    def test_decode_handshake(self):
        reserved = bytes([0] * 8)
        info_hash = bytes([random.randint(0, 255) for _ in range(20)])
        client_id = generate_peer_id()
        handshake = bytes([19]) + b'BitTorrent protocol' + reserved + info_hash + client_id

        msg = peer.Handshake.decode(handshake)
        self.assertIsInstance(msg, peer.Handshake)
        self.assertEqual(msg.pstrlen, 19)
        self.assertEqual(msg.protocol_id, b'BitTorrent protocol')
        self.assertEqual(msg.reserved_bytes, reserved)
        self.assertEqual(msg.info_hash, info_hash)
    
    def test_decode_handshake_2(self):
        buffer = b'\x13BitTorrent protocol\x00\x00\x00\x00\x00\x10\x00\x00\xd5@\xfcH\xeb\x12\xf2\x831c\xee\xd6B\x1dD\x9d\xd8\xf1\xce\x1f-lt0D60-,p\x13`\xdc\xf5?C\xa1\xa0\xf2\xc0\x00\x00\x01\xf5'
        msg = peer.Handshake.decode(buffer)
        self.assertIsInstance(msg, peer.Handshake)
        self.assertEqual(msg.pstrlen, 19)
        self.assertEqual(msg.protocol_id, b"BitTorrent protocol")
        self.assertEqual(msg.reserved_bytes, b"\x00\x00\x00\x00\x00\x10\x00\x00")
        self.assertEqual(msg.info_hash, b"\xd5@\xfcH\xeb\x12\xf2\x831c\xee\xd6B\x1dD\x9d\xd8\xf1\xce\x1f")

    def test_decode_keepalive(self):
        msg = peer.KeepAlive.decode(struct.pack('>I', 0))
        self.assertIsInstance(msg, peer.KeepAlive)

    def test_decode_choke(self):
        msg = peer.Choke.decode(struct.pack('>Ib', 1, 0))
        self.assertIsInstance(msg, peer.Choke)
    
    def test_decode_unchoke(self):
        msg = peer.Unchoke.decode(struct.pack('>Ib', 1, 1))
        self.assertIsInstance(msg, peer.Unchoke)
    
    def test_decode_interested(self):
        msg = peer.Interested.decode(struct.pack('>Ib', 1, 2))
        self.assertIsInstance(msg, peer.Interested)
    
    def test_decode_notinterested(self):
        msg = peer.NotInterested.decode(struct.pack('>Ib', 1, 3))
        self.assertIsInstance(msg, peer.NotInterested)
    
    def test_decode_have(self):
        msg = peer.Have.decode(struct.pack('>IbI', 5, 4, 23))
        self.assertIsInstance(msg, peer.Have)
        self.assertEqual(msg.piece_index, 23)
    
    def test_decode_bitfield(self):
        bitfield_length = 50
        bitfield = BitArray([i % 2 for i in range(bitfield_length)])
        bitfield_as_bytes = bitfield.tobytes()
        encoded = struct.pack('>Ib', 1 + len(bitfield_as_bytes), peer.BitField.ID) + bitfield_as_bytes

        msg = peer.BitField.decode(encoded)
        self.assertIsInstance(msg, peer.BitField)
        self.assertEqual(msg.bitfield[:len(bitfield)], bitfield)

    def test_decode_request(self):
        msg = peer.Request.decode(struct.pack('>IbIII', 13, 6, 0, 1, 16384))
        self.assertIsInstance(msg, peer.Request)
        self.assertEqual(msg.index, 0)
        self.assertEqual(msg.begin, 1)
        self.assertEqual(msg.length, 16384)
    
    def test_decode_piece(self):
        block_size = 2048
        block = bytes([random.randint(0, 255) for _ in range(block_size)])
        msg = peer.Piece.decode(struct.pack('>IbII', 9 + block_size, 7, 0, 1) + block)
        self.assertIsInstance(msg, peer.Piece)
        self.assertEqual(msg.index, 0)
        self.assertEqual(msg.begin, 1)
        self.assertEqual(msg.block, block)
    
    def test_decode_cancel(self):
        msg = peer.Cancel.decode(struct.pack('>IbIII', 13, 8, 0, 1, 16384))
        self.assertIsInstance(msg, peer.Cancel)
        self.assertEqual(msg.index, 0)
        self.assertEqual(msg.begin, 1)
        self.assertEqual(msg.length, 16384)


class TestEncodePeerMessages(TestCase):
    def test_encode_handshake(self):
        reserved = bytes([0] * 8)
        info_hash = bytes([random.randint(0, 255) for _ in range(20)])
        protocol_id = b'BitTorrent protocol'
        client_id = generate_peer_id()
        truth = bytes([19]) + protocol_id + reserved + info_hash + client_id

        message = peer.Handshake(info_hash, client_id, reserved, protocol_id)
        self.assertEqual(message.encode(), truth)
    
    def test_encode_keepalive(self):
        truth = struct.pack('>I', 0)

        self.assertEqual(peer.KeepAlive().encode(), truth)
    
    def test_encode_choke(self):
        truth = struct.pack('>Ib', 1, peer.Choke.ID)

        self.assertEqual(peer.Choke().encode(), truth)
    
    def test_encode_unchoke(self):
        truth = struct.pack('>Ib', 1, peer.Unchoke.ID)

        self.assertEqual(peer.Unchoke().encode(), truth)
    
    def test_encode_interested(self):
        truth = struct.pack('>Ib', 1, peer.Interested.ID)

        self.assertEqual(peer.Interested().encode(), truth)
    
    def test_encode_notinterested(self):
        truth = struct.pack('>Ib', 1, peer.NotInterested.ID)

        self.assertEqual(peer.NotInterested().encode(), truth)
    
    def test_encode_have(self):
        piece_index = 23
        truth = struct.pack('>IbI', 5, peer.Have.ID, piece_index)

        message = peer.Have(piece_index)
        self.assertEqual(message.encode(), truth)
    
    def test_encode_bitfield(self):
        bitfield_length = 50
        bitfield = BitArray([i % 2 for i in range(bitfield_length)])
        bitfield_as_bytes = bitfield.tobytes()
        truth = struct.pack('>Ib', 1 + len(bitfield_as_bytes), peer.BitField.ID) + bitfield_as_bytes

        message = peer.BitField(bitfield)
        self.assertEqual(message.encode(), truth)
    
    def test_encode_request(self):
        index = 0
        begin = 1
        length = 16384
        truth = struct.pack('>IbIII', 13, peer.Request.ID, index, begin, length)

        message = peer.Request(index, begin, length)
        self.assertEqual(message.encode(), truth)
    
    def test_encode_piece(self):
        index = 0
        begin = 1
        block_size = 2048
        block = bytes([random.randint(0, 255) for _ in range(block_size)])
        truth = struct.pack('>IbII', 9 + block_size, peer.Piece.ID, index, begin) + block

        message = peer.Piece(index, begin, block)
        self.assertEqual(message.encode(), truth)

    def test_encode_cancel(self):
        index = 0
        begin = 1
        length = 16384
        truth = struct.pack('>IbIII', 13, peer.Cancel.ID, index, begin, length)

        message = peer.Cancel(index, begin, length)
        self.assertEqual(message.encode(), truth)