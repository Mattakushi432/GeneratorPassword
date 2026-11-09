"""Secure clipboard for Windows 10/11.

Copied secrets are tagged so that Windows does NOT put them in clipboard
history (Win+V), does NOT sync them to the cloud clipboard, and clipboard
monitors (e.g. password-aware tools) skip them. After a timeout the
clipboard is wiped — but only if it still holds *our* secret, so we never
destroy something the user copied afterwards.
"""

from __future__ import annotations

import ctypes
import hashlib
import sys
import time

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _user32.OpenClipboard.argtypes = [wintypes.HWND]
    _user32.OpenClipboard.restype = wintypes.BOOL
    _user32.CloseClipboard.restype = wintypes.BOOL
    _user32.EmptyClipboard.restype = wintypes.BOOL
    _user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    _user32.SetClipboardData.restype = wintypes.HANDLE
    _user32.GetClipboardData.argtypes = [wintypes.UINT]
    _user32.GetClipboardData.restype = wintypes.HANDLE
    _user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    _user32.RegisterClipboardFormatW.restype = wintypes.UINT
    _user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    _user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

    _kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    _kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    _kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalLock.restype = wintypes.LPVOID
    _kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalUnlock.restype = wintypes.BOOL
    _kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalFree.restype = wintypes.HGLOBAL


class ClipboardError(RuntimeError):
    pass


def _open(retries: int = 10) -> None:
    for _ in range(retries):
        if _user32.OpenClipboard(None):
            return
        time.sleep(0.02)  # another app holds the clipboard; retry briefly
    raise ClipboardError("OpenClipboard failed")


def _set_handle(fmt: int, data: bytes) -> None:
    handle = _kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        raise ClipboardError("GlobalAlloc failed")
    ptr = _kernel32.GlobalLock(handle)
    if not ptr:
        _kernel32.GlobalFree(handle)
        raise ClipboardError("GlobalLock failed")
    ctypes.memmove(ptr, data, len(data))
    _kernel32.GlobalUnlock(handle)
    if not _user32.SetClipboardData(fmt, handle):
        _kernel32.GlobalFree(handle)  # ownership not transferred
        raise ClipboardError("SetClipboardData failed")


def _read_text() -> str | None:
    if not _user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return None
    handle = _user32.GetClipboardData(CF_UNICODETEXT)
    if not handle:
        return None
    ptr = _kernel32.GlobalLock(handle)
    if not ptr:
        return None
    try:
        return ctypes.wstring_at(ptr)
    finally:
        _kernel32.GlobalUnlock(handle)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SecureClipboard:
    """Copies secrets and remembers only a hash of what it copied."""

    def __init__(self) -> None:
        self._owned_hash: str | None = None

    @property
    def is_native(self) -> bool:
        return _IS_WINDOWS

    def copy(self, text: str) -> None:
        if not _IS_WINDOWS:
            raise ClipboardError("Native clipboard is only available on Windows")
        zero_dword = (0).to_bytes(4, "little")
        _open()
        try:
            if not _user32.EmptyClipboard():
                raise ClipboardError("EmptyClipboard failed")
            _set_handle(CF_UNICODETEXT, (text + "\0").encode("utf-16-le"))
            for name in ("ExcludeClipboardContentFromMonitorProcessing",
                         "CanIncludeInClipboardHistory",
                         "CanUploadToCloudClipboard"):
                fmt = _user32.RegisterClipboardFormatW(name)
                if fmt:
                    _set_handle(fmt, zero_dword)
        finally:
            _user32.CloseClipboard()
        self._owned_hash = _fingerprint(text)

    def owns_clipboard(self) -> bool:
        if not (_IS_WINDOWS and self._owned_hash):
            return False
        _open()
        try:
            current = _read_text()
        finally:
            _user32.CloseClipboard()
        return current is not None and _fingerprint(current) == self._owned_hash

    def clear_if_owned(self) -> bool:
        """Wipe the clipboard if it still contains our secret. Returns True if wiped."""
        try:
            if not self.owns_clipboard():
                self._owned_hash = None
                return False
            _open()
            try:
                _user32.EmptyClipboard()
            finally:
                _user32.CloseClipboard()
            return True
        except ClipboardError:
            return False
        finally:
            self._owned_hash = None
