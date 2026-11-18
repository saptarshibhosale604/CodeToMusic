from pathlib import Path
import sys

# Import the local core module from the current repo layout.
LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.insert(0, str(LIB_DIR))

from music_code import MusicCode

# Initialize MusicCode, set BPM
m = MusicCode(bpm=120)

print("=" * 60)
print("PIANO SCALE TEST - C Major (C D E F G A B C)")
print("Using Salamander Grand Piano V3 samples (v8 velocity layer)")
print("=" * 60)

# Map C-major scale to nearest available minor-thirds samples
# Available: A0-A7, C1-C8, D#1-D#7, F#1-F#7
piano_map = {
    "C4": "piano/C4v8.wav",      # Exact match
    "D4": "piano/D#4v8.wav",     # Nearest (D# = Eb)
    "E4": "piano/F#4v8.wav",     # Nearest (F# = Gb)
    "F4": "piano/F#4v8.wav",     # Nearest
    "G4": "piano/A4v8.wav",      # Nearest (A4)
    "A4": "piano/A4v8.wav",      # Exact match
    "B4": "piano/C5v8.wav",      # Nearest (C5)
    "C5": "piano/C5v8.wav",      # Exact match
}

# Load all piano samples
print("\nLoading piano samples...")
piano_samples = {}
for note, filename in piano_map.items():
    try:
        piano_samples[note] = m.sample("user", filename)
        print(f"  [OK] {note} -> {filename}")
    except Exception as e:
        print(f"  [FAIL] {note} -> {filename} FAILED: {e}")

# Test 1: Play each note individually (quarter notes)
print("\n--- Test 1: Individual Notes (Quarter Notes) ---")
scale_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
individual_waves = []

for note in scale_notes:
    if note in piano_samples:
        # Each note = 1/4 duration (quarter note at 120 BPM = 0.5 sec)
        wave = piano_samples[note].vol(0.7).fade(fade_in=1/64, fade_out=1/32)
        individual_waves.append(wave)
        print(f"  Playing {note}...")

scale_sequence = m.join_waves(tuple(individual_waves))
scale_sequence.bounce("piano_scale_individual.wav", show_visual=False)
print("  [OK] Exported: piano_scale_individual.wav")

# Test 2: Play as legato sequence (eighth notes, joined)
print("\n--- Test 2: Legato Sequence (Eighth Notes) ---")
legato_waves = []
for note in scale_notes:
    if note in piano_samples:
        wave = piano_samples[note].vol(0.6).fade(fade_in=1/128, fade_out=1/64)
        legato_waves.append(wave)

legato_sequence = m.join_waves(tuple(legato_waves))
legato_sequence.bounce("piano_scale_legato.wav", show_visual=False)
print("  [OK] Exported: piano_scale_legato.wav")

# Test 3: Play as chord (all notes simultaneously)
print("\n--- Test 3: C Major Chord (All Notes Together) ---")
chord_waves = []
for note in scale_notes:
    if note in piano_samples:
        wave = piano_samples[note].vol(0.35).fade(fade_in=1/64, fade_out=1/4)
        chord_waves.append(wave)

chord = m.add_waves(tuple(chord_waves))
chord.bounce("piano_cmaj_chord.wav", show_visual=False)
print("  [OK] Exported: piano_cmaj_chord.wav")

# Test 4: Arpeggio up and down
print("\n--- Test 4: Arpeggio Up & Down ---")
arp_up = scale_notes
arp_down = scale_notes[-2::-1]  # Reverse without duplicating top C
arp_notes = arp_up + arp_down

arp_waves = []
for note in arp_notes:
    if note in piano_samples:
        wave = piano_samples[note].vol(0.65).fade(fade_in=1/128, fade_out=1/32)
        arp_waves.append(wave)

arp_sequence = m.join_waves(tuple(arp_waves))
arp_sequence.bounce("piano_scale_arpeggio.wav", show_visual=False)
print("  [OK] Exported: piano_scale_arpeggio.wav")

# Test 5: Two-octave run (C4 to C6)
print("\n--- Test 5: Two-Octave Run (C4-C5-C6) ---")
# Map higher octave using available samples
high_map = {
    "C5": "piano/C5v8.wav",
    "D5": "piano/D#5v8.wav",
    "E5": "piano/F#5v8.wav",
    "F5": "piano/F#5v8.wav",
    "G5": "piano/A5v8.wav",
    "A5": "piano/A5v8.wav",
    "B5": "piano/C6v8.wav",
    "C6": "piano/C6v8.wav",
}

# Load high octave samples
high_samples = {}
for note, filename in high_map.items():
    try:
        high_samples[note] = m.sample("user", filename)
        print(f"  [OK] {note} -> {filename}")
    except Exception as e:
        print(f"  [FAIL] {note} -> {filename} FAILED: {e}")

two_octave_notes = scale_notes + list(high_map.keys())[1:]  # Skip duplicate C5
two_octave_waves = []

for note in two_octave_notes:
    src = piano_samples if note in piano_samples else high_samples
    if note in src:
        wave = src[note].vol(0.6).fade(fade_in=1/128, fade_out=1/64)
        two_octave_waves.append(wave)

two_octave_sequence = m.join_waves(tuple(two_octave_waves))
two_octave_sequence.bounce("piano_two_octave_run.wav", show_visual=False)
print("  [OK] Exported: piano_two_octave_run.wav")

print("\n" + "=" * 60)
print("ALL PIANO SCALE TESTS COMPLETE")
print("Output files in: Script/CodeToMusic/Music-Code/export/")
print("=" * 60)