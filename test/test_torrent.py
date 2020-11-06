import unittest
from unittest import TestCase

from bitsnpieces import torrent

class TestTorrentFile(TestCase):
    def test_torrent_load_ubuntu(self):
        torfile = torrent.load("test/data/ubuntu-20.04.1-desktop-amd64.iso.torrent")
        self.assertEqual(torfile.announce, "https://torrent.ubuntu.com/announce")
        self.assertEqual(torfile.announce_list, [
            ['https://torrent.ubuntu.com/announce'],
            ['https://ipv6.torrent.ubuntu.com/announce']])
    
    def test_torrent_load_ubuntu_info(self):
        torfile = torrent.load("test/data/ubuntu-20.04.1-desktop-amd64.iso.torrent")
        self.assertEqual(torfile.info.piece_length, 262144)
        self.assertEqual(len(torfile.info.files), 1)
        self.assertEqual(torfile.info.files[0].path, "ubuntu-20.04.1-desktop-amd64.iso")

if __name__ == '__main__':
    unittest.main()