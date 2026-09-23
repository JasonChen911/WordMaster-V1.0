"""
WordMaster Desktop Application Launcher.

Uses PyWebView to embed the web frontend in a native Windows window.
- No address bar, no browser dependency
- Native window controls (minimize, maximize, close)
- Auto-starts/stops the FastAPI backend
- JS→Python bridge for native file dialogs and progress reporting
"""

import sys
import os
import time
import socket
import threading
import logging
import json
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

BACKEND_DIR = BASE_DIR / "server"
FRONTEND_DIR = BASE_DIR / "web"

sys.path.insert(0, str(BACKEND_DIR))

from logging_config import startup_log  # noqa: E402

# ─── Logging ────────────────────────────────────────────────────
DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "WordMaster"
DATA_DIR.mkdir(parents=True, exist_ok=True)

log_handlers = [
    logging.FileHandler(DATA_DIR / "desktop.log", encoding="utf-8"),
]
if sys.stderr:
    log_handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("WordMaster.Desktop")
_native_icon_handles = []


# Backend startup budget — generous enough for a slow first launch (fresh DB
# creation, 40k+ word parsing, antivirus scanning the extracted EXE) without
# masking a real crash: the poll exits early the moment the thread errors out.
BACKEND_START_TIMEOUT = 18.0   # seconds
BACKEND_POLL_INTERVAL = 0.15   # seconds


def find_free_port(start=8000, end=8020) -> int:
    """Find a free port in the given range."""
    for port in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port in range {start}-{end}")


def start_backend(port: int) -> threading.Thread:
    """Start the FastAPI backend in a daemon thread and wait until ready.

    Readiness is signalled by ``GET /health`` returning 200 — only possible
    once ``app.py`` has finished ``init_db()`` (migrations + built-in word
    books) and uvicorn is actually serving. Real errors raised inside the
    backend thread are captured and reported as their actual cause instead of
    a generic timeout, distinguishing:
      A. backend crashed / failed to start  → report the real exception
      B. port already in use                 → clear "port in use" message
      C. backend merely slow                 → keep polling up to the budget
    """
    import uvicorn

    thread_error = {}

    def run_server():
        try:
            from app import app  # runs init_db() here (migrations + word books)
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
        except BaseException as exc:  # noqa: BLE001 — capture the real cause
            thread_error["exc"] = exc
            startup_log(f"backend thread exited: {type(exc).__name__}: {exc}")

    startup_log(f"starting backend on 127.0.0.1:{port} (WordMaster v0.1.0)")
    thread = threading.Thread(target=run_server, daemon=True, name="WordMaster-Backend")
    thread.start()

    import urllib.request
    import urllib.error

    health_url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + BACKEND_START_TIMEOUT

    while time.monotonic() < deadline:
        if thread_error:
            raise _backend_failure(port, thread_error["exc"])

        try:
            resp = urllib.request.urlopen(health_url, timeout=0.5)
            if resp.status == 200:
                startup_log("backend ready")
                logger.info(f"Backend ready on port {port}")
                return thread
        except (urllib.error.URLError, OSError):
            # Connection refused / not ready yet — keep polling.
            pass

        time.sleep(BACKEND_POLL_INTERVAL)

    # Budget exhausted — report the specific reason instead of a bare timeout.
    if thread_error:
        raise _backend_failure(port, thread_error["exc"])
    raise RuntimeError(
        f"Backend did not become ready within {BACKEND_START_TIMEOUT:.0f}s "
        f"(last checked {health_url}). See %APPDATA%\\WordMaster\\logs\\startup.log"
    )


def _backend_failure(port: int, exc: BaseException) -> RuntimeError:
    """Turn a captured backend exception into a clear, actionable error."""
    text = str(exc)
    lowered = text.lower()
    if "address already in use" in lowered or "errno 98" in lowered or "10048" in lowered:
        startup_log(f"backend FAILED: port {port} already in use")
        return RuntimeError(
            f"Backend failed to start: port {port} is already in use by another process."
        )
    startup_log(f"backend FAILED: {type(exc).__name__}: {text}")
    return RuntimeError(
        f"Backend process exited during startup: {type(exc).__name__}: {text}"
    )


def create_icon() -> str | None:
    """Return path to the WordMaster icon."""
    icon_path = BASE_DIR / "icon.ico"
    if icon_path.exists():
        return str(icon_path)
    logger.warning(f"Icon not found: {icon_path}")
    return None


def set_windows_window_icon(icon_path: str | None):
    """Apply the bundled icon to the native WinForms title bar on Windows."""
    if os.name != "nt" or not icon_path:
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        image_icon = 1
        lr_loadfromfile = 0x0010
        lr_defaultsize = 0x0040
        wm_seticon = 0x0080

        hwnd = user32.FindWindowW(None, "WordMaster")
        if not hwnd:
            logger.warning("Native WordMaster window handle not found")
            return
        handle = user32.LoadImageW(
            None,
            icon_path,
            image_icon,
            0,
            0,
            lr_loadfromfile | lr_defaultsize,
        )
        if handle:
            user32.SendMessageW(hwnd, wm_seticon, 0, handle)
            user32.SendMessageW(hwnd, wm_seticon, 1, handle)
            _native_icon_handles.append(handle)
            logger.info("Applied native window icon")
    except Exception as exc:
        logger.warning(f"Could not apply native window icon: {exc}")


# ═══════════════════════════════════════════════════════════════════
#  PyWebView JS→Python API Bridge
# ═══════════════════════════════════════════════════════════════════

class Api:
    """
    JavaScript-callable API exposed to the frontend via window.pywebview.api.

    From React:  window.pywebview.api.select_dictionary()
    """

    def __init__(self, port: int):
        self._port = port
        self._api_base = f"http://127.0.0.1:{port}"

    def select_dictionary(self) -> str:
        """Open Windows native file dialog to select a .mdx dictionary file.

        Returns the selected file path as a JSON string:
            {"path": "C:\\...\\dict.mdx"}
        or:
            {"cancelled": true}
        """
        import tkinter.filedialog
        import tkinter as tk

        logger.info("Api.select_dictionary() called from frontend")

        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            filepath = tkinter.filedialog.askopenfilename(
                title="选择 MDX 词库文件",
                filetypes=[("MDX 词典文件", "*.mdx"), ("所有文件", "*.*")],
            )
            root.destroy()

            if filepath:
                logger.info(f"User selected: {filepath}")
                return json.dumps({"path": filepath})
            else:
                logger.info("User cancelled file selection")
                return json.dumps({"cancelled": True})
        except Exception as e:
            logger.error(f"File dialog error: {e}")
            return json.dumps({"error": str(e)})

    def import_progress(self, progress_json: str):
        """Receive import progress updates from the backend (called from frontend polling).

        The frontend doesn't directly call this — instead the backend SSE/progress
        is polled via the REST API. This method is reserved for future streaming.

        For now, progress is handled via the /api/dictionary/import/progress endpoint.
        """
        pass

    def play_audio(self, audio_json: str) -> str:
        """Play audio silently — no windows, no terminal, no popups.

        Priority:
          1. Local audio file (.wav/.mp3) via winsound (zero-window)
          2. Windows SAPI TTS via pyttsx3 (silent in-process engine)

        Args:
            audio_json: JSON with {"word": "apple", "accent": "us", "filepath": "..."}
        Returns: JSON {"ok": true, "source": "file"|"tts"}
        """
        try:
            data = json.loads(audio_json)

            # ── Priority 1: play local audio file ──
            filepath = data.get("filepath", "")
            if filepath and Path(filepath).exists():
                import winsound
                # Run in thread so it doesn't block the UI
                def _play_file():
                    try:
                        winsound.PlaySound(
                            filepath,
                            winsound.SND_FILENAME | winsound.SND_ASYNC,
                        )
                    except Exception:
                        pass
                threading.Thread(target=_play_file, daemon=True).start()
                logger.info(f"Audio file: {filepath}")
                return json.dumps({"ok": True, "source": "file"})

            # ── Priority 2: Silent Windows TTS (no popups, no terminal) ──
            word = data.get("word", "")
            # GUARD: strip URLs — never speak http://...
            if isinstance(word, str) and ("http://" in word or "https://" in word):
                logger.warning(f"URL detected in TTS word, stripping: {word}")
                from pathlib import Path as _Path
                word = _Path(word).name or word.split("/")[-1]
            accent = data.get("accent", "us")
            if word:
                logger.info(f"TTS WORD: {word}")
                self._speak_tts(word, accent)
                return json.dumps({"ok": True, "source": "tts"})

            return json.dumps({"ok": False, "error": "No word or filepath"})
        except Exception as e:
            logger.error(f"Audio error: {e}")
            return json.dumps({"ok": False, "error": str(e)})

    def _speak_tts(self, word: str, accent: str = "us"):
        """Silent Windows SAPI TTS — runs in-process, zero windows."""
        import pyttsx3

        def _speak():
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")
                # Select voice by accent
                target = "zira" if accent == "us" else "hazel"
                for v in voices:
                    if target in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
                engine.setProperty("rate", 160)
                engine.say(word)
                engine.runAndWait()
            except Exception as e:
                logger.warning(f"TTS fallback failed: {e}")

        threading.Thread(target=_speak, daemon=True).start()

    def speak_word(self, word_json: str) -> str:
        """Legacy alias."""
        return self.play_audio(word_json)


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    import webview

    # ── 1. Start backend ──
    port = find_free_port(8000, 8020)
    url = f"http://127.0.0.1:{port}"

    logger.info("=" * 50)
    logger.info(f"  WordMaster v0.1.0 Beta — port {port}")
    logger.info("=" * 50)

    logger.info("Starting backend server...")
    server_thread = start_backend(port)

    # ── 2. Create icon ──
    icon_path = create_icon()

    # ── 3. Create JS API bridge ──
    api = Api(port)

    # ── 4. Create native window ──
    logger.info("Creating desktop window (1200x800)...")

    window = webview.create_window(
        title="WordMaster",
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False,
        easy_drag=True,
        background_color="#0a0a0a",
        text_select=False,
        js_api=api,  # ← Enables window.pywebview.api in JavaScript
    )
    window.events.shown += lambda *_args: set_windows_window_icon(icon_path)

    # ── 5. Start WebView event loop ──
    logger.info("Launching WordMaster window...")

    try:
        import inspect

        start_options = dict(
            debug=False,
            http_server=False,
            private_mode=False,
        )
        if icon_path and "icon" in inspect.signature(webview.start).parameters:
            start_options["icon"] = icon_path
        webview.start(**start_options)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"WebView error: {e}")
    finally:
        logger.info("WordMaster closed.")


if __name__ == "__main__":
    main()
