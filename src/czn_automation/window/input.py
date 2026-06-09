from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass
from platform import system

from czn_automation.runtime.context import RunContext
from czn_automation.window.attach import WindowInfo


INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SM_CXSCREEN = 0
SM_CYSCREEN = 1


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


@dataclass
class ClickResult:
    success: bool
    screen_x: int = 0
    screen_y: int = 0
    reason: str = ""

    def summary(self) -> str:
        if self.success:
            return f"screen=({self.screen_x},{self.screen_y})"
        return self.reason or "unknown"


class WindowInputService:
    def __init__(self, context: RunContext) -> None:
        self.context = context

    def click_client_point(self, window: WindowInfo, x: int, y: int) -> ClickResult:
        if system() != "Windows":
            return ClickResult(success=False, reason="当前不是 Windows 环境，无法执行 Win32 输入")

        if x < 0 or y < 0 or x >= window.width or y >= window.height:
            return ClickResult(
                success=False,
                reason=f"点击坐标超出客户区范围: point=({x},{y}) window={window.width}x{window.height}",
            )

        user32 = ctypes.windll.user32
        screen_x = window.left + x
        screen_y = window.top + y

        self.context.logger.info(
            "准备执行固定坐标点击: client=(%s,%s) screen=(%s,%s)",
            x,
            y,
            screen_x,
            screen_y,
        )

        if user32.IsIconic(window.hwnd):
            return ClickResult(success=False, reason="目标窗口已最小化，无法执行点击")

        try:
            user32.ShowWindow(window.hwnd, 5)
            user32.SetForegroundWindow(window.hwnd)
            time.sleep(0.2)
            self._send_mouse_click(screen_x, screen_y)
        except Exception as exc:  # pragma: no cover - Windows runtime path
            self.context.logger.exception("固定坐标点击失败")
            return ClickResult(success=False, reason=str(exc))

        return ClickResult(success=True, screen_x=screen_x, screen_y=screen_y)

    def _send_mouse_click(self, screen_x: int, screen_y: int) -> None:
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(SM_CXSCREEN)
        screen_height = user32.GetSystemMetrics(SM_CYSCREEN)
        absolute_x = int(screen_x * 65535 / max(screen_width - 1, 1))
        absolute_y = int(screen_y * 65535 / max(screen_height - 1, 1))

        inputs = (INPUT * 3)()
        inputs[0].type = INPUT_MOUSE
        inputs[0].mi = MOUSEINPUT(
            dx=absolute_x,
            dy=absolute_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
            time=0,
            dwExtraInfo=None,
        )
        inputs[1].type = INPUT_MOUSE
        inputs[1].mi = MOUSEINPUT(
            dx=absolute_x,
            dy=absolute_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE,
            time=0,
            dwExtraInfo=None,
        )
        inputs[2].type = INPUT_MOUSE
        inputs[2].mi = MOUSEINPUT(
            dx=absolute_x,
            dy=absolute_y,
            mouseData=0,
            dwFlags=MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE,
            time=0,
            dwExtraInfo=None,
        )

        sent = user32.SendInput(3, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        if sent != 3:
            raise RuntimeError(f"SendInput 发送失败，实际发送数量: {sent}")
