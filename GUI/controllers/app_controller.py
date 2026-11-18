"""
MusicCode GUI — Application Controller
Central controller coordinating models, views, and user interactions.
Implements undo/redo, project management, and high-level operations.
"""

from __future__ import annotations
from typing import Optional, List, Callable, Any
from dataclasses import dataclass, field
import copy
import os

from ..models.project import ProjectModel, TrackModel, PatternModel, SampleModel, MixModel
from ..models.code_gen import CodeGenerator
from ..parsers.musiccode_parser import parse_musiccode_file, parse_musiccode_source
from ..views.main_window import MainWindow


@dataclass
class Command:
    """Base class for undoable commands."""
    description: str
    
    def execute(self) -> None:
        raise NotImplementedError
    
    def undo(self) -> None:
        raise NotImplementedError


@dataclass
class AddSampleCommand(Command):
    project: ProjectModel
    sample: SampleModel
    
    def execute(self) -> None:
        self.project.register_sample(self.sample)
    
    def undo(self) -> None:
        if self.sample in self.project.samples:
            self.project.samples.remove(self.sample)


@dataclass
class RemoveSampleCommand(Command):
    project: ProjectModel
    sample: SampleModel
    index: int
    
    def execute(self) -> None:
        if self.sample in self.project.samples:
            self.index = self.project.samples.index(self.sample)
            self.project.samples.remove(self.sample)
    
    def undo(self) -> None:
        self.project.samples.insert(self.index, self.sample)


@dataclass
class AddTrackCommand(Command):
    project: ProjectModel
    track: TrackModel
    
    def execute(self) -> None:
        self.project.add_track(self.track)
    
    def undo(self) -> None:
        if self.track in self.project.tracks:
            self.project.tracks.remove(self.track)
            if self.track in self.project.mix.tracks:
                self.project.mix.tracks.remove(self.track)


@dataclass
class RemoveTrackCommand(Command):
    project: ProjectModel
    track: TrackModel
    index: int
    
    def execute(self) -> None:
        if self.track in self.project.tracks:
            self.index = self.project.tracks.index(self.track)
            self.project.tracks.remove(self.track)
            if self.track in self.project.mix.tracks:
                self.project.mix.tracks.remove(self.track)
    
    def undo(self) -> None:
        self.project.tracks.insert(self.index, self.track)
        self.project.mix.tracks.insert(self.index, self.track)


@dataclass
class SetPropertyCommand(Command):
    target: Any
    attr: str
    old_value: Any
    new_value: Any
    
    def execute(self) -> None:
        setattr(self.target, self.attr, self.new_value)
    
    def undo(self) -> None:
        setattr(self.target, self.attr, self.old_value)


class CommandHistory:
    """Manages undo/redo command history."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
    
    def execute(self, command: Command) -> None:
        command.execute()
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    
    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True
    
    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()


class AppController:
    """
    Central application controller.
    Coordinates between Model (ProjectModel), View (MainWindow), and Commands.
    """
    
    def __init__(self, view: MainWindow):
        self.view = view
        self.project: ProjectModel = ProjectModel()
        self.history = CommandHistory()
        self.current_file: Optional[str] = None
        self.modified: bool = False
        
        # Connect view callbacks
        self.view.on_project_changed = self._on_project_changed
    
    # ============================================================
    # PROJECT MANAGEMENT
    # ============================================================
    
    def new_project(self, name: str = "Untitled Project", tempo: int = 120) -> None:
        """Create a new project."""
        self.project = ProjectModel(name=name, tempo=tempo)
        self.current_file = None
        self.modified = False
        self.history.clear()
        self._refresh_view()
    
    def load_project(self, filepath: str) -> bool:
        """Load project from .mcproj file."""
        try:
            self.project = ProjectModel.load_project(filepath)
            self.current_file = filepath
            self.modified = False
            self.history.clear()
            self._refresh_view()
            return True
        except Exception as e:
            self.view._set_status(f"Load failed: {e}")
            return False
    
    def save_project(self, filepath: Optional[str] = None) -> bool:
        """Save project to .mcproj file."""
        if filepath:
            self.current_file = filepath
        elif not self.current_file:
            return False
        
        try:
            self.project.save_project(self.current_file)
            self.modified = False
            self.view._set_status(f"Saved: {os.path.basename(self.current_file)}")
            return True
        except Exception as e:
            self.view._set_status(f"Save failed: {e}")
            return False
    
    def import_python(self, filepath: str) -> bool:
        """Import MusicCode Python script."""
        try:
            self.project = parse_musiccode_file(filepath)
            self.current_file = None  # Not a project file
            self.modified = True
            self.history.clear()
            self._refresh_view()
            return True
        except Exception as e:
            self.view._set_status(f"Import failed: {e}")
            return False
    
    def export_python(self, filepath: str) -> bool:
        """Export project as MusicCode Python script."""
        try:
            generator = CodeGenerator(self.project)
            generator.save_to_file(filepath)
            self.view._set_status(f"Exported: {os.path.basename(filepath)}")
            return True
        except Exception as e:
            self.view._set_status(f"Export failed: {e}")
            return False
    
    # ============================================================
    # SAMPLE OPERATIONS
    # ============================================================
    
    def add_sample(self, name: str, index: int, time_edit: float = 1/8, 
                   volume: float = 1.0, pan: Optional[str] = None) -> SampleModel:
        """Add a sample to the project."""
        from ..models.project import SampleModel, PanPosition
        
        pan_enum = PanPosition(pan) if pan else None
        sample = SampleModel(name=name, index=index, time_edit=time_edit, 
                           volume=volume, pan=pan_enum)
        
        command = AddSampleCommand(
            description=f"Add sample {name}[{index}]",
            project=self.project,
            sample=sample
        )
        self.history.execute(command)
        self.modified = True
        self._refresh_view()
        return sample
    
    def remove_sample(self, sample: SampleModel) -> None:
        """Remove a sample from the project."""
        command = RemoveSampleCommand(
            description=f"Remove sample {sample.name}[{sample.index}]",
            project=self.project,
            sample=sample,
            index=-1
        )
        self.history.execute(command)
        self.modified = True
        self._refresh_view()
    
    # ============================================================
    # TRACK OPERATIONS
    # ============================================================
    
    def add_track(self, name: str) -> TrackModel:
        """Add a new track to the project."""
        track = TrackModel(name=name)
        
        command = AddTrackCommand(
            description=f"Add track {name}",
            project=self.project,
            track=track
        )
        self.history.execute(command)
        self.modified = True
        self._refresh_view()
        return track
    
    def remove_track(self, track: TrackModel) -> None:
        """Remove a track from the project."""
        command = RemoveTrackCommand(
            description=f"Remove track {track.name}",
            project=self.project,
            track=track,
            index=-1
        )
        self.history.execute(command)
        self.modified = True
        self._refresh_view()
    
    def set_track_volume(self, track: TrackModel, volume: float) -> None:
        """Set track volume with undo support."""
        command = SetPropertyCommand(
            description=f"Set {track.name} volume to {volume}",
            target=track,
            attr="volume",
            old_value=track.volume,
            new_value=volume
        )
        self.history.execute(command)
        self.modified = True
    
    def set_track_pan(self, track: TrackModel, pan: str) -> None:
        """Set track pan with undo support."""
        from ..models.project import PanPosition
        try:
            pan_enum = PanPosition(pan)
            command = SetPropertyCommand(
                description=f"Set {track.name} pan to {pan}",
                target=track,
                attr="pan",
                old_value=track.pan,
                new_value=pan_enum
            )
            self.history.execute(command)
            self.modified = True
        except ValueError:
            pass
    
    def toggle_track_solo(self, track: TrackModel) -> None:
        """Toggle track solo."""
        command = SetPropertyCommand(
            description=f"Toggle {track.name} solo",
            target=track,
            attr="solo",
            old_value=track.solo,
            new_value=not track.solo
        )
        self.history.execute(command)
        self.modified = True
    
    def toggle_track_mute(self, track: TrackModel) -> None:
        """Toggle track mute."""
        command = SetPropertyCommand(
            description=f"Toggle {track.name} mute",
            target=track,
            attr="mute",
            old_value=track.mute,
            new_value=not track.mute
        )
        self.history.execute(command)
        self.modified = True
    
    # ============================================================
    # PATTERN OPERATIONS
    # ============================================================
    
    def add_pattern(self, track: TrackModel, name: str, steps: int = 16, 
                    resolution: float = 1/8) -> PatternModel:
        """Add a pattern to a track."""
        pattern = PatternModel(name=name, resolution=resolution)
        # Initialize with rest steps
        for _ in range(steps):
            pattern.add_rest(resolution)
        
        track.add_pattern(pattern)
        self.modified = True
        self._refresh_view()
        return pattern
    
    def set_pattern_step(self, pattern: PatternModel, step_index: int, 
                         sample: Optional[SampleModel] = None, 
                         rest: Optional[float] = None) -> None:
        """Set a specific step in a pattern."""
        if 0 <= step_index < len(pattern.steps):
            old_step = copy.copy(pattern.steps[step_index])
            new_step = PatternStep(sample=sample, rest=rest)
            pattern.steps[step_index] = new_step
            self.modified = True
            self._refresh_view()
    
    def set_pattern_loop(self, pattern: PatternModel, loop_count: int) -> None:
        """Set pattern loop count."""
        if pattern.loop_count != loop_count:
            command = SetPropertyCommand(
                description=f"Set {pattern.name} loop to {loop_count}",
                target=pattern,
                attr="loop_count",
                old_value=pattern.loop_count,
                new_value=loop_count
            )
            self.history.execute(command)
            self.modified = True
    
    # ============================================================
    # MASTER / MIX OPERATIONS
    # ============================================================
    
    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        command = SetPropertyCommand(
            description=f"Set master volume to {volume}",
            target=self.project.mix,
            attr="master_volume",
            old_value=self.project.mix.master_volume,
            new_value=volume
        )
        self.history.execute(command)
        self.modified = True
    
    def set_tempo(self, tempo: int) -> None:
        """Set project tempo."""
        if self.project.tempo != tempo:
            command = SetPropertyCommand(
                description=f"Set tempo to {tempo}",
                target=self.project,
                attr="tempo",
                old_value=self.project.tempo,
                new_value=tempo
            )
            self.history.execute(command)
            self.modified = True
    
    def set_bounce_filename(self, filename: str) -> None:
        """Set bounce output filename."""
        self.project.mix.bounce_filename = filename
        self.modified = True
    
    # ============================================================
    # UNDO / REDO
    # ============================================================
    
    def undo(self) -> bool:
        """Undo last command."""
        result = self.history.undo()
        if result:
            self.modified = True
            self._refresh_view()
        return result
    
    def redo(self) -> bool:
        """Redo last undone command."""
        result = self.history.redo()
        if result:
            self.modified = True
            self._refresh_view()
        return result
    
    def can_undo(self) -> bool:
        return self.history.can_undo()
    
    def can_redo(self) -> bool:
        return self.history.can_redo()
    
    # ============================================================
    # CODE GENERATION / VALIDATION
    # ============================================================
    
    def generate_code(self) -> str:
        """Generate Python code from current project."""
        generator = CodeGenerator(self.project)
        return generator.generate()
    
    def validate_code(self) -> tuple[bool, str]:
        """Validate generated code syntax."""
        try:
            code = self.generate_code()
            ast.parse(code)
            return True, "Code is valid"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def bounce_audio(self) -> tuple[bool, str]:
        """Generate code and run it to produce audio."""
        import tempfile
        import subprocess
        import sys
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                generator = CodeGenerator(self.project)
                generator.save_to_file(f.name)
                temp_path = f.name
            
            result = subprocess.run([sys.executable, temp_path], 
                                  capture_output=True, text=True, timeout=60,
                                  cwd=os.path.dirname(temp_path))
            
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    # ============================================================
    # INTERNAL
    # ============================================================
    
    def _refresh_view(self) -> None:
        """Refresh the view from current project state."""
        if hasattr(self.view, '_refresh_ui'):
            self.view._refresh_ui()
    
    def _on_project_changed(self) -> None:
        """Callback when project changes in view."""
        self.modified = True


# For direct use in main_window
def create_controller(view: MainWindow) -> AppController:
    """Factory function to create and connect controller."""
    controller = AppController(view)
    return controller