import unittest
from unittest import TestCase

from bitsnpieces import torrent

class TestTorrentFile(TestCase):
    def test_torrent_load(self):
        torfile = torrent.load("test/data/ubuntu-16.04-desktop-amd64.iso.torrent")
        self.assertEqual(torfile.announce, "http://torrent.ubuntu.com:6969/announce")
        self.assertEqual(torfile.announce_list, [
            ['http://torrent.ubuntu.com:6969/announce'],
            ['http://ipv6.torrent.ubuntu.com:6969/announce']])
    
    def test_torrent_load_info(self):
        torfile = torrent.load("test/data/ubuntu-16.04-desktop-amd64.iso.torrent")
        self.assertEqual(torfile.info.piece_length, 524288)
        self.assertEqual(len(torfile.info.files), 1)
        self.assertEqual(torfile.info.files[0].path, "ubuntu-16.04-desktop-amd64.iso")

if __name__ == '__main__':
    unittest.main()