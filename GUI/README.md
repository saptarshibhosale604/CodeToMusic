# MusicCode GUI — Tactical Beat Constructor

**Mission:** Bidirectional GUI ↔ Code system for procedural music generation using the MusicCode library.

**Architecture:** MVC + AST Round-Trip (Architecture 1)

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GUI       │────▶│  Model      │────▶│   AST       │────▶│  Python     │
│  (Views)    │     │ (Project)   │     │ (CodeGen)   │     │  (.py)      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      ▲                                       │
      │                                       ▼
      │                              ┌─────────────┐
      └──────────────◀───────────────│   AST       │
         (Import)                     │ (Parser)    │
                                      └─────────────┘
```

**True Round-Trip:** GUI → Model → AST → Python → AST → Model → GUI

---

## Quick Start

```bash
# 1. Install dependencies
cd Github/CodeToMusic/GUI
pip install -r requirements.txt

# 2. Ensure MusicCode core is available
# The core library should be at: ../../core/music_code.py

# 3. Launch
python main.py
```

---

## Project Structure

```
GUI/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
├── models/
│   ├── __init__.py
│   ├── project.py         # ProjectModel, TrackModel, PatternModel, SampleModel, MixModel
│   └── code_gen.py        # CodeGenerator: Model → AST → Python
├── views/
│   ├── __init__.py
│   └── main_window.py     # MainWindow: Sample Rack | Pattern Grid | Mixer | Timeline
├── controllers/
│   ├── __init__.py
│   └── app_controller.py  # AppController: Commands, Undo/Redo, Project Ops
└── parsers/
    ├── __init__.py
    └── musiccode_parser.py # MusicCodeParser: Python → AST → Model
```

---

## Features

### ✅ Implemented
- **Project Model** — Complete data model (Project, Tracks, Patterns, Samples, Mix)
- **Code Generator** — Model → AST → formatted Python (with `black`)
- **AST Parser** — Python → AST → Model (handles `m.sample`, `m.join_waves`, `m.add_waves`, `m.sequence`, `m.arpeggio`, `.loop()`, `.vol()`, `.pan()`, `.LPF()`, `.bounce()`)
- **Main Window** — Four-panel layout: Sample Rack | Pattern Grid | Mixer | Timeline
- **Command System** — Undo/Redo with full history
- **File I/O** — `.mcproj` (JSON) + `.py` import/export
- **Bounce Audio** — Generate code and run to produce WAV

### 🚧 In Progress / Planned
- [ ] Pattern grid step editing (click to place samples)
- [ ] Drag-and-drop sample assignment
- [ ] Real-time audio preview
- [ ] Timeline arrangement view
- [ ] Effect parameter automation
- [ ] Keyboard shortcuts for step sequencing
- [ ] Project templates
- [ ] Sample waveform preview

---

## Usage Workflow

### 1. Create New Project
- File → New Project (Ctrl+N)
- Set BPM in timeline transport

### 2. Load Samples
- Sample Rack → "Load Sample" or "Scan Library"
- Enter sample name, library index, time edit (e.g., 1/8)

### 3. Create Tracks & Patterns
- Mixer → Add tracks (via code or future UI)
- Pattern Grid → Select track, set steps/resolution/loop
- Click grid cells to place samples/rests

### 4. Mix & Arrange
- Mixer → Set volume, pan, solo/mute per track
- Add effects (LPF, volume, pan)
- Timeline → Arrange patterns (future)

### 5. Export & Bounce
- File → Export Python (Ctrl+E) → Generates clean MusicCode script
- Tools → Bounce Audio (F5) → Runs script, produces WAV in `../export/`
- File → Save Project → Saves `.mcproj` for later editing

### 6. Round-Trip Editing
- File → Import MusicCode (Ctrl+I) → Parses existing `.py` into GUI
- Edit visually → Export again → Perfect fidelity

---

## MusicCode API Coverage

| Construct | Parse | Generate |
|-----------|-------|----------|
| `m = MusicCode(tempo)` | ✅ | ✅ |
| `m.sample('name', idx)` | ✅ | ✅ |
| `.time_edit(dur)` | ✅ | ✅ |
| `.vol(level)` | ✅ | ✅ |
| `.pan(pos)` | ✅ | ✅ |
| `m.rest(dur)` | ✅ | ✅ |
| `m.join_waves((a,b,c))` | ✅ | ✅ |
| `m.add_waves((a,b,c))` | ✅ | ✅ |
| `.loop(n)` | ✅ | ✅ |
| `m.sequence(...)` | ✅ (as expr) | ✅ |
| `m.arpeggio(...)` | ✅ (as expr) | ✅ |
| `.LPF(freq)` | ✅ | ✅ |
| `.bounce('file.wav')` | ✅ | ✅ |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project (.mcproj) |
| Ctrl+I | Import Python (.py) |
| Ctrl+S | Save Project |
| Ctrl+Shift+S | Save Project As |
| Ctrl+E | Export Python |
| F5 | Bounce Audio |
| Space | Preview Pattern |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |

---

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `customtkinter` | Modern dark-theme GUI | ✅ |
| `astor` | AST → source code | ✅ |
| `black` | Code formatting | ⚠️ Optional |
| `music_code` | Core synthesis library | ✅ (from `../core`) |

---

## Testing Round-Trip

```bash
# 1. Start with existing script
cp ../songs/own_beats_01.py test_input.py

# 2. Launch GUI
python main.py

# 3. File → Import MusicCode → Select test_input.py
# 4. Verify GUI shows: samples, patterns, tracks, mix
# 5. File → Export Python → test_output.py
# 6. Compare: diff test_input.py test_output.py
# 7. Run both: python test_input.py && python test_output.py
# 8. Verify identical WAV output
```

---

## Troubleshooting

**"Module music_code not found"**
```bash
# Ensure core is in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../../core"
# Or check main.py adds it automatically
```

**"customtkinter not found"**
```bash
pip install customtkinter
```

**"astor not found"**
```bash
pip install astor
```

**Black formatting fails**
- Code still generates, just unformatted
- Install black: `pip install black`

---

## Command Reference (for developers)

```python
# Direct model manipulation
from models.project import ProjectModel, TrackModel, PatternModel, SampleModel
from models.code_gen import CodeGenerator
from parsers.musiccode_parser import parse_musiccode_file

# Parse existing script
project = parse_musiccode_file("song.py")

# Modify model
project.tempo = 140
track = TrackModel(name="bass")
pattern = PatternModel(name="bassline", resolution=1/16)
# ... add steps ...
track.add_pattern(pattern)
project.add_track(track)

# Generate code
code = CodeGenerator(project).generate()
print(code)

# Save project
project.save_project("my_project.mcproj")

# Load project
project = ProjectModel.load_project("my_project.mcproj")
```

---

## License

Part of MusicCode project. See `../LICENSE.txt`.

---

**RPI — TACTICAL GUI DEPLOYED. AWAITING GENERAL SSB'S BEAT ORDERS.**