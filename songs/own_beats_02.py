
# add scripts folder to path
import sys
# sys.path.insert(0, r'C:\Users\wesle\Desktop\repository\music-code-master\scripts')
# sys.path.insert(0, r'.\Script\CodeToMusic\Music-Code\core')
sys.path.insert(0, r'E:\WORK\PROJECT\git\PersonalAssistant\Script\CodeToMusic\Music-Code\core')


# import library
from music_code import MusicCode

# initialize
m = MusicCode(120)



# import libraries for graphing 
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
# %matplotlib inline

# helper function for graphing waveforms
def graph(waveform,title):
    # plt.style.use('seaborn-dark-palette')
    try:
        plt.style.use('seaborn-v0_8-dark-palette')
    except OSError:
        plt.style.use('default')
    fig, axs = plt.subplots(1,figsize=(700/96, 200/96), dpi=96)
    fig.suptitle(title)
    axs.plot(waveform, color='mediumblue')
    plt.show()





# # initialize
# m = music_code.MusicCode(120)

# mysql database
# m.connect()


# load samples
kick = m.sample('kick',0).time_edit(1/8)
snare = m.sample('snare',2).time_edit(1/8).vol(1)
# snare = m.sample('snare',2).time_edit(1/4).vol(2)
# hihat1 = m.sample('hihat',3).time_edit(1/8).pan('L25')
hihat1 = m.sample('hihat',3).time_edit(1/8)
# hihat2 = m.sample('hihat',1).time_edit(1/8) .pan('R25')
hihat2 = m.sample('hihat',1).time_edit(1/8)




# # create rhythmic patterns
kick = m.join_waves((kick, m.rest(1/4),kick, m.rest(1/8), kick, m.rest(1/4)))
snare1 = m.join_waves((m.rest(1/4), snare, m.rest(1/8), m.rest(1/4), snare, m.rest(1/8)))
snare2 = m.join_waves((m.rest(1/4), snare, m.rest(1/8), m.rest(1/4), snare, snare))
hihat1 = m.join_waves((m.rest(1/8), hihat1)).loop(4)
# hihat1 = m.join_waves((m.rest(1/8), hihat1)).loop(4)
hihat2 = m.join_waves((hihat2, m.rest(1/8))).loop(4)


# # drum mix
# drums = m.add_waves((kick, snare, hihat1, hihat2)).loop(4)


# sub = m.sequence(['E0'], 'sine', rhythm=1/8, duration=2, fade_in=1/8, fade_out=1/8).LPF(100).vol(3)
# bass1 = m.sequence(['E3'], 'square', rhythm=1/8, duration=2, fade_in=1/8, fade_out=1/8, in_curve=5, out_curve=3).vol(3.4)
# bass2 = m.sequence(['E2'], 'tri', rhythm=1/8, duration=2, fade_in=1/8, fade_out=1/8).vol(2)
# bass3 = m.sequence(['E1'], 'sine', rhythm=1/8, duration=2, fade_in=1/8, fade_out=1/8, wt_pos=9999).vol(2)

# bass = m.add_waves((sub, bass1, bass2, bass3)).loop(2)



# layer_1 = m.arpeggio('min 7', 'E2', 'sine', rhythm=1/36, duration=2).pan('L20')
# layer_2 = m.arpeggio('min 9', 'E3', 'square', rhythm=1/36, duration=2).pan('L50')
# layer_3 = m.arpeggio('min 11', 'E3', 'saw1', rhythm=1/36, duration=2).pan('R50')
# layer_4 = m.arpeggio('min 7', 'E2', 'tri', rhythm=1/36, duration=2).pan('R20')

# stack = m.add_waves((layer_1,layer_2,layer_3,layer_4)).loop(2).vol(.5)



# drum and bass

# mix = m.add_waves((drums, bass, stack))
# mix01 = m.add_waves((kick))
mix01 = m.add_waves((kick, snare1))
mix02 = m.add_waves((kick, snare2))
mix03 = m.add_waves((kick, snare2, hihat1))
mix04 = m.add_waves((kick, snare2, hihat1, hihat2))


mix = m.join_waves((kick.loop(2), mix01.loop(2), mix02.loop(2), mix03.loop(2), mix04.loop(4)))
mix.time()
# mix.reverse().bounce('sick mix reverse.wav')
# mix.loop(1).bounce('sick mix reverse.wav')
# mix.vol(0.85).bounce("own_beat_1.wav", show_visual=False)
# print("Done! Check export/own_beat_1.wav")
# snare.loop(1).bounce('sick mix reverse.wav')
# hihat2.bounce()
# mix04.bounce()



## Graphs
# graph(kick, 'kick')
# graph(snare1, 'snare1')
# graph(snare2, 'snare2')
# graph(hihat1, 'hihat1')
# graph(hihat2, 'hihat2')

## Times
kick.time()
snare1.time()
snare2.time()
hihat1.time()
hihat2.time()


## Output
mix.vol(0.85).bounce("own_beat_1.wav", show_visual=False)
print("Done! Check export/own_beat_1.wav")
