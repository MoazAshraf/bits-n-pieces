# import requests
import aiohttp
from urllib.parse import urlencode

from .bencode import decoder
from .utils import get_str_prop, ip_from_bytes, decode_big_endian

class TrackerResponse(object):
    """
    Abstarcts a tracker response for a single torrent
    """
    
    def __init__(self, response_data):
        self._response = decoder.decode(response_data)
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
            port = decode_big_endian(peers_str[peer_start+4:peer_start+6])
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
    
    def __init__(self, torrent, raise_on_failure: bool=False):
        self.torrent = torrent
        self.http_session = aiohttp.ClientSession()
        self.raise_on_failure = raise_on_failure
    
    async def close(self):
        """
        Must be awaited and done before Tracker is deleted
        """

        # TODO: send a shutdown message to tracker
        await self.http_session.close()

    async def announce(self, client_id: bytes, port: int, uploaded: int, downloaded: int, event: str=None) -> TrackerResponse:
        """
        Makes an announce call to the tracker to update client's
        stats on the server as well as get a list of peers to
        connect to.

        If request is successful, a TrackerResponse object is
        returned.
        """

        params = {
            'info_hash': self.torrent.info.get_sha1(),
            'peer_id': client_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_size - downloaded,
            'compact': 1,
            'event': event
        }

        # generate HTTP GET URL
        url = self.torrent.announce + '?' + urlencode(params)

        # make the async GET request and get response
        async with self.http_session.get(url) as response:
            if not response.status == 200:
                raise ConnectionError(f"Unable to connect to the tracker, status code: {response.status}")
            data = await response.read()
        tracker_response = TrackerResponse(data)

        # raise an exception if announce request failed
        if self.raise_on_failure and tracker_response.failed:
            raise ConnectionError(f"Announce request to tracker failed, failure reason: {tracker_response.failure_reason}")
        return tracker_response