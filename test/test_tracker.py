import unittest
from unittest import TestCase
import asyncio

from bitsnpieces.utils import generate_peer_id
from bitsnpieces import torrent
from bitsnpieces.tracker import Tracker


class TestTracker(TestCase):
    def test_ubuntu_tracker_started(self):
        async def async_test(self):
            # load the torrent file
            torfile = torrent.load("test/data/ubuntu-20.04.1-desktop-amd64.iso.torrent")

            # announce a 'started' event to the tracker
            tracker = Tracker(torfile)
            peer_id = generate_peer_id()
            port = 6889
            tracker_response = await tracker.announce(peer_id, port, 0, 0, "started")
            await tracker.close()   # close the tracker client session

            self.assertEqual(tracker_response.failed, False)
        asyncio.run(async_test(self))