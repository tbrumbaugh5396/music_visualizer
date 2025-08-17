"""
Main entry point for running Music Visualizer as a module.

This file allows the package to be executed with:
    python -m music_visualizer

It imports and calls the main function from the music_visualizer module.
"""

# Import with fallback for different execution contexts
try:
    # Try relative import (standard package execution)
    from .music_visualizer import main
except ImportError:
    # Fall back to absolute import
    try:
        from music_visualizer.music_visualizer import main
    except ImportError:
        # Last resort - add current directory to path
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from music_visualizer import main

if __name__ == "__main__":
    main()
