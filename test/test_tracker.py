import unittest
from unittest import TestCase

from bitsnpieces import torrent
from bitsnpieces.tracker import Tracker


class TestTracker(TestCase):
    def test_ubuntu_tracker_started(self):
        torfile = torrent.load("test/data/ubuntu-16.04-desktop-amd64.iso.torrent")
        tracker = Tracker(torfile)
        peer_id = '-BP0001-005634896949'
        tracker.announce(peer_id, 6889, 0, 0, "started")