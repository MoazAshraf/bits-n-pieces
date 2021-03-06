import os.path
from collections import OrderedDict
import hashlib

from bitsnpieces import utils
from . import TorrentError
from bitsnpieces.bencode import encoder


INFO_KEYS = [b'piece length', b'pieces', b'private', b'name', b'files']
FILE_INFO_KEYS = [b'length', b'md5sum', b'path', b'name']


class DataInfo(object):
    """
    Abstracts torrent data files info
    """
    def __init__(self, info: OrderedDict=None):
        if info is None:
            self._info = OrderedDict()
            self._files = []
        else:
            for key in info.keys():
                if key not in INFO_KEYS and key not in FILE_INFO_KEYS:
                    # TODO: make this a warning for BitTorrent forward-compatibility
                    raise TorrentError(f"unknown info key '{key.decode('utf-8')}'")
            self._info = info
            fs = self._info.get(b'files')
            if fs is not None:
                self._files = [DataFileInfo(f) for f in fs]
            elif b'name' in self._info.keys():
                f = OrderedDict([
                    (b'length', self._info[b'length']),
                    (b'md5sum', self._info.get(b'md5sum')),
                    (b'path', self._info[b'name']),
                ])
                self._files = [DataFileInfo(f)]
            else:
                self._files = []

    def __str__(self) -> str:
        s = [
            f"piece length: {str(self.piece_length)}",
            f"private: {str(self.private)}",
            f"directory: {str(self.directory)}",
            f"files: {str(self.files)}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def piece_length(self) -> int:
        p_len = self._info.get(b'piece length')
        if p_len is not None:
            return p_len
        return None
    
    @property
    def piece_hashes(self) -> bytes:
        ps = self._info.get(b'pieces')
        if ps is not None:
            return ps
        return None
    
    def get_piece_hash(self, index) -> bytes:
        begin = index * 20
        end = begin + 20
        return self.piece_hashes[begin:end]
    
    @property
    def num_pieces(self) -> int:
        if self.piece_hashes is not None:
            return len(self.piece_hashes) // 20
        return None
    
    @property
    def total_length(self) -> int:
        return sum([f.length for f in self.files])
    
    @property
    def private(self) -> bool:
        prv = self._info.get(b'private')
        if prv is not None:
            return bool(prv)
        return None
    
    @property
    def directory(self) -> str:
        if b'files' in self._info.keys():
            name = self._info.get(b'name')
            if name is not None:
                return name
        return None
    
    @property
    def files(self) -> str:
        return self._files
    
    def get_sha1(self) -> bytes:
        """Calculate the SHA1 hash of the info dictionary. Used in Tracker requests"""
        encoded_info_dict = encoder.encode_dict(self._info)
        return utils.sha1(encoded_info_dict)

    def clear(self):
        self._info = OrderedDict()


class DataFileInfo(object):
    """Abstracts a data file's info"""
    def __init__(self, file: OrderedDict=None):
        if file is None:
            self._file = OrderedDict()
        else:
            for key in file.keys():
                if key not in FILE_INFO_KEYS:
                    # TODO: make this a warning for BitTorrent forward-compatibility
                    raise TorrentError(f"unknown file info key '{key.decode('utf-8')}'")
            self._file = file

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def length(self) -> int:
        l = self._file.get(b'length')
        if l is not None:
            return l
        return None
    
    @property
    def md5sum(self) -> bytes:
        md5 = self._file.get(b'md5sum')
        if md5 is not None:
            return md5
        return None

    @property
    def path(self) -> str:
        pth = self._file.get(b'path')
        if pth is not None:
            if isinstance(pth, bytes):
                return pth.decode('utf-8')
            elif isinstance(pth, list):
                return os.path.join(*(s.decode('utf-8') for s in pth))
        return None

    def clear(self):
        self._file = OrderedDict()