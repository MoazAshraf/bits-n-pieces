import requests
import urllib.parse

from .bencode import decoder
from .utils import get_str_prop, ip_from_bytes, decode_port

class TrackerResponse(object):
    """
    Abstarcts a tracker response for a single torrent
    """
    
    def __init__(self, http_response):
        self._response = decoder.decode(http_response.content)
        self._failed = b'failure reason' in self._response
        self._peers = None
        
        # parse the peers list
        if not self._failed:
            peers_list = self._response.get(b'peers')
            if isinstance(peers_list, bytes):
                # binary (compact) model
                self._peers = self._parse_binary_peers_list(peers_list)
            elif isinstance(peers_list, dict):
                # list of dictionaries model
                self._peers = self._parse_dict_peers_list(peers_list)
    
    def __str__(self) -> str:
        s = [
            f"failure reason: {str(self.failure_reason)}",
            f"warning message: {str(self.warning_message)}",
            f"interval: {str(self.interval)}s",
            f"complete (seeders): {str(self.complete)}",
            f"incomplete (leechers): {str(self.incomplete)}",
            f"peers: {str(self.peers)}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def _parse_binary_peers_list(self, peers_str):
        """parses a binary string of peers into a list of dictionaries of peers each with parsed IP and port"""
        
        peers_list = []
        for peer_start in range(0, len(peers_str), 6):
            ip = ip_from_bytes(peers_str[peer_start:peer_start+4])
            port = decode_port(peers_str[peer_start+4:peer_start+6])
            peers_list.append({'ip': ip, 'port': port})
        return peers_list
    
    def _parse_dict_peers_list(self, peers_list):
        """parses each peer's ID, IP and port in a list of dictionaries of peers"""

        parsed_peers_list = []
        for peer in peers_list:
            peer_id = peer.get(b'peer_id')
            ip = peer.get(b'ip').decode('utf-8')
            port = int(peer.get(b'port'))
            parsed_peer = {'peer_id': peer_id, 'ip': ip, 'port': port}
            parsed_peers_list.append(parsed_peer)
        return parsed_peers_list

    @property
    def failed(self) -> bool:
        return self._failed
    
    @property
    def failure_reason(self) -> str:
        return get_str_prop(self._response, b'failure_reason')
    
    @property
    def warning_message(self) -> str:
        return get_str_prop(self._response, b'warning message')
    
    @property
    def interval(self) -> int:
        return self._response.get(b'interval')
    
    @property
    def tracker_id(self) -> bytes:
        return self._response.get(b'tracker id')
    
    @property
    def complete(self) -> int:
        return self._response.get(b'complete')
    
    @property
    def incomplete(self) -> int:
        return self._response.get(b'incomplete')
    
    @property
    def peers(self) -> list:
        return self._peers


class Tracker(object):
    """
    Abstracts the BitTorrent tracker connection for a single torrent
    """
    
    def __init__(self, torrent):
        self.torrent = torrent

    def announce(self, peer_id: str, port: int, uploaded: int, downloaded: int, event: str=None) -> TrackerResponse:
        """
        Makes an announce call to the tracker to update client's
        stats on the server as well as get a list of peers to
        connect to.

        If request is successful, a TrackerResponse object is
        returned.
        """

        params = {
            'info_hash': self.torrent.info.get_sha1(),
            'peer_id': peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_size - downloaded,
            'compact': 1,
            'event': event
        }

        response = requests.get(self.torrent.announce, params=params)
        return TrackerResponse(response)