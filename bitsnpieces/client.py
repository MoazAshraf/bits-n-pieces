class TorrentClient(object):
    """
    Abstracts the BitTorrent client for a single torrent.
    """
    
    def __init__(self, client_id=None, ip=None, port=None, numwant=50):
        if client_id is None:
            client_id = generate_client_id()
        self.client_id = client_id
        
        # TODO: get process IP and port
        self.ip = ip
        self.port = port

        self.uploaded = 0
        self.downloaded = 0
        self.left = None

        self.numwant = numwant

def generate_client_id() -> str:
    """
    Generate a unique ID for a BitTorrent client.
    Used as peer_id in tracker requests.
    """
    # TODO:
    pass