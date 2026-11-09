# Inbox

New pictures waiting to be filed. Upload them here (or anywhere in the repo; a session will find
them), with nothing more than the file: a session working on the archive writes each one's record
in the archive's `gallery/`, renames the file to its record's id and moves it to `gallery/files/`,
leaving this folder empty again.

Only pictures that can be public for good belong in this repo (see the README at the top).

A photograph taken with a phone carries the place it was taken. A session finding one here takes the
location out at once, before anything else, and commits it:
`python3 -I tools/strip-location.py --write inbox/` (it changes nothing else in the file).

Agents bringing in records put each batch in a folder of its own,
`inbox/<subject>-records-YYYY-MM-DD/`, with its `citations.txt`, and leave everything else here
alone: the loose files (`IMG_####.JPEG` and the like) are the owner's own uploads. The method is
in `FAMILYSEARCH.md`.
