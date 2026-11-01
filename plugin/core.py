"""Pure logic: viewer annotation mtimes -> per-book "last read" updates. No Qt, no calibre imports."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


def annots_key(path: str) -> str:
    """Name (sans .json) of the viewer's per-book annotations file."""
    return hashlib.sha256(path.encode('utf-8')).hexdigest()


def needs_scan(mtimes: dict, known: dict, last_scan: float, now: float,
               recent_s: float = 600.0, cooldown_s: float = 60.0) -> bool:
    """Rescan the library's format paths only for unknown, recently written keys, at most once per cooldown."""
    if not last_scan:
        return True
    if now - last_scan <= cooldown_s:
        return False
    return any(now - m < recent_s and k not in known for k, m in mtimes.items())


@dataclass(frozen=True)
class Poll:
    updates: tuple  # ((book_id, mtime), ...) newest mtime per book
    resort: bool    # first poll (startup / library switch), or a different book became the most recent


class ReadTracker:
    def __init__(self):
        self._seen: dict = {}  # annots key -> mtime already applied
        self._started = False
        self._top = None  # book most recently read, i.e. at the top of the sorted list

    def reset(self) -> None:
        self._seen.clear()
        self._started = False
        self._top = None

    def poll(self, mtimes: dict, key_books: dict) -> Poll:
        updates: dict = {}
        for key, m in mtimes.items():
            book = key_books.get(key)
            if book is None or m <= self._seen.get(key, 0.0):
                continue  # unknown keys stay unseen so a later scan can still resolve them
            self._seen[key] = m
            if m > updates.get(book, 0.0):
                updates[book] = m
        newest = max(updates, key=updates.get) if updates else None
        # page turns in the book already on top change nothing about the order
        resort = not self._started or (newest is not None and newest != self._top)
        if newest is not None:
            self._top = newest
        self._started = True
        return Poll(tuple(sorted(updates.items())), resort)
