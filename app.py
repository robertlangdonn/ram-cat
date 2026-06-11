#!/usr/bin/env python3
"""
RAM Cat — menubar inference companion for Apple Silicon.

Uses macOS memory_pressure free% as primary signal (honest macOS metric).
Moods tuned for 16 GB M3:

  😴  > 70% free  — sleepy, nothing loaded
  😸  50–70% free — comfy, a model is running
  😾  30–50% free — alert, getting tight
  🙀  15–30% free — frazzled, swap imminent
  😱  < 15% free  — panic, you're swapping

Run:  python3 app.py
GIF:  load gemma-4-12B and screen-record the menubar going 😴→😱.
"""

import re
import subprocess
import rumps
import psutil

TOTAL_GB = psutil.virtual_memory().total / (1024 ** 3)

MOODS = [
    (70, "😴"),  # sleepy   — nothing loaded
    (50, "😸"),  # comfy    — model running fine
    (30, "😾"),  # alert    — getting tight
    (15, "🙀"),  # frazzled — swap imminent
]
PANIC = "😱"

MOOD_NAMES = {
    "😴": "Sleepy — nothing loaded",
    "😸": "Comfy — model running",
    "😾": "Alert — getting tight",
    "🙀": "Frazzled — swap imminent",
    "😱": "PANIC — swapping now",
}


def _mac_free_pct():
    """macOS-native free memory percentage via memory_pressure."""
    try:
        out = subprocess.check_output(
            ["memory_pressure"], timeout=3, stderr=subprocess.DEVNULL
        ).decode()
        m = re.search(r"memory free percentage:\s*(\d+)%", out, re.IGNORECASE)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    # fallback: psutil available / total
    vm = psutil.virtual_memory()
    return int(vm.available / vm.total * 100)


def _psutil_stats():
    vm = psutil.virtual_memory()
    used_gb = (vm.total - vm.available) / (1024 ** 3)
    free_gb = vm.available / (1024 ** 3)
    return used_gb, free_gb


def _mood(free_pct):
    for threshold, emoji in MOODS:
        if free_pct >= threshold:
            return emoji
    return PANIC


class RamCatApp(rumps.App):
    def __init__(self):
        super().__init__("", quit_button=None)
        free_pct = _mac_free_pct()
        used_gb, free_gb = _psutil_stats()
        mood = _mood(free_pct)

        self.title = f"{mood} {free_pct}% free"

        self._mood_item  = rumps.MenuItem(f"{mood}  {MOOD_NAMES.get(mood, '')}")
        self._free_item  = rumps.MenuItem(f"Free:    {free_pct}%  ({free_gb:.1f} GB)")
        self._used_item  = rumps.MenuItem(f"In use:  {used_gb:.1f} / {TOTAL_GB:.0f} GB")
        self._swap_item  = rumps.MenuItem("")
        self._quit_item  = rumps.MenuItem("Quit RAM Cat", callback=self._quit)

        self.menu = [
            self._mood_item,
            rumps.separator,
            self._free_item,
            self._used_item,
            self._swap_item,
            rumps.separator,
            self._quit_item,
        ]

    @rumps.timer(3)
    def update(self, _):
        free_pct = _mac_free_pct()
        used_gb, free_gb = _psutil_stats()
        mood = _mood(free_pct)
        swap = psutil.swap_memory()
        swap_str = f"Swap:    {swap.used / (1024**3):.1f} GB used" if swap.used > 0 else "Swap:    none"

        self.title = f"{mood} {free_pct}% free"
        self._mood_item.title = f"{mood}  {MOOD_NAMES.get(mood, '')}"
        self._free_item.title = f"Free:    {free_pct}%  ({free_gb:.1f} GB)"
        self._used_item.title = f"In use:  {used_gb:.1f} / {TOTAL_GB:.0f} GB"
        self._swap_item.title = swap_str

    def _quit(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    RamCatApp().run()
