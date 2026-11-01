import os
import threading
import time
from datetime import datetime, timezone

from qt.core import QIcon, QMenu, QTimer, pyqtSignal

from calibre import prints
from calibre.constants import config_dir
from calibre.gui2 import info_dialog
from calibre.gui2.actions import InterfaceAction

from calibre_plugins.last_read.config import get_cfg
from calibre_plugins.last_read.core import ReadTracker, annots_key, needs_scan

FIELD = '#last_read'
POLL_SECONDS = 3.0


def log(msg: str) -> None:
    prints(f'[last_read] {msg}')


def annot_mtimes(annots_dir: str) -> dict:
    out = {}
    try:
        with os.scandir(annots_dir) as it:
            for e in it:
                if e.name.endswith('.json'):
                    out[e.name[:-5]] = e.stat().st_mtime
    except OSError:
        pass
    return out


def is_older(current, mtime: float) -> bool:
    try:
        return current is None or current.year < 1900 or current.timestamp() < mtime
    except (OverflowError, OSError, ValueError):
        return True


class Monitor(threading.Thread):
    """Polls the viewer's annots dir and writes #last_read through the thread-safe new_api."""

    def __init__(self, gui, annots_dir, on_update):
        super().__init__(daemon=True, name='last-read-monitor')
        self._gui = gui
        self._annots_dir = annots_dir
        self._on_update = on_update
        self._stop_evt = threading.Event()
        self._tracker = ReadTracker()
        self._lib = None
        self._known = {}  # annots key -> book id
        self._last_scan = 0.0
        self._warned = None

    def stop(self) -> None:
        self._stop_evt.set()

    def _scan(self, db) -> None:
        known = {}
        for book_id in db.all_book_ids():
            for fmt in db.formats(book_id):
                p = db.format_abspath(book_id, fmt)
                if p:
                    known[annots_key(p)] = book_id
        self._known = known
        self._last_scan = time.time()

    def _column_ok(self, db) -> bool:
        fm = db.field_metadata
        if FIELD in fm and fm[FIELD]['datatype'] == 'datetime':
            return True
        problem = 'is not a date column' if FIELD in fm else 'does not exist'
        if self._warned != problem:  # once per state, not every poll
            log(f'column {FIELD} {problem}; not tracking')
            self._warned = problem
        return False

    def _write(self, db, updates) -> list:
        vals = {}
        for book_id, mtime in updates:
            if is_older(db.field_for(FIELD, book_id), mtime):
                vals[book_id] = datetime.fromtimestamp(mtime, tz=timezone.utc)
        if vals:
            db.set_field(FIELD, vals)
        return sorted(vals)

    def _poll(self) -> None:
        db = self._gui.current_db.new_api
        if db is not self._lib:  # library switched: rebuild everything for it
            self._lib, self._known, self._last_scan, self._warned = db, {}, 0.0, None
            self._tracker.reset()
        if not self._column_ok(db):
            return
        mtimes = annot_mtimes(self._annots_dir)
        if needs_scan(mtimes, self._known, self._last_scan, time.time()):
            self._scan(db)
        poll = self._tracker.poll(mtimes, {k: self._known[k] for k in mtimes if k in self._known})
        changed = self._write(db, poll.updates)
        if changed or poll.resort:
            self._on_update(changed, poll.resort)

    def run(self) -> None:
        log('monitor started')
        while not self._stop_evt.wait(POLL_SECONDS):
            try:
                self._poll()
            except Exception as e:  # never let the thread die
                log(f'monitor error: {e!r}')
        log('monitor stopped')


class LastReadAction(InterfaceAction):
    name = 'Last Read'
    action_spec = ('Last Read', None, 'Sort the library by when books were last read', None)
    action_type = 'current'
    action_add_menu = True
    popup_type = 2  # QToolButton.InstantPopup

    updated = pyqtSignal(object, bool)

    def genesis(self):
        self.qaction.setIcon(QIcon.ic('sort.png'))
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self.create_menu_action(self.menu, 'last_read_sort', 'Sort by last read now',
                                triggered=lambda: self._sort())
        self.create_menu_action(self.menu, 'last_read_settings', 'Settings…',
                                triggered=lambda: self.interface_action_base_plugin.do_user_config(self.gui))
        self.updated.connect(self._refresh)
        self.monitor = None

    def initialization_complete(self):
        self._ensure_column()
        self.monitor = Monitor(self.gui, os.path.join(config_dir, 'viewer', 'annots'), self.updated.emit)
        self.monitor.start()

    def shutting_down(self):
        if self.monitor:
            self.monitor.stop()

    def apply_settings(self):
        pass  # sort_enabled is read at use time

    def _ensure_column(self) -> None:
        fm = self.gui.current_db.new_api.field_metadata
        if FIELD in fm:
            return
        self.gui.current_db.create_custom_column('last_read', 'Last Read', 'datetime', False)
        info_dialog(self.gui, 'Last Read',
                    'Created the "Last Read" column. Restart calibre to start filling it in.', show=True)

    def _sort(self) -> None:
        self.gui.library_view.sort_by_named_field(FIELD, False)

    def _refresh(self, ids, resort) -> None:  # GUI thread
        try:
            if ids:
                self.gui.library_view.model().refresh_ids(list(ids))
            if resort and get_cfg()['sort_enabled']:
                QTimer.singleShot(0, self._sort)  # after calibre has finished restoring its own sort
        except Exception as e:
            log(f'refresh failed: {e!r}')
