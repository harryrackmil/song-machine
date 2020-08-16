import os

import wavio
import yaml
import numpy as np
from playsound import playsound

from music.constants import RATE
from music.instruments import instrument
from music.song.track import Note, TrackWithMetadata, Track


def get_panned_levels(pan):
    pan_max = 10.0
    right_pan = float(pan + pan_max) / (pan_max * 2)
    left_pan = 1.0 - right_pan
    return left_pan, right_pan


class Song(object):
    def __init__(self, tracks_with_metadata, loops=1.0):
        self.tracks_with_metadata = tracks_with_metadata
        self.length = max([
            int(
                track_with_metadata.track.loops * track_with_metadata.track.track_length
                + track_with_metadata.offset * RATE
            )
            for track_with_metadata
            in tracks_with_metadata
        ])
        self.loops = loops

    def get_data(self):
        song_data_left = np.zeros(self.length)
        song_data_right = np.zeros(self.length)
        for track_with_metadata in self.tracks_with_metadata:
            track_in_context = np.zeros(self.length)
            instrument = track_with_metadata.instrument
            track = track_with_metadata.track
            track_data = instrument.get_track(track) * track_with_metadata.level
            offset_steps = int(track_with_metadata.offset * RATE)
            track_in_context[offset_steps:int(offset_steps + track.track_length * track.loops)] = track_data

            left_pan, right_pan = get_panned_levels(track_with_metadata.pan)
            song_data_left += track_in_context * left_pan
            song_data_right += track_in_context * right_pan

        song_data = np.array([[left, right] for left, right in zip(song_data_left, song_data_right)])
        return np.tile(song_data, self.loops)

    def play(self):
        tmp_file = "tmp.wav"
        self.save(tmp_file)
        playsound(tmp_file)
        os.remove(tmp_file)

    def save(self, path):
        x = self.get_data()
        wavio.write(path, x, RATE, sampwidth=2)

    @classmethod
    def from_yaml(cls, yaml_path):
        song_config = yaml.safe_load(open(yaml_path, 'r'))
        bpm = song_config["bpm"]
        granularity = song_config["granularity"]
        tracks = song_config["tracks"]

        loops = 1.0
        if "loops" in song_config.keys():
            loops = song_config["loops"]

        tracks_with_metadata = []
        for track in tracks:
            instrument_args = track["instrument"]
            instrument_name = instrument_args.pop("name")
            instrument_obj_type = getattr(instrument, instrument_name)
            instrument_obj = instrument_obj_type(**instrument_args)

            pan = 0.0
            if "pan" in track.keys():
                pan = track["pan"]

            track_loops = 1.0
            if "loops" in track.keys():
                track_loops = track["loops"]

            level = 1.0
            if "level" in track.keys():
                level = float(track["level"])

            offset = 0.0
            if "offset" in track.keys():
                offset = float(track["offset"])

            if "file" in track.keys():
                notes_string = open(track["file"], 'r').read()
            elif "notes" in track.keys():
                notes_string = track["notes"]
            else:
                raise ValueError("No notes supplied in track!")

            tracks_with_metadata.append(
                TrackWithMetadata(
                    track=Track.from_fixed_beat(notes_string, granularity * 60.0 / bpm, track_loops),
                    instrument=instrument_obj,
                    level=level,
                    offset=offset,
                    pan=pan
                )
            )
        return cls(tracks_with_metadata, loops)
