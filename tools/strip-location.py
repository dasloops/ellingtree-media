#!/usr/bin/env python3
"""Find, and take out, the location a camera wrote into a photograph.

Usage:
  python3 -I tools/strip-location.py <file or dir> ...            list the pictures that carry a location
  python3 -I tools/strip-location.py --write <file or dir> ...    take the location out of them, in place

A phone writes where a photograph was taken (latitude, longitude, altitude, direction, the time by
satellite) into the file's EXIF block, in a part of it called the GPS IFD. This repo is public for
good, so no picture here may carry one: run this on every photograph before it is committed.

What --write changes, and what it leaves alone:
  - The GPS IFD and every value it points to are overwritten with zeros, and its entry is taken out
    of the EXIF directory, so no reader finds it and nothing is left in the file to recover.
  - Nothing else is touched. The picture itself is not decoded or compressed again, the file keeps
    its length, and the date, the camera, the orientation and the rest of the EXIF stay as they were.
  - A JPEG that holds more than one image (a phone's second, small image behind the first) has each
    image's EXIF block cleaned.

Only JPEG files are changed. A PNG, WebP, TIFF or HEIC that carries a location is listed as
"can't be cleaned here" and makes the run fail, so it is not missed.

Exit status: 0 if no picture carries a location (after cleaning, with --write), 1 otherwise.
"""
import argparse, os, struct, sys

IMAGES = ('.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff', '.heic', '.heif')
SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
GPS_TAG = 0x8825
EXIF = b'Exif\x00\x00'


def files_in(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d != '.git']
                for n in sorted(names):
                    yield os.path.join(root, n)
        else:
            yield p


def exif_blocks(data):
    """Every EXIF block in a JPEG, the second image's too: (start of its TIFF header, its length)."""
    at = 0
    while True:
        at = data.find(EXIF, at)
        if at < 0:
            return
        # An APP1 segment: FF E1, a two-byte length that counts itself, then "Exif\0\0".
        if at >= 4 and data[at - 4:at - 2] == b'\xff\xe1':
            length = struct.unpack('>H', data[at - 2:at])[0] - 2 - len(EXIF)
            if length > 8 and at + len(EXIF) + length <= len(data):
                yield at + len(EXIF), length
        at += len(EXIF)


def gps_entry(data, tiff, length):
    """Where the GPS pointer sits in this block's first directory, or None.

    Returns (byte order, directory offset, number of entries, index of the entry, GPS IFD offset),
    the offsets counted from the TIFF header.
    """
    order = {b'II': '<', b'MM': '>'}.get(bytes(data[tiff:tiff + 2]))
    if not order or struct.unpack(order + 'H', data[tiff + 2:tiff + 4])[0] != 42:
        return None
    ifd = struct.unpack(order + 'I', data[tiff + 4:tiff + 8])[0]
    if ifd + 2 > length:
        return None
    count = struct.unpack(order + 'H', data[tiff + ifd:tiff + ifd + 2])[0]
    if ifd + 2 + 12 * count + 4 > length:
        return None
    for i in range(count):
        entry = tiff + ifd + 2 + 12 * i
        tag, _, _, value = struct.unpack(order + 'HHII', data[entry:entry + 12])
        if tag == GPS_TAG:
            return order, ifd, count, i, value
    return None


def has_location(data):
    return any(gps_entry(data, tiff, length) for tiff, length in exif_blocks(data))


def strip(data):
    """Take the location out of every EXIF block of a JPEG. Returns the number of blocks cleaned."""
    cleaned = 0
    for tiff, length in list(exif_blocks(data)):
        found = gps_entry(data, tiff, length)
        if not found:
            continue
        order, ifd, count, index, gps = found
        # 1. Zero the GPS directory and everything it points to.
        if gps + 2 <= length:
            n = struct.unpack(order + 'H', data[tiff + gps:tiff + gps + 2])[0]
            end = gps + 2 + 12 * n + 4
            if end <= length:
                for i in range(n):
                    entry = tiff + gps + 2 + 12 * i
                    _, kind, items, value = struct.unpack(order + 'HHII', data[entry:entry + 12])
                    size = SIZES.get(kind, 1) * items
                    if size > 4 and value + size <= length:
                        data[tiff + value:tiff + value + size] = bytes(size)
                data[tiff + gps:tiff + end] = bytes(end - gps)
        # 2. Take its entry out of the first directory: the entries after it move up one place, the
        #    pointer to the next directory follows them, and the twelve bytes left over are zeroed.
        start = tiff + ifd
        entries = bytes(data[start + 2:start + 2 + 12 * count])
        following = bytes(data[start + 2 + 12 * count:start + 2 + 12 * count + 4])
        kept = entries[:12 * index] + entries[12 * (index + 1):]
        data[start:start + 2 + 12 * count + 4] = struct.pack(order + 'H', count - 1) + kept + following + bytes(12)
        cleaned += 1
    return cleaned


def other_location(path):
    """A location in a picture this script can't clean (anything but a JPEG), read with Pillow."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return bool(im.getexif().get_ifd(GPS_TAG))
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description='Find, or take out, the location in photographs.')
    ap.add_argument('--write', action='store_true', help='take the location out, in place')
    ap.add_argument('paths', nargs='+', help='pictures, or directories to search')
    a = ap.parse_args()
    seen = found = cleaned = 0
    left = []
    for path in files_in(a.paths):
        low = path.lower()
        if not low.endswith(IMAGES):
            continue
        seen += 1
        if low.endswith(('.jpg', '.jpeg')):
            with open(path, 'rb') as fh:
                data = bytearray(fh.read())
            if not has_location(data):
                continue
            found += 1
            if not a.write:
                print(f'location: {path}')
                continue
            size = len(data)
            strip(data)
            if has_location(data) or len(data) != size:
                left.append(path)
                print(f'NOT CLEANED: {path}')
                continue
            with open(path, 'wb') as fh:
                fh.write(data)
            cleaned += 1
            print(f'cleaned: {path}')
        elif other_location(path):
            found += 1
            left.append(path)
            print(f"location, and can't be cleaned here: {path}")
    if a.write:
        print(f'{seen} pictures looked at, {cleaned} cleaned, {len(left)} still carrying a location')
        sys.exit(1 if left else 0)
    print(f'{seen} pictures looked at, {found} carrying a location')
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
