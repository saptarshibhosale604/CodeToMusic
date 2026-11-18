"""
============================================================
MUSIC-CODE BASIC TUTORIAL - Minimal Working Example
============================================================

This script demonstrates the absolute basics of Music-Code.
Run it with: .venv/Scripts/python.exe songs/basic_tutorial.py
"""

from pathlib import Path
import sys

# 1. SETUP: Add the core library to Python path
LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(LIB_DIR))

from music_code import MusicCode


def main():
    # 2. CREATE MusicCode object with BPM (beats per minute)
    m = MusicCode(120)  # 120 BPM = standard tempo
    # m = MusicCode(90)  # 120 BPM = standard tempo

    # ============================================================
    # CORE CONCEPTS
    # ============================================================
    #
    # MusicCode creates audio. Two main classes:
    #   - MusicCode: generates musical material (notes, chords, samples)
    #   - Wave:      represents audio data (numpy array with DSP methods)
    #
    # Timing (relative mode, default):
    #   duration=1    -> 1 full bar (4 beats at current BPM)
    #   duration=1/4  -> quarter note (1 beat)
    #   duration=1/8  -> eighth note (half beat)
    #   duration=4    -> 4 bars
    #
    # Waveforms available:
    #   'sine', 'tri', 'saw1', 'saw2', 'square'
    #   Blends: 'sine-tri', 'sine-saw', 'sine-square', 'saw-square', 'tri-saw', 'tri-square'
    #
    # Notes: "C4", "D#4", "F#3" or raw frequencies (440, 220, etc.)
    # Rest:  "rest"
    # ============================================================

    # ------------------------------------------------------------------
    # 3. CREATE A SIMPLE MELODY (single notes in sequence)
    # ------------------------------------------------------------------
    # sequence(note_list, waveform, rhythm, duration)
    #   rhythm = duration of EACH note (here: eighth notes = 1/8 bar each)
    #   duration = TOTAL length (here: 2 bars = 16 eighth notes)
    melody = m.sequence(
        ["C4", "E4", "G4", "C5", "G4", "E4", "C4", "rest",   # Bar 1
         "C4", "E4", "G4", "C5", "G4", "E4", "C4", "rest"],  # Bar 2
        "sine-tri",    # waveform: bright, playful
        rhythm=1/8,    # each note = eighth note
        duration=2,    # total = 2 bars
        fade_in=1/32,  # smooth start
        fade_out=1/32  # smooth end
    ).vol(0.6)         # volume 0.6 (0.0 to 1.0+)

    # ------------------------------------------------------------------
    # 4. CREATE A BASS LINE
    # ------------------------------------------------------------------
    bass = m.sequence(
        ["C2", "C2", "G1", "C2", "C2", "G1", "F1", "C2"],  # 8 notes
        "sine",           # pure sine = clean sub bass
        rhythm=1/4,       # quarter notes
        duration=2,       # 2 bars
        fade_in=1/32,
        fade_out=1/32
    ).LPF(100).vol(0.8)   # Low-pass filter at 100Hz, volume 0.8

    # ------------------------------------------------------------------
    # 5. CREATE CHORDS (harmony)
    # ------------------------------------------------------------------
    # chord(chord_type, root_note, waveform, duration)
    # Chord types from data/chords_blueprint.csv:
    #   "maj triad", "maj 7", "maj 9", "min triad", "min 7", "min 9", "dominant 7", etc.
    chord1 = m.chord("maj 7", "C3", "sine-tri", duration=1).HPF(150).vol(0.4)  # Bar 1: Cmaj7
    chord2 = m.chord("min 7", "A3", "sine-tri", duration=1).HPF(150).vol(0.4)  # Bar 2: Amin7

    chords = m.join_waves((chord1, chord2))  # Join back-to-back

    # ------------------------------------------------------------------
    # 6. CREATE DRUMS (using built-in samples)
    # ------------------------------------------------------------------
    try:
        kick = m.sample("kick", "kick_06.wav").time_edit(1/16).vol(1.0)
        snare = m.sample("snare", "snare_04.wav").time_edit(1/16).vol(0.8)
        hat = m.sample("hihat", "hihat_02.wav").time_edit(1/16).vol(0.3).pan("R20")

        # Helper: build a 1-bar pattern from a list of 1/0 hits
        def pattern(m, wave, hits, step):
            return m.join_waves(tuple(wave if h else m.rest(step) for h in hits))

        # 16th-note grid (16 steps per bar)
        kick_pat = pattern(m, kick, [1,0,0,0, 1,0,0,0, 1,0,1,0, 1,0,0,0], 1/16)
        snare_pat = pattern(m, snare, [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 1/16)
        hat_pat = pattern(m, hat, [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1], 1/16)

        drums_1bar = m.add_waves((kick_pat, snare_pat, hat_pat))  # Layer them
        drums = drums_1bar.loop(2)  # Repeat for 2 bars

    except Exception:
        # Fallback: synthesized drums if samples missing
        print("Samples not found, using synthesized drums")
        kick = m.create_wave(["C1"], "sine", 1/16).vol(1.5).LPF(80)
        snare = m.create_wave(["G2"], "saw1", 1/16).vol(0.6).HPF(200).LPF(2000)
        hat = m.create_wave(["C6"], "sine", 1/32).vol(0.2).HPF(4000)

        def pattern(m, wave, hits, step):
            return m.join_waves(tuple(wave if h else m.rest(step) for h in hits))

        kick_pat = pattern(m, kick, [1,0,0,0, 1,0,0,0, 1,0,1,0, 1,0,0,0], 1/16)
        snare_pat = pattern(m, snare, [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 1/16)
        hat_pat = pattern(m, hat, [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1], 1/16)

        drums_1bar = m.add_waves((kick_pat, snare_pat, hat_pat))
        drums = drums_1bar.loop(2)

    # ------------------------------------------------------------------
    # 7. ARRANGE: Combine everything
    # ------------------------------------------------------------------
    # add_waves = MIX (layer on top of each other, plays simultaneously)
    # join_waves = SEQUENCE (play one after another)
    # song = m.add_waves((melody, bass, chords, drums))
    # song = m.join_waves((melody, bass, chords, drums))
    # song = melody
    song = bass

    # song = song.loop(3)  # Repeat entire 2-bar arrangement 3 times = 6 bars

    # ------------------------------------------------------------------
    # 8. EXPORT: Bounce to WAV file
    # ------------------------------------------------------------------
    # Output goes to export/ folder
    # song.vol(0.85).bounce("basic_tutorial_custom.wav", show_visual=False)
    song.vol(0.85).bounce("basic_tutorial_custom.wav", show_visual=True)
    print("Done! Check export/basic_tutorial_custom.wav")


if __name__ == "__main__":
    main()