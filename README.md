# Bits 'n' Pieces
A BitTorrent client written in Python.

## Features:
- Bencode encoding and decoding
- Parse torrent files
- Communicate with trackers
- Peer communication protocol
- Simple file download strategy: divide data into small temporary files and concatenate them when the download is over

## Installation and Usage:
**Note**: you need to have python 3.7+ installed since the project uses asyncio features only available since 3.7.

Install the bitsnpieces package:
```
$ python setup.py install
```

To run invoke the bitsnpieces command. You should see the following output:
```
Bits 'n' Pieces v0.1.0

```

## Technical Details:
- Used python 3.7 asyncio features to stop I/O blocking.
- Wrote unit tests for each module.