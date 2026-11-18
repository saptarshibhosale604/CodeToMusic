"""
MusicCode GUI — Main Entry Point
Tactical Beat Constructor for General SSB
"""

import sys
import os

# Add project root and core to path
gui_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(gui_dir)
core_dir = os.path.join(project_root, 'core')

sys.path.insert(0, project_root)
sys.path.insert(0, core_dir)

# Check dependencies
def check_dependencies():
    """Check and report missing dependencies."""
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        import astor
    except ImportError:
        missing.append("astor")
    
    try:
        import black
    except ImportError:
        missing.append("black (optional, for code formatting)")
    
    try:
        import music_code
    except ImportError:
        missing.append("music_code (core library)")
    
    if missing:
        print("MISSING DEPENDENCIES:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with:")
        print("  pip install customtkinter astor black")
        print("  # music_code should be available from ../core")
        return False
    return True


def main():
    """Launch the MusicCode GUI application."""
    print("=" * 60)
    print("  MusicCode GUI — Tactical Beat Constructor")
    print("  Mission: Bidirectional GUI <-> Code Music Generation")
    print("  Target: General SSB")
    print("=" * 60)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Import after dependency check
    from GUI.views.main_window import MainWindow
    from GUI.controllers.app_controller import create_controller
    
    print("\n[INIT] Initializing Main Window...")
    app = MainWindow()
    
    print("[INIT] Connecting App Controller...")
    controller = create_controller(app)
    
    # Replace view's internal methods with controller-driven ones
    app._new_project = lambda: controller.new_project()
    app._open_project = lambda: controller.load_project(
        __import__('tkinter').filedialog.askopenfilename(
            title="Open MusicCode Project",
            filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
        )
    ) if __import__('tkinter').filedialog.askopenfilename(
        title="Open MusicCode Project",
        filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
    ) else None
    
    app._save_project = lambda: controller.save_project()
    app._save_project_as = lambda: controller.save_project(
        __import__('tkinter').filedialog.asksaveasfilename(
            title="Save MusicCode Project",
            defaultextension=".mcproj",
            filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
        )
    ) if __import__('tkinter').filedialog.asksaveasfilename(
        title="Save MusicCode Project",
        defaultextension=".mcproj",
        filetypes=[("MusicCode Project", "*.mcproj"), ("All Files", "*.*")]
    ) else None
    
    app._import_python = lambda: controller.import_python(
        __import__('tkinter').filedialog.askopenfilename(
            title="Import MusicCode Script",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
    ) if __import__('tkinter').filedialog.askopenfilename(
        title="Import MusicCode Script",
        filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
    ) else None
    
    app._export_python = lambda: controller.export_python(
        __import__('tkinter').filedialog.asksaveasfilename(
            title="Export MusicCode Script",
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
    ) if __import__('tkinter').filedialog.asksaveasfilename(
        title="Export MusicCode Script",
        defaultextension=".py",
        filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
    ) else None
    
    app._undo = lambda: controller.undo()
    app._redo = lambda: controller.redo()
    app._validate_code = lambda: controller.validate_code()
    app._bounce_audio = lambda: controller.bounce_audio()
    
    print("[INIT] Systems nominal. Launching interface...")
    print("-" * 60)
    
    app.mainloop()
    
    print("-" * 60)
    print("[SHUTDOWN] MusicCode GUI terminated.")


if __name__ == "__main__":
    main()