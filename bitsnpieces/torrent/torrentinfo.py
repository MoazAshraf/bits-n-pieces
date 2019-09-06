import os.path
from collections import OrderedDict


class TorrentInfo(object):
    """base class for abstracting torrent data files info, for inheriting"""
    def __init__(self, piecelength=None, pieces=None, private=None, name=None):
        self.piece_length = piecelength
        self.pieces = pieces
        self.private = private
        if self.private is not None:
            self.private = bool(self.private)
        self.name = name


class SingleFileTorrentInfo(TorrentInfo):
    """class for abstracting single data-file torrent info"""
    def __init__(self, piecelength=None, pieces=None, private=None, name=None, length=None, md5sum=None):
        super().__init__(piecelength, pieces, private, name)
        self.length = length
        self.md5sum = md5sum

    def __str__(self) -> str:
        s = [
            f"piece length: {str(self.piece_length)}",
            f"private: {str(self.private)}",
            f"name: {str(self.name)}",
            f"length: {str(self.length)}",
            f"md5sum: {str(self.md5sum)}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))

    def __repr__(self) -> str:
        return self.__str__()


class DataFileInfo(object):
    """class for abstracting data-file info"""
    def __init__(self, length=None, md5sum=None, path=None):
        self.length = length
        self.md5sum = md5sum
        self.path = path

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return self.__str__()


class MultiFileTorrentInfo(TorrentInfo):
    """class for abstracting multiple data-file torrent info"""
    def __init__(self, piecelength=None, pieces=None, private=None, name=None, files=None):
        super().__init__(piecelength, pieces, private, name)
        self.files=files

    def __str__(self) -> str:
        s = [
            f"piece length: {str(self.piece_length)}",
            f"private: {str(self.private)}",
            f"name: {str(self.name)}",
            f"files: {str(self.files)}"
        ]
        return '\n'.join(filter(lambda x: not x.endswith('None'), s))

    def __repr__(self) -> str:
        return self.__str__()


def from_dict(d: OrderedDict) -> TorrentInfo:
    """creates a TorrentInfo object from an info OrderedDict"""
    # determine type (single or multi) and create object
    t = None
    common_keys = (
        d[b'piece length'],
        d[b'pieces'],
        d.get(b'private'),  # optional
        d[b'name'].decode('utf-8')
    )
    if b'files' in d.keys():
        # parse each file
        files = []
        for f in d[b'files']:
            args = f[b'length'], f.get(b'md5sum'), os.path.join(*f[b'path'])
            files.append(DataFileInfo(*args))
        t = MultiFileTorrentInfo(*common_keys, files=files)
    else:
        length = d[b'length']
        md5sum = d.get(b'md5sum')   # optional
        t = SingleFileTorrentInfo(*common_keys, length=length, md5sum=md5sum)
    return t

def from_bencode(bs: bytes) -> TorrentInfo:
    """creates a TorrentInfo object from a Bencoded info dictionary"""
    # TODO:
    pass

def to_bencode(info: TorrentInfo) -> bytes:
    # TODO:
    pass