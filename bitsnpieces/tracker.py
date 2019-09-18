import requests
import urllib.parse

class TrackerResponse(object):
    """
    Abstarcts a tracker response for a single torrent
    """
    
    def __init__(self, httpresponse):
        # TODO:
        pass


class Tracker(object):
    """
    Abstracts the BitTorrent tracker connection for a single torrent
    """
    
    def __init__(self, torrent):
        self.torrent = torrent

    def announce(self, peer_id: str, port: int, uploaded: int, downloaded: int, event: str) -> TrackerResponse:
        """
        Makes an announce call to the tracker to update client's
        stats on the server as well as get a list of peers to
        connect to.

        If request is successful, a TrackerResponse object is
        returned.
        """
        
        info_hash = urllib.parse.quote(self.torrent.info.get_sha1())
        left = self.torrent.fullsize - downloaded

        params = {
            'info_hash': info_hash,
            'peer_id': urllib.parse.quote(peer_id),
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'event': event
        }
        print(requests.get(self.torrent.announce, params=params))