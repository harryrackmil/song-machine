import random

import numpy as np
from playsound import playsound
import wavio

from music.constants import NOTE_TO_FREQ, RATE


def sin(freq, length):
    T = length  # sample duration (seconds)
    f = float(freq)  # sound frequency (Hz)
    t = np.linspace(0, T, T * RATE, endpoint=False)
    x = np.sin(2 * np.pi * f * t)
    return x


def sawtooth(freq, length):
    p = 1.0 / freq  # period
    T = length  # sample duration (seconds)
    t = np.linspace(0, T, T * RATE, endpoint=False)
    x = -2.0 / np.pi * np.arctan(1.0 / np.tan((t * np.pi / p)))
    return x


def triangle(freq, length):
    x = sawtooth(freq, length)
    return np.abs(x) - 0.5

def get_freq(note, octave):
    note_4 = NOTE_TO_FREQ[note]
    freq = note_4 * (2 ** (octave - 4))
    return freq


def half_step_up(note, octave):
    notes = NOTE_TO_FREQ.keys()
    for idx in range(len(notes)):
        if notes[idx] == note:
            if idx + 1 < len(notes):
                return (notes[idx + 1], octave)
            else:
                return (notes[0], octave + 1)
    raise ValueError("Invalid Note!")


def n_steps_up(note, octave, steps):
    new_note = note
    new_octave = octave
    for _ in range(int(steps * 2)):
        new_note, new_octave = half_step_up(new_note, new_octave)

    return new_note, new_octave


class Instrument(object):
    def __init__(
        self,
        attack=0.0,
        decay=0.0,
        sustain=1.0,
        release=0.0
    ):
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

    def get_voice(self, freq, length):
        raise NotImplementedError()

    def envelope(self, x):
        volume_vec = np.zeros(len(x))

        attack_steps = int(self.attack * RATE)
        decay_steps = int(self.decay * RATE)
        release_steps = int(self.release * RATE)

        volume_vec[:attack_steps] = np.linspace(0, 1.0, attack_steps, endpoint=False)

        volume_vec[attack_steps:attack_steps + decay_steps] = np.linspace(1.0, self.sustain, decay_steps, endpoint=False)

        volume_vec[attack_steps + decay_steps:] = self.sustain
        if release_steps > 0:
            volume_vec[-release_steps:] =  np.linspace(self.sustain, 0, release_steps, endpoint=False)

        return x * volume_vec

    def get_enveloped_voice(self, freq, length):
        return self.envelope(self.get_voice(freq, length))

    def tone(self, freq, length):
        voice = self.get_voice(freq, length)
        return self._play(voice)

    def _play(self, x):
        wavio.write("tmp.wav", x, RATE, sampwidth=2)
        playsound("tmp.wav")

    def note(self, note, length, octave=4):
        self.tone(
            freq=get_freq(note, octave),
            length=length
        )

    def _chord(self, root_note, length, step_list, octave=4):
        notes = [n_steps_up(root_note, octave, step) for step in step_list]

        freqs = [get_freq(note, octv) for note, octv in notes]
        voices = [self.get_voice(freq, length) for freq in freqs]

        self._play(sum(voices))

    def major_triad(self, root_note, length, octave=4):
        self._chord(root_note, length, [0, 2, 3.5], octave=octave)

    def minor_triad(self, root_note, length, octave=4):
        self._chord(root_note, length, [0, 1.5, 3.5], octave=octave)

    def seventh_chord(self, root_note, length, octave=4):
        self._chord(root_note, length, [0, 2, 3.5, 5], octave=octave)

    def get_track(self, track):
        base_track = np.zeros(shape=track.track_length)
        for note in track.notes:
            if note.note == 'r':
                continue
            freq = get_freq(note.note, note.octave)
            voice = self.get_enveloped_voice(freq=freq, length=note.length)
            in_context_voice = np.zeros(track.track_length)
            offset_steps = int(note.offset * RATE)
            in_context_voice[offset_steps:offset_steps + len(voice)] = voice
            base_track = base_track + in_context_voice

        full_rotations = int(track.loops)
        partial_rotation = track.loops % 1
        return np.append(np.tile(base_track, full_rotations), base_track[:int(partial_rotation * len(base_track))])

    def play_track(self, track):
        self._play(self.get_track(track))


class SinMachine(Instrument):
    def get_voice(self, freq, length):
        return sin(freq, length)


class DetunedSinMachine(Instrument):
    def get_voice(self, freq, length):
        return sin(freq=freq, length=length) + sin(freq=freq + 1, length=length)


class SawTooth(Instrument):
    def get_voice(self, freq, length):
        return sawtooth(freq, length)


class TriangleWave(Instrument):
    def get_voice(self, freq, length):
        return triangle(freq, length)


class UniformNoise(Instrument):
    def get_voice(self, freq, length):
        return np.random.rand(int(length * RATE))


class Bell(TriangleWave):
    def __init__(self, attack=0.0, decay=0.1, sustain=0, release=0.0):
        super(TriangleWave, self).__init__(attack, decay, sustain, release)


class Crash(UniformNoise):
    def __init__(self, attack=0.0, decay=0.125, sustain=0.0, release=0.0):
        super(Crash, self).__init__(attack, decay, sustain, release)


class ManyRands(Instrument):
    def __init__(self, n_rands=100, attack=0.0, decay=0.125, sustain=0, release=0.0):
        super(ManyRands, self).__init__(attack, decay, sustain, release)
        self.n_rands = n_rands

    def get_voice(self, freq, length):
        x = np.zeros(int(length * RATE))
        for _ in range(self.n_rands):
            x += sin(random.randrange(220, 1760), length)
        return x
