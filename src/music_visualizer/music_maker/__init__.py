"""
Music Maker - A music composition and creation module for Music Visualizer.

This subpackage provides tools for creating, editing, and composing music
with a visual interface integrated into the Music Visualizer application.
"""

__version__ = "1.0.0"
__author__ = "Music Visualizer Developer"

# Import main classes for easy access
from .music_maker import (
    Note,
    Track,
    MusicMakerFrame,
    MusicMakerApp
)

# Define what gets imported with "from music_visualizer.music_maker import *"
__all__ = [
    'Note',
    'Track', 
    'MusicMakerFrame',
    'MusicMakerApp',
    'main'
]


def main():
    """
    Main entry point for the Music Maker application.
    
    Creates and runs the Music Maker wxPython application.
    Can be called from the main visualizer or standalone.
    """
    app = MusicMakerApp()
    app.MainLoop()


# Convenience function to launch music maker window
def launch_music_maker():
    """
    Launch Music Maker as a separate window.
    
    Returns:
        MusicMakerFrame: The created music maker window
    """
    import wx
    
    # Check if there's already a wx.App running
    app = wx.GetApp()
    if app is None:
        # No app running, create one
        app = wx.App()
        should_start_mainloop = True
    else:
        should_start_mainloop = False
    
    # Create the music maker frame
    frame = MusicMakerFrame()
    frame.Show()
    
    # Only start main loop if we created the app
    if should_start_mainloop:
        app.MainLoop()
    
    return frame


# Compatibility with direct module execution
if __name__ == "__main__":
    main()

