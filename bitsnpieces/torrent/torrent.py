from collections import OrderedDict

from bitsnpieces.bencode import decoder
from .torrentinfo import TorrentInfo
from . import torrentinfo


TORRENT_KEYS = [
    b'announce',
    b'announce-list',
    b'comment',
    b'created by',
    b'creation date',
    b'encoding'
]

class TorrentError(Exception):
    pass


class Torrent(object):
    """class for abstracting .torrent files"""
    def __init__(self):
        # setup torrent meta-info dictionary
        self.clear()
    
    def __str__(self) -> str:
        info_str = '\n  ' + str(self.info).replace('\n', '\n  ')
        s = [
            f"announce: {str(self.announce)}",
            f"announce-list: {str(self.announce_list)}",
            f"comment: {str(self.comment)}",
            f"created by: {str(self.created_by)}",
            f"creation date: {str(self.creation_date)}",
            f"encoding: {str(self.encoding)}",
            f"file info: {info_str}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))
    
    def __repr__(self) -> str:
        return self.__str__()

    def clear(self):
        """clears torrent meta-info"""
        self.announce = None
        self.announce_list = None
        self.comment = None
        self.created_by = None
        self.creation_date = None
        self.encoding = None
        self.info = None


def from_bencode(bs: bytes):
    """creates a torrent from Bencoded data"""
    # decode the B-encoded content
    meta_info = decoder.decode(bs)
    # create Torrent object
    t = Torrent()
    # store key-value pairs in meta-info dictionary
    if not isinstance(meta_info, OrderedDict):
        raise TorrentError("torrent file must be contain a root-level dictionary")
    for key in meta_info:
        if key in [b'announce', b'comment', b'created by', b'encoding']:
            setattr(t, key.decode('utf-8'), meta_info[key].decode('utf-8'))
        elif key == b'announce-list':
            t.announce_list = [[i.decode('utf-8') for i in l] for l in meta_info[key]]
        elif key == b'creation date':
            t.creation_date = meta_info[key]
        elif key == b'info':
            t.info = torrentinfo.from_dict(meta_info[key])
        else:
            # TODO: make this a warning for BitTorrent forward-compatibility
            raise TorrentError(f"unknown torrent meta-info key '{key.decode('utf-8')}'")
    return t

def to_bencode(torrent: Torrent) -> bytes:
    """encodes a torrent in Bencode"""
    # TODO:
    pass

def load(filepath: str) -> Torrent:
    """load a torrent from file"""
    # open .torrent file for binary reading
    with open(filepath, 'rb') as f:
        content = f.read()
    return from_bencode(content)

def save(torrent: Torrent, filepath: str):
    """save a torrent to file"""
    # TODO:
    pass