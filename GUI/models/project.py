"""
MusicCode GUI — Project Data Models
Pydantic models for the internal representation of a MusicCode project.
Supports round-trip: GUI ↔ Model ↔ AST ↔ Python Code
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
import json


class WaveformType(str, Enum):
    """Supported waveform types for synthesis."""
    SINE = "sine"
    SQUARE = "square"
    SAW = "saw"
    SAW1 = "saw1"
    TRI = "tri"
    NOISE = "noise"


class ChordType(str, Enum):
    """Supported chord/arpeggio types."""
    MAJ = "maj"
    MIN = "min"
    MAJ7 = "maj7"
    MIN7 = "min7"
    DOM7 = "dom7"
    DIM7 = "dim7"
    MAJ9 = "maj9"
    MIN9 = "min9"
    MIN11 = "min11"
    DOM9 = "dom9"


class PanPosition(str, Enum):
    """Pan positions."""
    CENTER = "C"
    LEFT = "L"
    RIGHT = "R"
    LEFT_25 = "L25"
    LEFT_50 = "L50"
    RIGHT_25 = "R25"
    RIGHT_50 = "R50"


@dataclass
class SampleModel:
    """Represents a loaded sample with its parameters."""
    name: str                    # e.g., "kick", "snare", "hihat"
    index: int                   # Sample index in library
    time_edit: Optional[float] = None   # Duration (e.g., 1/8, 1/4)
    volume: float = 1.0          # Volume multiplier
    pan: Optional[PanPosition] = None   # Pan position
    # Raw AST node for round-trip preservation
    _ast_node: Any = field(default=None, repr=False, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "index": self.index,
            "time_edit": self.time_edit,
            "volume": self.volume,
            "pan": self.pan.value if self.pan else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SampleModel:
        pan = PanPosition(data["pan"]) if data.get("pan") else None
        return cls(
            name=data["name"],
            index=data["index"],
            time_edit=data.get("time_edit"),
            volume=data.get("volume", 1.0),
            pan=pan,
        )


@dataclass
class PatternStep:
    """A single step in a pattern grid."""
    sample: Optional[SampleModel] = None
    rest: Optional[float] = None   # Rest duration (e.g., 1/8, 1/4)
    # For complex steps: could be a joined wave expression
    expression: Optional[str] = None  # Raw code expression if not simple

    def is_rest(self) -> bool:
        return self.rest is not None and self.sample is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample": self.sample.to_dict() if self.sample else None,
            "rest": self.rest,
            "expression": self.expression,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternStep:
        sample = SampleModel.from_dict(data["sample"]) if data.get("sample") else None
        return cls(
            sample=sample,
            rest=data.get("rest"),
            expression=data.get("expression"),
        )


@dataclass
class PatternModel:
    """A rhythmic pattern — sequence of steps."""
    name: str
    steps: List[PatternStep] = field(default_factory=list)
    loop_count: int = 1
    resolution: float = 1/8  # Default step resolution (eighth note)
    operation: str = "join_waves"  # "join_waves" or "add_waves"
    # Raw AST for round-trip
    _ast_node: Any = field(default=None, repr=False, compare=False)

    def add_step(self, step: PatternStep) -> None:
        self.steps.append(step)

    def add_rest(self, duration: float) -> None:
        self.steps.append(PatternStep(rest=duration))

    def add_sample(self, sample: SampleModel, rest_after: float = 0) -> None:
        self.steps.append(PatternStep(sample=sample))
        if rest_after > 0:
            self.steps.append(PatternStep(rest=rest_after))

    def total_duration(self) -> float:
        """Calculate total duration in beats."""
        total = 0.0
        for step in self.steps:
            if step.sample and step.sample.time_edit:
                total += step.sample.time_edit
            elif step.rest:
                total += step.rest
        return total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "steps": [s.to_dict() for s in self.steps],
            "loop_count": self.loop_count,
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternModel:
        pattern = cls(
            name=data["name"],
            loop_count=data.get("loop_count", 1),
            resolution=data.get("resolution", 1/8),
        )
        pattern.steps = [PatternStep.from_dict(s) for s in data.get("steps", [])]
        return pattern


@dataclass
class TrackModel:
    """A track containing patterns and mix parameters."""
    name: str
    patterns: List[PatternModel] = field(default_factory=list)
    volume: float = 1.0
    pan: Optional[PanPosition] = None
    solo: bool = False
    mute: bool = False
    effects: List[Dict[str, Any]] = field(default_factory=list)  # e.g., [{"type": "LPF", "freq": 100}]
    # For joined wave expressions (mix01, mix02, etc.)
    join_expression: Optional[str] = None
    _ast_node: Any = field(default=None, repr=False, compare=False)

    def add_pattern(self, pattern: PatternModel) -> None:
        self.patterns.append(pattern)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "patterns": [p.to_dict() for p in self.patterns],
            "volume": self.volume,
            "pan": self.pan.value if self.pan else None,
            "solo": self.solo,
            "mute": self.mute,
            "effects": self.effects,
            "join_expression": self.join_expression,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackModel:
        track = cls(
            name=data["name"],
            volume=data.get("volume", 1.0),
            pan=PanPosition(data["pan"]) if data.get("pan") else None,
            solo=data.get("solo", False),
            mute=data.get("mute", False),
            effects=data.get("effects", []),
            join_expression=data.get("join_expression"),
        )
        track.patterns = [PatternModel.from_dict(p) for p in data.get("patterns", [])]
        return track


@dataclass
class MixModel:
    """Final mix configuration."""
    tracks: List[TrackModel] = field(default_factory=list)
    master_volume: float = 1.0
    master_effects: List[Dict[str, Any]] = field(default_factory=list)
    bounce_filename: str = "output.wav"
    show_visual: bool = False
    _ast_node: Any = field(default=None, repr=False, compare=False)

    def add_track(self, track: TrackModel) -> None:
        self.tracks.append(track)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracks": [t.to_dict() for t in self.tracks],
            "master_volume": self.master_volume,
            "master_effects": self.master_effects,
            "bounce_filename": self.bounce_filename,
            "show_visual": self.show_visual,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MixModel:
        mix = cls(
            master_volume=data.get("master_volume", 1.0),
            master_effects=data.get("master_effects", []),
            bounce_filename=data.get("bounce_filename", "output.wav"),
            show_visual=data.get("show_visual", False),
        )
        mix.tracks = [TrackModel.from_dict(t) for t in data.get("tracks", [])]
        return mix


@dataclass
class ProjectModel:
    """Root project model — contains everything."""
    name: str = "Untitled Project"
    tempo: int = 120
    samples: List[SampleModel] = field(default_factory=list)  # Library samples used
    tracks: List[TrackModel] = field(default_factory=list)
    mix: Optional[MixModel] = None
    # Metadata
    created: str = ""
    modified: str = ""
    version: str = "1.0"
    # Raw AST of the entire parsed file for perfect round-trip
    _ast_module: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self.mix is None:
            self.mix = MixModel()

    def add_track(self, track: TrackModel) -> None:
        self.tracks.append(track)
        self.mix.add_track(track)

    def get_sample(self, name: str, index: int) -> Optional[SampleModel]:
        for s in self.samples:
            if s.name == name and s.index == index:
                return s
        return None

    def register_sample(self, sample: SampleModel) -> SampleModel:
        """Register a sample in the library, return existing if duplicate."""
        existing = self.get_sample(sample.name, sample.index)
        if existing:
            return existing
        self.samples.append(sample)
        return sample

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tempo": self.tempo,
            "samples": [s.to_dict() for s in self.samples],
            "tracks": [t.to_dict() for t in self.tracks],
            "mix": self.mix.to_dict() if self.mix else None,
            "version": self.version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectModel:
        project = cls(
            name=data.get("name", "Untitled Project"),
            tempo=data.get("tempo", 120),
            version=data.get("version", "1.0"),
        )
        project.samples = [SampleModel.from_dict(s) for s in data.get("samples", [])]
        project.tracks = [TrackModel.from_dict(t) for t in data.get("tracks", [])]
        if data.get("mix"):
            project.mix = MixModel.from_dict(data["mix"])
        return project

    @classmethod
    def from_json(cls, json_str: str) -> ProjectModel:
        return cls.from_dict(json.loads(json_str))

    def save_project(self, filepath: str) -> None:
        """Save project as .mcproj (JSON)."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load_project(cls, filepath: str) -> ProjectModel:
        """Load project from .mcproj (JSON)."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())