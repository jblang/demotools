# C64 Reverse-Engineering Tools

This is a set of tools for reverse engineering C64 demos. 

## debooze

This tool allows extracting files and trackmo chains from disk images created using ByteBoozer [1.1](https://csdb.dk/release/?id=109317) and [2.0](https://csdb.dk/release/?id=145031) crunching algorithms and the [BoozeLoader](https://csdb.dk/release/?id=145208) trackmo loader and corresponding [Disk](https://csdb.dk/release/?id=145209) creation utility by HCL/Booze Design.

This came out of my experience partially [disassembling](https://github.com/jblang/uncensored) [Uncensored](https://csdb.dk/release/?id=133934) by Booze Design. This involved a lot of manual work, so I wrote this tool to fully automate extraction and decrunching of the files and trackmo chains from the D64 image. 

To extract a Booze Design demo disk, type `debooze DiskName.d64`. This will create a directory structure like this:

- `DiskName.dump`
  - `dir.txt`: Unicode approximation of the PETSCII directory listing
  - `files`: All normal files on the disk with Unicode translation of the PETSCII filename.
    - `decrunched`: decrunched version of the extracted files
  - `trackmo`
    - e.g. `00-01-14.prg`: decrunched trackmo chains named as index-track-sector.prg

The tool automatically figures out which sector contains the trackmo index by looking for a sector with a bunch of valid track/sector pairs padded at the end with zeros.  Usually this is on track 18 sector 9, but some older demos use different sectors (e.g., sector 6 for Edge of Disgrace).  It will also automatically detect the version of ByteBoozer used based on the signature of the decrunching code in the bootloader and then try to use the same version to decrunch all the trackmo files as well. If the tool incorrectly detects something, it is possible to manually override it by passing parameters to the appropriate functions, but currently I haven't made commandline switches for this, so it would require editing the code.

I have extensively verified the results for [Uncensored](https://csdb.dk/release/?id=133934), and less extensively verified that the results for [Remains](https://csdb.dk/release/?id=187524), confirming that the decrunched files match the decrunched data dumped from the VICE monitor, so I think I got both algorithms right. It appears to successfully extract and decrunch [1991](https://csdb.dk/release/?id=101506), [Edge of Disgrace](https://csdb.dk/release/?id=72550), and [The Elder Scrollers](https://csdb.dk/release/?id=179123), but I haven't done any verification yet. It doesn't find any crunched files or trackmo indexes on some other demos like [Mekanix](https://csdb.dk/release/?id=94438) or [Royal Arte](https://csdb.dk/release/?id=11619) and I haven't investigated why yet.


## disassembler

`program.py` contains the beginnings of a disassembler I'm currently trying to build. It is inspired by features from [Regenerator](https://csdb.dk/release/?id=149429) by Nostalgia and [Ghidra](https://ghidra-sre.org/) by the Naughty Spying Agency. I like both of these tools but they both do things that annoy me, so I'm writing my own and hopefully I'll learn a lot in the process.

Currently this is very much a work in progress. It can correctly parse BASIC tokens and do simple tracing disassembly from a starting address. Right now it is just a set of functions and classes that can be called from an Jupyter notebook or IPython shell. Interactive features are still to come. I will probably prototype the UI using the Python curses library and I may consider doing a graphical or web-based version later.  I am planning to use sqlite to store the code blocks, labels, comments, etc.

## MIT License

Copyright (c) 2021 J.B. Langston

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
