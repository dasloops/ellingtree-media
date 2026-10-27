# Bringing records from FamilySearch into this repo

For an agent with a browser pane signed in to FamilySearch, a shell in its own environment, and
push access to this repo. This is the agreed method, tested end to end: follow it as written
rather than working out another. It suits any site the pane is signed in to, not only
FamilySearch.

## The rules

1. **Nothing goes to the owner's computer.** Never use the viewer's Download button, "Save as" or
   the downloads folder. Images travel from the browser tab to your own environment through the
   tool results, as below.
2. **This repo is public for good.** Whatever is pushed here stays public, even if it is taken out
   later. Only these belong here:
   - government records, and publications from before 1931;
   - nothing that names a member of the family who may be living (born within about the last
     100 years). Leave such a record out entirely, and mention it, with its ark, only in your
     final reply, never in the repo.
   - Copyrighted material (modern books and journals, Find a Grave photos, newspaper clippings
     from subscription sites): transcribe the few lines that matter in `citations.txt`, and
     upload no image.
3. **Locked images stay locked.** A padlock in the viewer, or a 403 at the image address, means
   the account can't see it. Don't try to get round that: cite the record as index-only or not
   viewable.
4. **Read-only on FamilySearch.** Don't edit the Family Tree, attach sources or merge anyone. Use
   the Tree only for leads, and say so when a lead came from it.
5. **Touch only your own batch folder.** `inbox/` holds the owner's own uploads (`IMG_####.JPEG`
   and the like), which are a separate project. Never move, rename, delete or re-commit anything
   you didn't add.
6. **One image at a time**, and only the images the task needs. No bulk crawling.

## Why this way

These alternatives have all been tried or ruled out. Don't spend time on them.

- The Download button or any saved file: it lands on the owner's computer.
- `curl` or `wget` from the shell: the shell has no FamilySearch session. Don't copy cookies or
  tokens out of the browser.
- API tokens: there are none, by design.
- Driving GitHub's web upload page from the browser: fragile, and it commits as the owner.
- Screenshots of the image: too low in resolution. We want the original.

So the bytes travel: FamilySearch → the signed-in tab → base64 text in tool results → your
shell → git.

## Step by step

1. **Find the image's ark.** A record page (`ark:/61903/1:1:…`) links to its image, and the
   film viewer's address carries it: `ark:/61903/3:1:XXXX-XXXX-XXX`. Note the viewer's "image N
   of M" and the DGS (film) number for the citation.
2. **Open the original in the tab itself:**
   `https://sg30p0.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/3:1:XXXX-XXXX-XXX/dist.jpg`.
   - This is the full-size original, the same file the viewer's Download button gives, and it
     opens only for images the account can already view.
   - A 403 means the image is locked: stop there for this one.
   - It must be open in the tab itself, so that the fetch below comes from the same address and
     the browser allows it.
   - If the address ever stops working, take the image address the viewer's download option
     uses.
3. **Run snippet A** in that tab with the JavaScript tool.
   - It fetches the image, computes its SHA-256 and base64, and decides how many pieces to send.
   - It returns `{bytes, type, sha256, pieces}`. Keep the `sha256`.
   - "NOT AN IMAGE" means you are signed out, or the image is locked.
4. **Run snippet B once for each piece**, i = 1 … n, one call each.
   - Each result is at least 650,000 characters, so it is saved to a file under `tool-results/`
     instead of being shown. The padding means even a one-piece image is saved.
   - Don't read the pieces into your context.
   - If a result is ever shown inline, run that piece again.
5. **Join them in the shell:**
   ```
   python3 -I tools/fs-join.py --sha <sha256> --out inbox/<batch>/<name>.jpg <tool-results directory>
   ```
   - The message that says a result was saved gives its path, usually
     `~/.claude/projects/<project>/tool-results/`. Passing the whole directory is fine.
   - The script finds the pieces by their header, in any order, and checks they are all there.
     It decodes them, checks the SHA-256 against the browser's, and checks the image opens.
   - It writes nothing unless every check passes. If it names missing pieces, run snippet B for
     those again.
6. **Run snippet C** to free the tab's memory, then go on to the next image.
7. **Write the image's entry in `citations.txt` now**, while the record is open. Commit and push
   every few images, so a dropped session loses nothing.

## The snippets

**A: fetch the image open in this tab**

```js
(async () => {
  const r = await fetch(location.href, { credentials: 'include' });
  const type = r.headers.get('content-type') || '';
  if (!r.ok || type.includes('html')) return `NOT AN IMAGE: HTTP ${r.status} ${type}`;
  const buf = await r.arrayBuffer();
  const sha = [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))]
    .map(b => b.toString(16).padStart(2, '0')).join('');
  const b64 = await new Promise((ok, no) => {
    const fr = new FileReader();
    fr.onload = () => ok(fr.result.slice(fr.result.indexOf(',') + 1));
    fr.onerror = no;
    fr.readAsDataURL(new Blob([buf]));
  });
  const n = Math.ceil(b64.length / 700000);
  window.__img = { b64, sha, n, size: Math.ceil(b64.length / n) };
  window.__imgInfo = JSON.stringify({ bytes: buf.byteLength, type, sha256: sha, pieces: n });
  return window.__imgInfo;
})()
```

If your tool returns before the promise settles, run `window.__imgInfo` a moment later to read
the result.

**B: return piece i** (change the `1` at the end to the piece number)

```js
((i) => {
  const m = window.__img;
  const body = m.b64.slice((i - 1) * m.size, i * m.size);
  const out = `@@B64 ${i}/${m.n} ${m.sha} @@${body}@@END@@`;
  return out + '.'.repeat(Math.max(0, 650000 - out.length));
})(1)
```

**C: free the memory**

```js
delete window.__img; delete window.__imgInfo; 'cleared'
```

## The batch

- **Folder:** `inbox/<subject>-records-YYYY-MM-DD/`, for example
  `inbox/allee-records-2026-10-28/`. A second batch on the same day ends in `b`.
- **File names:** lowercase, with hyphens, `<kind>-<year>-<place>-<surname>.jpg`.
  - Kinds: census, marriage-record, birth-record, death-record, death-certificate, probate, will,
    deed, pension-card, military, draft-card.
  - Examples: `census-1850-lenox-allee.jpg`, `marriage-record-allee-sargent-1852.jpg`,
    `death-certificate-hayes-1912.jpg`.
  - A document of several pages is one folder named for it, holding `1.jpg`, `2.jpg` … in page
    order, never a file per page: `probate-1866-ashtabula-allee/1.jpg`.
- An index entry with no image needs no picture: transcribe every field in `citations.txt`.
- The archive files the batch later: it renames each picture to its record's id and moves it
  to `gallery/files/`. You don't.

## citations.txt

One text file in the batch folder, laid out as below. Transcribe in full.
- Mark doubtful readings [?] and the census taker's ditto marks [ditto].
- Put your own explanations in [square brackets].
- Don't guess.

```
CITATIONS - <subject> records, batch <n> (FamilySearch, searched <date>)

Folder: <folder>
<n> files. All images are FamilySearch's full-size originals (dist.jpg).

KEY POINTS
- Five to ten lines: what this batch proves, plainly.

==========================================================================================

census-1850-lenox-allee.jpg              [item 2]
  Collection: United States, Census, 1850
  Record:    https://www.familysearch.org/ark:/61903/1:1:XXXX-XXX (the indexed name)
  Image:     https://www.familysearch.org/ark:/61903/3:1:XXXX-XXXX-XXX
             image N of M, DGS 00000000 (the film's title as FamilySearch gives it)
  Held by:   the custodian and creator, as FamilySearch gives them
  Header:    the page heading as written (page no., place, date, enumerator)
  Where:     lines 8-11, near the top
  Transcription (the columns, named):
    8  Walter Allee | 54 | M | Farmer | ... | N.Y.
  Notes:     anything a reader needs: neighbours, oddities, why this is the right person.

==========================================================================================
NOT FOUND OR NOT VIEWABLE (no file)

<item>. What was wanted: not found. Collections, years, places and spellings tried; for a
   locked image, the DGS and image number.
```

**Identity.** A matching name and age is not enough. Accept a record only if it also matches a
spouse, a child, a parent or the place in the task. If you are unsure, upload it and say why in
its Notes.

## Committing

- Start from the latest `main` (`git fetch origin main`). Add only your folder
  (`git add inbox/<batch>/`), never everything.
- Commit with a GitHub no-reply email address: commit details are public here.
- Message: `Inbox: <subject> records from FamilySearch (<n> images, citations.txt)`.
- Push to `main`. The owner uploads often, so if the push is rejected, run
  `git pull --rebase origin main` (only your own unpushed commits are replayed) and push again.
  Never force-push.
- GitHub refuses files over 100 MB. The originals are 1-10 MB.

## When you finish

Reply with:
- the folder's name;
- what was found, a line each;
- what wasn't;
- anything left out because it names someone who may be living, with its ark, for the owner to
  decide.
