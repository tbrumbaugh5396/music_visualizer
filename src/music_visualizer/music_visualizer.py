import wx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import threading
import time
import os
import glob

# Note: For full functionality, you would need pygame for audio playback
# and librosa for audio analysis. This is a demo version with simulated data.

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioVisualizer:

    def __init__(self):
        self.is_playing = False
        self.current_file = None
        self.volume = 70
        self.position = 0
        self.duration = 100

        if PYGAME_AVAILABLE:
            pygame.mixer.init(frequency=22050,
                              size=-16,
                              channels=2,
                              buffer=1024)

    def load_file(self, filepath):
        self.current_file = filepath
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.load(filepath)
                # Get approximate duration (would need librosa for exact duration)
                self.duration = 180  # Default 3 minutes for demo
                return True
            except Exception:
                return False
        return True

    def play(self):
        if PYGAME_AVAILABLE and self.current_file:
            pygame.mixer.music.play()
        self.is_playing = True

    def pause(self):
        if PYGAME_AVAILABLE:
            pygame.mixer.music.pause()
        self.is_playing = False

    def stop(self):
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.position = 0

    def set_volume(self, volume):
        self.volume = volume
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(volume / 100.0)

    def get_spectrum_data(self):
        """Generate demo spectrum data - in real implementation, use FFT on audio stream"""
        if self.is_playing:
            # Generate realistic-looking spectrum data
            freqs = np.linspace(0, 22050, 512)

            # Simulate different frequency responses for different types of music
            base_response = np.exp(-freqs / 5000) * np.random.random(512) * 0.8

            # Add some peaks for bass, mids, and highs
            bass_peak = np.exp(-((freqs - 80) / 50)**2) * 0.6
            mid_peak = np.exp(-((freqs - 1000) / 200)**2) * 0.4
            high_peak = np.exp(-((freqs - 8000) / 1000)**2) * 0.3

            spectrum = base_response + bass_peak + mid_peak + high_peak
            spectrum += np.random.random(512) * 0.1  # Add some noise

            return freqs[:256], spectrum[:256]  # Return half for display
        else:
            return np.linspace(0, 22050, 256), np.zeros(256)

    def get_waveform_data(self):
        """Generate demo waveform data"""
        if self.is_playing:
            t = np.linspace(0, 1, 1024)
            # Create a complex waveform with multiple harmonics
            wave = (np.sin(2 * np.pi * 440 * t) * 0.5 +
                    np.sin(2 * np.pi * 880 * t) * 0.3 +
                    np.sin(2 * np.pi * 1320 * t) * 0.2)
            wave += np.random.random(1024) * 0.1 - 0.05
            return t, wave
        else:
            return np.linspace(0, 1, 1024), np.zeros(1024)


class MusicVisualizerFrame(wx.Frame):

    def __init__(self):
        super().__init__(None, title="Music Visualizer", size=(1200, 800))

        self.audio_visualizer = AudioVisualizer()
        self.update_timer = None
        self.playlist = []
        self.current_track_index = 0

        # Center the window on screen
        self.Center()
        
        # Ensure window comes to front
        self.Raise()
        
        # Print startup message
        print("🎵 Music Visualizer starting...")
        print("🪟 GUI window should be visible now")

        self.init_ui()
        self.start_visualization_timer()

    def init_ui(self):
        # Create panel
        panel = wx.Panel(self)

        # Create menu bar
        self.create_menu_bar()

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Top section - Controls
        controls_panel = wx.Panel(panel)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # File controls
        open_btn = wx.Button(controls_panel, label="Open File")
        open_btn.Bind(wx.EVT_BUTTON, self.on_open_file)
        controls_sizer.Add(open_btn, 0, wx.ALL, 5)

        open_folder_btn = wx.Button(controls_panel, label="Open Folder")
        open_folder_btn.Bind(wx.EVT_BUTTON, self.on_open_folder)
        controls_sizer.Add(open_folder_btn, 0, wx.ALL, 5)

        music_maker_btn = wx.Button(controls_panel, label="Music Maker")
        music_maker_btn.Bind(wx.EVT_BUTTON, self.on_music_maker)
        controls_sizer.Add(music_maker_btn, 0, wx.ALL, 5)

        controls_sizer.Add(wx.StaticLine(controls_panel, style=wx.LI_VERTICAL),
                           0, wx.ALL | wx.EXPAND, 5)

        # Playback controls
        self.play_btn = wx.Button(controls_panel, label="Play")
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        controls_sizer.Add(self.play_btn, 0, wx.ALL, 5)

        pause_btn = wx.Button(controls_panel, label="Pause")
        pause_btn.Bind(wx.EVT_BUTTON, self.on_pause)
        controls_sizer.Add(pause_btn, 0, wx.ALL, 5)

        stop_btn = wx.Button(controls_panel, label="Stop")
        stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        controls_sizer.Add(stop_btn, 0, wx.ALL, 5)

        controls_sizer.Add(wx.StaticLine(controls_panel, style=wx.LI_VERTICAL),
                           0, wx.ALL | wx.EXPAND, 5)

        # Volume control
        controls_sizer.Add(wx.StaticText(controls_panel, label="Volume:"), 0,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.volume_slider = wx.Slider(controls_panel,
                                       value=70,
                                       minValue=0,
                                       maxValue=100,
                                       style=wx.SL_HORIZONTAL)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        controls_sizer.Add(self.volume_slider, 0,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.volume_label = wx.StaticText(controls_panel, label="70%")
        controls_sizer.Add(self.volume_label, 0,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        controls_panel.SetSizer(controls_sizer)
        main_sizer.Add(controls_panel, 0, wx.ALL | wx.EXPAND, 5)

        # Progress bar
        progress_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.time_label = wx.StaticText(panel, label="00:00")
        progress_sizer.Add(self.time_label, 0,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.progress_slider = wx.Slider(panel,
                                         value=0,
                                         minValue=0,
                                         maxValue=100,
                                         style=wx.SL_HORIZONTAL)
        self.progress_slider.Bind(wx.EVT_SLIDER, self.on_seek)
        progress_sizer.Add(self.progress_slider, 1,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.duration_label = wx.StaticText(panel, label="00:00")
        progress_sizer.Add(self.duration_label, 0,
                           wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        main_sizer.Add(progress_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # Current track info
        self.track_info = wx.StaticText(panel, label="No track loaded")
        font = self.track_info.GetFont()
        font.PointSize += 2
        font = font.Bold()
        self.track_info.SetFont(font)
        main_sizer.Add(self.track_info, 0, wx.ALL | wx.CENTER, 5)

        # Main content area
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left side - Playlist
        playlist_panel = wx.Panel(panel)
        playlist_sizer = wx.BoxSizer(wx.VERTICAL)

        playlist_sizer.Add(wx.StaticText(playlist_panel, label="Playlist"), 0,
                           wx.ALL, 5)

        self.playlist_ctrl = wx.ListCtrl(playlist_panel,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.playlist_ctrl.AppendColumn("Track", width=200)
        self.playlist_ctrl.AppendColumn("Duration", width=80)
        self.playlist_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                                self.on_playlist_double_click)

        playlist_sizer.Add(self.playlist_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # Playlist buttons
        playlist_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        clear_playlist_btn = wx.Button(playlist_panel, label="Clear")
        clear_playlist_btn.Bind(wx.EVT_BUTTON, self.on_clear_playlist)
        playlist_btn_sizer.Add(clear_playlist_btn, 0, wx.ALL, 2)

        shuffle_btn = wx.Button(playlist_panel, label="Shuffle")
        shuffle_btn.Bind(wx.EVT_BUTTON, self.on_shuffle_playlist)
        playlist_btn_sizer.Add(shuffle_btn, 0, wx.ALL, 2)

        playlist_sizer.Add(playlist_btn_sizer, 0, wx.ALL | wx.CENTER, 5)

        playlist_panel.SetSizer(playlist_sizer)
        content_sizer.Add(playlist_panel, 0, wx.ALL | wx.EXPAND, 5)

        # Right side - Visualizations
        viz_panel = wx.Panel(panel)
        viz_sizer = wx.BoxSizer(wx.VERTICAL)

        # Visualization controls
        viz_controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        viz_controls_sizer.Add(
            wx.StaticText(viz_panel, label="Visualization:"), 0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.viz_choice = wx.Choice(
            viz_panel, choices=["Spectrum", "Waveform", "Bars", "Circle"])
        self.viz_choice.SetSelection(0)
        self.viz_choice.Bind(wx.EVT_CHOICE, self.on_viz_changed)
        viz_controls_sizer.Add(self.viz_choice, 0, wx.ALL, 5)

        self.color_btn = wx.Button(viz_panel, label="Colors")
        self.color_btn.Bind(wx.EVT_BUTTON, self.on_change_colors)
        viz_controls_sizer.Add(self.color_btn, 0, wx.ALL, 5)

        viz_sizer.Add(viz_controls_sizer, 0, wx.ALL | wx.CENTER, 5)

        # Visualization canvas
        self.figure = Figure(figsize=(8, 6), facecolor='black')
        self.canvas = FigureCanvas(viz_panel, -1, self.figure)
        viz_sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 5)

        viz_panel.SetSizer(viz_sizer)
        content_sizer.Add(viz_panel, 1, wx.ALL | wx.EXPAND, 5)

        main_sizer.Add(content_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Status bar
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("Ready")

        panel.SetSizer(main_sizer)

        # Initialize visualization
        self.viz_colors = ['cyan', 'magenta', 'yellow', 'lime']
        self.current_color_index = 0
        self.update_visualization()

    def create_menu_bar(self):
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "&Open Audio File\tCtrl+O")
        file_menu.Append(wx.ID_ANY, "Open &Folder\tCtrl+Shift+O")
        file_menu.AppendSeparator()
        music_maker_id = wx.NewId()
        file_menu.Append(music_maker_id, "&Music Maker\tCtrl+M", "Launch Music Maker")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit")
        menu_bar.Append(file_menu, "&File")

        # Playback menu
        playback_menu = wx.Menu()
        playback_menu.Append(wx.ID_ANY, "&Play\tSpace")
        playback_menu.Append(wx.ID_ANY, "&Pause\tP")
        playback_menu.Append(wx.ID_ANY, "&Stop\tS")
        playback_menu.AppendSeparator()
        playback_menu.Append(wx.ID_ANY, "&Next Track\tCtrl+Right")
        playback_menu.Append(wx.ID_ANY, "&Previous Track\tCtrl+Left")
        menu_bar.Append(playback_menu, "&Playback")

        # View menu
        view_menu = wx.Menu()
        view_menu.Append(wx.ID_ANY, "&Fullscreen Visualization\tF11")
        view_menu.Append(wx.ID_ANY, "&Settings")
        menu_bar.Append(view_menu, "&View")

        self.SetMenuBar(menu_bar)

        # Bind events
        self.Bind(wx.EVT_MENU, self.on_open_file, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_music_maker, id=music_maker_id)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

    def start_visualization_timer(self):
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_update)
        self.update_timer.Start(50)  # Update every 50ms

    def on_timer_update(self, event):
        if self.audio_visualizer.is_playing:
            # Update progress
            self.audio_visualizer.position += 0.05  # Simulated progress
            if self.audio_visualizer.position >= self.audio_visualizer.duration:
                self.audio_visualizer.position = self.audio_visualizer.duration
                self.on_stop(None)

            # Update UI
            self.update_progress_display()
            self.update_visualization()

    def update_progress_display(self):
        position = self.audio_visualizer.position
        duration = self.audio_visualizer.duration

        # Update progress slider
        if duration > 0:
            progress_percent = (position / duration) * 100
            self.progress_slider.SetValue(int(progress_percent))

        # Update time labels
        pos_min, pos_sec = divmod(int(position), 60)
        dur_min, dur_sec = divmod(int(duration), 60)

        self.time_label.SetLabel(f"{pos_min:02d}:{pos_sec:02d}")
        self.duration_label.SetLabel(f"{dur_min:02d}:{dur_sec:02d}")

    def on_open_file(self, event):
        wildcard = "Audio files (*.mp3;*.wav;*.ogg)|*.mp3;*.wav;*.ogg|All files (*.*)|*.*"

        with wx.FileDialog(self,
                           "Open audio file",
                           wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                self.load_audio_file(filepath)

    def on_open_folder(self, event):
        with wx.DirDialog(self, "Choose a folder with audio files") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                folder_path = dialog.GetPath()
                self.load_folder(folder_path)

    def load_audio_file(self, filepath):
        if self.audio_visualizer.load_file(filepath):
            self.track_info.SetLabel(os.path.basename(filepath))
            self.status_bar.SetStatusText(
                f"Loaded: {os.path.basename(filepath)}")

            # Add to playlist if not already there
            if filepath not in [item[0] for item in self.playlist]:
                self.add_to_playlist(filepath)
        else:
            wx.MessageBox("Failed to load audio file.", "Error",
                          wx.OK | wx.ICON_ERROR)

    def load_folder(self, folder_path):
        audio_extensions = ['*.mp3', '*.wav', '*.ogg', '*.flac', '*.m4a']
        audio_files = []

        for ext in audio_extensions:
            audio_files.extend(glob.glob(os.path.join(folder_path, ext)))
            audio_files.extend(
                glob.glob(os.path.join(folder_path, ext.upper())))

        if audio_files:
            self.playlist.clear()
            self.playlist_ctrl.DeleteAllItems()

            for filepath in sorted(audio_files):
                self.add_to_playlist(filepath)

            # Load first file
            if self.playlist:
                self.load_audio_file(self.playlist[0][0])

            self.status_bar.SetStatusText(
                f"Loaded {len(audio_files)} audio files")
        else:
            wx.MessageBox("No audio files found in the selected folder.",
                          "No Files", wx.OK | wx.ICON_WARNING)

    def add_to_playlist(self, filepath):
        filename = os.path.basename(filepath)
        duration = "03:30"  # Demo duration

        self.playlist.append((filepath, duration))

        index = self.playlist_ctrl.InsertItem(len(self.playlist) - 1, filename)
        self.playlist_ctrl.SetItem(index, 1, duration)

    def on_playlist_double_click(self, event):
        selected = event.GetIndex()
        if selected >= 0 and selected < len(self.playlist):
            filepath = self.playlist[selected][0]
            self.load_audio_file(filepath)
            self.current_track_index = selected

    def on_clear_playlist(self, event):
        self.playlist.clear()
        self.playlist_ctrl.DeleteAllItems()
        self.current_track_index = 0

    def on_shuffle_playlist(self, event):
        import random
        random.shuffle(self.playlist)
        self.update_playlist_display()

    def update_playlist_display(self):
        self.playlist_ctrl.DeleteAllItems()
        for i, (filepath, duration) in enumerate(self.playlist):
            filename = os.path.basename(filepath)
            index = self.playlist_ctrl.InsertItem(i, filename)
            self.playlist_ctrl.SetItem(index, 1, duration)

    def on_play(self, event):
        self.audio_visualizer.play()
        self.play_btn.SetLabel("Playing...")
        self.status_bar.SetStatusText("Playing")

    def on_pause(self, event):
        self.audio_visualizer.pause()
        self.play_btn.SetLabel("Play")
        self.status_bar.SetStatusText("Paused")

    def on_stop(self, event):
        self.audio_visualizer.stop()
        self.play_btn.SetLabel("Play")
        self.progress_slider.SetValue(0)
        self.time_label.SetLabel("00:00")
        self.status_bar.SetStatusText("Stopped")

    def on_volume_change(self, event):
        volume = self.volume_slider.GetValue()
        self.audio_visualizer.set_volume(volume)
        self.volume_label.SetLabel(f"{volume}%")

    def on_seek(self, event):
        if self.audio_visualizer.duration > 0:
            position = (self.progress_slider.GetValue() /
                        100.0) * self.audio_visualizer.duration
            self.audio_visualizer.position = position

    def on_viz_changed(self, event):
        self.update_visualization()

    def on_change_colors(self, event):
        self.current_color_index = (self.current_color_index + 1) % len(
            self.viz_colors)
        self.update_visualization()

    def update_visualization(self):
        self.figure.clear()

        viz_type = self.viz_choice.GetSelection()
        color = self.viz_colors[self.current_color_index]

        if viz_type == 0:  # Spectrum
            self.draw_spectrum(color)
        elif viz_type == 1:  # Waveform
            self.draw_waveform(color)
        elif viz_type == 2:  # Bars
            self.draw_bars(color)
        elif viz_type == 3:  # Circle
            self.draw_circle(color)

        self.canvas.draw()

    def draw_spectrum(self, color):
        ax = self.figure.add_subplot(111, facecolor='black')

        freqs, spectrum = self.audio_visualizer.get_spectrum_data()

        ax.fill_between(freqs, spectrum, alpha=0.7, color=color)
        ax.plot(freqs, spectrum, color=color, linewidth=2)

        ax.set_xlim(0, 10000)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Frequency (Hz)', color='white')
        ax.set_ylabel('Amplitude', color='white')
        ax.set_title('Frequency Spectrum', color='white')
        ax.tick_params(colors='white')

        # Remove spines
        for spine in ax.spines.values():
            spine.set_color('white')

    def draw_waveform(self, color):
        ax = self.figure.add_subplot(111, facecolor='black')

        t, wave = self.audio_visualizer.get_waveform_data()

        ax.plot(t, wave, color=color, linewidth=1)
        ax.fill_between(t, wave, alpha=0.3, color=color)

        ax.set_xlim(0, 1)
        ax.set_ylim(-1, 1)
        ax.set_xlabel('Time', color='white')
        ax.set_ylabel('Amplitude', color='white')
        ax.set_title('Waveform', color='white')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')

    def draw_bars(self, color):
        ax = self.figure.add_subplot(111, facecolor='black')

        freqs, spectrum = self.audio_visualizer.get_spectrum_data()

        # Group frequencies into bars
        num_bars = 32
        bar_width = len(spectrum) // num_bars
        bar_heights = []

        for i in range(num_bars):
            start_idx = i * bar_width
            end_idx = min((i + 1) * bar_width, len(spectrum))
            bar_heights.append(np.mean(spectrum[start_idx:end_idx]))

        bars = ax.bar(range(num_bars), bar_heights, color=color, alpha=0.8)

        # Add glow effect
        for bar in bars:
            height = bar.get_height()
            ax.bar(bar.get_x(),
                   height * 0.5,
                   bar.get_width(),
                   bottom=height * 0.5,
                   color=color,
                   alpha=0.3)

        ax.set_xlim(-0.5, num_bars - 0.5)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Frequency Bands', color='white')
        ax.set_ylabel('Amplitude', color='white')
        ax.set_title('Frequency Bars', color='white')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')

    def draw_circle(self, color):
        ax = self.figure.add_subplot(111, facecolor='black')

        freqs, spectrum = self.audio_visualizer.get_spectrum_data()

        # Create circular visualization
        num_points = 64
        angles = np.linspace(0, 2 * np.pi, num_points)

        # Sample spectrum data
        indices = np.linspace(0, len(spectrum) - 1, num_points).astype(int)
        amplitudes = spectrum[indices]

        # Convert to polar coordinates
        radius_base = 0.3
        radius = radius_base + amplitudes * 0.4

        x = radius * np.cos(angles)
        y = radius * np.sin(angles)

        # Close the circle
        x = np.append(x, x[0])
        y = np.append(y, y[0])

        ax.fill(x, y, alpha=0.7, color=color)
        ax.plot(x, y, color=color, linewidth=2)

        # Add center circle
        circle = plt.Circle((0, 0), radius_base, color=color, alpha=0.3)
        ax.add_patch(circle)

        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect('equal')
        ax.set_title('Circular Spectrum', color='white')
        ax.axis('off')

    def on_music_maker(self, event):
        """Launch the Music Maker application."""
        try:
            # Try different import strategies to handle both package and script execution
            launch_music_maker = None
            
            # Strategy 1: Relative import (when running as package)
            try:
                from .music_maker import launch_music_maker
            except (ImportError, SystemError, ValueError):
                # Strategy 2: Absolute import (when running as script)
                try:
                    from music_visualizer.music_maker import launch_music_maker
                except ImportError:
                    # Strategy 3: Direct import with path manipulation
                    import sys
                    import os
                    import importlib.util
                    
                    # Get the directory of this file
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    music_maker_path = os.path.join(current_dir, 'music_maker', '__init__.py')
                    
                    if os.path.exists(music_maker_path):
                        spec = importlib.util.spec_from_file_location("music_maker", music_maker_path)
                        music_maker_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(music_maker_module)
                        launch_music_maker = music_maker_module.launch_music_maker
                    else:
                        raise ImportError("Could not locate music_maker module")
            
            if launch_music_maker:
                launch_music_maker()
                self.status_bar.SetStatusText("Music Maker launched")
            else:
                raise ImportError("Could not import launch_music_maker function")
                
        except Exception as e:
            error_msg = f"Failed to launch Music Maker: {e}"
            print(f"Debug: {error_msg}")  # Debug output
            wx.MessageBox(error_msg, "Error", wx.OK | wx.ICON_ERROR)

    def on_exit(self, event):
        if self.update_timer:
            self.update_timer.Stop()
        self.Close()


class MusicVisualizerApp(wx.App):

    def OnInit(self):
        frame = MusicVisualizerFrame()
        frame.Show()
        return True


def main():
    """
    Main entry point for the Music Visualizer application.
    
    Creates and runs the wxPython application instance.
    """
    print("🚀 Starting Music Visualizer...")
    print("📱 If you don't see the window, check your dock/taskbar")
    
    app = MusicVisualizerApp()
    print("✅ Application created, starting main loop...")
    app.MainLoop()
    
    print("👋 Music Visualizer closed.")


if __name__ == "__main__":
    main()
