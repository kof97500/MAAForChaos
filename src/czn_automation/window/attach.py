from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from platform import system

from czn_automation.runtime.context import RunContext


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    left: int
    top: int
    width: int
    height: int
    visible: bool
    minimized: bool

    def matches_keyword(self, keyword: str) -> bool:
        return keyword.casefold() in self.title.casefold()

    def summary(self) -> str:
        return (
            f"hwnd={self.hwnd} title={self.title!r} "
            f"pos=({self.left},{self.top}) size={self.width}x{self.height} "
            f"visible={self.visible} minimized={self.minimized}"
        )


@dataclass
class AttachResult:
    found: bool
    window: WindowInfo | None = None
    matched_title: str = ""
    reason: str = ""

    def summary(self) -> str:
        if self.found:
            if self.window is None:
                return f"matched_title={self.matched_title}"
            return self.window.summary()
        return self.reason or "unknown"


class GameWindowService:
    def __init__(self, context: RunContext) -> None:
        self.context = context

    def attach(self) -> AttachResult:
        self.context.progress.update(
            stage="窗口连接",
            step="扫描系统窗口",
            status="进行中",
            detail="正在枚举可见顶层窗口",
        )
        self.context.logger.info("开始窗口扫描")

        if system() != "Windows":
            return AttachResult(
                found=False,
                reason="当前不是 Windows 环境，窗口连接能力将在 Windows 机器上验证",
            )

        windows = self._enumerate_windows()
        self.context.logger.info("窗口扫描完成，候选窗口数量：%s", len(windows))

        if not windows:
            return AttachResult(
                found=False,
                reason="未扫描到任何可见顶层窗口",
            )

        self._log_candidate_windows(windows)
        self.context.progress.update(
            stage="窗口连接",
            step="匹配目标窗口",
            status="进行中",
            detail=f"候选窗口 {len(windows)} 个，开始按关键字与分辨率筛选",
        )

        matched_window = self._match_window(windows)
        if matched_window is None:
            return AttachResult(
                found=False,
                reason="未找到标题与分辨率均匹配的游戏窗口",
            )

        if not self._is_supported_resolution(matched_window.width, matched_window.height):
            reason = (
                f"窗口标题已匹配，但分辨率不受支持："
                f"{matched_window.width}x{matched_window.height}"
            )
            self.context.logger.warning(reason)
            return AttachResult(
                found=False,
                window=matched_window,
                matched_title=matched_window.title,
                reason=reason,
            )

        self.context.logger.info("窗口连接成功：%s", matched_window.summary())
        return AttachResult(
            found=True,
            window=matched_window,
            matched_title=matched_window.title,
        )

    def _log_candidate_windows(self, windows: list[WindowInfo]) -> None:
        for index, window in enumerate(windows, start=1):
            self.context.logger.info("候选窗口 #%s: %s", index, window.summary())

    def _match_window(self, windows: list[WindowInfo]) -> WindowInfo | None:
        keywords = self.context.config.game_window.title_keywords
        matched_by_title = [
            window
            for window in windows
            if any(window.matches_keyword(keyword) for keyword in keywords)
        ]

        self.context.logger.info("标题关键字匹配窗口数量：%s", len(matched_by_title))
        if not matched_by_title:
            return None

        exact_resolution = [
            window
            for window in matched_by_title
            if self._is_supported_resolution(window.width, window.height)
        ]

        if exact_resolution:
            selected = exact_resolution[0]
            self.context.logger.info("选中支持分辨率窗口：%s", selected.summary())
            return selected

        selected = matched_by_title[0]
        self.context.logger.warning(
            "找到了标题匹配窗口，但分辨率不符合要求，优先返回首个标题匹配项：%s",
            selected.summary(),
        )
        return selected

    def _is_supported_resolution(self, width: int, height: int) -> bool:
        return any(
            item.width == width and item.height == height
            for item in self.context.config.game_window.supported_resolutions
        )

    def _enumerate_windows(self) -> list[WindowInfo]:
        user32 = ctypes.windll.user32
        windows: list[WindowInfo] = []
        enum_windows_proc = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )

        def callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            if user32.IsIconic(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return True

            rect = wintypes.RECT()
            if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
                return True

            top_left = wintypes.POINT(0, 0)
            if not user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
                return True

            width = rect.right - rect.left
            height = rect.bottom - rect.top
            windows.append(
                WindowInfo(
                    hwnd=int(hwnd),
                    title=title,
                    left=top_left.x,
                    top=top_left.y,
                    width=width,
                    height=height,
                    visible=True,
                    minimized=False,
                )
            )
            return True

        user32.EnumWindows(enum_windows_proc(callback), 0)
        return windows
