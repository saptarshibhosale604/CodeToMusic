"""
MusicCode GUI — Code Generator
Converts ProjectModel → AST → formatted Python code (MusicCode DSL).
Uses Python's `ast` module for programmatic AST construction.
"""

from __future__ import annotations
import ast
import astor
try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False

from .project import (
    ProjectModel, TrackModel, PatternModel, SampleModel, MixModel,
    PatternStep, WaveformType, ChordType, PanPosition
)


class CodeGenerator:
    """
    Generates MusicCode Python code from ProjectModel.
    Builds AST programmatically for perfect round-trip fidelity.
    """

    def __init__(self, project: ProjectModel):
        self.project = project
        self.module_body: list[ast.stmt] = []
        self._sample_vars: dict[tuple[str, int], str] = {}  # (name, index) -> var_name
        self._track_vars: dict[str, str] = {}  # track_name -> var_name
        self._pattern_vars: dict[str, str] = {}  # pattern_name -> var_name

    def generate(self) -> str:
        """Generate complete Python source code."""
        self.module_body = []
        self._sample_vars = {}
        self._track_vars = {}
        self._pattern_vars = {}

        # 1. Path setup and imports - generate as string prefix to ensure correct order
        import os
        core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
        self._code_prefix = f'''import sys
sys.path.insert(0, {repr(core_path)})
from music_code import MusicCode

'''

        # 2. Initialize MusicCode
        self._add_musiccode_init()

        # 3. Load samples
        self._add_sample_loading()

        # 4. Create patterns for each track
        self._add_pattern_creation()

        # 5. Create track mix expressions (join_waves, add_waves, loop)
        self._add_track_mixing()

        # 6. Final mix and bounce
        self._add_final_mix()

        # Build module and convert to source
        module = ast.Module(body=self.module_body, type_ignores=[])
        ast.fix_missing_locations(module)
        
        source = astor.to_source(module)
        
        # Format with black if available
        if BLACK_AVAILABLE:
            try:
                source = black.format_str(source, mode=black.FileMode(line_length=100))
            except Exception:
                pass  # Fall back to unformatted
        
        # Prepend the prefix
        return self._code_prefix + source

    def _add_imports(self) -> None:
        """Add import statements - no longer used, kept for compatibility."""
        pass

    def _add_path_setup(self) -> None:
        """Add sys.path.insert for core module - no longer used, kept for compatibility."""
        pass

    def _add_musiccode_init(self) -> None:
        """Initialize MusicCode with tempo."""
        init_call = ast.Call(
            func=ast.Name(id='MusicCode', ctx=ast.Load()),
            args=[ast.Constant(value=self.project.tempo)],
            keywords=[]
        )
        assign = ast.Assign(
            targets=[ast.Name(id='m', ctx=ast.Store())],
            value=init_call
        )
        self.module_body.append(assign)

    def _add_sample_loading(self) -> None:
        """Generate sample loading code."""
        for sample in self.project.samples:
            var_name = f"{sample.name}_{sample.index}"
            self._sample_vars[(sample.name, sample.index)] = var_name
            
            # m.sample('name', index)
            sample_call = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='m', ctx=ast.Load()),
                    attr='sample',
                    ctx=ast.Load()
                ),
                args=[
                    ast.Constant(value=sample.name),
                    ast.Constant(value=sample.index)
                ],
                keywords=[]
            )
            
            # Chain .time_edit(), .vol(), .pan() if present
            current = sample_call
            if sample.time_edit is not None:
                current = ast.Call(
                    func=ast.Attribute(
                        value=current,
                        attr='time_edit',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=sample.time_edit)],
                    keywords=[]
                )
            if sample.volume != 1.0:
                current = ast.Call(
                    func=ast.Attribute(
                        value=current,
                        attr='vol',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=sample.volume)],
                    keywords=[]
                )
            if sample.pan is not None:
                current = ast.Call(
                    func=ast.Attribute(
                        value=current,
                        attr='pan',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=sample.pan.value)],
                    keywords=[]
                )
            
            assign = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=current
            )
            self.module_body.append(assign)

    def _add_pattern_creation(self) -> None:
        """Generate pattern creation code for each track."""
        for track in self.project.tracks:
            for pattern in track.patterns:
                self._generate_pattern_code(track, pattern)

    def _generate_pattern_code(self, track: TrackModel, pattern: PatternModel) -> None:
        """Generate code for a single pattern."""
        # Use the original variable name from the parser if available
        # The parser stores patterns with their original variable names as keys
        original_var_name = None
        if hasattr(self, '_parser_pattern_vars'):
            # Find the key in parser_pattern_vars that maps to this pattern
            for key, parser_pattern in self._parser_pattern_vars.items():
                if parser_pattern is pattern:
                    original_var_name = key
                    break
        
        if original_var_name:
            var_name = original_var_name
        else:
            var_name = f"{track.name}_{pattern.name}".replace(' ', '_')
        
        # Store with both track-prefixed key and direct pattern name key for compatibility
        self._pattern_vars[f"{track.name}.{pattern.name}"] = var_name
        self._pattern_vars[pattern.name] = var_name
        # Also store the original pattern name as a key for direct lookup
        self._pattern_vars[f"orig_{pattern.name}"] = var_name
        
        if not pattern.steps:
            # Empty pattern
            assign = ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='m', ctx=ast.Load()),
                        attr='rest',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=pattern.resolution)],
                    keywords=[]
                )
            )
            self.module_body.append(assign)
            return

        # Build join_waves call with all steps
        step_exprs = []
        for step in pattern.steps:
            if step.expression:
                # Check if it's a loop expression like "var.loop(n)"
                import re
                loop_match = re.match(r'(\w+)\.loop\((\d+)\)', step.expression)
                if loop_match:
                    loop_var_name = loop_match.group(1)
                    loop_count = int(loop_match.group(2))
                    # Create var.loop(n) call
                    base_expr = ast.Name(id=loop_var_name, ctx=ast.Load())
                    loop_expr = ast.Call(
                        func=ast.Attribute(
                            value=base_expr,
                            attr='loop',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=loop_count)],
                        keywords=[]
                    )
                    step_exprs.append(loop_expr)
                else:
                    # Regular variable reference
                    step_exprs.append(ast.Name(id=step.expression, ctx=ast.Load()))
            elif step.sample:
                sample_var = self._sample_vars.get((step.sample.name, step.sample.index))
                if sample_var:
                    step_exprs.append(ast.Name(id=sample_var, ctx=ast.Load()))
                else:
                    # Inline sample creation (shouldn't happen if samples registered)
                    step_exprs.append(ast.Constant(value=None))
            elif step.rest is not None:
                rest_call = ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='m', ctx=ast.Load()),
                        attr='rest',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=step.rest)],
                    keywords=[]
                )
                step_exprs.append(rest_call)

        if len(step_exprs) == 1:
            pattern_expr = step_exprs[0]
        else:
            # Use the pattern's operation type
            op_attr = getattr(pattern, 'operation', 'join_waves')
            pattern_expr = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='m', ctx=ast.Load()),
                    attr=op_attr,
                    ctx=ast.Load()
                ),
                args=[ast.Tuple(elts=step_exprs, ctx=ast.Load())],
                keywords=[]
            )

        # Apply .loop() if loop_count > 1
        if pattern.loop_count > 1:
            pattern_expr = ast.Call(
                func=ast.Attribute(
                    value=pattern_expr,
                    attr='loop',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value=pattern.loop_count)],
                keywords=[]
            )

        assign = ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=pattern_expr
        )
        self.module_body.append(assign)

    def _add_track_mixing(self) -> None:
        """Generate track mixing code (join_waves, add_waves for each track)."""
        # Check if there's a "Mix" track with a final mix pattern that should be used directly
        mix_track = None
        final_mix_pattern = None
        for track in self.project.tracks:
            if track.name == "Mix":
                mix_track = track
                for p in track.patterns:
                    if p.name == "mix" and p.steps:
                        all_loops = all(
                            step.expression and '.loop(' in step.expression 
                            for step in p.steps
                        )
                        if all_loops:
                            final_mix_pattern = p
                            break
                break
        
        if final_mix_pattern:
            # Use the final mix pattern directly as the output
            pattern_var = self._pattern_vars.get(f"{mix_track.name}.{final_mix_pattern.name}") or self._pattern_vars.get(final_mix_pattern.name)
            if pattern_var:
                mix_var = "final_mix"
                expr = ast.Name(id=pattern_var, ctx=ast.Load())
                
                # Apply master volume
                if self.project.mix.master_volume != 1.0:
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=expr,
                            attr='vol',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=self.project.mix.master_volume)],
                        keywords=[]
                    )
                
                assign = ast.Assign(
                    targets=[ast.Name(id=mix_var, ctx=ast.Store())],
                    value=expr
                )
                self.module_body.append(assign)
                self._track_vars['final_mix'] = mix_var
                return
        
        # Otherwise, do normal track mixing
        for track in self.project.tracks:
            track_var = f"{track.name}_mix".replace(' ', '_')
            self._track_vars[track.name] = track_var

            if track.join_expression:
                # Custom join expression provided
                expr = ast.Name(id=track.join_expression, ctx=ast.Load())
            elif track.patterns:
                # Join all patterns in this track normally
                pattern_vars = []
                for p in track.patterns:
                    # Try track-prefixed key first, then direct pattern name
                    var = self._pattern_vars.get(f"{track.name}.{p.name}") or self._pattern_vars.get(p.name)
                    if var:
                        pattern_vars.append(var)
                
                if len(pattern_vars) == 1:
                    expr = ast.Name(id=pattern_vars[0], ctx=ast.Load())
                elif pattern_vars:
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='m', ctx=ast.Load()),
                            attr='join_waves',
                            ctx=ast.Load()
                        ),
                        args=[ast.Tuple(
                            elts=[ast.Name(id=v, ctx=ast.Load()) for v in pattern_vars],
                            ctx=ast.Load()
                        )],
                        keywords=[]
                    )
                else:
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='m', ctx=ast.Load()),
                            attr='rest',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=1.0)],
                        keywords=[]
                    )
            else:
                expr = ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='m', ctx=ast.Load()),
                        attr='rest',
                        ctx=ast.Load()
                    ),
                    args=[ast.Constant(value=1.0)],
                    keywords=[]
                )

            # Apply track effects (vol, pan, LPF, etc.)
            for effect in track.effects:
                if effect.get('type') == 'vol':
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=expr,
                            attr='vol',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=effect.get('value', 1.0))],
                        keywords=[]
                    )
                elif effect.get('type') == 'pan':
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=expr,
                            attr='pan',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=effect.get('value', 'C'))],
                        keywords=[]
                    )
                elif effect.get('type') == 'LPF':
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=expr,
                            attr='LPF',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=effect.get('freq', 1000))],
                        keywords=[]
                    )

            assign = ast.Assign(
                targets=[ast.Name(id=track_var, ctx=ast.Store())],
                value=expr
            )
            self.module_body.append(assign)
        
        # Also create the final mix variable that combines all tracks
        # This is needed for the bounce call
        if self.project.tracks:
            track_vars = [self._track_vars.get(t.name) for t in self.project.tracks]
            track_vars = [v for v in track_vars if v]
            
            if track_vars:
                mix_var = "final_mix"
                if len(track_vars) == 1:
                    expr = ast.Name(id=track_vars[0], ctx=ast.Load())
                else:
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='m', ctx=ast.Load()),
                            attr='add_waves',
                            ctx=ast.Load()
                        ),
                        args=[ast.Tuple(
                            elts=[ast.Name(id=v, ctx=ast.Load()) for v in track_vars],
                            ctx=ast.Load()
                        )],
                        keywords=[]
                    )
                
                # Apply master volume
                if self.project.mix.master_volume != 1.0:
                    expr = ast.Call(
                        func=ast.Attribute(
                            value=expr,
                            attr='vol',
                            ctx=ast.Load()
                        ),
                        args=[ast.Constant(value=self.project.mix.master_volume)],
                        keywords=[]
                    )
                
                assign = ast.Assign(
                    targets=[ast.Name(id=mix_var, ctx=ast.Store())],
                    value=expr
                )
                self.module_body.append(assign)
                self._track_vars['final_mix'] = mix_var

    def _add_final_mix(self) -> None:
        """Generate final mix and bounce code."""
        mix = self.project.mix
        
        # Use the final_mix variable created in _add_track_mixing
        mix_var = self._track_vars.get('final_mix')
        if not mix_var:
            return
        
        mix_expr = ast.Name(id=mix_var, ctx=ast.Load())

        # Bounce
        bounce_call = ast.Call(
            func=ast.Attribute(
                value=mix_expr,
                attr='bounce',
                ctx=ast.Load()
            ),
            args=[ast.Constant(value=mix.bounce_filename)],
            keywords=[
                ast.keyword(arg='show_visual', value=ast.Constant(value=mix.show_visual))
            ]
        )
        
        self.module_body.append(ast.Expr(value=bounce_call))
        
        # Print confirmation
        print_call = ast.Call(
            func=ast.Name(id='print', ctx=ast.Load()),
            args=[ast.Constant(value=f'Done! Check export/{mix.bounce_filename}')],
            keywords=[]
        )
        self.module_body.append(ast.Expr(value=print_call))

    def save_to_file(self, filepath: str) -> None:
        """Generate and save to file."""
        source = self.generate()
        with open(filepath, 'w') as f:
            f.write(source)


def generate_code(project: ProjectModel) -> str:
    """Convenience function to generate code from project."""
    generator = CodeGenerator(project)
    return generator.generate()