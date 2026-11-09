# Ellingtree Media

The public picture repo of the Ellingtree Research Archive. Whatever is pushed here is public
for good (`README.md`).

- Bringing record images in from FamilySearch, or any site signed in in a browser pane: read
  `FAMILYSEARCH.md` first and follow it exactly. Never save a file to the owner's computer.
- Agents bringing records in add only their own batch folder, and never move, rename, delete or
  re-commit anything else, above all the owner's own uploads in `inbox/` (`IMG_####.JPEG` and the
  like), which are a separate project.
- No picture here may carry the place it was taken: a phone writes its location into every
  photograph, and this repo is public. Whenever a session works here, it runs
  `python3 -I tools/strip-location.py .` and, if anything is listed (the owner's uploads included),
  cleans it with `--write` and commits that first. This is the one change a session makes to files
  it didn't add; the tool takes out the location and nothing else (`README.md`, "Adding pictures").
- A session filing an agent's batch into the archive's gallery moves its pictures to
  `gallery/files/` under their record ids and removes what was folded into the archive (the batch's
  `citations.txt`, index screenshots), as `inbox/README.md` says; the owner's uploads stay as they are.
