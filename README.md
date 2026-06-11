# RAM Cat

**Know before you load.**

A macOS menubar companion for Apple Silicon that reacts to RAM pressure in real time — built for people running LLMs locally.

![RAM Cat demo](demo/ram-cat-demo.gif)

---

## Why

Every time you run `mlx_lm.generate` on a 12B model you're playing RAM roulette. Will it fit? Will it swap? Will the system grind to a halt halfway through a response?

RAM Cat watches `memory_pressure` (the honest macOS metric — not `psutil`, which overstates free RAM) and tells you exactly what's happening: a mood emoji that reacts to pressure, a loading spinner when RAM is actively filling, and a one-line answer to "can I load another model right now?"

---

## Moods

| Title bar | Meaning |
|-----------|---------|
| `RAM 😴 71%` | Idle — nothing loaded |
| `RAM 😸 58%` | Comfortable — model running fine |
| `RAM 😾 42%` | Alert — getting tight |
| `RAM 🙀 22%` | Frazzled — swap imminent |
| `RAM 😱 10%` | PANIC — you're swapping |

When RAM is actively filling (model loading), a braille spinner appears: `RAM 😾⣾ 42%` → `RAM 😾⣽ 40%`. When the mood changes, the title blinks three times so you catch it even if you're not watching.

---

## Click to open

```
Trend:   ▁▁▂▄▅▆▇▇██
──────────────────────────────────
Free:    38%  (6.1 GB)
In use:  9.9 / 16 GB
Wired:   2.3 GB  (model weights)
Swap:    none
──────────────────────────────────
4-bit:   ✓1B  ✓3B  ✓7B  ✓8B  ✓13B  ✗27B  ✗32B   (6.1 GB free)
Running: mlx-community/gemma-4-it-4bit  [mlx_lm]
──────────────────────────────────
Quit RAM Cat
```

The **4-bit fits row** is the main feature: given current free RAM, it shows which 4-bit quantised models will load and which won't. No mental arithmetic, no trial and error.

The **sparkline** shows the last 30 seconds of pressure history (10 × 3s polls). A flat line means stable; a climbing staircase means a model is loading.

---

## Install

```bash
git clone https://github.com/robertlangdonn/ram-cat.git
cd ram-cat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Requires macOS (Apple Silicon recommended). Uses the `memory_pressure` CLI which ships with macOS — no sudo, no extra dependencies.

---

## Model fit reference (4-bit)

| Model size | RAM needed | Fits on 16 GB? |
|-----------|------------|---------------|
| 1B        | ~0.8 GB    | ✓ always |
| 3B        | ~2 GB      | ✓ always |
| 7B        | ~4.5 GB    | ✓ usually |
| 8B        | ~5 GB      | ✓ usually |
| 13B       | ~8 GB      | ✓ with some headroom |
| 27B       | ~16 GB     | ✗ tight even at idle |
| 32B       | ~20 GB     | ✗ no |
| 70B       | ~40 GB     | ✗ no |

Numbers are approximate. RAM Cat uses live free memory to compute the table in real time — load a model and the ✓/✗ marks update accordingly.

---

## Detecting running models

RAM Cat scans processes for `mlx_lm.generate`, `mlx_lm.chat`, `mlx_lm.server`, `mlx_vlm`, and `ollama`. If it finds one it shows the model name (`--model` argument) in the dropdown.

---

## Roadmap

- [ ] `py2app` bundle so non-technical users can double-click
- [ ] Homebrew formula
- [ ] Alert when wired memory exceeds a threshold (model load complete signal)
- [ ] Ollama model name resolution

---

Built on Apple M3 · 16 GB · macOS. Tested with [mlx-lm](https://github.com/ml-explore/mlx-lm).
