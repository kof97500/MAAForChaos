from __future__ import annotations

import ctypes
import struct
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from platform import system

from czn_automation.runtime.context import RunContext
from czn_automation.window.attach import WindowInfo


SRCCOPY = 0x00CC0020
BI_RGB = 0
DIB_RGB_COLORS = 0


@dataclass
class CaptureResult:
    success: bool
    path: Path | None = None
    reason: str = ""

    def summary(self) -> str:
        if self.success and self.path is not None:
            return str(self.path)
        return self.reason or "unknown"


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


class WindowScreenshotService:
    def __init__(self, context: RunContext) -> None:
        self.context = context

    def capture_to_debug_file(self, window: WindowInfo) -> CaptureResult:
        if system() != "Windows":
            return CaptureResult(
                success=False,
                reason="当前不是 Windows 环境，无法执行 Win32 窗口截图",
            )

        output_path = self.context.root_dir / "debug" / "screenshots" / "last_window_capture.bmp"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._capture_bitmap(window, output_path)
        except Exception as exc:  # pragma: no cover - Windows runtime path
            self.context.logger.exception("窗口截图失败")
            return CaptureResult(success=False, reason=str(exc))

        self.context.logger.info("窗口截图保存成功：%s", output_path)
        return CaptureResult(success=True, path=output_path)

    def _capture_bitmap(self, window: WindowInfo, output_path: Path) -> None:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hwnd = wintypes.HWND(window.hwnd)
        window_dc = user32.GetDC(hwnd)
        if not window_dc:
            raise RuntimeError("GetDC 返回空句柄")

        memory_dc = gdi32.CreateCompatibleDC(window_dc)
        if not memory_dc:
            user32.ReleaseDC(hwnd, window_dc)
            raise RuntimeError("CreateCompatibleDC 失败")

        bitmap = gdi32.CreateCompatibleBitmap(window_dc, window.width, window.height)
        if not bitmap:
            gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(hwnd, window_dc)
            raise RuntimeError("CreateCompatibleBitmap 失败")

        previous_object = gdi32.SelectObject(memory_dc, bitmap)
        try:
            copied = gdi32.BitBlt(
                memory_dc,
                0,
                0,
                window.width,
                window.height,
                window_dc,
                0,
                0,
                SRCCOPY,
            )
            if not copied:
                raise RuntimeError("BitBlt 截图失败")

            raw_bytes = self._read_bitmap_bytes(memory_dc, bitmap, window.width, window.height)
            self._write_bitmap_file(output_path, raw_bytes, window.width, window.height)
        finally:
            gdi32.SelectObject(memory_dc, previous_object)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(hwnd, window_dc)

    def _read_bitmap_bytes(self, memory_dc: int, bitmap: int, width: int, height: int) -> bytes:
        gdi32 = ctypes.windll.gdi32

        bitmap_info = BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = -height
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = BI_RGB

        image_size = width * height * 4
        buffer = ctypes.create_string_buffer(image_size)

        result = gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            height,
            buffer,
            ctypes.byref(bitmap_info),
            DIB_RGB_COLORS,
        )
        if result == 0:
            raise RuntimeError("GetDIBits 读取位图失败")

        return buffer.raw

    def _write_bitmap_file(self, output_path: Path, raw_bytes: bytes, width: int, height: int) -> None:
        file_header_size = 14
        info_header_size = 40
        pixel_data_offset = file_header_size + info_header_size
        file_size = pixel_data_offset + len(raw_bytes)

        bitmap_file_header = struct.pack(
            "<2sIHHI",
            b"BM",
            file_size,
            0,
            0,
            pixel_data_offset,
        )
        bitmap_info_header = struct.pack(
            "<IiiHHIIiiII",
            info_header_size,
            width,
            -height,
            1,
            32,
            BI_RGB,
            len(raw_bytes),
            0,
            0,
            0,
            0,
        )

        output_path.write_bytes(bitmap_file_header + bitmap_info_header + raw_bytes)
