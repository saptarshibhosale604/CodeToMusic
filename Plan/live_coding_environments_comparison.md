# Live Coding Environments Comparison

> **Context:** Music-Code is a **render-to-disk** library (write script → run → WAV file).  
> These 4 tools are **real-time live coding environments** — code modifies *running* audio instantly.

---

## Quick Comparison Matrix

| Feature | **SuperCollider** | **FoxDot** | **TidalCycles** | **Sonic Pi** |
|---------|-------------------|------------|-----------------|--------------|
| **Language** | SuperCollider (Smalltalk-like) | Python | Haskell | Ruby (DSL) |
| **Learning Curve** | Steep | Moderate (if you know Python) | Steep (Haskell) | Gentle |
| **Audio Engine** | Built-in (scsynth) | SuperCollider (via OSC) | SuperCollider (via OSC) | Built-in (Sonic Pi server) |
| **Paradigm** | Object-oriented, imperative | Python OO + pattern language | Functional, pattern-based | Imperative, beginner-friendly |
| **Pattern System** | Pbind, Pseq, Patterns | Player objects, Pattern | Mini-notation, Euclidean | Live loops, rings |
| **Time Model** | Sample-accurate, scheduled | Quantized to clock | Cycle-based, functional time | Beat-based, sync'd loops |
| **MIDI/OSC** | Full support | Full support | Full support | Full support |
| **GUI/Editor** | ScIDE, VS Code, Vim, Emacs | Any Python editor | VS Code (tidalcycles), Emacs | Built-in IDE (Sonic Pi app) |
| **Community** | Large, academic, pro | Growing, Python-centric | Niche, academic/artistic | Large, education-focused |
| **Installation** | Moderate (sc3-plugins, etc.) | `pip install FoxDot` + SC | Complex (Haskell, Stack, SC) | Easy (single installer) |
| **Performance** | Sample-accurate, pro-grade | Good (depends on SC) | Excellent (SC backend) | Good (built-in server) |
| **Best For** | Pro audio, research, complex DSP | Pythonistas wanting live coding | Algorithmic composition, patterns | Beginners, education, quick jams |

---

## Deep Dive

---

### 1. SuperCollider (The Grandfather)

**Language:** SuperCollider (sclang) — Smalltalk-inspired, object-oriented  
**Audio Server:** scsynth (separate process, OSC communication)  
**Since:** 1996 (James McCartney)

```supercollider
// Simple synth
SynthDef(\beep, { |freq=440, dur=0.1|
    var sig = SinOsc.ar(freq) * EnvGen.ar(Env.perc(0.01, dur), doneAction: 2);
    Out.ar(0, sig ! 2)
}).add;

// Play pattern
Pbind(
    \instrument, \beep,
    \degree, Pseq([0, 2, 4, 5, 7, 9, 11, 12], inf),
    \dur, 0.25
).play;
```

| Strengths | Weaknesses |
|-----------|------------|
| **Ultimate control** — sample-accurate timing, custom UGens | **Steep learning curve** — new language, new paradigm |
| **Industry standard** — used by pros (Autechre, Alva Noto, etc.) | **ScIDE is dated** — many use VS Code/Vim/Emacs |
| **Massive UGen library** — 300+ built-in, thousands more via sc3-plugins | **Two-process model** — language + server, can desync |
| **Mature ecosystem** — 25+ years of libraries, tutorials | **Error messages** — cryptic for beginners |
| **Multi-channel, ambisonics, granular** — anything is possible | **No built-in pattern notation** — build your own |

**Install:** Download from supercollider.github.io + sc3-plugins  
**Editor:** VS Code + `supercollider` extension (recommended)

---

### 2. FoxDot (Python → SuperCollider)

**Language:** Python 3  
**Backend:** SuperCollider (via OSC) — requires SC running  
**Since:** 2015 (Ryan Kirkbride)

```python
# FoxDot - Python live coding
from FoxDot import *

# Define a synth (in SuperCollider, but triggered from Python)
# SynthDefs usually written in .scd files, but can use built-ins

# Play patterns
p1 >> pluck([0, 2, 4, 5, 7, 9, 11, 12], dur=1/4, amp=0.5)
p2 >> bass([0, 0, 3, 5], dur=1/2, oct=4, amp=0.8)
d1 >> play("x-o-", sample=1)  # Mini-notation for drums

# Modify live
p1.degree = [0, 3, 5, 7]  # Change melody instantly
p1.dur = 1/8              # Double speed
```

| Strengths | Weaknesses |
|-----------|------------|
| **Write Python** — familiar syntax, your editor, your tools | **Requires SuperCollider running** — two apps |
| **Pattern language** — `>>`, `P[]`, `var()`, `linvar()` | **Less control** than raw SC — abstraction layer |
| **Mini-notation** — `"x-o-"` for drums, very expressive | **Documentation** — smaller community, fewer tutorials |
| **Jupyter support** — `FoxDot.jupyter` extension | **Python GIL** — not for heavy DSP in Python |
| **MIDI/OSC/Ableton Link** — full integration | **Debugging** — errors span Python ↔ SC boundary |

**Install:**
```bash
pip install FoxDot
# Then start SuperCollider, run: FoxDot.start
```

**Editor:** Any Python editor (VS Code, PyCharm, Vim) + FoxDot REPL

---

### 3. TidalCycles (Haskell, Pattern-First)

**Language:** Haskell (embedded DSL)  
**Backend:** SuperCollider (via OSC) — requires SC + Dirt sampler  
**Since:** 2009 (Alex McLean)

```haskell
-- TidalCycles - functional patterns
d1 $ sound "bd sd ~ bd"  -- Mini-notation: bd=sound, ~=rest

-- Euclidean rhythms
d1 $ sound "bd(3,8)"     -- 3 hits over 8 steps

-- Melody with mini-notation
d1 $ note "c4 e4 g4 c5" # s "superpiano"

-- Transform patterns functionally
d1 $ fast 2 $ sound "bd sd"        -- Double speed
d1 $ rev $ sound "bd sd cp"        -- Reverse
d1 $ every 3 (fast 2) $ sound "bd" -- Every 3rd cycle, double speed

-- Combine patterns
d1 $ stack [
    sound "bd(5,8)",
    sound "sd*2",
    note "c3 e3 g3" # s "superpiano" # gain 0.8
  ]
```

| Strengths | Weaknesses |
|-----------|------------|
| **Pattern-first thinking** — music as transforming patterns | **Haskell required** — steep if new to FP |
| **Mini-notation** — incredibly concise for rhythms | **Installation complex** — Haskell (GHC), Stack, SC, Dirt |
| **Functional composition** — `every`, `sometimes`, `fold` | **No traditional variables** — state via patterns |
| **Cycle-based time** — natural for repetitive music | **Editor support** — mainly VS Code + Emacs |
| **Algorithmic composition** — built for generative music | **Smaller community** — niche but passionate |

**Install:** See tidalcycles.org — involves Haskell (ghcup), Stack, SuperCollider, Dirt  
**Editor:** VS Code + `tidalcycles` extension (best), Emacs + `tidal.el`

---

### 4. Sonic Pi (Ruby, Education-First)

**Language:** Ruby (custom DSL)  
**Backend:** Built-in audio server (Sonic Pi Server) — no external deps  
**Since:** 2012 (Sam Aaron)

```ruby
# Sonic Pi - beginner-friendly live coding
use_bpm 120

live_loop :drums do
  sample :bd_haus, amp: 1.5
  sleep 0.5
  sample :sn_dub, amp: 1
  sleep 0.5
end

live_loop :bass do
  use_synth :fm
  play :c2, release: 0.2, cutoff: 80
  sleep 0.5
  play :c2, release: 0.2, cutoff: 80
  sleep 0.25
  play :eb2, release: 0.2, cutoff: 80
  sleep 0.25
end

live_loop :melody do
  use_synth :prophet
  play_pattern_timed [:c4, :e4, :g4, :c5], [0.25, 0.25, 0.25, 0.25], release: 0.3
end
```

| Strengths | Weaknesses |
|-----------|------------|
| **Zero-install almost** — single installer (Win/Mac/Linux/Raspberry Pi) | **Ruby DSL** — not standard Ruby, limited ecosystem |
| **Built-in IDE** — code editor + log + scope + help + prefs | **Less powerful** — no custom UGens, limited DSP |
| **Designed for teaching** — amazing docs, tutorials, error messages | **Timing** — beat-based, not sample-accurate |
| **Great for jamming** — `live_loop` syncs automatically | **No pattern language** — manual loops |
| **MIDI/OSC/Ableton Link** — works great | **Performance ceiling** — not for pro stage use |

**Install:** Download from sonic-pi.net (single .exe/.dmg/.deb)  
**Editor:** Built-in (Sonic Pi app) — or VS Code + `sonic-pi` extension

---

## Decision Guide

### Choose **SuperCollider** if:
- You want **maximum control** and **pro-grade audio**
- You're willing to learn a new language
- You need custom synthesis, granular, ambisonics, physical modeling
- You're doing research or professional performance

### Choose **FoxDot** if:
- You **know Python** and want to live code *now*
- You want pattern language + mini-notation
- You're okay running SuperCollider in background
- You want Jupyter integration

### Choose **TidalCycles** if:
- You think in **patterns, transformations, algorithms**
- You know or want to learn **Haskell/functional programming**
- You want the most **expressive pattern notation** (mini-notation)
- You're into **algorithmic/generative composition**

### Choose **Sonic Pi** if:
- You're **new to live coding** — lowest barrier to entry
- You want **zero setup** — download and run
- You're **teaching** or **learning** — best docs/tutorials
- You want to **jam quickly** with `live_loop` sync

---

## For Music-Code Users Specifically

| If you like... | Try... |
|----------------|--------|
| `m.sequence()`, `m.chord()`, `m.arpeggio()` | **FoxDot** — similar pattern thinking in Python |
| Writing `.py` scripts, want live feedback | **FoxDot** or **Sonic Pi** (easiest transition) |
| Functional composition, transforming patterns | **TidalCycles** |
| Building custom synths, DSP from scratch | **SuperCollider** |
| Quick sketches, education, jamming | **Sonic Pi** |

---

## Hybrid Workflow (Recommended)

```
Music-Code (render-to-disk)
    │
    ├── Sketch ideas, design sounds, export stems
    │
    └── Import stems → Live code with FoxDot/Sonic Pi
         │
         ├── Real-time arrangement
         ├── Live performance
         └── Record session → back to Music-Code for final mix
```

---

## Resources

| Tool | Website | Docs | Community |
|------|---------|------|-----------|
| **SuperCollider** | supercollider.github.io | doc.sccode.org | scsynth.org, Discord |
| **FoxDot** | foxdot.org | foxdot.org/docs | Discord, GitHub |
| **TidalCycles** | tidalcycles.org | tidalcycles.org/docs | Discord, Forum |
| **Sonic Pi** | sonic-pi.net | sonic-pi.net/tutorial.html | Discord, Forum |

---

*Generated for Music-Code project | Script/CodeToMusic/Plan/live_coding_environments_comparison.md*