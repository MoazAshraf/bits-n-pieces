# Bits 'n' Pieces
A BitTorrent client written in Python. I followed the specification presented [here](https://wiki.theory.org/BitTorrentSpecification).

## Features:
- Bencode encoding and decoding
- Parse torrent files
- Communicate with trackers
- Peer communication protocol
- Simple file download strategy: divide data into small temporary files and concatenate them when the download is over

## Installation and Usage:
**Note**: you need to have python 3.7+ installed since the project uses asyncio features only available since 3.7.

Install the bitsnpieces package using the setup.py file. For example on Linux:
```
$ sudo python3.7 setup.py install
```

To run, invoke the bitsnpieces command. You should see the following output:
```
usage: bitsnpieces [-h] [--path PATH] torrent
bitsnpieces: error: the following arguments are required: torrent
```

You can view all the options using ```bitsnpieces -h```:
```
usage: bitsnpieces [-h] [--path PATH] torrent

Bits 'n' Pieces v0.1.1

positional arguments:
  torrent      The metainfo file path (.torrent)

optional arguments:
  -h, --help   show this help message and exit
  --path PATH  The download directory path, defaults to './downloads'
```

## Technical Details:
- Used python 3.7 asyncio features to stop I/O blocking.
- Wrote unit tests for each module.