import unittest
from unittest import TestCase

from bitsnpieces.utils import generate_client_id
from bitsnpieces import torrent
from bitsnpieces.tracker import Tracker


class TestTracker(TestCase):
    def test_ubuntu_tracker_started(self):
        torfile = torrent.load("test/data/ubuntu-19.04-desktop-amd64.iso.torrent")
        tracker = Tracker(torfile)
        peer_id = generate_client_id()
        port = 6889
        tracker_response = tracker.announce(peer_id, port, 0, 0, "started")

        self.assertEqual(tracker_response.failed, False)