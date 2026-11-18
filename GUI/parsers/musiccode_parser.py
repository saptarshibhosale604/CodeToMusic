"""
MusicCode GUI — MusicCode AST Parser
Parses MusicCode Python scripts into ProjectModel using AST analysis.
Handles the MusicCode DSL: m.sample, m.join_waves, m.add_waves, m.sequence, 
m.arpeggio, .loop(), .vol(), .pan(), .LPF(), .bounce(), etc.
"""

from __future__ import annotations
import ast
import re
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field

from ..models.project import (
    ProjectModel, TrackModel, PatternModel, SampleModel, MixModel,
    PatternStep, WaveformType, ChordType, PanPosition
)


@dataclass
class ParseContext:
    """Context during parsing - tracks variable assignments and state."""
    project: ProjectModel
    sample_vars: Dict[str, SampleModel] = field(default_factory=dict)  # var_name -> SampleModel
    pattern_vars: Dict[str, PatternModel] = field(default_factory=dict)  # var_name -> PatternModel
    track_vars: Dict[str, TrackModel] = field(default_factory=dict)  # var_name -> TrackModel
    current_track: Optional[TrackModel] = None
    tempo: int = 120
    bounce_filename: str = "output.wav"
    show_visual: bool = False
    master_volume: float = 1.0
    master_effects: List[Dict[str, Any]] = field(default_factory=list)


class MusicCodeParser(ast.NodeVisitor):
    """
    AST Visitor that extracts MusicCode constructs from Python source.
    Builds a ProjectModel representing the musical structure.
    """
    
    def __init__(self):
        self.context = ParseContext(project=ProjectModel())
        self._errors: List[str] = []
    
    def parse(self, source: str) -> ProjectModel:
        """Parse source code and return ProjectModel."""
        tree = ast.parse(source)
        self.visit(tree)
        self._build_track_structure()
        return self.context.project
    
    def _build_track_structure(self) -> None:
        """Infer track structure from parsed patterns."""
        # If no tracks exist but we have patterns, create inferred tracks
        if not self.context.project.tracks and self.context.pattern_vars:
            # Group patterns by sample type / role
            track_groups = {
                "Kick": [],
                "Snare": [],
                "Hihat": [],
                "Percussion": [],
                "Bass": [],
                "Synth": [],
                "Mix": [],
            }
            
            for var_name, pattern in self.context.pattern_vars.items():
                # Determine track group from pattern name / content
                name_lower = var_name.lower()
                if 'kick' in name_lower:
                    track_groups["Kick"].append(pattern)
                elif 'snare' in name_lower:
                    track_groups["Snare"].append(pattern)
                elif 'hihat' in name_lower or 'hat' in name_lower:
                    track_groups["Hihat"].append(pattern)
                elif 'mix' in name_lower and var_name != 'mix':
                    track_groups["Mix"].append(pattern)
                elif 'mix' == name_lower:
                    track_groups["Mix"].append(pattern)
                elif any(kw in name_lower for kw in ['bass', 'sub', 'lead', 'arp', 'pad', 'chord']):
                    track_groups["Synth"].append(pattern)
                else:
                    track_groups["Percussion"].append(pattern)
            
            # Create tracks for non-empty groups
            for track_name, patterns in track_groups.items():
                if patterns:
                    track = TrackModel(name=track_name)
                    for pattern in patterns:
                        track.add_pattern(pattern)
                    self.context.project.add_track(track)
    
    def parse_file(self, filepath: str) -> ProjectModel:
        """Parse a Python file and return ProjectModel."""
        with open(filepath, 'r') as f:
            source = f.read()
        return self.parse(source)
    
    @property
    def errors(self) -> List[str]:
        return self._errors
    
    def _add_error(self, msg: str, node: ast.AST = None) -> None:
        lineno = getattr(node, 'lineno', '?')
        self._errors.append(f"Line {lineno}: {msg}")
    
    # ============================================================
    # VISITOR METHODS
    # ============================================================
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Handle variable assignments: var = m.sample(...), var = m.join_waves(...), etc."""
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            self.generic_visit(node)
            return
        
        var_name = node.targets[0].id
        value = node.value
        
        # Detect what kind of assignment this is
        if self._is_sample_call(value):
            # Get the base sample call from the chain
            base_call = self._get_base_sample_call(value)
            if base_call:
                sample = self._parse_sample_call(value, var_name)  # Parse full chain
                if sample:
                    self.context.sample_vars[var_name] = sample
                    self.context.project.register_sample(sample)
        
        elif self._is_join_waves_call(value) or self._is_add_waves_call(value):
            # Get the base call
            base_call = self._get_base_join_waves_call(value) or self._get_base_add_waves_call(value)
            if base_call:
                # Temporarily remove var_name from pattern_vars to avoid self-reference
                # when the RHS references the same variable name (e.g., kick = m.join_waves((kick, ...)))
                was_in_pattern_vars = var_name in self.context.pattern_vars
                old_pattern = self.context.pattern_vars.pop(var_name, None)
                
                pattern = self._parse_wave_combination(base_call, var_name)
                
                # Restore if it was there
                if was_in_pattern_vars and old_pattern:
                    self.context.pattern_vars[var_name] = old_pattern
                
                if pattern:
                    # Check for .loop() on the full chain
                    current = value
                    while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
                        if current.func.attr == 'loop' and current.args:
                            pattern.loop_count = self._get_constant_value(current.args[0]) or 1
                        current = current.func.value
                    
                    self.context.pattern_vars[var_name] = pattern
                    if self.context.current_track:
                        self.context.current_track.add_pattern(pattern)
        
        elif self._is_sequence_call(value) or self._is_arpeggio_call(value):
            # Get the base call
            base_call = self._get_base_sequence_call(value) or self._get_base_arpeggio_call(value)
            if base_call:
                # Same self-reference handling
                was_in_pattern_vars = var_name in self.context.pattern_vars
                old_pattern = self.context.pattern_vars.pop(var_name, None)
                
                pattern = self._parse_synthesis_call(base_call, var_name)
                
                if was_in_pattern_vars and old_pattern:
                    self.context.pattern_vars[var_name] = old_pattern
                
                if pattern:
                    # Check for .loop() on the full chain
                    current = value
                    while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
                        if current.func.attr == 'loop' and current.args:
                            pattern.loop_count = self._get_constant_value(current.args[0]) or 1
                        current = current.func.value
                    
                    self.context.pattern_vars[var_name] = pattern
                    if self.context.current_track:
                        self.context.current_track.add_pattern(pattern)
        
        elif self._is_loop_call(value):
            # var = something.loop(n) - update the pattern's loop count
            self._handle_loop_assignment(var_name, value)
        
        elif self._is_effect_chain(value):
            # var = something.vol(x).pan(y).LPF(z) - track effects
            self._handle_effect_chain(var_name, value)
        
        self.generic_visit(node)
    
    def visit_Expr(self, node: ast.Expr) -> None:
        """Handle expression statements: bounce(), print(), etc."""
        if isinstance(node.value, ast.Call):
            if self._is_bounce_call(node.value):
                self._parse_bounce_call(node.value)
            elif self._is_time_call(node.value):
                # .time() calls - ignore for now
                pass
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Handle direct calls not in assignments."""
        # Check for m = MusicCode(120)
        if (isinstance(node.func, ast.Name) and node.func.id == 'MusicCode' 
            and node.args and isinstance(node.args[0], ast.Constant)):
            self.context.tempo = node.args[0].value
            self.context.project.tempo = node.args[0].value
        
        self.generic_visit(node)
    
    # ============================================================
    # DETECTION HELPERS
    # ============================================================
    
    def _is_sample_call(self, node: ast.AST) -> bool:
        """Check if node is m.sample(...) or m.sample(...).time_edit(...).vol(...).pan(...)
        Returns True for the BASE call (m.sample) anywhere in the chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'sample'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return True
            current = current.func.value
        return False
    
    def _get_base_sample_call(self, node: ast.AST) -> Optional[ast.Call]:
        """Extract the base m.sample(...) call from a chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'sample'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return current
            current = current.func.value
        return None
    
    def _is_join_waves_call(self, node: ast.AST) -> bool:
        """Check if node is m.join_waves(...) or chained from it"""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'join_waves'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return True
            current = current.func.value
        return False
    
    def _is_add_waves_call(self, node: ast.AST) -> bool:
        """Check if node is m.add_waves(...) or chained from it"""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'add_waves'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return True
            current = current.func.value
        return False
    
    def _get_base_join_waves_call(self, node: ast.AST) -> Optional[ast.Call]:
        """Extract the base m.join_waves(...) call from a chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'join_waves'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return current
            current = current.func.value
        return None
    
    def _get_base_add_waves_call(self, node: ast.AST) -> Optional[ast.Call]:
        """Extract the base m.add_waves(...) call from a chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'add_waves'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return current
            current = current.func.value
        return None
    
    def _is_sequence_call(self, node: ast.AST) -> bool:
        """Check if node is m.sequence(...) or chained from it"""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'sequence'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return True
            current = current.func.value
        return False
    
    def _is_arpeggio_call(self, node: ast.AST) -> bool:
        """Check if node is m.arpeggio(...) or chained from it"""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'arpeggio'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return True
            current = current.func.value
        return False
    
    def _get_base_sequence_call(self, node: ast.AST) -> Optional[ast.Call]:
        """Extract the base m.sequence(...) call from a chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'sequence'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return current
            current = current.func.value
        return None
    
    def _get_base_arpeggio_call(self, node: ast.AST) -> Optional[ast.Call]:
        """Extract the base m.arpeggio(...) call from a chain."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if (current.func.attr == 'arpeggio'
                and isinstance(current.func.value, ast.Name)
                and current.func.value.id == 'm'):
                return current
            current = current.func.value
        return None
    
    def _is_loop_call(self, node: ast.AST) -> bool:
        """Check if node is something.loop(...)"""
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'loop')
    
    def _is_effect_chain(self, node: ast.AST) -> bool:
        """Check if node is a chain of effects: .vol().pan().LPF()"""
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Attribute):
            return False
        return node.func.attr in ('vol', 'pan', 'LPF', 'HPF', 'reverb', 'delay', 'distort')
    
    def _is_bounce_call(self, node: ast.AST) -> bool:
        """Check if node is something.bounce(...)"""
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'bounce')
    
    def _is_time_call(self, node: ast.AST) -> bool:
        """Check if node is something.time()"""
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'time')
    
    def _is_rest_call(self, node: ast.AST) -> bool:
        """Check if node is m.rest(...)"""
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'rest'
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'm')
    
    # ============================================================
    # PARSING METHODS
    # ============================================================
    
    def _parse_sample_call(self, node: ast.Call, var_name: str) -> Optional[SampleModel]:
        """Parse m.sample('name', index).time_edit(x).vol(y).pan(z) - handles full chain"""
        # Find the base m.sample call
        base_call = self._get_base_sample_call(node)
        if not base_call or len(base_call.args) < 2:
            return None
        
        name = self._get_constant_value(base_call.args[0])
        index = self._get_constant_value(base_call.args[1])
        
        if name is None or index is None:
            return None
        
        sample = SampleModel(name=name, index=index)
        
        # Parse chained methods from the full node
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            attr = current.func.attr
            if attr == 'time_edit' and current.args:
                sample.time_edit = self._get_constant_value(current.args[0])
            elif attr == 'vol' and current.args:
                sample.volume = self._get_constant_value(current.args[0]) or 1.0
            elif attr == 'pan' and current.args:
                pan_val = self._get_constant_value(current.args[0])
                if pan_val:
                    try:
                        sample.pan = PanPosition(pan_val)
                    except ValueError:
                        pass
            # Move to the base of the chain
            current = current.func.value
        
        return sample
    
    def _parse_wave_combination(self, node: ast.Call, var_name: str) -> Optional[PatternModel]:
        """Parse m.join_waves((a, b, c)) or m.add_waves((a, b, c))"""
        # Extract the tuple argument
        if not node.args:
            return None
        
        tuple_arg = node.args[0]
        if not isinstance(tuple_arg, ast.Tuple):
            return None
        
        # Determine operation type
        operation = "join_waves"
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'add_waves':
            operation = "add_waves"
        
        pattern = PatternModel(name=var_name, operation=operation)
        
        for elt in tuple_arg.elts:
            if isinstance(elt, ast.Name):
                # Reference to a variable - check pattern_vars FIRST since a variable
                # may have been used for both sample and pattern (reassignment)
                var_ref = elt.id
                if var_ref in self.context.pattern_vars:
                    # Reference to a pattern - this is a join of patterns
                    step = PatternStep(expression=var_ref)
                    pattern.steps.append(step)
                elif var_ref in self.context.sample_vars:
                    # Reference to a sample
                    sample = self.context.sample_vars[var_ref]
                    pattern.add_sample(sample)
            elif self._is_rest_call(elt):
                # m.rest(duration)
                duration = self._get_constant_value(elt.args[0]) if elt.args else 1/4
                pattern.add_rest(duration)
            elif isinstance(elt, ast.Call) and self._is_sample_call(elt):
                # Inline sample creation
                sample = self._parse_sample_call(elt, f"inline_{len(pattern.steps)}")
                if sample:
                    pattern.add_sample(sample)
            elif isinstance(elt, ast.Call) and (self._is_join_waves_call(elt) or self._is_add_waves_call(elt)):
                # Nested join/add - treat as expression
                step = PatternStep(expression=f"nested_{len(pattern.steps)}")
                pattern.steps.append(step)
            elif isinstance(elt, ast.Call) and isinstance(elt.func, ast.Attribute) and elt.func.attr == 'loop':
                # Handle var.loop(n) - reference to a pattern with loop
                base_var = self._get_base_variable(elt)
                if base_var and base_var in self.context.pattern_vars:
                    # Create a step that references the pattern with loop info
                    step = PatternStep(expression=f"{base_var}.loop({self._get_constant_value(elt.args[0]) if elt.args else 1})")
                    pattern.steps.append(step)
                else:
                    # Unknown loop reference
                    step = PatternStep(expression=f"loop_ref_{len(pattern.steps)}")
                    pattern.steps.append(step)
        
        return pattern
    
    def _parse_synthesis_call(self, node: ast.Call, var_name: str) -> Optional[PatternModel]:
        """Parse m.sequence(...) or m.arpeggio(...)"""
        pattern = PatternModel(name=var_name)
        
        if self._is_sequence_call(node):
            # m.sequence(['E0'], 'sine', rhythm=1/8, duration=2, fade_in=1/8, fade_out=1/8)
            # For now, store as expression since it's complex synthesis
            step = PatternStep(expression=f"m.sequence({self._call_to_string(node)})")
            pattern.steps.append(step)
        elif self._is_arpeggio_call(node):
            # m.arpeggio('min 7', 'E2', 'sine', rhythm=1/36, duration=2)
            step = PatternStep(expression=f"m.arpeggio({self._call_to_string(node)})")
            pattern.steps.append(step)
        
        # Check for .loop()
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            if current.func.attr == 'loop' and current.args:
                pattern.loop_count = self._get_constant_value(current.args[0]) or 1
            current = current.func.value
        
        return pattern
    
    def _parse_bounce_call(self, node: ast.Call) -> None:
        """Parse mix.bounce('filename.wav', show_visual=False)"""
        if node.args:
            self.context.bounce_filename = self._get_constant_value(node.args[0]) or "output.wav"
            self.context.project.mix.bounce_filename = self.context.bounce_filename
        
        for kw in node.keywords:
            if kw.arg == 'show_visual':
                self.context.show_visual = self._get_constant_value(kw.value) or False
                self.context.project.mix.show_visual = self.context.show_visual
    
    def _handle_loop_assignment(self, var_name: str, node: ast.Call) -> None:
        """Handle var = something.loop(n)"""
        if node.args:
            loop_count = self._get_constant_value(node.args[0]) or 1
            # Find the base variable
            base_var = self._get_base_variable(node.func.value)
            if base_var and base_var in self.context.pattern_vars:
                self.context.pattern_vars[base_var].loop_count = loop_count
    
    def _handle_effect_chain(self, var_name: str, node: ast.Call) -> None:
        """Handle var = something.vol(x).pan(y).LPF(z) - track effects"""
        # Find the base variable this chain applies to
        base_var = self._get_base_variable(node)
        if not base_var:
            return
        
        # Determine which track this belongs to
        track = None
        if base_var in self.context.track_vars:
            track = self.context.track_vars[base_var]
        elif base_var in self.context.pattern_vars:
            # Find track containing this pattern
            for t in self.context.project.tracks:
                if any(p.name == self.context.pattern_vars[base_var].name for p in t.patterns):
                    track = t
                    break
        
        if not track:
            return
        
        # Parse the effect chain
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            attr = current.func.attr
            if attr == 'vol' and current.args:
                val = self._get_constant_value(current.args[0])
                if val is not None:
                    track.effects.append({'type': 'vol', 'value': val})
            elif attr == 'pan' and current.args:
                val = self._get_constant_value(current.args[0])
                if val is not None:
                    track.effects.append({'type': 'pan', 'value': val})
            elif attr == 'LPF' and current.args:
                val = self._get_constant_value(current.args[0])
                if val is not None:
                    track.effects.append({'type': 'LPF', 'freq': val})
            current = current.func.value
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _get_constant_value(self, node: ast.AST) -> Any:
        """Extract constant value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return -node.operand.value
        elif isinstance(node, ast.BinOp):
            # Handle simple expressions like 1/8
            left = self._get_constant_value(node.left)
            right = self._get_constant_value(node.right)
            if left is not None and right is not None:
                if isinstance(node.op, ast.Div):
                    return left / right
                elif isinstance(node.op, ast.Mult):
                    return left * right
                elif isinstance(node.op, ast.Add):
                    return left + right
                elif isinstance(node.op, ast.Sub):
                    return left - right
        return None
    
    def _get_base_variable(self, node: ast.AST) -> Optional[str]:
        """Get the base variable name from a chained call."""
        current = node
        while isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
            current = current.func.value
        if isinstance(current, ast.Name):
            return current.id
        return None
    
    def _call_to_string(self, node: ast.Call) -> str:
        """Convert a call node back to string representation (best effort)."""
        # This is a simplified version - in practice you'd use astor or similar
        parts = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                parts.append(repr(arg.value))
            elif isinstance(arg, ast.List):
                elts = [self._get_constant_value(e) for e in arg.elts]
                parts.append(str(elts))
            elif isinstance(arg, ast.Name):
                parts.append(arg.id)
        for kw in node.keywords:
            val = self._get_constant_value(kw.value)
            if val is not None:
                parts.append(f"{kw.arg}={repr(val)}")
        return ", ".join(parts)


def parse_musiccode_file(filepath: str) -> ProjectModel:
    """Convenience function to parse a MusicCode file."""
    parser = MusicCodeParser()
    return parser.parse_file(filepath)


def parse_musiccode_source(source: str) -> ProjectModel:
    """Convenience function to parse MusicCode source string."""
    parser = MusicCodeParser()
    return parser.parse(source)