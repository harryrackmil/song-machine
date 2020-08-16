import math

import numpy as np

from music.constants import RATE


def parse_fixed_format_1(notes_str, step_size):
    offset = 0
    lines = notes_str.splitlines()
    all_notes = []
    for line in lines:
        line = line.rstrip()
        if line == "":
            continue
        if line == "-":
            all_notes.append(Note("r", step_size, offset))
            offset += step_size
            continue
        length = 1
        if "(" in line:
            length = int(line[line.find('x') + 1:])
            line = line[line.find('(') + 1:line.find(')')]
        note_strings = line.split(',')
        for note_string in note_strings:
            if len(note_string) == 1:
                all_notes.append(Note(note_string, length=length * step_size, offset=offset))
            elif len(note_string) == 2:
                all_notes.append(Note(note_string[0], octave=int(note_string[1]), length=length * step_size, offset=offset))
            elif len(note_string) > 2:
                raise ValueError("Received Badly Formatted Note: {}".format(len(note_string)))
        offset += step_size * length
    return all_notes


class Note(object):
    def __init__(self, note, length=1, offset=0, octave=4):
        super(Note, self).__init__()
        self.note = note
        self.octave = octave
        self.offset = offset
        self.length = length


class Track(object):
    def __init__(self, notes, loops=1.0):
        self.track_length = int(math.ceil(max([note.length + note.offset for note in notes]) * RATE))
        self.notes = notes
        self.loops = loops

    @classmethod
    def from_fixed_beat(cls, notes_string, step_size=0.25, loops=1.0):
        return cls(notes=parse_fixed_format_1(notes_string, step_size=step_size), loops=loops)

    def visualize(self, step_size=0.25):
        empty = np.zeros(int(self.track_length / (RATE * step_size)))
        # for note in notes:
        #     start_space = int(note.offset / step_size)
        #     end_space = start_space + length / step_size
        #     empty[:


class TrackWithMetadata(object):
    def __init__(self, track, instrument, offset=0.0, level=1.0, pan=0.0):
        self.track = track
        self.instrument = instrument
        self.offset = offset
        self.level = level
        self.pan = pan



