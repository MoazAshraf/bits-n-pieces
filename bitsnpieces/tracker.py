import requests

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

    def announce(self, client) -> TrackerResponse:
        """
        Makes an announce call to the tracker to update client's
        stats on the server as well as get a list of peers to
        connect to.

        If request is successful, a TrackerResponse object is
        returned.
        """
        # TODO:
        pass