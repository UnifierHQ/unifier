"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2023-present  UnifierHQ

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import zstandard
from io import BytesIO
from typing import Optional, Union

def compress(data: bytes, filename: Optional[str], chunk_size: int, level: int = 1, threads: int = -1) -> None or bytes:
    """Compresses bytes using Zstandard then writes it to disk."""

    # instantiate compressor
    compressor = zstandard.ZstdCompressor(threads=threads, level=level)

    # get appropriate BytesIO object
    if filename:
        target = open(filename, 'wb')
    else:
        target = BytesIO()

    # compress to Zstandard
    with compressor.stream_writer(target) as f:
        for i in range(0, len(data), chunk_size):
            f.write(data[i:i + chunk_size])
        f.flush()
        target.seek(0)
        result = target.read()

    # return bytes if filename is None
    if not filename:
        return result

def decompress(file: Union[bytes, str], chunk_size: int) -> bytes:
    """Decompresses a file compressed using Zstandard."""

    # instantiate decompressor
    decompressor = zstandard.ZstdDecompressor()

    # prepare bytearray
    data = bytearray()

    # get appropriate BytesIO object
    if type(file) is bytes:
        target = BytesIO(file)
    else:
        target = open(file, 'rb')

    # decompress from LZMA
    with decompressor.stream_reader(target) as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            data.extend(chunk)

    # return bytes
    return bytes(data)
