#!/usr/bin/env python3
"""
RAM Cat — menubar inference companion for Apple Silicon.

Know before you load. Emoji mood reacts to RAM pressure; spinner fires when
a model is loading; flash signals a mood change.

Moods (memory_pressure free%):
  😴  > 70%  — nothing loaded
  😸  50–70% — model running fine
  😾  30–50% — getting tight
  🙀  15–30% — swap imminent
  😱  < 15%  — you're swapping

Run:  python3 app.py
"""

import re
import subprocess
import collections
import rumps
import psutil

TOTAL_GB = psutil.virtual_memory().total / (1024 ** 3)

MOODS = [
    (70, "😴", "Sleepy — nothing loaded"),
    (50, "😸", "Comfy — model running fine"),
    (30, "😾", "Alert — getting tight"),
    (15, "🙀", "Frazzled — swap imminent"),
    (0,  "😱", "PANIC — swapping now"),
]

_MODEL_SIZES = [
    ("32B", 20.0),
    ("27B", 16.0),
    ("13B",  8.0),
    ("8B",   5.0),
    ("7B",   4.5),
    ("3B",   2.0),
    ("1B",   0.8),
]

_SPINNER      = "⣾⣽⣻⢿⡿⣟⣯⣷"
_FLASH_TICKS  = 6   # 6 × 150 ms = 0.9 s, 3 on/off blinks

_MLX_PROCS = (
    "mlx_lm.generate", "mlx_lm.chat", "mlx_lm.server",
    "mlx_lm/generate", "mlx_lm/chat", "mlx_lm/server",
    "mlx_vlm", "ollama",
)
_MODEL_FLAGS = ("--model", "-m")


def _noop(_):
    pass


# ─── Metrics ─────────────────────────────────────────────────────────────────

def _mac_free_pct():
    try:
        out = subprocess.check_output(
            ["memory_pressure"], timeout=3, stderr=subprocess.DEVNULL
        ).decode()
        m = re.search(r"memory free percentage:\s*(\d+)%", out, re.IGNORECASE)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    vm = psutil.virtual_memory()
    return int(vm.available / vm.total * 100)


def _psutil_stats():
    vm = psutil.virtual_memory()
    used_gb = (vm.total - vm.available) / (1024 ** 3)
    free_gb = vm.available / (1024 ** 3)
    return used_gb, free_gb


def _wired_gb():
    try:
        out = subprocess.check_output(
            ["vm_stat"], timeout=3, stderr=subprocess.DEVNULL
        ).decode()
        page_size = 4096
        m = re.search(r"page size of (\d+) bytes", out)
        if m:
            page_size = int(m.group(1))
        m2 = re.search(r"Pages wired down:\s+(\d+)", out)
        if m2:
            return int(m2.group(1)) * page_size / (1024 ** 3)
    except Exception:
        pass
    return None


def _mood(free_pct):
    for threshold, emoji, label in MOODS:
        if free_pct >= threshold:
            return emoji, label
    return "😱", "PANIC — swapping now"


def _sparkline(history):
    if not history:
        return "—"
    chars = "▁▂▃▄▅▆▇█"
    return "".join(
        chars[min(int((100 - pct) / 100 * len(chars)), len(chars) - 1)]
        for pct in history
    )


def _fits_row(free_gb):
    parts = []
    for name, needed in reversed(_MODEL_SIZES):
        parts.append(("✓" if free_gb >= needed else "✗") + name)
    return "  ".join(parts)


def _climbing(history):
    """True when the last 3 free% readings are all declining (RAM filling up)."""
    if len(history) < 3:
        return False
    last = list(history)[-3:]
    return last[0] > last[1] > last[2]


def _extract_model_name(cmdline):
    for i, arg in enumerate(cmdline):
        if arg in _MODEL_FLAGS and i + 1 < len(cmdline):
            path = cmdline[i + 1]
            parts = path.rstrip("/").split("/")
            return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    return None


def _running_model():
    try:
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                cmd_str = " ".join(cmdline)
                if not any(p in cmd_str for p in _MLX_PROCS):
                    continue
                label = "ollama" if "ollama" in cmd_str else "mlx_lm"
                return label, _extract_model_name(cmdline)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return None, None


def _label(text):
    return rumps.MenuItem(text, callback=_noop)


# ─── App ─────────────────────────────────────────────────────────────────────

class RamCatApp(rumps.App):
    def __init__(self):
        super().__init__("", quit_button=None)
        self._history     = collections.deque(maxlen=10)
        self._spinner_idx = 0
        self._flash_count = 0

        free_pct = _mac_free_pct()
        used_gb, free_gb = _psutil_stats()
        emoji, _ = _mood(free_pct)
        self._history.append(free_pct)

        self._cur_emoji   = emoji
        self._cur_pct     = free_pct
        self._cur_loading = False

        self.title = f"RAM {emoji} {free_pct}%"

        wired = _wired_gb()
        self._spark_item = _label(f"Trend:   {_sparkline(self._history)}")
        self._free_item  = _label(f"Free:    {free_pct}%  ({free_gb:.1f} GB)")
        self._used_item  = _label(f"In use:  {used_gb:.1f} / {TOTAL_GB:.0f} GB")
        self._wired_item = _label(
            f"Wired:   {wired:.1f} GB  (model weights)" if wired else "Wired:   —"
        )
        self._swap_item  = _label("Swap:    none")
        self._fits_item  = _label(
            f"4-bit:   {_fits_row(free_gb)}   ({free_gb:.1f} GB free)"
        )
        self._model_item = _label("Idle")
        self._quit_item  = rumps.MenuItem("Quit RAM Cat", callback=self._quit)

        self.menu = [
            self._spark_item,
            rumps.separator,
            self._free_item,
            self._used_item,
            self._wired_item,
            self._swap_item,
            rumps.separator,
            self._fits_item,
            self._model_item,
            rumps.separator,
            self._quit_item,
        ]

    @rumps.timer(3)
    def poll(self, _):
        """Slow poll — updates metrics and menu text."""
        free_pct = _mac_free_pct()
        used_gb, free_gb = _psutil_stats()
        emoji, _ = _mood(free_pct)
        self._history.append(free_pct)

        # Trigger flash when mood emoji changes
        if emoji != self._cur_emoji:
            self._flash_count = _FLASH_TICKS

        self._cur_emoji   = emoji
        self._cur_pct     = free_pct
        self._cur_loading = _climbing(self._history)

        swap = psutil.swap_memory()
        wired = _wired_gb()

        self._spark_item.title = f"Trend:   {_sparkline(self._history)}"
        self._free_item.title  = f"Free:    {free_pct}%  ({free_gb:.1f} GB)"
        self._used_item.title  = f"In use:  {used_gb:.1f} / {TOTAL_GB:.0f} GB"
        self._wired_item.title = (
            f"Wired:   {wired:.1f} GB  (model weights)" if wired else "Wired:   —"
        )
        self._swap_item.title  = (
            f"Swap:    {swap.used / (1024**3):.1f} GB used"
            if swap.used > 0 else "Swap:    none"
        )
        self._fits_item.title  = (
            f"4-bit:   {_fits_row(free_gb)}   ({free_gb:.1f} GB free)"
        )

        proc_label, model_name = _running_model()
        self._model_item.title = (
            f"Running: {model_name}  [{proc_label}]" if model_name
            else f"Running: {proc_label}" if proc_label
            else "Idle"
        )

    @rumps.timer(0.15)
    def animate(self, _):
        """Fast tick — handles title bar flash and loading spinner."""
        emoji = self._cur_emoji
        pct   = self._cur_pct

        if self._flash_count > 0:
            # Blink: show emoji on even counts, blank on odd
            show = self._flash_count % 2 == 0
            self.title = f"RAM {emoji} {pct}%" if show else f"RAM     {pct}%"
            self._flash_count -= 1
        elif self._cur_loading:
            frame = _SPINNER[self._spinner_idx % len(_SPINNER)]
            self.title = f"RAM {emoji}{frame} {pct}%"
            self._spinner_idx += 1
        else:
            self.title = f"RAM {emoji} {pct}%"

    def _quit(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    RamCatApp().run()
