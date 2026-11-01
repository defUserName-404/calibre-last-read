# calibre-last-read

calibre GUI plugin that keeps a **Last Read** date column current from the e-book viewer and sorts the library
by it, newest first.

- Works however the viewer was launched (calibre GUI, Finder/Dock, standalone), on any OS calibre runs on.
- Signal: the viewer rewrites `<calibre config>/viewer/annots/<sha256(book path)>.json` on page turns; its mtime is
  the last-read time. The plugin maps that hash to a book by hashing every book's format paths.
- On startup it backfills the column from existing annots files, so reads made while calibre was closed count.
- Sorts by the column on startup and whenever a different book becomes the most recently read (not on every page turn).

## Install
1. Download `LastRead.zip` from the latest release, then in calibre: Preferences → Plugins → **Load plugin from file**.
2. Restart calibre. If the library has no `#last_read` column the plugin creates a date column "Last Read" and asks
   for one more restart. An existing `#last_read` column must be a **date** column; a different type is left alone
   (see the calibre debug output).
3. Make sure the Last Read column is visible (right-click a column header → Add your own columns).

Setting: Preferences → Plugins → Last Read → Customize (turn the automatic sort off). The toolbar menu has
"Sort by last read now".

## Limitations
- Live updates need the calibre main window running (the plugin lives there); the startup backfill covers the rest.
- Only books in the current library (matched by file path hash). Writing the column updates the book's
  "modified" date, as any metadata change does.

## Build
```sh
./build.sh              # dist/LastRead.zip
./build.sh --install    # also calibre-customize -a (quit calibre first)
/usr/bin/python3 -m unittest discover -s tests
```
Debug with `calibre-debug -g` (log lines are prefixed `[last_read]`).

## License
[MIT](LICENSE)
