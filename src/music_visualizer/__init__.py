"""
Music Visualizer - A wxPython-based audio visualization application.

This package provides a complete music visualizer application with support for:
- Multiple audio formats (MP3, WAV, OGG, FLAC, M4A)
- Real-time audio visualization (spectrum, waveform, bars, circular)
- Playlist management and playback controls
- Customizable visualization colors and themes
- Cross-platform GUI using wxPython
"""

__version__ = "1.0.0"
__author__ = "Music Visualizer Developer"
__email__ = "developer@musicvisualizer.com"
__license__ = "MIT"

# Lazy import to avoid circular import issues
_classes_imported = False
AudioVisualizer = None
MusicVisualizerFrame = None
MusicVisualizerApp = None

def _ensure_imports():
    """Ensure classes are imported when needed."""
    global _classes_imported, AudioVisualizer, MusicVisualizerFrame, MusicVisualizerApp
    
    if not _classes_imported:
        # Try different import strategies for robustness
        try:
            # Strategy 1: Relative import (when used as package)
            from .music_visualizer import (
                AudioVisualizer as _AudioVisualizer,
                MusicVisualizerFrame as _MusicVisualizerFrame,
                MusicVisualizerApp as _MusicVisualizerApp
            )
        except (ImportError, SystemError, ValueError):
            # Strategy 2: Absolute import (when running as script)
            try:
                from music_visualizer.music_visualizer import (
                    AudioVisualizer as _AudioVisualizer,
                    MusicVisualizerFrame as _MusicVisualizerFrame,
                    MusicVisualizerApp as _MusicVisualizerApp
                )
            except ImportError:
                # Strategy 3: Direct file import
                import sys
                import os
                import importlib.util
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                music_viz_path = os.path.join(current_dir, 'music_visualizer.py')
                
                if os.path.exists(music_viz_path):
                    spec = importlib.util.spec_from_file_location("music_visualizer_module", music_viz_path)
                    music_viz_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(music_viz_module)
                    
                    _AudioVisualizer = music_viz_module.AudioVisualizer
                    _MusicVisualizerFrame = music_viz_module.MusicVisualizerFrame
                    _MusicVisualizerApp = music_viz_module.MusicVisualizerApp
                else:
                    raise ImportError("Could not locate music_visualizer.py file")
        
        AudioVisualizer = _AudioVisualizer
        MusicVisualizerFrame = _MusicVisualizerFrame
        MusicVisualizerApp = _MusicVisualizerApp
        _classes_imported = True

# Define what gets imported with "from music_visualizer import *"
__all__ = [
    'AudioVisualizer',
    'MusicVisualizerFrame', 
    'MusicVisualizerApp',
    'main',
    'music_maker'
]

def main():
    """
    Main entry point for the Music Visualizer application.
    
    This function creates and runs the wxPython application.
    Can be called from command line via: python -m music_visualizer
    """
    _ensure_imports()
    app = MusicVisualizerApp()
    app.MainLoop()

# Module-level getattr to support dynamic imports
def __getattr__(name):
    """Support for dynamic attribute access."""
    if name in ('AudioVisualizer', 'MusicVisualizerFrame', 'MusicVisualizerApp'):
        _ensure_imports()
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Compatibility with direct module execution
if __name__ == "__main__":
    main()
