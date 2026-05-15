from __future__ import annotations

import hashlib
import logging
from typing import Callable

import httpx
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt6.QtGui import QPixmap

from ...core.paths import INSTALL_ROOT

log = logging.getLogger(__name__)

_IMG_CACHE_DIR = INSTALL_ROOT / "img_cache"
_MEM_CACHE: dict[str, QPixmap] = {}


class _ImageSignals(QObject):
    ready = pyqtSignal(str, object)  # url, QPixmap


class _ImageTask(QRunnable):
    def __init__(self, url: str, signals: _ImageSignals) -> None:
        super().__init__()
        self._url = url
        self._signals = signals
        self.setAutoDelete(True)

    def run(self) -> None:
        url = self._url
        h = hashlib.md5(url.encode()).hexdigest()
        disk_path = _IMG_CACHE_DIR / f"{h}.png"

        if disk_path.exists():
            pix = QPixmap(str(disk_path))
            if not pix.isNull():
                _MEM_CACHE[url] = pix
                self._signals.ready.emit(url, pix)
                return

        try:
            resp = httpx.get(url, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            _IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            disk_path.write_bytes(resp.content)
            pix = QPixmap()
            pix.loadFromData(resp.content)
            if not pix.isNull():
                _MEM_CACHE[url] = pix
                self._signals.ready.emit(url, pix)
        except Exception:
            log.debug("Image load failed: %s", url, exc_info=True)


class ImageLoader(QObject):
    """Singleton image loader — thread-pool workers, 2-layer cache (memory + disk)."""

    _instance: "ImageLoader | None" = None

    @classmethod
    def instance(cls) -> "ImageLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)
        self._pending_signals: dict[str, _ImageSignals] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def request(self, url: str, callback: Callable[[QPixmap], None]) -> None:
        """Request image at *url*. *callback(pixmap)* is called on the main thread."""
        if not url:
            return
        if url in _MEM_CACHE:
            callback(_MEM_CACHE[url])
            return
        if url not in self._callbacks:
            self._callbacks[url] = []
            sig = _ImageSignals(self)
            sig.ready.connect(self._on_ready)
            self._pending_signals[url] = sig
            self._pool.start(_ImageTask(url, sig))
        self._callbacks[url].append(callback)

    def _on_ready(self, url: str, pixmap: QPixmap) -> None:
        for cb in self._callbacks.pop(url, []):
            try:
                cb(pixmap)
            except RuntimeError:
                pass  # widget deleted before image arrived — harmless
            except Exception:
                log.exception("Image callback error for %s", url)
        self._pending_signals.pop(url, None)
