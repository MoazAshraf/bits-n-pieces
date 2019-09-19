from collections import OrderedDict
from datetime import datetime

from bitsnpieces.utils import get_str_prop
from bitsnpieces.bencode import decoder
from . import TorrentError
from . import datainfo
from .datainfo import DataInfo


TORRENT_KEYS = [b'announce', b'announce-list', b'comment', b'created by', b'creation date', b'encoding', b'info']


class Torrent(object):
    """class for abstracting .torrent files"""
    def __init__(self, meta_info: OrderedDict=None):
        # setup torrent meta-info dictionary
        if meta_info is None:
            self._meta_info = OrderedDict()
            self._info = DataInfo()
        else:
            for key in meta_info.keys():
                if key not in TORRENT_KEYS:
                    # TODO: make this a warning for BitTorrent forward-compatibility
                    raise TorrentError(f"unknown torrent meta-info key '{key.decode('utf-8')}'")
            self._meta_info = meta_info
            self._info = DataInfo(self._meta_info.get(b'info'))
    
    def __str__(self) -> str:
        info_str = '\n  ' + str(self.info).replace('\n', '\n  ')
        s = [
            f"announce: {str(self.announce)}",
            f"announce-list: {str(self.announce_list)}",
            f"comment: {str(self.comment)}",
            f"created by: {str(self.created_by)}",
            f"creation date: {str(self.creation_date)}",
            f"encoding: {str(self.encoding)}",
            f"info: {info_str}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def announce(self) -> str:
        return get_str_prop(self._meta_info, b'announce')
    
    @property
    def announce_list(self) -> list:
        ann_ls = self._meta_info.get(b'announce-list')
        if ann_ls is not None:
            return [[url.decode('utf-8') for url in tier] for tier in ann_ls]
        return None
    
    @property
    def comment(self) -> str:
        return get_str_prop(self._meta_info, b'comment')
    
    @property
    def created_by(self) -> str:
        return get_str_prop(self._meta_info, b'created by')
    
    @property
    def creation_date(self) -> datetime:
        cr_date = self._meta_info.get(b'creation date')
        if cr_date is not None:
            return datetime.fromtimestamp(cr_date)
        return None
    
    @property
    def encoding(self) -> str:
        return get_str_prop(self._meta_info, b'encoding')
    
    @property
    def info(self) -> DataInfo:
        return self._info
    
    @property
    def total_size(self) -> int:
        return sum(f.length for f in self.info.files)

    def clear(self):
        """clears torrent meta-info"""
        self._meta_info = OrderedDict()


def load(filepath: str) -> Torrent:
    """load a torrent from file"""
    # open .torrent file for binary reading
    with open(filepath, 'rb') as f:
        content = f.read()
    # decode the B-encoded content
    meta_info = decoder.decode(content)
    # create Torrent object
    t = Torrent(meta_info)
    return t

def to_bencode(torrent: Torrent) -> bytes:
    """encodes a torrent in Bencode"""
    # TODO:
    pass

def save(torrent: Torrent, filepath: str):
    """save a torrent to file"""
    # TODO:
    pass