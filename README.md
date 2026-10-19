# Ellingtree Media

The pictures of the Ellingtree Research Archive, a family history of the Ellingwood, Holbrook,
Dwyer, Flynn and allied families: the original files of the Gallery's public pictures
(portraits, photographs, documents, record images and maps), kept as they were received.

Each picture's record (what it shows, when and where, who is in it, and its credit, which says
where it comes from) is kept with the archive, not here. The archive's site downloads this repo
when it is built.

```
gallery/files/<id>.jpg        a picture, named by its record's id (any image type)
gallery/files/<id>/1.jpg …    a document of several pages, its pages in order
inbox/                        new uploads, waiting for their records (inbox/README.md)
```

## Adding pictures

- Only pictures the archive publishes as they are (`access: public` in their record). A private
  picture stays in the archive's own repo: whatever is pushed here is public for good, even if
  it is taken out again.
- Push here first, then the archive's records, so its build finds the pictures.
- Commit with a GitHub no-reply email address: commit details are public here.
- GitHub refuses single files over 100 MB.

How the archive uses this repo is in its `gallery/README.md`, "Where the originals are kept".
