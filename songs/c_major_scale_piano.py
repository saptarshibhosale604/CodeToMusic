"""
Simple C Major Scale (C D E F G A B C) using user/piano samples.
Falls back to synthesis for notes not available in the sample library.
"""

from pathlib import Path
import sys

LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(LIB_DIR))

from music_code import MusicCode


def main():
    m = MusicCode(120)

    # Available piano samples in samples/user/piano/
    # Format: {note_name: filename}
    # We have: C1-C8, D#1-D#7, F#1-F#7, A0-A7
    piano_samples = {
        # "C4": "piano/C4v8.wav",
        "C4": None,
        "D4": None,      # Not available - will synthesize
        "E4": None,      # Not available - will synthesize
        "F4": None,      # Not available - will synthesize
        "G4": None,      # Not available - will synthesize
        # "A4": "piano/A4v8.wav",
        "A4": None,
        "B4": None,      # Not available - will synthesize
        # "C5": "piano/C5v8.wav",
        "C5": None,
    }

    # Try to load samples, synthesize missing ones
    scale_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    scale_waves = []

    for note in scale_notes:
        filename = piano_samples[note]
        if filename is not None:
            try:
                # Load piano sample from user/piano/ subfolder
                wave = m.sample("user", filename).time_edit(1/4).vol(0.8)
                print(f"Loaded sample: {filename} for {note}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}, synthesizing...")
                wave = synthesize_piano_note(m, note)
        else:
            print(f"Synthesizing {note} (no sample available)")
            wave = synthesize_piano_note(m, note)

        scale_waves.append(wave)

    # Join all notes in sequence (each gets 1/4 note = quarter note)
    # rhythm=1/4 means each note is a quarter note, duration=2 bars = 8 quarter notes
    scale = m.join_waves(tuple(scale_waves))

    # Add a little reverb-like tail using delay
    # delay(time, feedback, mix, spread)
    scale = scale.delay(1/4, 0.3, 0.3, 0.5).vol(0.9)

    # Export
    # scale.bounce("c_major_scale_piano.wav", show_visual=False)
    scale.bounce("c_major_scale_piano.wav", show_visual=True)
    print("Done! Check export/c_major_scale_piano.wav")


# def synthesize_piano_note(m, note, duration=1/4):
def synthesize_piano_note(m, note, duration=1):
    """
    Synthesize a piano-like note using sine-tri waveform with
    quick attack and exponential decay (piano envelope).
    """
    # Piano-like: bright attack (sine-tri), fast decay, slight inharmonicity
    wave = m.create_wave([note], "sine-tri", duration, wt_pos=2)
    
    # Piano envelope: fast attack, exponential decay
    # Approximate with fade_in very short, fade_out longer
    wave = wave.fade(fade_in=1/128, fade_out=duration/2)
    
    # Add slight high-frequency content for "brightness"
    wave = wave.HPF(80).LPF(4000)
    
    return wave.vol(0.7)


if __name__ == "__main__":
    main()