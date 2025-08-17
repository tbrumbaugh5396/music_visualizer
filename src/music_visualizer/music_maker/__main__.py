"""
Main entry point for running Music Maker as a module.

This file allows the music_maker subpackage to be executed with:
    python -m music_visualizer.music_maker

It imports and calls the main function from the music_maker module.
"""

from . import main

if __name__ == "__main__":
    main()

