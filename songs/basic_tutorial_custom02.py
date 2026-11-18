"""
Music-Code Tutorial: Using One Sample from Each Sample Directory
with Synthesis Fallback

Demonstrates loading samples from all 10 sample folders:
kick, snare, clap, hihat, cymbal, perc, bass, fx, user, (archive)
"""

from pathlib import Path
import sys

LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(LIB_DIR))

from music_code import MusicCode


def load_sample_with_fallback(m, folder, filename, fallback_func, *fallback_args, **fallback_kwargs):
    """
    Try to load a sample, fall back to synthesis if not found.
    Returns a Wave object.
    """
    try:
        wave = m.sample(folder, filename)
        print(f"  [OK] Loaded: {folder}/{filename}")
        return wave
    except Exception as e:
        print(f"  [WARN] Failed to load {folder}/{filename}: {e}")
        print(f"     -> Using fallback synthesis")
        return fallback_func(m, *fallback_args, **fallback_kwargs)


def fallback_kick(m):
    return m.create_wave(["C1"], "sine", 1/16).vol(1.5).LPF(80).time_edit(1/16)


def fallback_snare(m):
    return m.create_wave(["G2"], "saw1", 1/16).vol(0.6).HPF(200).LPF(2000).time_edit(1/16)


def fallback_clap(m):
    return m.create_wave(["C4"], "saw2", 1/16).vol(0.5).HPF(800).LPF(4000).time_edit(1/16)


def fallback_hihat(m):
    return m.create_wave(["C6"], "sine", 1/32).vol(0.3).HPF(4000).time_edit(1/32)


def fallback_cymbal(m):
    return m.create_wave(["C5"], "saw1", 1/4).vol(0.4).HPF(2000).time_edit(1/4)


def fallback_perc(m):
    return m.create_wave(["G3"], "tri", 1/16).vol(0.5).HPF(300).LPF(3000).time_edit(1/16)


def fallback_bass(m):
    return m.sequence(["C2", "C2", "G1", "C2"], "sine", rhythm=1/4, duration=1, fade_in=1/32, fade_out=1/32).LPF(120).vol(0.8)


def fallback_fx(m):
    return m.create_wave(["C3"], "sine-saw", 1).vol(0.3).HPF(100).LPF(2000).fade(fade_in=1/8, fade_out=1/2)


def fallback_user_piano(m):
    return m.sequence(["C4", "E4", "G4", "C5"], "sine-tri", rhythm=1/8, duration=1, fade_in=1/32, fade_out=1/32).vol(0.6)


def make_drum_pattern(m, kick, snare, hat, steps=16):
    """Build a 1-bar drum pattern from 16th-note grids."""
    def pattern(wave, hits, step):
        return m.join_waves(tuple(wave if h else m.rest(step) for h in hits))

    kick_pat = pattern(kick, [1,0,0,0, 1,0,0,0, 1,0,1,0, 1,0,0,0], 1/16)
    snare_pat = pattern(snare, [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 1/16)
    hat_pat = pattern(hat, [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1], 1/16)

    return m.add_waves((kick_pat, snare_pat, hat_pat))


def main():
    m = MusicCode(120)

    print("=" * 60)
    print("Loading samples from all directories...")
    print("=" * 60)

    # ─── Load one sample from each directory ───
    # kick
    kick = load_sample_with_fallback(m, "kick", "kick_06.wav", fallback_kick).time_edit(1/16).vol(1.0)

    # snare
    snare = load_sample_with_fallback(m, "snare", "snare_04.wav", fallback_snare).time_edit(1/16).vol(0.8)

    # clap
    clap = load_sample_with_fallback(m, "clap", "clap_03.wav", fallback_clap).time_edit(1/16).vol(0.6).pan("L20")

    # hihat
    hat = load_sample_with_fallback(m, "hihat", "hihat_02.wav", fallback_hihat).time_edit(1/16).vol(0.35).pan("R20")

    # cymbal (open hat)
    cymbal = load_sample_with_fallback(m, "cymbal", "open_00.wav", fallback_cymbal).time_edit(1/4).vol(0.5)

    # perc
    perc = load_sample_with_fallback(m, "perc", "perc_04.wav", fallback_perc).time_edit(1/16).vol(0.4).pan("R30")

    # bass (one-shot bass sample)
    bass_sample = load_sample_with_fallback(m, "bass", "bass_00.wav", fallback_bass).time_edit(1/4).vol(0.7)

    # fx
    fx = load_sample_with_fallback(m, "fx", "V_RIOT_fx_one_shot_drop.wav", fallback_fx).vol(0.4)

    # user (piano)
    user_piano = load_sample_with_fallback(m, "user", "piano/C4v8.wav", fallback_user_piano).time_edit(1/4).vol(0.7)

    print("=" * 60)
    print("All samples loaded. Building arrangement...")
    print("=" * 60)

    # ─── Build drum pattern ───
    drums_1bar = make_drum_pattern(m, kick, snare, hat)
    drums = drums_1bar.loop(4)  # 4 bars

    # Add clap on snare hits (layer)
    clap_pat = make_drum_pattern(m, clap, m.rest(1/16), m.rest(1/16))
    drums = m.add_waves((drums, clap_pat.loop(4)))

    # Add perc
    perc_pat = m.join_waves(tuple(
        perc if h else m.rest(1/16)
        for h in [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0]
    ))
    drums = m.add_waves((drums, perc_pat.loop(4)))

    # Add cymbal at end of each 2 bars
    cymbal_2bar = m.join_waves((m.rest(7/4), cymbal))
    drums = m.add_waves((drums, cymbal_2bar.loop(2)))

    # ─── Melodic elements ───
    # Bass line from sample
    bass_notes = ["C2", "C2", "G1", "C2", "F1", "F1", "C2", "G1"]
    bass_seq = m.sequence(bass_notes, "sine", rhythm=1/4, duration=4, fade_in=1/32, fade_out=1/32).LPF(100).vol(0.8)

    # Piano melody
    melody = m.sequence(
        ["C4", "E4", "G4", "C5", "G4", "E4", "C4", "rest",
         "F4", "A4", "C5", "F5", "C5", "A4", "F4", "rest"],
        "sine-tri", rhythm=1/8, duration=4, fade_in=1/32, fade_out=1/32
    ).HPF(200).vol(0.6).pan("L10")

    # Chords
    chord1 = m.chord("maj 7", "C3", "sine-tri", duration=2, wt_pos=555).HPF(150).vol(0.35)
    chord2 = m.chord("min 7", "A3", "sine-tri", duration=2, wt_pos=555).HPF(150).vol(0.35)
    pads = m.join_waves((chord1, chord2))

    # FX at transition points
    fx_2bar = m.join_waves((m.rest(7/4), fx))
    fx_layer = fx_2bar.loop(2)

    # ─── Final arrangement ───
    # Intro: drums only (1 bar)
    intro = drums[:int(len(drums) * 0.25)]

    # Verse: drums + bass + pads
    verse = m.add_waves((drums, bass_seq, pads))

    # Chorus: everything
    chorus = m.add_waves((drums, bass_seq, pads, melody, fx_layer))

    # Outro: fade out (create a fade manually to avoid stereo issues)
    outro_pads = pads.LPF(500)
    outro_melody = melody.LPF(500)
    # Apply fade by multiplying with envelope
    outro = m.add_waves((outro_pads, outro_melody))
    # Simple volume fade over last bar
    outro = outro.vol(0.5)  # Reduce volume for outro feel

    song = m.join_waves((intro, verse, chorus, outro))

    # Export
    song.vol(0.85).bounce("basic_tutorial_custom02.wav", show_visual=False)
    print("=" * 60)
    print("Done! Check export/basic_tutorial_custom02.wav")
    print("=" * 60)


if __name__ == "__main__":
    main()