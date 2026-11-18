# Music-Code Tutorial

> **Music-Code** is a Python toolkit for making music with code. It combines synthesis, chord/sequence generation, sample playback, DSP, and WAV export in a single local project.

---

## Quick Start

### 1. Environment Setup
```bash
cd Script/CodeToMusic/Music-Code
python -m venv .venv
.venv\Scripts\activate.bat
pip install numpy pandas matplotlib scipy scikit-learn soundfile ipython seaborn
```

### 2. Run Examples
```bash
# Basic tutorial
.venv\Scripts\python.exe songs/basic_tutorial.py

# Doraemon theme
.venv\Scripts\python.exe songs/doraemon_theme.py

# Original example song
.venv\Scripts\python.exe songs/song_1.py
```

Output files appear in `export/`.

---

## Core Concepts

### Two Main Classes

| Class | Purpose |
|-------|---------|
| `MusicCode` | Generates musical material (notes, chords, samples, sequences) |
| `Wave` | Represents audio data (numpy array with DSP methods) |

### Timing (Relative Mode - Default)

| Value | Musical Meaning |
|-------|-----------------|
| `1` | 1 bar (4 beats) |
| `1/2` | Half note (2 beats) |
| `1/4` | Quarter note (1 beat) |
| `1/8` | Eighth note (½ beat) |
| `1/16` | Sixteenth note (¼ beat) |
| `4` | 4 bars |

> **Formula:** `duration_in_seconds = (60 / BPM) * 4 * duration_value`

---

## MusicCode Methods

### Create Melodies / Bass Lines
```python
m.sequence(note_list, waveform, rhythm, duration, **kwargs)
```

| Parameter | Description |
|-----------|-------------|
| `note_list` | List of note names `["C4", "E4", "G4"]` or frequencies `[440, 220]` or `"rest"` |
| `waveform` | `'sine'`, `'tri'`, `'saw1'`, `'saw2'`, `'square'`, `'sine-tri'`, etc. |
| `rhythm` | Duration of **each** note (e.g., `1/8` = eighth notes) |
| `duration` | **Total** length in bars (e.g., `2` = 2 bars) |
| `wt_pos` | Wavetable position (timbre variation, default=1) |
| `fade_in` / `fade_out` | Smooth edges (e.g., `1/32`) |

### Create Chords
```python
m.chord(chord_type, root_note, waveform, duration, **kwargs)
```

**Common chord types** (from `data/chords_blueprint.csv`):
- `maj triad`, `maj 7`, `maj 9`, `maj 13`
- `min triad`, `min 7`, `min 9`, `min 11`
- `dominant 7`, `dominant 9`, `dominant 13`
- `suspended chord`, `power chord`, `diminish triad`

### Create Arpeggios
```python
m.arpeggio(chord_type, root_note, waveform, rhythm, duration, **kwargs)
```

### Load Samples
```python
m.sample(folder, sample_id)
```

**Built-in folders:** `kick`, `snare`, `clap`, `hihat`, `perc`, `cymbal`, `bass`, `fx`, `user`

```python
kick = m.sample("kick", "kick_06.wav")      # by filename
snare = m.sample("snare", 0)                # by index (sorted)
```

### Create Silence
```python
m.rest(duration)  # e.g., m.rest(1/4)
```

---

## Wave Methods (Chainable)

All return a new `Wave` object — chain them!

| Method | Purpose | Example |
|--------|---------|---------|
| `.vol(level)` | Volume (0.0–1.0+) | `.vol(0.8)` |
| `.LPF(freq)` | Low-pass filter | `.LPF(200)` |
| `.HPF(freq)` | High-pass filter | `.HPF(100)` |
| `.pan(pos)` | Stereo pan | `.pan("L30")`, `.pan("R20")`, `.pan("C")` |
| `.fade(in, out)` | Fade in/out | `.fade(fade_in=1/32, fade_out=1/32)` |
| `.time_edit(ratio)` | Time stretch | `.time_edit(1/8)` |
| `.loop(n)` | Repeat n times | `.loop(4)` |
| `.reverse()` | Reverse audio | `.reverse()` |
| `.delay(time, feedback)` | Delay effect | `.delay(1/4, 0.5)` |
| `.LFO(rate, depth)` | Modulation | `.LFO(5, 0.3)` |

---

## Arrangement

### Layer Sounds (Play Simultaneously)
```python
m.add_waves((wave1, wave2, wave3))  # Mixes to shortest length
```

### Sequence Sounds (Play One After Another)
```python
m.join_waves((wave1, wave2, wave3))  # Concatenates
```

---

## Waveforms Available

| Category | Types |
|----------|-------|
| **Pure** | `sine`, `tri`, `saw1`, `saw2`, `square` |
| **Blends** | `sine-tri`, `sine-saw`, `sine-square`, `saw-square`, `tri-saw`, `tri-square` |

> **Tip:** `sine` = pure/clean, `square` = hollow/retro, `saw` = bright/buzzy, `tri` = soft/mellow. Blends combine characteristics.

---

## Complete Minimal Example

```python
from pathlib import Path
import sys

LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(LIB_DIR))

from music_code import MusicCode

m = MusicCode(120)

# Melody
melody = m.sequence(
    ["C4", "E4", "G4", "C5", "G4", "E4", "C4", "rest"],
    "sine-tri", rhythm=1/8, duration=1, fade_in=1/32, fade_out=1/32
).vol(0.6)

# Bass
bass = m.sequence(
    ["C2", "C2", "G1", "C2"],
    "sine", rhythm=1/4, duration=1, fade_in=1/32, fade_out=1/32
).LPF(100).vol(0.8)

# Chords
chord = m.chord("maj 7", "C3", "sine-tri", duration=1).HPF(150).vol(0.4)

# Drums (with fallback)
try:
    kick = m.sample("kick", "kick_06.wav").time_edit(1/16).vol(1.0)
    snare = m.sample("snare", "snare_04.wav").time_edit(1/16).vol(0.8)
except:
    kick = m.create_wave(["C1"], "sine", 1/16).vol(1.5).LPF(80)
    snare = m.create_wave(["G2"], "saw1", 1/16).vol(0.6).HPF(200).LPF(2000)

kick_pat = m.join_waves(tuple(kick if h else m.rest(1/16) for h in [1,0,0,0, 1,0,0,0]))
snare_pat = m.join_waves(tuple(snare if h else m.rest(1/16) for h in [0,0,0,0, 1,0,0,0]))
drums = m.add_waves((kick_pat, snare_pat)).loop(1)

# Arrange & Export
song = m.add_waves((melody, bass, chord, drums))
song.vol(0.85).bounce("my_first_track.wav", show_visual=False)
```

---

## Project Structure

```
Music-Code/
├── core/
│   └── music_code.py          # Main library
├── data/
│   ├── chords_blueprint.csv   # Chord definitions
│   └── frequency_musical notes.csv
├── samples/                   # Built-in WAV samples
│   ├── kick/
│   ├── snare/
│   ├── hihat/
│   └── ...
├── songs/                     # Example compositions
│   ├── song_1.py
│   ├── basic_tutorial.py
│   └── doraemon_theme.py
├── export/                    # Rendered WAV output
├── notebooks/                 # Jupyter tutorials
└── tests/
    └── tests.py               # Smoke tests
```

---

## Tips & Gotchas

1. **Always use the venv Python:** `.venv\Scripts\python.exe songs/your_script.py`
2. **Import path:** Adjust `LIB_DIR` based on where your script lives
3. **Chord names must match exactly** — check `data/chords_blueprint.csv`
4. **`add_waves` trims to shortest** — pad shorter parts with `m.rest()` if needed
5. **Volume stacking:** Multiple `.vol()` calls multiply; keep final mix under ~0.9
6. **Sample rate:** Fixed at 44100 Hz
7. **Auto-increment:** `bounce()` won't overwrite — adds `_1`, `_2`, etc.

---

## Next Steps

- Read `core/music_code.py` for full API
- Explore `notebooks/tutorials/` for interactive guides
- Run `tests/tests.py` to verify all features work
- Check `songs/song_1.py` for advanced arrangement techniques

---

*Generated for Music-Code v1.0 | Repository: https://github.com/wesleyLaurence/Music-Code*