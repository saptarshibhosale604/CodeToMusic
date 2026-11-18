"""
MusicCode GUI — Main Window
Primary application window with layout: Sample Rack | Pattern Grid | Mixer | Timeline
"""

from __future__ import annotations
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable
import os

from ..models.project import ProjectModel
from ..models.code_gen import CodeGenerator
from ..parsers.musiccode_parser import parse_musiccode_file


class MainWindow(ctk.CTk):
    """Main application window for MusicCode GUI."""
    
    def __init__(self):
        super().__init__()
        
        self.title("MusicCode GUI — Tactical Beat Constructor")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # State
        self.project: ProjectModel = ProjectModel()
        self.current_file: Optional[str] = None
        self.modified: bool = False
        
        # Callbacks
        self.on_project_changed: Optional[Callable] = None
        
        # Build UI
        self._build_menu()
        self._build_layout()
        self._bind_shortcuts()
        
        # Load default project
        self._new_project()
    
    def _build_menu(self) -> None:
        """Build application menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self._new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project (.mcproj)", command=self._open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Import MusicCode (.py)", command=self._import_python, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Save Project", command=self._save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self._save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Python (.py)", command=self._export_python, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences", command=self._show_preferences)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Sample Rack", command=lambda: self._toggle_panel("rack"))
        view_menu.add_command(label="Pattern Grid", command=lambda: self._toggle_panel("grid"))
        view_menu.add_command(label="Mixer", command=lambda: self._toggle_panel("mixer"))
        view_menu.add_command(label="Timeline", command=lambda: self._toggle_panel("timeline"))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Bounce Audio", command=self._bounce_audio, accelerator="F5")
        tools_menu.add_command(label="Preview Pattern", command=self._preview_pattern, accelerator="Space")
        tools_menu.add_separator()
        tools_menu.add_command(label="Validate Code", command=self._validate_code)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="MusicCode Docs", command=self._open_docs)
    
    def _build_layout(self) -> None:
        """Build main layout with four panels."""
        # Configure grid
        self.grid_columnconfigure(0, weight=0, minsize=280)   # Sample Rack
        self.grid_columnconfigure(1, weight=3, minsize=500)   # Pattern Grid
        self.grid_columnconfigure(2, weight=1, minsize=300)   # Mixer
        self.grid_rowconfigure(0, weight=3, minsize=400)      # Main area
        self.grid_rowconfigure(1, weight=1, minsize=150)      # Timeline
        
        # Panel visibility flags
        self.panel_visible = {
            "rack": True,
            "grid": True,
            "mixer": True,
            "timeline": True,
        }
        
        # --- LEFT: Sample Rack ---
        self.rack_frame = ctk.CTkFrame(self, corner_radius=8)
        self.rack_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(8, 4), pady=8)
        self.rack_frame.grid_rowconfigure(1, weight=1)
        self.rack_frame.grid_columnconfigure(0, weight=1)
        
        rack_header = ctk.CTkLabel(self.rack_frame, text="SAMPLE RACK", font=ctk.CTkFont(weight="bold", size=14))
        rack_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        self.rack_list = ctk.CTkScrollableFrame(self.rack_frame, label_text="Loaded Samples")
        self.rack_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        
        rack_btn_frame = ctk.CTkFrame(self.rack_frame, fg_color="transparent")
        rack_btn_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 12))
        rack_btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(rack_btn_frame, text="Load Sample", command=self._load_sample_dialog).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(rack_btn_frame, text="Scan Library", command=self._scan_sample_library).grid(row=0, column=1, padx=4, sticky="ew")
        
        # --- CENTER: Pattern Grid ---
        self.grid_frame = ctk.CTkFrame(self, corner_radius=8)
        self.grid_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=8)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        
        grid_header = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        grid_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        grid_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(grid_header, text="PATTERN GRID", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, sticky="w")
        
        # Track selector
        self.track_var = tk.StringVar()
        self.track_combo = ctk.CTkComboBox(grid_header, variable=self.track_var, values=[], command=self._on_track_change)
        self.track_combo.grid(row=0, column=1, sticky="e", padx=8)
        
        # Pattern grid canvas
        self.pattern_canvas = ctk.CTkCanvas(self.grid_frame, bg="#1a1a2e", highlightthickness=0)
        self.pattern_canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        
        # Grid controls
        grid_ctrl = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        grid_ctrl.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 12))
        
        ctk.CTkLabel(grid_ctrl, text="Steps:").grid(row=0, column=0, padx=(0, 4))
        self.steps_var = tk.IntVar(value=16)
        ctk.CTkEntry(grid_ctrl, textvariable=self.steps_var, width=50).grid(row=0, column=1, padx=4)
        
        ctk.CTkLabel(grid_ctrl, text="Resolution:").grid(row=0, column=2, padx=(12, 4))
        self.resolution_var = tk.StringVar(value="1/8")
        ctk.CTkComboBox(grid_ctrl, variable=self.resolution_var, values=["1/4", "1/8", "1/16", "1/32"], width=70).grid(row=0, column=3, padx=4)
        
        ctk.CTkLabel(grid_ctrl, text="Loop:").grid(row=0, column=4, padx=(12, 4))
        self.loop_var = tk.IntVar(value=1)
        ctk.CTkEntry(grid_ctrl, textvariable=self.loop_var, width=50).grid(row=0, column=5, padx=4)
        
        ctk.CTkButton(grid_ctrl, text="Add Step", command=self._add_step).grid(row=0, column=6, padx=8)
        ctk.CTkButton(grid_ctrl, text="Clear", command=self._clear_pattern).grid(row=0, column=7, padx=4)
        
        # --- RIGHT: Mixer ---
        self.mixer_frame = ctk.CTkFrame(self, corner_radius=8)
        self.mixer_frame.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)
        self.mixer_frame.grid_rowconfigure(1, weight=1)
        self.mixer_frame.grid_columnconfigure(0, weight=1)
        
        mixer_header = ctk.CTkLabel(self.mixer_frame, text="MIXER", font=ctk.CTkFont(weight="bold", size=14))
        mixer_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        self.mixer_list = ctk.CTkScrollableFrame(self.mixer_frame, label_text="Tracks")
        self.mixer_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        
        # Master section
        master_frame = ctk.CTkFrame(self.mixer_frame)
        master_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 12))
        master_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(master_frame, text="MASTER", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=8)
        
        ctk.CTkLabel(master_frame, text="Volume:").grid(row=1, column=0, padx=8, sticky="w")
        self.master_vol = tk.DoubleVar(value=1.0)
        ctk.CTkSlider(master_frame, variable=self.master_vol, from_=0, to=2, command=self._on_master_vol).grid(row=1, column=1, padx=8, pady=4, sticky="ew")
        ctk.CTkLabel(master_frame, textvariable=tk.StringVar(value="1.00")).grid(row=1, column=2, padx=8)
        
        ctk.CTkButton(master_frame, text="BOUNCE", command=self._bounce_audio, fg_color="#d62828", hover_color="#a61e1e", height=40).grid(row=2, column=0, columnspan=3, padx=8, pady=12, sticky="ew")
        
        # --- BOTTOM: Timeline ---
        self.timeline_frame = ctk.CTkFrame(self, corner_radius=8)
        self.timeline_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=8, pady=(0, 8))
        self.timeline_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.timeline_frame, text="TIMELINE", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, padx=12, pady=8, sticky="w")
        
        # Transport controls
        transport = ctk.CTkFrame(self.timeline_frame, fg_color="transparent")
        transport.grid(row=0, column=1, sticky="e", padx=12, pady=8)
        
        ctk.CTkButton(transport, text="⏮", width=40, command=self._rewind).grid(row=0, column=0, padx=2)
        ctk.CTkButton(transport, text="⏯", width=40, command=self._play_pause).grid(row=0, column=1, padx=2)
        ctk.CTkButton(transport, text="⏹", width=40, command=self._stop).grid(row=0, column=2, padx=2)
        ctk.CTkButton(transport, text="⏭", width=40, command=self._forward).grid(row=0, column=3, padx=2)
        
        ctk.CTkLabel(transport, text="  BPM:").grid(row=0, column=4, padx=(12, 4))
        self.bpm_var = tk.IntVar(value=120)
        ctk.CTkEntry(transport, textvariable=self.bpm_var, width=60).grid(row=0, column=5, padx=4)
        
        # Timeline canvas
        self.timeline_canvas = ctk.CTkCanvas(self.timeline_frame, bg="#0f0f1a", height=80, highlightthickness=0)
        self.timeline_canvas.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready — MusicCode GUI Operational")
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", font=ctk.CTkFont(size=11))
        status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
    
    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.bind("<Control-n>", lambda e: self._new_project())
        self.bind("<Control-o>", lambda e: self._open_project())
        self.bind("<Control-i>", lambda e: self._import_python())
        self.bind("<Control-s>", lambda e: self._save_project())
        self.bind("<Control-Shift-S>", lambda e: self._save_project_as())
        self.bind("<Control-e>", lambda e: self._export_python())
        self.bind("<F5>", lambda e: self._bounce_audio())
        self.bind("<space>", lambda e: self._preview_pattern())
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
    
    # ============================================================
    # FILE OPERATIONS
    # ============================================================
    
    def _new_project(self) -> None:
        """Create a new empty project."""
        self.project = ProjectModel(name="Untitled Project", tempo=120)
        self.current_file = None
        self.modified = False
        self._refresh_ui()
        self._set_status("New project created")
    
    def _open_project(self) -> None:
        """Open a .mcproj file."""
        filepath = filedialog.askopenfilename(
            title="Open MusicCode Project",
            filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                self.project = ProjectModel.load_project(filepath)
                self.current_file = filepath
                self.modified = False
                self._refresh_ui()
                self._set_status(f"Loaded project: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project:\n{e}")
    
    def _save_project(self) -> None:
        """Save project to current file or prompt for new."""
        if self.current_file:
            try:
                self.project.save_project(self.current_file)
                self.modified = False
                self._set_status(f"Saved: {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project:\n{e}")
        else:
            self._save_project_as()
    
    def _save_project_as(self) -> None:
        """Save project with new filename."""
        filepath = filedialog.asksaveasfilename(
            title="Save MusicCode Project",
            defaultextension=".mcproj",
            filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
        )
        if filepath:
            self.current_file = filepath
            self._save_project()
    
    def _import_python(self) -> None:
        """Import a MusicCode Python script."""
        filepath = filedialog.askopenfilename(
            title="Import MusicCode Script",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                self.project = parse_musiccode_file(filepath)
                self.current_file = None  # Not a .mcproj file
                self.modified = True
                self._refresh_ui()
                self._set_status(f"Imported: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to parse Python file:\n{e}")
    
    def _export_python(self) -> None:
        """Export project as MusicCode Python script."""
        filepath = filedialog.asksaveasfilename(
            title="Export MusicCode Script",
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                generator = CodeGenerator(self.project)
                generator.save_to_file(filepath)
                self._set_status(f"Exported: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to generate code:\n{e}")
    
    # ============================================================
    # SAMPLE RACK OPERATIONS
    # ============================================================
    
    def _load_sample_dialog(self) -> None:
        """Dialog to load a sample into the rack."""
        # For now, just add a placeholder
        dialog = ctk.CTkToplevel(self)
        dialog.title("Load Sample")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Sample Name:").pack(pady=(20, 4))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(pady=4, padx=20, fill="x")
        
        ctk.CTkLabel(dialog, text="Library Index:").pack(pady=(12, 4))
        index_entry = ctk.CTkEntry(dialog)
        index_entry.pack(pady=4, padx=20, fill="x")
        
        ctk.CTkLabel(dialog, text="Time Edit (e.g., 1/8):").pack(pady=(12, 4))
        time_entry = ctk.CTkEntry(dialog)
        time_entry.pack(pady=4, padx=20, fill="x")
        time_entry.insert(0, "1/8")
        
        def add_sample():
            name = name_entry.get().strip()
            try:
                index = int(index_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Index must be an integer")
                return
            
            time_str = time_entry.get().strip()
            try:
                if '/' in time_str:
                    num, den = time_str.split('/')
                    time_edit = float(num) / float(den)
                else:
                    time_edit = float(time_str)
            except ValueError:
                time_edit = 1/8
            
            from ..models.project import SampleModel
            sample = SampleModel(name=name, index=index, time_edit=time_edit)
            self.project.register_sample(sample)
            self._refresh_rack()
            self.modified = True
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Add Sample", command=add_sample).pack(pady=20)
    
    def _scan_sample_library(self) -> None:
        """Scan the samples directory for available samples."""
        samples_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples")
        samples_dir = os.path.normpath(samples_dir)
        
        if not os.path.exists(samples_dir):
            messagebox.showwarning("Not Found", f"Samples directory not found:\n{samples_dir}")
            return
        
        # List subdirectories (sample categories)
        categories = [d for d in os.listdir(samples_dir) 
                     if os.path.isdir(os.path.join(samples_dir, d))]
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Sample Library")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Available Sample Categories:", font=ctk.CTkFont(weight="bold")).pack(pady=12)
        
        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=12, pady=8)
        
        for cat in categories:
            cat_path = os.path.join(samples_dir, cat)
            files = [f for f in os.listdir(cat_path) if f.endswith(('.wav', '.mp3', '.ogg', '.flac'))]
            if files:
                frame = ctk.CTkFrame(list_frame)
                frame.pack(fill="x", pady=4, padx=4)
                ctk.CTkLabel(frame, text=f"{cat} ({len(files)} files)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=8, pady=4)
                for f in files[:5]:  # Show first 5
                    ctk.CTkLabel(frame, text=f"  • {f}", anchor="w").pack(anchor="w", padx=16)
                if len(files) > 5:
                    ctk.CTkLabel(frame, text=f"  ... and {len(files) - 5} more", anchor="w").pack(anchor="w", padx=16)
    
    def _refresh_rack(self) -> None:
        """Refresh the sample rack display."""
        for widget in self.rack_list.winfo_children():
            widget.destroy()
        
        for i, sample in enumerate(self.project.samples):
            frame = ctk.CTkFrame(self.rack_list)
            frame.pack(fill="x", pady=2, padx=4)
            frame.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(frame, text=f"{sample.name}[{sample.index}]", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=8, pady=4, sticky="w")
            
            info = []
            if sample.time_edit:
                info.append(f"t={sample.time_edit}")
            if sample.volume != 1.0:
                info.append(f"vol={sample.volume}")
            if sample.pan:
                info.append(f"pan={sample.pan.value}")
            ctk.CTkLabel(frame, text=" | ".join(info), text_color="gray").grid(row=0, column=1, padx=8, pady=4, sticky="w")
            
            ctk.CTkButton(frame, text="×", width=28, height=28, fg_color="#d62828", 
                         command=lambda s=sample: self._remove_sample(s)).grid(row=0, column=2, padx=4, pady=4)
    
    def _remove_sample(self, sample: SampleModel) -> None:
        """Remove a sample from the rack."""
        self.project.samples.remove(sample)
        self._refresh_rack()
        self.modified = True
    
    # ============================================================
    # PATTERN GRID OPERATIONS
    # ============================================================
    
    def _on_track_change(self, track_name: str) -> None:
        """Handle track selection change."""
        self._refresh_pattern_grid()
    
    def _refresh_pattern_grid(self) -> None:
        """Refresh the pattern grid for current track."""
        track_name = self.track_var.get()
        if not track_name:
            return
        
        # Find track
        track = None
        for t in self.project.tracks:
            if t.name == track_name:
                track = t
                break
        
        if not track:
            return
        
        # Update track combo values
        track_names = [t.name for t in self.project.tracks]
        self.track_combo.configure(values=track_names)
        
        # Clear canvas
        self.pattern_canvas.delete("all")
        
        # Draw grid
        steps = self.steps_var.get()
        canvas_width = self.pattern_canvas.winfo_width() or 600
        canvas_height = self.pattern_canvas.winfo_height() or 300
        cell_width = canvas_width / steps
        cell_height = canvas_height / max(len(track.patterns), 1)
        
        # Draw pattern rows
        for row, pattern in enumerate(track.patterns):
            y = row * cell_height
            # Pattern name
            self.pattern_canvas.create_text(10, y + cell_height/2, text=pattern.name, anchor="w", fill="white", font=("Consolas", 10))
            
            # Steps
            for step_idx, step in enumerate(pattern.steps):
                x = 120 + step_idx * cell_width
                color = "#2a2a4a"
                text = ""
                
                if step.sample:
                    color = "#1e3a5f"
                    text = step.sample.name[:4]
                elif step.rest:
                    color = "#1a1a2e"
                    text = "—"
                elif step.expression:
                    color = "#3a2a1e"
                    text = "EXPR"
                
                self.pattern_canvas.create_rectangle(x, y, x + cell_width - 1, y + cell_height - 1, 
                                                    fill=color, outline="#3a3a5a")
                if text:
                    self.pattern_canvas.create_text(x + cell_width/2, y + cell_height/2, 
                                                   text=text, fill="white", font=("Consolas", 8))
    
    def _add_step(self) -> None:
        """Add a step to the current pattern."""
        track_name = self.track_var.get()
        if not track_name:
            return
        
        # Simple implementation - add a rest step
        for track in self.project.tracks:
            if track.name == track_name and track.patterns:
                pattern = track.patterns[0]  # First pattern
                resolution = 1/8
                res_str = self.resolution_var.get()
                if '/' in res_str:
                    num, den = res_str.split('/')
                    resolution = float(num) / float(den)
                pattern.add_rest(resolution)
                self._refresh_pattern_grid()
                self.modified = True
                break
    
    def _clear_pattern(self) -> None:
        """Clear the current pattern."""
        track_name = self.track_var.get()
        if not track_name:
            return
        
        for track in self.project.tracks:
            if track.name == track_name and track.patterns:
                track.patterns[0].steps.clear()
                self._refresh_pattern_grid()
                self.modified = True
                break
    
    # ============================================================
    # MIXER OPERATIONS
    # ============================================================
    
    def _refresh_mixer(self) -> None:
        """Refresh the mixer display."""
        for widget in self.mixer_list.winfo_children():
            widget.destroy()
        
        for track in self.project.tracks:
            frame = ctk.CTkFrame(self.mixer_list)
            frame.pack(fill="x", pady=4, padx=4)
            frame.grid_columnconfigure(1, weight=1)
            
            # Track name
            ctk.CTkLabel(frame, text=track.name, font=ctk.CTkFont(weight="bold", size=12)).grid(row=0, column=0, columnspan=3, pady=4)
            
            # Volume
            ctk.CTkLabel(frame, text="Vol:").grid(row=1, column=0, padx=8, sticky="w")
            vol_var = tk.DoubleVar(value=track.volume)
            vol_slider = ctk.CTkSlider(frame, variable=vol_var, from_=0, to=2, 
                                      command=lambda v, t=track: self._on_track_vol(t, v))
            vol_slider.grid(row=1, column=1, padx=8, sticky="ew")
            ctk.CTkLabel(frame, textvariable=tk.StringVar(value=f"{track.volume:.2f}")).grid(row=1, column=2, padx=8)
            
            # Pan
            ctk.CTkLabel(frame, text="Pan:").grid(row=2, column=0, padx=8, sticky="w")
            pan_var = tk.StringVar(value=track.pan.value if track.pan else "C")
            pan_combo = ctk.CTkComboBox(frame, variable=pan_var, values=["L50", "L25", "L", "C", "R", "R25", "R50"], width=80,
                                       command=lambda v, t=track: self._on_track_pan(t, v))
            pan_combo.grid(row=2, column=1, padx=8, sticky="ew")
            
            # Solo/Mute
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=3, column=0, columnspan=3, pady=4)
            
            solo_var = tk.BooleanVar(value=track.solo)
            ctk.CTkCheckBox(btn_frame, text="S", variable=solo_var, width=30,
                           command=lambda t=track, v=solo_var: self._on_track_solo(t, v.get())).pack(side="left", padx=4)
            
            mute_var = tk.BooleanVar(value=track.mute)
            ctk.CTkCheckBox(btn_frame, text="M", variable=mute_var, width=30,
                           command=lambda t=track, v=mute_var: self._on_track_mute(t, v.get())).pack(side="left", padx=4)
            
            # Effects
            if track.effects:
                eff_text = ", ".join([f"{e['type']}" for e in track.effects])
                ctk.CTkLabel(frame, text=f"FX: {eff_text}", text_color="gray", font=ctk.CTkFont(size=10)).grid(row=4, column=0, columnspan=3, padx=8, pady=2, sticky="w")
    
    def _on_track_vol(self, track: TrackModel, value: float) -> None:
        track.volume = value
        self.modified = True
    
    def _on_track_pan(self, track: TrackModel, value: str) -> None:
        from ..models.project import PanPosition
        try:
            track.pan = PanPosition(value)
            self.modified = True
        except ValueError:
            pass
    
    def _on_track_solo(self, track: TrackModel, value: bool) -> None:
        track.solo = value
        self.modified = True
    
    def _on_track_mute(self, track: TrackModel, value: bool) -> None:
        track.mute = value
        self.modified = True
    
    def _on_master_vol(self, value: float) -> None:
        self.project.mix.master_volume = value
        self.modified = True
    
    # ============================================================
    # TRANSPORT / TIMELINE
    # ============================================================
    
    def _play_pause(self) -> None:
        self._set_status("Play/Pause — Not implemented")
    
    def _stop(self) -> None:
        self._set_status("Stop — Not implemented")
    
    def _rewind(self) -> None:
        self._set_status("Rewind — Not implemented")
    
    def _forward(self) -> None:
        self._set_status("Forward — Not implemented")
    
    def _preview_pattern(self) -> None:
        self._set_status("Preview — Not implemented")
    
    def _bounce_audio(self) -> None:
        """Export audio by running the generated Python code."""
        self._set_status("Generating code and bouncing...")
        try:
            # Export to temp file and run
            import tempfile
            import subprocess
            import sys
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                generator = CodeGenerator(self.project)
                generator.save_to_file(f.name)
                temp_path = f.name
            
            # Run the script
            result = subprocess.run([sys.executable, temp_path], 
                                  capture_output=True, text=True, timeout=60,
                                  cwd=os.path.dirname(temp_path))
            
            os.unlink(temp_path)
            
            if result.returncode == 0:
                self._set_status(f"Bounce complete: {result.stdout.strip()}")
                messagebox.showinfo("Success", f"Audio exported successfully!\n{result.stdout}")
            else:
                self._set_status("Bounce failed")
                messagebox.showerror("Bounce Error", f"Failed to generate audio:\n{result.stderr}")
        except Exception as e:
            self._set_status("Bounce error")
            messagebox.showerror("Error", f"Bounce failed:\n{e}")
    
    def _validate_code(self) -> None:
        """Validate the generated code without running."""
        try:
            generator = CodeGenerator(self.project)
            code = generator.generate()
            # Try to parse it
            ast.parse(code)
            messagebox.showinfo("Validation", "Code is syntactically valid!")
            self._set_status("Code validation passed")
        except SyntaxError as e:
            messagebox.showerror("Syntax Error", f"Generated code has syntax error:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed:\n{e}")
    
    # ============================================================
    # UI HELPERS
    # ============================================================
    
    def _refresh_ui(self) -> None:
        """Refresh all UI panels from project model."""
        self.bpm_var.set(self.project.tempo)
        self._refresh_rack()
        self._refresh_mixer()
        self._refresh_pattern_grid()
        
        # Update track combo
        track_names = [t.name for t in self.project.tracks]
        self.track_combo.configure(values=track_names)
        if track_names and not self.track_var.get():
            self.track_var.set(track_names[0])
    
    def _toggle_panel(self, panel: str) -> None:
        """Toggle panel visibility."""
        self.panel_visible[panel] = not self.panel_visible[panel]
        # Implementation would show/hide frames
        self._set_status(f"{panel.capitalize()} panel: {'visible' if self.panel_visible[panel] else 'hidden'}")
    
    def _set_status(self, message: str) -> None:
        self.status_var.set(message)
    
    def _undo(self) -> None:
        self._set_status("Undo — Not implemented")
    
    def _redo(self) -> None:
        self._set_status("Redo — Not implemented")
    
    def _show_preferences(self) -> None:
        self._set_status("Preferences — Not implemented")
    
    def _show_about(self) -> None:
        messagebox.showinfo("About", "MusicCode GUI v1.0\nTactical Beat Constructor\nBuilt for General SSB")
    
    def _open_docs(self) -> None:
        import webbrowser
        webbrowser.open("https://github.com/your-repo/MusicCode")


def main():
    """Entry point for the GUI application."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()