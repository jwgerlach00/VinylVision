from typing import List
from src.discogs.model.models import Track

class Vinyl:
    R_OUTER = 5.75  # inches, start of grooves
    R_INNER = 2.5  # inches, end of grooves
    R_GROOVE_RANGE = R_OUTER - R_INNER  # inches, total usable groove space

    def __init__(self, tracks: List[Track], starting_side: str):
        self.tracks: List[Track] = tracks
        self.current_side = starting_side
        self.current_track_pos: str = tracks[0].position[1]
        self.tracks_on_side = self.get_tracks_on_side(starting_side)
        self.total_len_of_side = self.get_total_len_of_side(starting_side)

    def set_current_track_pos(self, pos: str):
        self.current_track_pos = pos

    def get_tracks_on_side(self, side: str):
        return [track for track in self.tracks if track.position[0] == side]
    
    def get_total_len_of_side(self, side: str):
        track_seconds = [Vinyl.duration_to_seconds(track.duration) for track in self.get_tracks_on_side(side)]
        return sum(track_seconds)

    # @staticmethod
    # def map_vinyl(tracks: List[Track]):
    #     vinyl = {}
    #     for track in tracks:
    #         if track.position not in vinyl:
    #             vinyl[track.position] = seconds_to_revolutions(duration_to_seconds(track.duration))
    #     return vinyl
    
    @staticmethod
    def duration_to_seconds(duration: str):
        minutes, seconds = duration.split(":")
        return (int(minutes) * 60) + int(seconds)

    # def seconds_to_revolutions(seconds: int):
    #     rpm = (100 / 3)
    #     rps = rpm / 60
    #     return seconds / rps