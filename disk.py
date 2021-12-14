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

import struct
from collections import namedtuple

import petscii

# From https://vice-emu.sourceforge.io/vice_17.html#SEC345
# fmt: off
TRACK_START = ( 
    -21, 0, 21, 42, 63, 84, 105, 126, 147, 168, 189, 210, 231, 252, 273, 
    294, 315, 336, 357, 376, 395, 414, 433, 452, 471, 490, 508, 526, 544,
    562, 580, 598, 615, 632, 649, 666, 683, 700, 717, 734, 751, 768, 785
)
# fmt: on


def disk_offset(track, sector):
    return (TRACK_START[track] + sector) * 256


def track_sectors(track):
    if track > 0 and track < len(TRACK_START):
        return TRACK_START[track] - TRACK_START[track - 1]


BAM_STRUCT = "< 3B x 140s 16s 2x 5s 5x 20s 20s 44x"
BAM = namedtuple(
    "BAM",
    "dir_sector dir_track dos_version bam disk_name disk_id dolphin_bam speed_bam",
)
DIR_STRUCT = "< 5B 16s 3B 6x h"
TYPE_NAMES = ("del", "seq", "prg", "usr", "rel")


class File:
    def __init__(
        self,
        disk,
        next_track,
        next_sector,
        file_type,
        file_track,
        file_sector,
        filename,
        side_track,
        side_sector,
        rel_length,
        sector_count,
    ):
        self.disk = disk
        self.next_track = next_track
        self.next_sector = next_sector
        self.file_type = file_type
        type_index = file_type & 0xF
        file_flags = file_type & 0xF0
        self.is_closed = bool(file_flags & 0x80)
        self.is_locked = bool(file_flags & 0x40)
        self.is_scratched = self.file_type == 0
        self.type_name = TYPE_NAMES[type_index] if type_index < 5 else ""
        self.file_track = file_track
        self.file_sector = file_sector
        self.filename = filename
        self.side_track = side_track
        self.side_sector = side_sector
        self.rel_length = rel_length
        self.sector_count = sector_count

    def dir_entry(self, lower=False):
        if self.file_type != 0:
            splat = " " if self.is_closed else "*"
            lock = "<" if self.is_locked else " "
            filename = f'"{petscii.to_unicode(self.filename, lower)}"'
            filetype = self.type_name
            if not lower:
                filetype = filetype.upper()
            sectors = self.sector_count
            return f"{sectors:<4} {filename:<18}{splat}{filetype}{lock}"
        else:
            return ""

    def dos_name(self, lower=False):
        filename = petscii.to_unicode(self.filename, lower)
        ext = self.type_name
        if not lower:
            ext = ext.upper()
        return f"{filename}.{ext}"

    def dump_data(self):
        if self.file_type != 0:
            return self.disk.dump_chain(self.file_track, self.file_sector)


class Disk:
    def __init__(self, filename):
        self.filename = filename
        with open(filename, "rb") as f:
            self.image = f.read()
        self.parse_bam()
        self.parse_dir()

    def dump_block(self, track, sector):
        offset = disk_offset(track, sector)
        return self.image[offset : offset + 256]

    def dump_chain(self, track, sector, trim_link=True, trim_last=True):
        data = b""
        while track > 0:
            block = self.dump_block(track, sector)
            track = block[0]
            sector = block[1]
            if trim_last and track == 0:
                block = block[: sector + 1]
            if trim_link:
                block = block[2:]
            data += block
        return data

    def parse_bam(self):
        bam = BAM._make(struct.unpack(BAM_STRUCT, self.dump_block(18, 0)))
        self.disk_id = bam.disk_id
        self.disk_name = bam.disk_name
        self.dos_version = bam.dos_version
        self.bam = bam.bam
        self.blocks_free = 0
        for track, i in enumerate(range(0, len(self.bam), 4), 1):
            if track != 18:
                self.blocks_free += self.bam[i]

    def parse_dir(self):
        self.files = []
        dir = self.dump_chain(18, 1, trim_link=False, trim_last=False)
        for entry in [dir[i : i + 32] for i in range(0, len(dir), 32)]:
            file = File(self, *struct.unpack(DIR_STRUCT, entry))
            if not file.is_scratched:
                self.files.append(file)

    def dir_header(self, lower=False):
        disk_name = petscii.to_unicode(self.disk_name, lower)
        disk_id = petscii.to_unicode(self.disk_id, lower)
        return f'0 "{disk_name}" {disk_id}'

    def dir_list(self, lower=False):
        header = self.dir_header(lower)
        listing = "\n".join(f.dir_entry(lower) for f in self.files)
        footer = f"{self.blocks_free} BLOCKS FREE."
        if lower:
            footer = footer.lower()
        return f"{header}\n{listing}\n{footer}\n"
