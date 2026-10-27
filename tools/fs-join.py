#!/usr/bin/env python3
"""Rebuild an image fetched in the browser pane from the pieces saved under tool-results/.

Usage:
  python3 -I tools/fs-join.py --sha <sha256> --out inbox/<folder>/<name>.jpg <file or dir> ...

Each piece is the text the browser returned for one call: a header
"@@B64 <i>/<n> <sha256> @@", the base64 piece, "@@END@@", and padding. The script reads the
files and directories given (a directory is searched for pieces), keeps the pieces whose header
carries the given sha256, checks that pieces 1..n are all there, joins and decodes them, checks
the SHA-256 of the result against the browser's, and checks the image opens. Nothing is written
unless every check passes. See FAMILYSEARCH.md.
"""
import argparse, base64, hashlib, os, re, sys

PIECE = re.compile(r'@@B64 (\d+)/(\d+) ([0-9a-f]{64}) @@([A-Za-z0-9+/=]*)@@END@@')


def files_in(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in names:
                    yield os.path.join(root, n)
        else:
            yield p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sha', required=True, help='the sha256 the browser reported')
    ap.add_argument('--out', required=True, help='where to write the image')
    ap.add_argument('paths', nargs='+', help='tool-result files or directories')
    a = ap.parse_args()
    sha = a.sha.lower()
    pieces, total = {}, None
    for f in files_in(a.paths):
        try:
            text = open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        if '@@B64 ' not in text:
            continue
        text = text.replace('\\/', '/')          # in case the result was saved JSON-escaped
        for m in PIECE.finditer(text):
            i, n, s, body = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            if s != sha:
                continue
            if total not in (None, n):
                sys.exit(f'pieces disagree on the total: {total} and {n}')
            total = n
            if i in pieces and pieces[i] != body:
                sys.exit(f'two different versions of piece {i}')
            pieces[i] = body
    if total is None:
        sys.exit(f'no pieces found for sha {sha}')
    missing = [i for i in range(1, total + 1) if i not in pieces]
    if missing:
        sys.exit(f'missing pieces: {missing} (of {total})')
    data = base64.b64decode(''.join(pieces[i] for i in range(1, total + 1)), validate=True)
    got = hashlib.sha256(data).hexdigest()
    if got != sha:
        sys.exit(f'sha256 mismatch: got {got}')
    kind = ('jpeg' if data[:3] == b'\xff\xd8\xff' else 'png' if data[:8] == b'\x89PNG\r\n\x1a\n'
            else 'tiff' if data[:4] in (b'II*\x00', b'MM\x00*') else None)
    if not kind:
        sys.exit('not an image (an error or login page?): ' + repr(data[:60]))
    size = ''
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            size = f' {im.size[0]}x{im.size[1]}'
    except ImportError:
        pass
    except Exception as e:
        sys.exit(f'the image does not open: {e}')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'wb') as fh:
        fh.write(data)
    print(f'ok {a.out}: {len(data)} bytes, {kind}{size}, {total} pieces, sha256 {got}')


if __name__ == '__main__':
    main()
