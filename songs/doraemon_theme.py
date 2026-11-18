from pathlib import Path
import sys

# Allow importing the local music_code module.
LIB_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(LIB_DIR))

from music_code import MusicCode


def main():
    m = MusicCode(140)  # Doraemon theme tempo ~140 BPM

    # ============================================================
    # DORAEMON THEME MELODY (Main melody - "Doraemon no Uta")
    # Key: C Major
    # ============================================================
    
    # Main melody notes (simplified but recognizable)
    # "Aa, Doraemon, Doraemon..." - 8 bars, 16 eighth notes per bar = 128 notes total
    # Using rhythm=1/8 (eighth notes), duration=8 bars
    melody_notes = [
        # Bar 1: "Aa, Do-ra-e-mon" (8 eighth notes)
        "C5", "E5", "G5", "C6", "G5", "E5", "C5", "rest",
        # Bar 2: "Do-ra-e-mon" (8 eighth notes)
        "C5", "E5", "G5", "C6", "G5", "E5", "C5", "rest",
        # Bar 3: "Na-ka-yo-shi" (8 eighth notes)
        "G4", "B4", "D5", "G5", "D5", "B4", "G4", "rest",
        # Bar 4: "Na-ka-yo-shi" (8 eighth notes)
        "G4", "B4", "D5", "G5", "D5", "B4", "G4", "rest",
        # Bar 5: "Do-ra-e-mon" (8 eighth notes)
        "C5", "E5", "G5", "C6", "G5", "E5", "C5", "rest",
        # Bar 6: "Do-ra-e-mon" (8 eighth notes)
        "C5", "E5", "G5", "C6", "G5", "E5", "C5", "rest",
        # Bar 7: "Yume wo ka-nae-te" (8 eighth notes)
        "E5", "G5", "A5", "G5", "E5", "D5", "C5", "rest",
        # Bar 8: "Do-ra-e-mon" (8 eighth notes)
        "C5", "E5", "G5", "C6", "G5", "E5", "C5", "rest",
    ]

    # Create main melody with a bright, playful synth sound
    # rhythm=1/8 means each note is an eighth note, duration=8 bars
    melody = m.sequence(
        melody_notes,
        "sine-tri",  # Bright, playful timbre
        rhythm=1/8,
        duration=8,  # 8 bars
        fade_in=1/32,
        fade_out=1/32,
        wt_pos=3,
    ).HPF(200).vol(0.7).pan("C")

    # ============================================================
    # BASS LINE - Simple walking bass
    # ============================================================
    bass_notes = [
        # Bar 1-2: C major
        "C2", "E2", "G2", "C3", "C2", "E2", "G2", "C3",
        # Bar 3-4: G major (V)
        "G1", "B1", "D2", "G2", "G1", "B1", "D2", "G2",
        # Bar 5-6: C major
        "C2", "E2", "G2", "C3", "C2", "E2", "G2", "C3",
        # Bar 7: F major (IV) -> G major (V)
        "F1", "A1", "C2", "F2", "G1", "B1", "D2", "G2",
        # Bar 8: C major
        "C2", "E2", "G2", "C3", "C2", "E2", "G2", "C3",
    ]
    
    bass = m.sequence(
        bass_notes,
        "sine",  # Clean sub bass
        rhythm=1/8,
        duration=8,
        fade_in=1/32,
        fade_out=1/32,
    ).LPF(120).vol(0.8)

    # ============================================================
    # CHORDS / PAD - Warm sustained chords
    # ============================================================
    # Bar 1-2: Cmaj7
    chord1 = m.chord("maj 7", "C3", "sine-tri", duration=2, wt_pos=555).HPF(150).vol(0.4)
    # Bar 3-4: G7 (dominant 7)
    chord2 = m.chord("dominant 7", "G3", "sine-tri", duration=2, wt_pos=555).HPF(150).vol(0.4)
    # Bar 5-6: Cmaj7
    chord3 = m.chord("maj 7", "C3", "sine-tri", duration=2, wt_pos=555).HPF(150).vol(0.4)
    # Bar 7: Fmaj7 -> G7
    chord4a = m.chord("maj 7", "F3", "sine-tri", duration=1, wt_pos=555).HPF(150).vol(0.4)
    chord4b = m.chord("dominant 7", "G3", "sine-tri", duration=1, wt_pos=555).HPF(150).vol(0.4)
    # Bar 8: Cmaj7
    chord5 = m.chord("maj 7", "C3", "sine-tri", duration=1, wt_pos=555).HPF(150).vol(0.4)

    pads = m.join_waves((chord1, chord2, chord3, chord4a, chord4b, chord5))

    # ============================================================
    # DRUMS - Simple beat using samples
    # ============================================================
    try:
        kick = m.sample("kick", "kick_06.wav").time_edit(1/16).vol(1.0)
        snare = m.sample("snare", "snare_04.wav").time_edit(1/16).vol(0.8)
        hat = m.sample("hihat", "hihat_02.wav").time_edit(1/16).vol(0.35).pan("R20")
        
        # 4/4 pattern: Kick on 1, 3; Snare on 2, 4; Hats on 8ths
        def make_drum_bar(m, kick, snare, hat):
            kick_pattern = [1, 0, 0, 0, 1, 0, 0, 0]  # 1 and 3
            snare_pattern = [0, 0, 0, 0, 1, 0, 0, 0]  # 3 (backbeat on 3 for half-time feel)
            hat_pattern = [1, 1, 1, 1, 1, 1, 1, 1]    # 8th notes
            
            def step_seq(m, wave, pattern, step):
                steps = []
                for hit in pattern:
                    steps.append(wave if hit else m.rest(step))
                return m.join_waves(tuple(steps))
            
            kick_bar = step_seq(m, kick, kick_pattern, 1/8)
            snare_bar = step_seq(m, snare, snare_pattern, 1/8)
            hat_bar = step_seq(m, hat, hat_pattern, 1/8)
            
            return m.add_waves((kick_bar, snare_bar, hat_bar))
        
        drum_bar = make_drum_bar(m, kick, snare, hat)
        drums = drum_bar.loop(8)
        
    except Exception as e:
        print(f"Samples not found, using synthesized drums: {e}")
        # Fallback: synthesized drums
        kick_synth = m.create_wave("C1", "sine", 1/8).vol(1.5).LPF(80).time_edit(1/16)
        snare_synth = m.create_wave("G2", "saw1", 1/8).vol(0.6).HPF(200).LPF(2000).time_edit(1/16)
        hat_synth = m.create_wave("C6", "sine", 1/16).vol(0.2).HPF(4000).time_edit(1/32)
        
        def make_drum_bar(m, kick, snare, hat):
            kick_pattern = [1, 0, 0, 0, 1, 0, 0, 0]
            snare_pattern = [0, 0, 0, 0, 1, 0, 0, 0]
            hat_pattern = [1, 1, 1, 1, 1, 1, 1, 1]
            
            def step_seq(m, wave, pattern, step):
                steps = []
                for hit in pattern:
                    steps.append(wave if hit else m.rest(step))
                return m.join_waves(tuple(steps))
            
            kick_bar = step_seq(m, kick, kick_pattern, 1/8)
            snare_bar = step_seq(m, snare, snare_pattern, 1/8)
            hat_bar = step_seq(m, hat, hat_pattern, 1/8)
            
            return m.add_waves((kick_bar, snare_bar, hat_bar))
        
        drum_bar = make_drum_bar(m, kick_synth, snare_synth, hat_synth)
        drums = drum_bar.loop(8)

    # ============================================================
    # ARPEGGIO - Sparkly high arpeggio for flavor
    # ============================================================
    arp1 = m.arpeggio("maj 7", "C5", "sine", rhythm=1/16, duration=2, wt_pos=1).HPF(800).vol(0.15).pan("L30")
    arp2 = m.arpeggio("dominant 7", "G5", "sine", rhythm=1/16, duration=2, wt_pos=1).HPF(800).vol(0.15).pan("R30")
    arp3 = m.arpeggio("maj 7", "C5", "sine", rhythm=1/16, duration=2, wt_pos=1).HPF(800).vol(0.15).pan("L30")
    arp4a = m.arpeggio("maj 7", "F5", "sine", rhythm=1/16, duration=1, wt_pos=1).HPF(800).vol(0.15).pan("R30")
    arp4b = m.arpeggio("dominant 7", "G5", "sine", rhythm=1/16, duration=1, wt_pos=1).HPF(800).vol(0.15).pan("L30")
    arp5 = m.arpeggio("maj 7", "C5", "sine", rhythm=1/16, duration=1, wt_pos=1).HPF(800).vol(0.15).pan("C")

    arpeggios = m.join_waves((arp1, arp2, arp3, arp4a, arp4b, arp5))

    # ============================================================
    # FINAL MIX
    # ============================================================
    # Structure: Intro (pads only) -> Verse (melody + bass + pads) -> Full (all) -> Outro
    # Create separate pad sections for intro and outro to avoid slicing issues
    intro_pads = m.join_waves((chord1,))  # First 2 bars (Cmaj7)
    
    verse = m.add_waves((melody, bass, pads, drums))
    
    full = m.add_waves((melody, bass, pads, drums, arpeggios))
    
    # Outro: Last 2 bars (Fmaj7 -> G7 -> Cmaj7) with fade out
    outro_pads = m.join_waves((chord4a, chord4b, chord5)).LPF(500).fade(fade_out=1)

    song = m.join_waves((intro_pads, verse, full, outro_pads))
    
    # Normalize and export
    song.vol(0.85).bounce("doraemon_theme.wav", show_visual=False)
    print("Doraemon theme rendered to export/doraemon_theme.wav")


if __name__ == "__main__":
    main()