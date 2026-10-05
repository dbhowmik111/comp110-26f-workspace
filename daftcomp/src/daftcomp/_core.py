"""Reference registration and immutable, integer-step compilation."""

from dataclasses import dataclass, replace
from threading import Lock, current_thread, main_thread
from uuid import uuid4

REST: int = -1
HOLD: int = -2
KICK: int = 36
SNARE: int = 38
HAT: int = 42


@dataclass(frozen=True)
class Event:
    pitch: int
    start_step: int
    duration_steps: int


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    voice: str
    source_group_id: str
    steps: tuple[int, ...]
    events: tuple[Event, ...]


@dataclass(frozen=True)
class SourceGroup:
    id: str
    track_ids: tuple[str, ...]


@dataclass(frozen=True)
class Song:
    schema_version: int
    session_id: str
    title: str
    bpm: int
    steps_per_beat: int
    song_steps: int
    source_groups: tuple[SourceGroup, ...]
    tracks: tuple[Track, ...]


@dataclass(frozen=True)
class Registration:
    name: str
    notes: list[int]
    voice: str


def text_value(value: object, label: str, limit: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text.")
    value = value.strip()
    if not value or len(value) > limit:
        raise ValueError(f"{label} must be nonblank and at most {limit} characters.")
    return value


def integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer, not {type(value).__name__}.")
    return value


def validate_launch(port: int, open_browser: bool) -> None:
    integer(port, "port")
    if port != 0 and not 1024 <= port <= 65535:
        raise ValueError("port must be 0 (automatic), or from 1024 through 65535.")
    if type(open_browser) is not bool:
        raise TypeError("open_browser must be True or False.")


def compile_steps(name: str, steps: tuple[int, ...], voice: str = "pulse") -> tuple[Event, ...]:
    if not steps:
        raise ValueError(f"{name}: the list is empty; add at least one step before run().")
    if len(steps) > 1024:
        raise ValueError(f"{name}: the list has {len(steps)} steps; the limit is 1024.")
    events: list[Event] = []
    active = False
    for index, value in enumerate(steps):
        prefix = f"{name}: notes[{index}]"
        if type(value) is not int:
            if voice == "drums":
                raise TypeError(f"{prefix} is {value!r}; use integer KICK, SNARE, HAT, or REST.")
            raise TypeError(f"{prefix} is {value!r}; use an integer pitch, REST, or HOLD.")
        if voice == "drums":
            if value not in (KICK, SNARE, HAT, REST):
                label = "HOLD" if value == HOLD else str(value)
                raise ValueError(f"{prefix} is {label}; use KICK, SNARE, HAT, or REST.")
            if value != REST:
                events.append(Event(value, index, 1))
            continue
        if value == REST:
            active = False
        elif value == HOLD:
            if not active:
                raise ValueError(f"{prefix} is HOLD, but there is no preceding note to continue.")
            events[-1] = replace(events[-1], duration_steps=events[-1].duration_steps + 1)
        elif 0 <= value <= 127:
            events.append(Event(value, index, 1))
            active = True
        else:
            raise ValueError(f"{prefix} is {value}; use a pitch from 0 to 127, REST, or HOLD.")
    return tuple(events)


class Registry:
    def __init__(self) -> None:
        self._tracks: list[Registration] = []
        self._lock = Lock()
        self._active = False

    def _require_idle(self) -> None:
        if self._active:
            raise RuntimeError("The player is running; stop it before changing registrations.")

    def add_track(self, *, name: str, notes: list[int], voice: str = "pulse") -> None:
        with self._lock:
            self._require_idle()
            name = text_value(name, "Track name", 80)
            if not isinstance(notes, list):
                raise TypeError(f"{name}: notes must be a Python list of integers.")
            if not isinstance(voice, str):
                raise TypeError("voice must be text.")
            if voice not in ("pulse", "triangle", "drums"):
                raise ValueError('voice must be "pulse", "triangle", or "drums".')
            if any(track.name == name for track in self._tracks):
                raise ValueError(f"Track name {name!r} is already registered; use a unique name.")
            if len(self._tracks) >= 8:
                raise ValueError("The limit is 8 tracks; clear registrations before adding more.")
            self._tracks.append(Registration(name, notes, voice))

    def clear(self) -> None:
        with self._lock:
            self._require_idle()
            self._tracks.clear()

    def begin_run(self) -> None:
        with self._lock:
            if current_thread() is not main_thread():
                raise RuntimeError("Call run() from the main thread.")
            self._require_idle()
            self._active = True

    def end_run(self) -> None:
        with self._lock:
            self._active = False

    def snapshot(self, *, title: str = "My Band", bpm: int = 120, steps_per_beat: int = 2) -> Song:
        title = text_value(title, "title", 120)
        integer(bpm, "bpm")
        integer(steps_per_beat, "steps_per_beat")
        if not 30 <= bpm <= 300:
            raise ValueError("bpm must be from 30 through 300.")
        if steps_per_beat not in (1, 2, 4):
            raise ValueError("steps_per_beat must be 1, 2, or 4.")
        with self._lock:
            if not self._tracks:
                raise ValueError("Add at least one track before run().")
            groups: dict[int, str] = {}
            group_tracks: dict[str, list[str]] = {}
            tracks: list[Track] = []
            for index, registration in enumerate(self._tracks, start=1):
                identity = id(registration.notes)
                if identity not in groups:
                    groups[identity] = f"list-{len(groups) + 1}"
                group_id = groups[identity]
                track_id = f"track-{index}"
                group_tracks.setdefault(group_id, []).append(track_id)
                steps = tuple(registration.notes)
                events = compile_steps(registration.name, steps, registration.voice)
                tracks.append(
                    Track(track_id, registration.name, registration.voice, group_id, steps, events)
                )
            song_steps = max(len(track.steps) for track in tracks)
            seconds = song_steps * 60 / bpm / steps_per_beat
            if seconds > 120:
                raise ValueError(
                    f"The song lasts {seconds:g} seconds; the current limit is 120 seconds."
                )
            return Song(
                1,
                uuid4().hex,
                title,
                bpm,
                steps_per_beat,
                song_steps,
                tuple(SourceGroup(key, tuple(ids)) for key, ids in group_tracks.items()),
                tuple(tracks),
            )
