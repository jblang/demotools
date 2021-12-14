# Copyright (c) 2021 J.B. Langston
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
from collections import namedtuple
from disk import track_sectors
from util import to_word, to_bytes

# Reference:
# BoozeLoader 1.0: https://csdb.dk/release/?id=145208
# Disk 1.0: https://csdb.dk/release/?id=145209
# ByteBoozer 1.1: https://csdb.dk/release/?id=109317
# ByteBoozer 2.0: https://csdb.dk/release/?id=145031

Format = namedtuple("Format", "signature version dest first next")
FORMATS = {
    "b1none": Format(signature=None, version=1, dest=3, first=2, next=5),
    "b1clean": Format(
        signature=b"\x01\x08\x0b\x08\x00\x00\x9e\x32\x30\x36\x31\x00\x00\x00\x78\xa9\x34\x85\x01\xa2\x3d",
        version=1,
        dest=0x113,
        first=0x112,
        next=0x115,
    ),
    "b1normal": Format(
        signature=b"\x01\x08\x0b\x08\x00\x00\x9e\x32\x30\x36\x31\x00\x00\x00\x78\xa9\x34\x85\x01\xa2\x3b",
        version=1,
        dest=0x11D,
        first=0x11C,
        next=0x11F,
    ),
    "b1loader": Format(
        signature=b"\x01\x08\x0b\x08\x00\x00\x9e\x32\x30\x36\x34\x00\x00\x00\x4c\x3c\x08\xa5\xba\x20\xb1",
        version=1,
        dest=0x16B,
        first=0x16A,
        next=0x16D,
    ),
    "b2none": Format(signature=None, version=2, dest=2, first=None, next=4),
    "b2clean": Format(
        signature=b"\x01\x08\x0b\x08\x00\x00\x9e\x32\x30\x36\x31\x00\x00\x00\x78\xa9\x34\x85\x01\xa2\xb7",
        version=2,
        dest=0x87,
        first=None,
        next=0xD7,
    ),
}


def format_info(data, format=None):
    if format in FORMATS:
        return format, FORMATS[format]
    elif data is not None:
        for format, info in FORMATS.items():
            if info.signature is not None and len(info.signature) <= len(data):
                if data[0 : len(info.signature)] == info.signature:
                    return format, info
    return "raw", None


class Deboozer:
    def __init__(self, data, format=None, debug_level=0, **kwargs):
        self.data = data
        self.debug_level = debug_level
        self.format, info = format_info(data, format)
        if self.format == "raw":
            return
        self.dest = to_word(data[info.dest : info.dest + 2])
        self.version = info.version
        if self.version == 1:
            self.bits = data[info.first]
        else:
            self.bits = 0x80
        self.next = info.next
        self.print_debug(
            1,
            f"Initialized {self.format}: "
            f"dest = {self.dest:04x}; "
            f"first = {self.bits:02x}; "
            f"next = {data[info.next]:02x}",
        )

    def print_debug(self, level, text):
        if level < self.debug_level:
            print(text)

    def nextbyte(self):
        byte = self.data[self.next]
        self.next += 1
        self.print_debug(3, f"nextbyte {byte:02x}")
        return byte

    def nextbit(self):
        self.bits <<= 1
        if not self.bits & 0xFF:
            self.bits = self.nextbyte() << 1 | self.bits >> 8 & 1
        bit = self.bits >> 8 & 1
        self.print_debug(3, f"nextbit {bit}")
        return bit

    def copylen(self):
        length = 1
        while length < 0x80 and self.nextbit() == 1:
            length = length << 1 | self.nextbit()
        return length

    def offset1(self, index):
        tab = (4, 2, 2, 2, 5, 2, 2, 3)
        offset = 0
        while offset <= 0xFFFF:
            for _ in range(tab[index]):
                offset = offset << 1 | self.nextbit()
            if index & 3 == 0:
                break
            index -= 1
            offset += 1
        return -offset

    def offset2(self, index):
        tab = (0xDF, 0xFB, 0x00, 0x80, 0xEF, 0xFD, 0x80, 0xF0)
        offset = tab[index]
        if offset != 0:
            while True:
                offset = offset << 1 | self.nextbit()
                if offset & 0x100 == 0:
                    break
        if offset & 0x80:
            offset |= 0xFF00
        else:
            offset = (offset ^ 0xFF) << 8 | self.nextbyte()
        if offset & 0x8000:
            offset = (offset & 0x7FFF) - 0x8000
        return offset

    def offset(self, length):
        index = self.nextbit() << 1 | self.nextbit()
        if length >= 3:
            index += 4
        if self.version == 1:
            return self.offset1(index)
        elif self.version == 2:
            return self.offset2(index)

    def decrunch(self):
        if self.format == "raw":
            return self.data
        mem = bytearray(64 * 1024)
        put = self.dest
        copy = 0
        while True:
            copy = copy or self.nextbit()
            length = self.copylen()
            if copy:
                if length == 0xFF:
                    break
                length += 1
                offset = self.offset(length)
                get = put + offset
                self.print_debug(
                    2,
                    f"copying {length:02x} byte pattern offset by {offset:04x} to {put:04x}",
                )
                for _ in range(length):
                    mem[put] = mem[get]
                    put += 1
                    get += 1
                copy = 0
            else:  # literal
                self.print_debug(2, f"copying {length:02x} byte literal to {put:04x}")
                for _ in range(length):
                    mem[put] = self.nextbyte()
                    put += 1
                copy = length < 0xFF
        return to_bytes(self.dest) + mem[self.dest : put]


def validate_index(block):
    last = False
    for i in range(0, len(block), 2):
        track = block[i]
        sector = block[i + 1]
        if track == 0:
            if i == 0 or sector != 0:
                return False
            else:
                last = True
        elif last or track > 35 or sector >= track_sectors(track):
            return False
    return True


def parse_index(block):
    index = []
    for i in range(0, len(block), 2):
        if block[i] == 0:
            break
        index.append((block[i], block[i + 1]))
    return index


def find_index(disk, track=18, sector="find", **kwargs):
    tracks = range(1, 35) if track == "find" else (track,)
    for track in tracks:
        if sector == "find":
            sectors = range(track_sectors(track))
        else:
            sectors = (sector,)
        for sector in sectors:
            block = disk.dump_block(track, sector)
            if validate_index(block):
                return track, sector, parse_index(block)
    return None, None, None


def extract_trackmo(disk, outdir, format=None, **kwargs):
    track, sector, index = find_index(disk, **kwargs)
    os.makedirs(outdir, exist_ok=True)
    if index is not None:
        print(f"Likely trackmo index found on track {track} at sector {sector}")
        for i, (track, sector) in enumerate(index):
            data = disk.dump_chain(track, sector)
            if format is not None:
                data = Deboozer(data, format).decrunch()
            filename = f"{i:02}-{track:02}-{sector:02}.prg"
            with open(os.path.join(outdir, filename), "wb") as f:
                f.write(data)


def extract_disk(
    disk, outdir, dirfile="dir.txt", fileformat=None, trackformat=None, **kwargs
):
    os.makedirs(outdir, exist_ok=True)
    if dirfile is not None:
        with open(os.path.join(outdir, dirfile), "w") as f:
            f.write(disk.dir_list(**kwargs))
    filedir = os.path.join(outdir, "files")
    decdir = os.path.join(filedir, "decrunched")
    os.makedirs(filedir, exist_ok=True)
    for file in disk.files:
        if file.type_name != "del":
            data = file.dump_data()
            if data is not None:
                with open(os.path.join(filedir, file.dos_name(**kwargs)), "wb") as f:
                    f.write(data)
                if fileformat != "raw":
                    decr = Deboozer(data, fileformat)
                    if decr.format != "raw":
                        if trackformat is None:
                            trackformat = decr.format[:2] + "none"
                        data = decr.decrunch()
                        os.makedirs(decdir, exist_ok=True)
                        with open(
                            os.path.join(decdir, file.dos_name(**kwargs)), "wb"
                        ) as f:
                            f.write(data)
    extract_trackmo(disk, os.path.join(outdir, "trackmo"), format=trackformat, **kwargs)
