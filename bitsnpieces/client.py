class TorrentClient(object):
    """
    Abstracts the BitTorrent client for a single torrent.
    """
    
    def __init__(self, id=None, ip=None, port=None):
        if id is None:
            id = generate_client_id()
        self.id = id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        self.uploaded = 0
        self.downloaded = 0

def generate_client_id() -> str:
    """
    Generate a unique ID for a BitTorrent client.
    Used as peer_id in tracker requests.
    """
    # TODO:
    return ""