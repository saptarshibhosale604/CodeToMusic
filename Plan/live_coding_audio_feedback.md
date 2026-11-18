# Live Audio Feedback While Coding - Music-Code

> **Goal:** Edit code → hear changes instantly — without manual "run → open file → listen" loop.

---

## Available Options

### 1. Jupyter Notebooks (Built-in, Best for Exploration)
The repo includes `notebooks/` and imports `IPython.display as ipd`.

```python
# In a notebook cell:
from music_code import MusicCode
m = MusicCode(120)
wave = m.sequence(["C4","E4","G4"], "sine-tri", 1/8, 1).vol(0.6)
wave.bounce("test.wav", show_visual=False)

# Play inline (auto-updates on re-run)
import IPython.display as ipd
ipd.Audio("export/test.wav")
```

| Pros | Cons |
|------|------|
| Native audio player | Not a `.py` file workflow |
| Re-run cells instantly | |
| Keep state between cells | |

**Run:** `cd Music-Code && .venv\Scripts\jupyter.exe notebook`

---

### 2. IPython REPL (Interactive Shell)
```bash
.venv\Scripts\ipython.exe
```
```python
from music_code import MusicCode
m = MusicCode(120)
wave = m.sequence(["C4","E4","G4"], "sine-tri", 1/8, 1).vol(0.6)
wave.bounce("test.wav", show_visual=False)

import IPython.display as ipd
ipd.Audio("export/test.wav")
```

| Pros | Cons |
|------|------|
| Full Python state persists | Audio playback depends on terminal frontend |
| Test snippets fast | |

---

### 3. VS Code + Python Interactive / Jupyter Extension
- Open `.py` file → add `# %%` cell markers → **Run Cell**
- Uses same kernel, shows `ipd.Audio` output inline

| Pros | Cons |
|------|------|
| Edit `.py` files directly | Requires VS Code setup |
| Cell-based execution | |
| Inline audio player | |

---

### 4. Auto-Reload + Auto-Play (File Watcher)

#### A. Python Watchdog Script (Cross-Platform)
```python
# watch_and_play.py
import time, subprocess, glob, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Changed: {event.src_path}")
            subprocess.run([".venv/Scripts/python.exe", event.src_path])
            # Auto-play latest WAV
            wavs = glob.glob("export/*.wav")
            if wavs:
                latest = max(wavs, key=os.path.getmtime)
                os.startfile(latest)  # Windows

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Handler(), "songs", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

**Install:** `pip install watchdog`

#### B. Simpler: `entr` (Linux/Mac/WSL)
```bash
ls songs/*.py | entr -c .venv/Scripts/python.exe /_
```

| Pros | Cons |
|------|------|
| Works with existing `.py` files | Extra setup |
| Instant feedback on save | Plays *after* full render |

---

### 5. Simple "Play Latest" Helper (Low-Tech, Reliable) ⭐ **Recommended**

Add to your script:
```python
import os, glob

def play_latest_export(export_dir="../export"):
    wavs = glob.glob(os.path.join(export_dir, "*.wav"))
    if wavs:
        latest = max(wavs, key=os.path.getmtime)
        os.startfile(latest)  # Windows opens default player

# At end of main():
song.bounce("my_track.wav", show_visual=False)
play_latest_export()
```

| Pros | Cons |
|------|------|
| Zero dependencies | Opens external player (not inline) |
| Works with any `.py` script | Must re-run script to hear changes |
| One-line addition | |
| Reliable on Windows | |

---

### 6. True Live Coding Environments (Not This Library)
If you want *real-time* audio modification (change code → hear instantly without re-render):
- **SuperCollider** - Industry standard live coding
- **FoxDot** - Python → SuperCollider bridge
- **TidalCycles** - Haskell pattern language
- **Sonic Pi** - Ruby-based, beginner-friendly

*Music-Code is a render-to-disk library, not a real-time audio engine.*

---

## Recommendation Matrix

| Your Workflow | Best Option |
|---------------|-------------|
| Exploring, learning, sketching ideas | **Jupyter Notebooks** (`notebooks/tutorials/`) |
| Writing full `.py` songs, want auto-play | **Option 5** — `play_latest_export()` helper |
| Tinkering interactively, keep state | **IPython REPL** (`.venv\Scripts\ipython.exe`) |
| VS Code user | **Python Interactive / Jupyter extension** |
| Want true live coding (real-time) | **FoxDot / SuperCollider / TidalCycles** |

---

## Quick Implementation: Add Auto-Play to Any Script

```python
# 1. Add at top of your song file
import os, glob

def play_latest_export(export_dir="../export"):
    wavs = glob.glob(os.path.join(export_dir, "*.wav"))
    if wavs:
        latest = max(wavs, key=os.path.getmtime)
        os.startfile(latest)

# 2. Call at end of main()
song.bounce("my_track.wav", show_visual=False)
play_latest_export()
```

**Now every run = hear it instantly.** 🎧

---

## For This Project Specifically

The repo already has:
- `notebooks/tutorials/` — ready for Jupyter exploration
- `IPython` installed in `.venv`
- `export/` folder for output

**Fastest start:** Open `notebooks/tutorials/` in Jupyter and experiment.

**For `.py` workflow:** Add the `play_latest_export()` helper to your song files.

---

*Generated for Music-Code project | Script/CodeToMusic/Plan/live_coding_audio_feedback.md*