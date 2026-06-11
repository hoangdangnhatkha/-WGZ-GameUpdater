from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

from PyQt6.QtCore import QPoint, QSize, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QMouseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizeGrip,
    QVBoxLayout, QWidget,
)

log = logging.getLogger(__name__)

_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,}$")

# Hosts / URL substrings that serve YouTube ads, trackers, and analytics.
# Blocked at the network layer so the player skips ad preroll entirely.
_AD_BLOCK_SUBSTRINGS = (
    "doubleclick.net",
    "googleadservices.com",
    "googlesyndication.com",
    "googletagservices.com",
    "googletagmanager.com",
    "google-analytics.com",
    "/pagead/",
    "/ptracking",
    "/api/stats/ads",
    "/api/stats/qoe",
    "/api/stats/atr",
    "/get_midroll_info",
    "/log_event",
    "/youtubei/v1/log_event",
    "/youtubei/v1/player/ad_break",
    "adservice.google.",
)


def _make_ad_interceptor():
    """Build a QWebEngineUrlRequestInterceptor that blocks ad/tracker URLs."""
    from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

    class _AdInterceptor(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info) -> None:
            url = info.requestUrl().toString()
            for needle in _AD_BLOCK_SUBSTRINGS:
                if needle in url:
                    info.block(True)
                    return

    return _AdInterceptor()


def youtube_video_id(url: str) -> str | None:
    """Extract YouTube video ID from any common URL form."""
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None

    host = (parsed.hostname or "").lower().lstrip("www.")
    video_id: str | None = None

    if host in ("youtu.be",):
        video_id = parsed.path.lstrip("/").split("/", 1)[0]
    elif host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        path = parsed.path or ""
        if path.startswith("/embed/"):
            video_id = path[len("/embed/"):].split("/", 1)[0]
        elif path.startswith("/shorts/"):
            video_id = path[len("/shorts/"):].split("/", 1)[0]
        elif path == "/watch":
            qs = parse_qs(parsed.query)
            v = qs.get("v")
            if v:
                video_id = v[0]

    if video_id and _YT_ID_RE.match(video_id):
        return video_id
    return None


def youtube_to_embed(url: str, *, autoplay: bool = True, mute: bool = True) -> str | None:
    """Build a full youtube.com watch URL with autoplay+mute params.

    Returns None if the URL isn't a recognizable YouTube link.

    Note: we use the full watch page rather than /embed/ because PyPI
    PyQt6-WebEngine wheels lack the proprietary codecs / Widevine needed
    for the iframe-embed player's ad preroll (causes errors 152/153).
    The watch page falls back to VP9/WebM which QtWebEngine supports.
    """
    video_id = youtube_video_id(url)
    if not video_id:
        return None
    params = {
        "autoplay": "1" if autoplay else "0",
        "mute": "1" if mute else "0",
    }
    return f"https://www.youtube.com/watch?v={video_id}&{urlencode(params)}"


class _StreamResolver(QThread):
    """Resolve a YouTube watch URL to a direct CDN stream URL via yt-dlp.

    Uses the 'tv_embedded' / 'android_embedded' clients which bypass age
    verification, and prefers VP9/WebM formats that QtWebEngine can play
    natively without proprietary codecs.
    """

    resolved = pyqtSignal(str, str)   # (stream_url, request_token)
    failed = pyqtSignal(str, str)     # (error_message, request_token)

    def __init__(self, watch_url: str, token: str, parent=None) -> None:
        super().__init__(parent)
        self._watch_url = watch_url
        self._token = token

    # Ordered list of resolve strategies. Each entry produces yt-dlp opts;
    # we try them in order until one returns a playable stream URL. Latter
    # strategies are heavier (browser cookie scraping) so kept as fallback.
    _STRATEGIES = (
        {
            "name": "tv+mweb+ios clients",
            "clients": ["tv", "mweb", "ios", "tv_embedded", "android_embedded"],
            "cookies_browser": None,
        },
        {
            "name": "web_safari + web_creator clients",
            "clients": ["web_safari", "web_creator", "web_embedded"],
            "cookies_browser": None,
        },
        {
            "name": "edge browser cookies",
            "clients": ["web", "tv", "mweb"],
            "cookies_browser": ("edge",),
        },
        {
            "name": "chrome browser cookies",
            "clients": ["web", "tv", "mweb"],
            "cookies_browser": ("chrome",),
        },
        {
            "name": "firefox browser cookies",
            "clients": ["web", "tv", "mweb"],
            "cookies_browser": ("firefox",),
        },
    )

    def _try_strategy(self, strategy: dict) -> tuple[str | None, str]:
        """Return (stream_url, error_msg). url is None on failure."""
        import yt_dlp
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "format": (
                "best[ext=mp4][acodec!=none][vcodec!=none]/"
                "best[ext=webm][acodec!=none][vcodec!=none]/"
                "best[acodec!=none][vcodec!=none]/best"
            ),
            "extractor_args": {
                "youtube": {"player_client": strategy["clients"]},
            },
        }
        if strategy["cookies_browser"]:
            opts["cookiesfrombrowser"] = strategy["cookies_browser"]
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self._watch_url, download=False)
            url = info.get("url") if info else None
            if not url and info and info.get("formats"):
                fmt = info["formats"][-1]
                url = fmt.get("url")
            if not url:
                return None, "no playable URL"
            return url, ""
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    def run(self) -> None:
        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            self.failed.emit("yt-dlp not installed", self._token)
            return
        last_error = ""
        for strategy in self._STRATEGIES:
            url, err = self._try_strategy(strategy)
            if url:
                log.info("Trailer resolved via strategy: %s", strategy["name"])
                self.resolved.emit(url, self._token)
                return
            log.debug("Strategy '%s' failed: %s", strategy["name"], err)
            last_error = f"{strategy['name']}: {err}"
        self.failed.emit(last_error or "all strategies failed", self._token)


class _DragHeader(QWidget):
    """Header bar that propagates drag events to the parent popup."""

    def __init__(self, popup: TrailerPopup) -> None:
        super().__init__(popup)
        self._popup = popup
        self.setObjectName("TrailerPopupHeader")
        self.setFixedHeight(24)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._popup._begin_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._popup._continue_drag(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._popup._end_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class TrailerPopup(QWidget):
    """Floating YouTube trailer popup pinned inside the parent widget.

    - Auto-plays muted (browser autoplay policy friendly).
    - Header bar drags the popup within the parent's bounds.
    - QSizeGrip in the bottom-right corner resizes the popup.
    - Close button hides + stops playback.
    - Mute button toggles audio by reloading the embed URL with mute=0/1.
    """

    DEFAULT_SIZE = QSize(360, 226)
    MIN_SIZE = QSize(240, 160)
    MARGIN = 16

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("TrailerPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.resize(self.DEFAULT_SIZE)
        self.setMinimumSize(self.MIN_SIZE)
        self.hide()

        self._current_url: str = ""
        self._muted: bool = True
        self._user_moved: bool = False
        self._drag_offset: QPoint | None = None
        self._resolver: _StreamResolver | None = None
        self._resolve_token: int = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header (drag handle + title + mute + close)
        self._header = _DragHeader(self)
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(8, 0, 4, 0)
        hl.setSpacing(6)

        title = QLabel("// TRAILER", self._header)
        title.setObjectName("TrailerPopupTitle")
        hl.addWidget(title, 1)

        close_btn = QPushButton("✕", self._header)
        close_btn.setObjectName("TrailerCloseBtn")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Đóng")
        close_btn.clicked.connect(self._on_close)
        hl.addWidget(close_btn)

        outer.addWidget(self._header)

        # Video host frame (web view fills it, size grip overlays bottom-right)
        self._video_host = QWidget(self)
        self._video_host.setObjectName("TrailerPopupVideo")
        host_layout = QVBoxLayout(self._video_host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)

        self._view: QWidget | None = None
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
            self._view = QWebEngineView(self._video_host)
            self._view.loadFinished.connect(self._on_load_finished)
            self._view.urlChanged.connect(self._on_url_event)
            self._view.titleChanged.connect(self._on_title_event)
            # Use a Chrome-like UA so YouTube serves the modern embed player
            # (default Qt UA can trigger "Lỗi 153 / video playback config" errors).
            profile = self._view.page().profile()
            # Qt's default UA contains "QtWebEngine/x.y" — YouTube flags it as
            # a non-standard client and refuses to play (error 152). Replace
            # with a clean Chrome UA matching the bundled Chromium (134 for Qt 6.10).
            profile.setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/134.0.0.0 Safari/537.36"
            )
            # Install ad-blocker. Kept as an attribute so it isn't garbage-
            # collected (profile only holds a weak ref to the interceptor).
            self._ad_interceptor = _make_ad_interceptor()
            profile.setUrlRequestInterceptor(self._ad_interceptor)
            settings = self._view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            host_layout.addWidget(self._view)
        except Exception as exc:
            log.warning("Trailer popup disabled (%s): %s", type(exc).__name__, exc)
            placeholder = QLabel("// WEB ENGINE UNAVAILABLE", self._video_host)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color:#5e5e62;font-family:'Cascadia Mono',Consolas,monospace;")
            host_layout.addWidget(placeholder)

        outer.addWidget(self._video_host, 1)

        # Size grip in bottom-right corner (floats over video)
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(14, 14)
        self._grip.raise_()

    # ── public ────────────────────────────────────────────────────

    def play(self, trailer_url: str) -> bool:
        """Resolve and load trailer; popup stays hidden until playback starts.

        Strategy: resolve to a direct CDN stream URL via yt-dlp in a
        background thread. This sidesteps the embed player entirely so
        age-gated videos play, and there is no ad preroll because the
        direct stream contains only the video itself.
        """
        video_id = youtube_video_id(trailer_url)
        if not video_id:
            log.warning("Trailer URL not recognized as YouTube: %r", trailer_url)
            self.stop()
            self.hide()
            return False
        self._current_url = trailer_url
        if self._view is None:
            return False

        # Show popup immediately with loading state; actual video HTML
        # replaces this once resolver completes.
        self._show_loading()
        if not self.isVisible():
            self.show()
            self.raise_()

        # Cancel any in-flight resolve, start a fresh one
        self._resolve_token += 1
        token = str(self._resolve_token)
        if self._resolver is not None:
            try:
                self._resolver.resolved.disconnect()
                self._resolver.failed.disconnect()
            except Exception:
                pass
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        self._resolver = _StreamResolver(watch_url, token, parent=self)
        self._resolver.resolved.connect(self._on_stream_resolved)
        self._resolver.failed.connect(self._on_stream_failed)
        self._resolver.start()
        return True

    def _show_loading(self) -> None:
        """Render loading placeholder until the trailer stream is ready."""
        if self._view is None:
            return
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>"
            "html,body{margin:0;padding:0;background:#000;width:100%;height:100%;"
            "overflow:hidden;font-family:'Cascadia Mono',Consolas,monospace;color:#ecece7;}"
            ".wrap{position:absolute;inset:0;display:flex;flex-direction:column;"
            "align-items:center;justify-content:center;gap:14px;}"
            ".spinner{width:34px;height:34px;border:2px solid #393945;"
            "border-top-color:#d8ff3a;border-radius:50%;animation:spin 0.9s linear infinite;}"
            ".lbl{font-size:10px;letter-spacing:1.8px;color:#b8b8b3;font-weight:700;}"
            ".sub{font-size:9px;letter-spacing:1.2px;color:#5e5e62;}"
            "@keyframes spin{to{transform:rotate(360deg);}}"
            "</style></head><body>"
            "<div class='wrap'>"
            "<div class='spinner'></div>"
            "<div class='lbl'>// LOADING TRAILER</div>"
            "<div class='sub'>RESOLVING STREAM…</div>"
            "</div></body></html>"
        )
        try:
            self._view.setHtml(html, QUrl("about:blank"))
        except Exception:
            log.exception("Failed to render trailer loading state")

    def _on_stream_resolved(self, stream_url: str, token: str) -> None:
        if token != str(self._resolve_token) or self._view is None:
            return
        muted_js = "true" if self._muted else "false"
        volume_js = "0" if self._muted else "1"
        # The <video> element is built WITHOUT a src; we set src only after
        # `muted=true` is applied, so the browser never begins fetching/
        # decoding audio while unmuted (autoplay starts the moment src is
        # assigned). Readiness is signalled via document.title change
        # (caught by view.titleChanged) so we don't trigger a navigation.
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>__wgz_idle__</title>"
            "<style>html,body{margin:0;padding:0;background:#000;"
            "width:100%;height:100%;overflow:hidden;}"
            "video{width:100%;height:100%;object-fit:contain;display:block;background:#000;}"
            "</style></head><body>"
            "<video id='v' playsinline controls controlsList='nodownload' muted></video>"
            "<script>(function(){"
            "var v=document.getElementById('v');"
            f"window.__wgz_force_mute={muted_js};"
            f"v.muted={muted_js};v.volume={volume_js};"
            "v.setAttribute('muted','');"
            "var fired=false;"
            "function ready(){if(fired)return;fired=true;"
            "  if(window.__wgz_force_mute){v.muted=true;v.volume=0;}"
            "  document.title='__wgz_playing__';}"
            "v.addEventListener('playing',ready,{once:true});"
            "v.addEventListener('volumechange',function(){"
            "  if(window.__wgz_force_mute){"
            "    if(!v.muted)v.muted=true;if(v.volume>0)v.volume=0;}"
            "});"
            f"v.src={stream_url!r};"
            "var p=v.play();if(p&&p.catch)p.catch(function(){});"
            "})();</script>"
            "</body></html>"
        )
        try:
            self._view.setHtml(html, QUrl("https://www.youtube.com/"))
        except Exception:
            log.exception("Failed to load resolved trailer stream")

    def _on_title_event(self, title: str) -> None:
        if title == "__wgz_playing__":
            # Belt-and-braces: enforce mute again right before reveal.
            if self._muted and self._view is not None:
                try:
                    self._view.page().runJavaScript(
                        "var v=document.querySelector('video');"
                        "if(v){v.muted=true;v.volume=0;}"
                    )
                except Exception:
                    pass
            if not self.isVisible():
                self.show()
                self.raise_()

    def _on_stream_failed(self, error: str, token: str) -> None:
        if token != str(self._resolve_token) or self._view is None:
            return
        log.warning("Trailer stream resolve failed: %s", error)
        video_id = youtube_video_id(self._current_url)
        # Age-restricted / sign-in required → no in-app playback possible
        # without user-supplied cookies. Show a clickable thumbnail that
        # opens the video in the system browser instead.
        if video_id and ("Sign in to confirm your age" in error
                         or "age-restricted" in error.lower()
                         or "login required" in error.lower()):
            self._show_age_gate_fallback(video_id)
            return
        # Other failures — try the watch URL embed (may still work)
        embed = youtube_to_embed(self._current_url, autoplay=True, mute=self._muted)
        if embed:
            try:
                self._view.setUrl(QUrl(embed))
            except Exception:
                log.exception("Fallback watch URL load failed")

    def _show_age_gate_fallback(self, video_id: str) -> None:
        """Render a clickable thumbnail that opens the video externally."""
        if self._view is None:
            return
        thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>"
            "html,body{margin:0;padding:0;background:#000;width:100%;height:100%;"
            "overflow:hidden;font-family:'Cascadia Mono',Consolas,monospace;color:#ecece7;}"
            ".wrap{position:relative;width:100vw;height:100vh;cursor:pointer;}"
            ".wrap img{width:100%;height:100%;object-fit:cover;opacity:.55;}"
            ".overlay{position:absolute;inset:0;display:flex;flex-direction:column;"
            "align-items:center;justify-content:center;text-align:center;padding:12px;}"
            ".play{font-size:42px;color:#d8ff3a;margin-bottom:8px;line-height:1;}"
            ".lbl{font-size:10px;letter-spacing:1.6px;color:#ecece7;font-weight:700;}"
            ".sub{font-size:9px;letter-spacing:1.2px;color:#5e5e62;margin-top:6px;}"
            ".wrap:hover .play{color:#ffffff;}"
            "</style></head><body>"
            "<div class='wrap' onclick=\"window.location.href='wgz-open://"
            f"{video_id}'\">"
            f"<img src='{thumb}' onerror=\"this.src='https://i.ytimg.com/vi/{video_id}/0.jpg'\">"
            "<div class='overlay'>"
            "<div class='play'>▶</div>"
            "<div class='lbl'>XEM TRÊN YOUTUBE</div>"
            "<div class='sub'>// AGE-RESTRICTED · MỞ TRÌNH DUYỆT</div>"
            "</div></div>"
            "</body></html>"
        )
        try:
            self._view.setHtml(html, QUrl("about:blank"))
        except Exception:
            log.exception("Failed to render age-gate fallback")
        if not self.isVisible():
            self.show()
            self.raise_()

    def _on_url_event(self, url: QUrl) -> None:
        """Dispatch custom-scheme navigations from the embedded HTML."""
        u = url.toString()
        if u.startswith("wgz-open://"):
            video_id = u[len("wgz-open://"):].rstrip("/")
            QDesktopServices.openUrl(QUrl(f"https://www.youtube.com/watch?v={video_id}"))
            # Reload the thumbnail HTML so the popup stays interactive
            self._show_age_gate_fallback(video_id)

    def stop(self) -> None:
        # Invalidate any pending resolver result so it doesn't replace
        # the blanked page if it finishes after stop().
        self._resolve_token += 1
        if self._view is not None:
            try:
                self._view.setUrl(QUrl("about:blank"))
            except Exception:
                pass

    def _on_load_finished(self, ok: bool) -> None:
        """Strip YouTube chrome so only the video player is visible."""
        if not ok or self._view is None:
            return
        url = self._view.url().toString()
        if "youtube.com/watch" not in url:
            return
        # Watch URL = fallback path (yt-dlp failed but not age-gated); reveal
        # the popup now that the page has loaded.
        if not self.isVisible():
            self.show()
            self.raise_()
        # Hide masthead/comments/sidebar, expand video player to fill viewport.
        js = r"""
        (function(){
          var s = document.getElementById('__wgz_trailer_style');
          if (s) return;
          s = document.createElement('style');
          s.id = '__wgz_trailer_style';
          s.textContent = `
            html, body { margin:0!important; padding:0!important; overflow:hidden!important; background:#000!important; }
            ytd-masthead, #masthead-container, #masthead,
            tp-yt-app-drawer, #guide, ytd-mini-guide-renderer,
            #below, ytd-watch-metadata, #secondary, #comments,
            ytd-merch-shelf-renderer, ytd-popup-container,
            ytd-banner-promo-renderer, ytd-display-ad-renderer,
            ytd-promoted-sparkles-web-renderer, ytd-companion-slot-renderer,
            .ytp-ad-overlay-container, .ytp-ad-image-overlay,
            .ytp-ad-text-overlay, .ytp-ad-message-container,
            .video-ads, #player-ads, .ytp-ad-module,
            .ytp-pause-overlay, .ytp-ce-element, .ytp-cards-teaser,
            #chat, #chat-container, ytd-live-chat-frame,
            ytd-watch-next-secondary-results-renderer,
            ytd-engagement-panel-section-list-renderer { display:none!important; }
            #content.ytd-app, ytd-page-manager, ytd-watch-flexy,
            #primary, #primary-inner, #player, #player-container-outer,
            #player-container, #player-container-inner, #movie_player {
              width:100vw!important; height:100vh!important;
              max-width:100vw!important; max-height:100vh!important;
              margin:0!important; padding:0!important; top:0!important; left:0!important;
            }
            ytd-watch-flexy[flexy] #player.ytd-watch-flexy { min-width:100vw!important; }
            video { width:100vw!important; height:100vh!important; object-fit:contain!important; }
            ytd-app { --ytd-masthead-height: 0px!important; }
          `;
          document.documentElement.appendChild(s);
          window.scrollTo(0,0);

          function forceMute(){
            var vids = document.querySelectorAll('video');
            for (var i=0;i<vids.length;i++){
              try { vids[i].muted = true; vids[i].volume = 0; } catch(e){}
            }
            var mp = document.getElementById('movie_player');
            if (mp && typeof mp.mute === 'function') {
              try { mp.mute(); } catch(e){}
              try { mp.setVolume(0); } catch(e){}
            }
          }
          forceMute();

          if (window.__wgz_ad_killer) return;
          window.__wgz_ad_killer = setInterval(function(){
            forceMute();
            var skip = document.querySelector(
              '.ytp-ad-skip-button, .ytp-ad-skip-button-modern, ' +
              '.ytp-skip-ad-button, button.ytp-ad-skip-button-modern'
            );
            if (skip) { try { skip.click(); } catch(e){} }
            var v = document.querySelector('.ad-showing video, .html5-video-player.ad-showing video');
            if (v) {
              try { v.muted = true; v.playbackRate = 16; v.currentTime = v.duration || 999; } catch(e){}
            }
            var overlay = document.querySelector('.ytp-ad-overlay-close-button');
            if (overlay) { try { overlay.click(); } catch(e){} }
          }, 250);
        })();
        """
        try:
            self._view.page().runJavaScript(js)
        except Exception:
            log.exception("Failed to inject trailer CSS")

    def reset_position(self) -> None:
        """Forget user drag; snap back to default top-right corner."""
        self._user_moved = False
        self._reposition_default()

    # ── internal ──────────────────────────────────────────────────

    def _on_close(self) -> None:
        self.stop()
        self.hide()

    # Drag handling (called from _DragHeader)
    def _begin_drag(self, global_pos: QPoint) -> None:
        self._drag_offset = global_pos - self.pos()

    def _continue_drag(self, global_pos: QPoint) -> None:
        if self._drag_offset is None:
            return
        parent = self.parentWidget()
        if parent is None:
            return
        new_pos = global_pos - self._drag_offset
        max_x = max(0, parent.width() - self.width())
        max_y = max(0, parent.height() - self.height())
        new_pos.setX(max(0, min(new_pos.x(), max_x)))
        new_pos.setY(max(0, min(new_pos.y(), max_y)))
        self.move(new_pos)
        self._user_moved = True

    def _end_drag(self) -> None:
        self._drag_offset = None

    def _reposition_default(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        x = parent.width() - self.width() - self.MARGIN
        y = self.MARGIN
        self.move(max(0, x), max(0, y))

    # Keep size grip pinned bottom-right; auto-reposition if user hasn't dragged
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._grip.move(self.width() - self._grip.width() - 2,
                        self.height() - self._grip.height() - 2)

    def parent_resized(self) -> None:
        """Called by the host page when its own geometry changes."""
        if not self._user_moved:
            self._reposition_default()
        else:
            # Clamp within new parent bounds
            parent = self.parentWidget()
            if parent is None:
                return
            x = min(self.x(), max(0, parent.width() - self.width()))
            y = min(self.y(), max(0, parent.height() - self.height()))
            self.move(max(0, x), max(0, y))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._user_moved:
            self._reposition_default()
        self.raise_()
