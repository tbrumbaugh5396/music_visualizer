import wx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
import threading
import time
import json
import os


class Note:

    def __init__(self, pitch, duration, start_time, velocity=80):
        self.pitch = pitch  # MIDI note number
        self.duration = duration  # In beats
        self.start_time = start_time  # In beats
        self.velocity = velocity  # 0-127

    def __repr__(self):
        return f"Note(pitch={self.pitch}, duration={self.duration}, start={self.start_time})"


class Track:

    def __init__(self, name="Track", instrument=0, channel=0):
        self.name = name
        self.instrument = instrument
        self.channel = channel
        self.notes = []
        self.volume = 80
        self.muted = False
        self.solo = False

    def add_note(self, note):
        self.notes.append(note)

    def remove_note(self, note):
        if note in self.notes:
            self.notes.remove(note)

    def get_notes_in_range(self, start_time, end_time):
        return [
            note for note in self.notes
            if note.start_time < end_time and note.start_time +
            note.duration > start_time
        ]


class MusicProject:

    def __init__(self):
        self.tracks = []
        self.tempo = 120  # BPM
        self.time_signature = (4, 4)  # (numerator, denominator)
        self.key = "C"
        self.length = 16  # bars
        self.project_name = "Untitled"

    def add_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track):
        if track in self.tracks:
            self.tracks.remove(track)


class MusicMakerFrame(wx.Frame):

    def __init__(self):
        super().__init__(None, title="Music Maker", size=(1400, 900))

        self.project = MusicProject()
        self.current_track = None
        self.is_playing = False
        self.playback_position = 0
        self.selected_notes = []

        # Music theory data
        self.note_names = [
            'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
        ]
        self.scales = {
            'Major': [0, 2, 4, 5, 7, 9, 11],
            'Minor': [0, 2, 3, 5, 7, 8, 10],
            'Pentatonic': [0, 2, 4, 7, 9],
            'Blues': [0, 3, 5, 6, 7, 10],
            'Dorian': [0, 2, 3, 5, 7, 9, 10],
            'Mixolydian': [0, 2, 4, 5, 7, 9, 10]
        }

        # Initialize pygame mixer if available
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050,
                                  size=-16,
                                  channels=2,
                                  buffer=512)
                self.audio_enabled = True
            except:
                self.audio_enabled = False
        else:
            self.audio_enabled = False

        self.init_ui()
        self.create_default_track()

    def init_ui(self):
        panel = wx.Panel(self)

        # Create menu bar
        self.create_menu_bar()

        # Create notebook for different views
        self.notebook = wx.Notebook(panel)

        # Piano Roll tab
        self.piano_roll_panel = wx.Panel(self.notebook)
        self.setup_piano_roll_tab()
        self.notebook.AddPage(self.piano_roll_panel, "Piano Roll")

        # Mixer tab
        self.mixer_panel = wx.Panel(self.notebook)
        self.setup_mixer_tab()
        self.notebook.AddPage(self.mixer_panel, "Mixer")

        # Pattern tab
        self.pattern_panel = wx.Panel(self.notebook)
        self.setup_pattern_tab()
        self.notebook.AddPage(self.pattern_panel, "Patterns")

        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Transport controls
        transport_panel = wx.Panel(panel)
        transport_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.play_btn = wx.Button(transport_panel, label="▶ Play")
        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        transport_sizer.Add(self.play_btn, 0, wx.ALL, 5)

        self.stop_btn = wx.Button(transport_panel, label="⏹ Stop")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        transport_sizer.Add(self.stop_btn, 0, wx.ALL, 5)

        self.record_btn = wx.Button(transport_panel, label="⏺ Record")
        self.record_btn.Bind(wx.EVT_BUTTON, self.on_record)
        transport_sizer.Add(self.record_btn, 0, wx.ALL, 5)

        # Tempo control
        transport_sizer.Add(wx.StaticText(transport_panel, label="Tempo:"), 0,
                            wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.tempo_ctrl = wx.SpinCtrl(transport_panel,
                                      min=60,
                                      max=200,
                                      initial=120)
        self.tempo_ctrl.Bind(wx.EVT_SPINCTRL, self.on_tempo_changed)
        transport_sizer.Add(self.tempo_ctrl, 0, wx.ALL, 5)

        # Position display
        transport_sizer.Add(wx.StaticText(transport_panel, label="Position:"),
                            0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.position_text = wx.StaticText(transport_panel, label="0:0:0")
        transport_sizer.Add(self.position_text, 0,
                            wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        transport_panel.SetSizer(transport_sizer)
        main_sizer.Add(transport_panel, 0, wx.ALL | wx.EXPAND, 5)

        # Notebook
        main_sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(main_sizer)

        # Status bar
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("Ready" + (
            " - Audio Enabled" if self.audio_enabled else " - Audio Disabled"))

    def setup_piano_roll_tab(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left panel - Tools and track list
        left_panel = wx.Panel(self.piano_roll_panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Tools
        tools_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel, "Tools")

        self.select_tool = wx.RadioButton(left_panel,
                                          label="Select",
                                          style=wx.RB_GROUP)
        self.select_tool.SetValue(True)
        tools_box.Add(self.select_tool, 0, wx.ALL, 5)

        self.pencil_tool = wx.RadioButton(left_panel, label="Pencil")
        tools_box.Add(self.pencil_tool, 0, wx.ALL, 5)

        self.eraser_tool = wx.RadioButton(left_panel, label="Eraser")
        tools_box.Add(self.eraser_tool, 0, wx.ALL, 5)

        left_sizer.Add(tools_box, 0, wx.ALL | wx.EXPAND, 5)

        # Track list
        tracks_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel, "Tracks")

        self.tracks_list = wx.ListBox(left_panel, size=(200, 200))
        self.tracks_list.Bind(wx.EVT_LISTBOX, self.on_track_selected)
        tracks_box.Add(self.tracks_list, 1, wx.ALL | wx.EXPAND, 5)

        # Track controls
        track_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_track_btn = wx.Button(left_panel, label="Add", size=(60, 25))
        add_track_btn.Bind(wx.EVT_BUTTON, self.on_add_track)
        track_btn_sizer.Add(add_track_btn, 0, wx.ALL, 2)

        remove_track_btn = wx.Button(left_panel, label="Remove", size=(60, 25))
        remove_track_btn.Bind(wx.EVT_BUTTON, self.on_remove_track)
        track_btn_sizer.Add(remove_track_btn, 0, wx.ALL, 2)

        tracks_box.Add(track_btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        left_sizer.Add(tracks_box, 1, wx.ALL | wx.EXPAND, 5)

        # Note properties
        props_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel,
                                      "Note Properties")

        props_sizer = wx.FlexGridSizer(4, 2, 5, 5)

        props_sizer.Add(wx.StaticText(left_panel, label="Pitch:"))
        self.pitch_ctrl = wx.SpinCtrl(left_panel, min=0, max=127, initial=60)
        props_sizer.Add(self.pitch_ctrl)

        props_sizer.Add(wx.StaticText(left_panel, label="Velocity:"))
        self.velocity_ctrl = wx.SpinCtrl(left_panel,
                                         min=1,
                                         max=127,
                                         initial=80)
        props_sizer.Add(self.velocity_ctrl)

        props_sizer.Add(wx.StaticText(left_panel, label="Duration:"))
        self.duration_choice = wx.Choice(
            left_panel, choices=["1/16", "1/8", "1/4", "1/2", "1"])
        self.duration_choice.SetSelection(2)  # 1/4 note
        props_sizer.Add(self.duration_choice)

        props_sizer.Add(wx.StaticText(left_panel, label="Quantize:"))
        self.quantize_choice = wx.Choice(
            left_panel, choices=["None", "1/16", "1/8", "1/4"])
        self.quantize_choice.SetSelection(3)  # 1/4 note
        props_sizer.Add(self.quantize_choice)

        props_box.Add(props_sizer, 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(props_box, 0, wx.ALL | wx.EXPAND, 5)

        # Scale helper
        scale_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel, "Scale Helper")

        scale_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scale_sizer.Add(wx.StaticText(left_panel, label="Key:"), 0,
                        wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.key_choice = wx.Choice(left_panel, choices=self.note_names)
        self.key_choice.SetSelection(0)  # C
        scale_sizer.Add(self.key_choice, 0, wx.ALL, 5)

        scale_sizer.Add(wx.StaticText(left_panel, label="Scale:"), 0,
                        wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.scale_choice = wx.Choice(left_panel,
                                      choices=list(self.scales.keys()))
        self.scale_choice.SetSelection(0)  # Major
        scale_sizer.Add(self.scale_choice, 0, wx.ALL, 5)

        scale_box.Add(scale_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.snap_to_scale_cb = wx.CheckBox(left_panel, label="Snap to Scale")
        scale_box.Add(self.snap_to_scale_cb, 0, wx.ALL, 5)

        left_sizer.Add(scale_box, 0, wx.ALL | wx.EXPAND, 5)

        left_panel.SetSizer(left_sizer)
        sizer.Add(left_panel, 0, wx.ALL | wx.EXPAND, 5)

        # Right panel - Piano roll display
        self.piano_roll_figure = Figure(figsize=(12, 8))
        self.piano_roll_canvas = FigureCanvas(self.piano_roll_panel, -1,
                                              self.piano_roll_figure)
        self.piano_roll_canvas.Bind(wx.EVT_LEFT_DOWN, self.on_piano_roll_click)
        self.piano_roll_canvas.Bind(wx.EVT_MOTION, self.on_piano_roll_motion)
        sizer.Add(self.piano_roll_canvas, 1, wx.ALL | wx.EXPAND, 5)

        self.piano_roll_panel.SetSizer(sizer)

    def setup_mixer_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Mixer strips
        mixer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create mixer strips for tracks
        self.mixer_strips = []

        # Master strip
        master_strip = self.create_mixer_strip(self.mixer_panel,
                                               "Master",
                                               is_master=True)
        mixer_sizer.Add(master_strip, 0, wx.ALL | wx.EXPAND, 5)

        sizer.Add(mixer_sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Effects section
        effects_box = wx.StaticBoxSizer(wx.HORIZONTAL, self.mixer_panel,
                                        "Effects")

        # Add some basic effect controls
        reverb_box = wx.StaticBoxSizer(wx.VERTICAL, self.mixer_panel, "Reverb")
        self.reverb_cb = wx.CheckBox(self.mixer_panel, label="Enable Reverb")
        reverb_box.Add(self.reverb_cb, 0, wx.ALL, 5)

        reverb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reverb_sizer.Add(wx.StaticText(self.mixer_panel, label="Room Size:"),
                         0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.reverb_size_slider = wx.Slider(self.mixer_panel,
                                            value=50,
                                            minValue=0,
                                            maxValue=100)
        reverb_sizer.Add(self.reverb_size_slider, 1, wx.ALL | wx.EXPAND, 5)
        reverb_box.Add(reverb_sizer, 0, wx.ALL | wx.EXPAND, 5)

        effects_box.Add(reverb_box, 1, wx.ALL | wx.EXPAND, 5)

        sizer.Add(effects_box, 0, wx.ALL | wx.EXPAND, 5)

        self.mixer_panel.SetSizer(sizer)

    def setup_pattern_tab(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left panel - Pattern controls
        left_panel = wx.Panel(self.pattern_panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Pattern list
        patterns_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel, "Patterns")

        self.patterns_list = wx.ListBox(left_panel, size=(200, 150))
        patterns_box.Add(self.patterns_list, 1, wx.ALL | wx.EXPAND, 5)

        pattern_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        new_pattern_btn = wx.Button(left_panel, label="New", size=(60, 25))
        new_pattern_btn.Bind(wx.EVT_BUTTON, self.on_new_pattern)
        pattern_btn_sizer.Add(new_pattern_btn, 0, wx.ALL, 2)

        load_pattern_btn = wx.Button(left_panel, label="Load", size=(60, 25))
        load_pattern_btn.Bind(wx.EVT_BUTTON, self.on_load_pattern)
        pattern_btn_sizer.Add(load_pattern_btn, 0, wx.ALL, 2)

        patterns_box.Add(pattern_btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        left_sizer.Add(patterns_box, 0, wx.ALL | wx.EXPAND, 5)

        # Chord progression
        chord_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel,
                                      "Chord Progression")

        self.chord_text = wx.TextCtrl(left_panel,
                                      style=wx.TE_MULTILINE,
                                      size=(200, 100))
        self.chord_text.SetValue("C - Am - F - G")
        chord_box.Add(self.chord_text, 1, wx.ALL | wx.EXPAND, 5)

        generate_chord_btn = wx.Button(left_panel, label="Generate Chords")
        generate_chord_btn.Bind(wx.EVT_BUTTON, self.on_generate_chords)
        chord_box.Add(generate_chord_btn, 0, wx.ALL | wx.EXPAND, 5)

        left_sizer.Add(chord_box, 1, wx.ALL | wx.EXPAND, 5)

        # Rhythm patterns
        rhythm_box = wx.StaticBoxSizer(wx.VERTICAL, left_panel,
                                       "Rhythm Patterns")

        rhythm_choices = [
            "4/4 Basic", "4/4 Rock", "3/4 Waltz", "6/8 Compound", "Custom"
        ]
        self.rhythm_choice = wx.Choice(left_panel, choices=rhythm_choices)
        self.rhythm_choice.SetSelection(0)
        rhythm_box.Add(self.rhythm_choice, 0, wx.ALL | wx.EXPAND, 5)

        apply_rhythm_btn = wx.Button(left_panel, label="Apply Rhythm")
        apply_rhythm_btn.Bind(wx.EVT_BUTTON, self.on_apply_rhythm)
        rhythm_box.Add(apply_rhythm_btn, 0, wx.ALL | wx.EXPAND, 5)

        left_sizer.Add(rhythm_box, 0, wx.ALL | wx.EXPAND, 5)

        left_panel.SetSizer(left_sizer)
        sizer.Add(left_panel, 0, wx.ALL | wx.EXPAND, 5)

        # Right panel - Pattern visualization
        self.pattern_figure = Figure(figsize=(8, 6))
        self.pattern_canvas = FigureCanvas(self.pattern_panel, -1,
                                           self.pattern_figure)
        sizer.Add(self.pattern_canvas, 1, wx.ALL | wx.EXPAND, 5)

        self.pattern_panel.SetSizer(sizer)

    def create_mixer_strip(self, parent, name, is_master=False):
        strip_panel = wx.Panel(parent)
        strip_sizer = wx.BoxSizer(wx.VERTICAL)

        # Track name
        name_label = wx.StaticText(strip_panel, label=name)
        strip_sizer.Add(name_label, 0, wx.ALL | wx.CENTER, 5)

        # Volume fader
        volume_slider = wx.Slider(strip_panel,
                                  value=80,
                                  minValue=0,
                                  maxValue=127,
                                  style=wx.SL_VERTICAL | wx.SL_LABELS,
                                  size=(50, 200))
        strip_sizer.Add(volume_slider, 1, wx.ALL | wx.CENTER, 5)

        # Mute/Solo buttons
        if not is_master:
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

            mute_btn = wx.ToggleButton(strip_panel, label="M", size=(25, 25))
            btn_sizer.Add(mute_btn, 0, wx.ALL, 2)

            solo_btn = wx.ToggleButton(strip_panel, label="S", size=(25, 25))
            btn_sizer.Add(solo_btn, 0, wx.ALL, 2)

            strip_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)

        strip_panel.SetSizer(strip_sizer)
        self.mixer_strips.append(strip_panel)

        return strip_panel

    def create_menu_bar(self):
        menu_bar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New Project\tCtrl+N")
        file_menu.Append(wx.ID_OPEN, "&Open Project\tCtrl+O")
        file_menu.Append(wx.ID_SAVE, "&Save Project\tCtrl+S")
        file_menu.Append(wx.ID_SAVEAS, "Save &As...")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_ANY, "&Export MIDI")
        file_menu.Append(wx.ID_ANY, "&Export Audio")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit")
        menu_bar.Append(file_menu, "&File")

        # Edit menu
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z")
        edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y")
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        edit_menu.Append(wx.ID_DELETE, "&Delete\tDel")
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        menu_bar.Append(edit_menu, "&Edit")

        # View menu
        view_menu = wx.Menu()
        view_menu.Append(wx.ID_ANY, "&Piano Roll")
        view_menu.Append(wx.ID_ANY, "&Mixer")
        view_menu.Append(wx.ID_ANY, "&Pattern Editor")
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_ANY, "&Zoom In\tCtrl++")
        view_menu.Append(wx.ID_ANY, "&Zoom Out\tCtrl+-")
        menu_bar.Append(view_menu, "&View")

        # Tools menu
        tools_menu = wx.Menu()
        tools_menu.Append(wx.ID_ANY, "&Metronome")
        tools_menu.Append(wx.ID_ANY, "&Tuner")
        tools_menu.Append(wx.ID_ANY, "&Scale Helper")
        tools_menu.Append(wx.ID_ANY, "&Chord Generator")
        menu_bar.Append(tools_menu, "&Tools")

        self.SetMenuBar(menu_bar)

        # Bind events
        self.Bind(wx.EVT_MENU, self.on_new_project, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_open_project, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save_project, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

    def create_default_track(self):
        """Create a default track"""
        track = Track("Track 1", instrument=0)
        self.project.add_track(track)
        self.current_track = track
        self.update_tracks_list()
        self.update_piano_roll()

    def update_tracks_list(self):
        """Update the tracks list display"""
        self.tracks_list.Clear()
        for i, track in enumerate(self.project.tracks):
            self.tracks_list.Append(f"{i+1}: {track.name}")

        if self.current_track and self.current_track in self.project.tracks:
            index = self.project.tracks.index(self.current_track)
            self.tracks_list.SetSelection(index)

    def update_piano_roll(self):
        """Update the piano roll display"""
        self.piano_roll_figure.clear()

        ax = self.piano_roll_figure.add_subplot(111)

        # Set up the piano roll grid
        measures = self.project.length
        beats_per_measure = self.project.time_signature[0]
        total_beats = measures * beats_per_measure

        # MIDI note range (show piano keys)
        min_note = 36  # C2
        max_note = 96  # C7

        ax.set_xlim(0, total_beats)
        ax.set_ylim(min_note, max_note)

        # Draw grid
        # Vertical lines (beats)
        for beat in range(int(total_beats) + 1):
            color = 'black' if beat % beats_per_measure == 0 else 'gray'
            alpha = 0.8 if beat % beats_per_measure == 0 else 0.3
            ax.axvline(beat, color=color, alpha=alpha, linewidth=1)

        # Horizontal lines (piano keys)
        for note in range(min_note, max_note + 1):
            note_name = self.note_names[note % 12]
            color = 'black' if '#' in note_name else 'gray'
            alpha = 0.3 if '#' in note_name else 0.1
            ax.axhline(note, color=color, alpha=alpha, linewidth=0.5)

        # Draw notes for current track
        if self.current_track:
            for note in self.current_track.notes:
                # Draw note as rectangle
                rect = plt.Rectangle((note.start_time, note.pitch - 0.4),
                                     note.duration,
                                     0.8,
                                     facecolor='blue',
                                     edgecolor='darkblue',
                                     alpha=0.7)
                ax.add_patch(rect)

        # Draw playback position
        if self.is_playing:
            ax.axvline(self.playback_position,
                       color='red',
                       linewidth=2,
                       alpha=0.8)

        ax.set_xlabel('Time (beats)')
        ax.set_ylabel('MIDI Note')
        ax.set_title(
            f'Piano Roll - {self.current_track.name if self.current_track else "No Track"}'
        )

        # Add note names on y-axis
        note_ticks = []
        note_labels = []
        for octave in range(2, 8):  # C2 to C7
            for i, note_name in enumerate(self.note_names):
                if note_name in ['C', 'E',
                                 'G']:  # Show only some notes to avoid clutter
                    note_num = octave * 12 + i
                    if min_note <= note_num <= max_note:
                        note_ticks.append(note_num)
                        note_labels.append(f'{note_name}{octave}')

        ax.set_yticks(note_ticks)
        ax.set_yticklabels(note_labels)

        self.piano_roll_figure.tight_layout()
        self.piano_roll_canvas.draw()

    def update_pattern_display(self):
        """Update the pattern visualization"""
        self.pattern_figure.clear()

        # Create a chord progression visualization
        ax = self.pattern_figure.add_subplot(111)

        chord_text = self.chord_text.GetValue()
        chords = [
            chord.strip() for chord in chord_text.split('-') if chord.strip()
        ]

        if chords:
            x_positions = range(len(chords))
            ax.bar(x_positions, [1] * len(chords),
                   alpha=0.7,
                   color='lightblue')

            for i, chord in enumerate(chords):
                ax.text(i,
                        0.5,
                        chord,
                        ha='center',
                        va='center',
                        fontsize=12,
                        fontweight='bold')

            ax.set_xlim(-0.5, len(chords) - 0.5)
            ax.set_ylim(0, 1)
            ax.set_xlabel('Chord Position')
            ax.set_title('Chord Progression')
            ax.set_xticks(x_positions)
            ax.set_xticklabels([f'{i+1}' for i in x_positions])
            ax.set_yticks([])

        self.pattern_figure.tight_layout()
        self.pattern_canvas.draw()

    def note_name_to_midi(self, note_name):
        """Convert note name (e.g., 'C4') to MIDI number"""
        if len(note_name) < 2:
            return 60  # Default to C4

        note = note_name[:-1]
        try:
            octave = int(note_name[-1])
        except:
            octave = 4

        if note in self.note_names:
            note_num = self.note_names.index(note)
            return octave * 12 + note_num
        return 60

    def midi_to_note_name(self, midi_num):
        """Convert MIDI number to note name"""
        octave = midi_num // 12
        note = self.note_names[midi_num % 12]
        return f"{note}{octave}"

    def get_duration_value(self):
        """Get duration value from selection"""
        duration_map = {
            "1/16": 0.25,
            "1/8": 0.5,
            "1/4": 1.0,
            "1/2": 2.0,
            "1": 4.0
        }
        return duration_map.get(self.duration_choice.GetStringSelection(), 1.0)

    def on_piano_roll_click(self, event):
        """Handle clicks on piano roll"""
        if not self.current_track:
            return

        # Get click position - convert wxPython coordinates to matplotlib data coordinates
        ax = self.piano_roll_figure.get_axes()[0]
        
        # Get mouse position in pixels from wxPython event
        pos = event.GetPosition()
        
        # Convert display coordinates to data coordinates
        try:
            # Transform from display coordinates to data coordinates
            inv = ax.transData.inverted()
            x, y = inv.transform(pos)
        except:
            return

        if x is None or y is None:
            return

        # Quantize position if enabled
        quantize_value = self.get_quantize_value()
        if quantize_value > 0:
            x = round(x / quantize_value) * quantize_value

        # Round y to nearest semitone
        y = int(round(y))

        # Snap to scale if enabled
        if self.snap_to_scale_cb.GetValue():
            y = self.snap_to_scale(y)

        if self.pencil_tool.GetValue():
            # Add note
            duration = self.get_duration_value()
            velocity = self.velocity_ctrl.GetValue()

            # Check if note already exists at this position
            existing_note = None
            for note in self.current_track.notes:
                if (abs(note.start_time - x) < 0.1 and note.pitch == y):
                    existing_note = note
                    break

            if not existing_note:
                new_note = Note(y, duration, x, velocity)
                self.current_track.add_note(new_note)
                self.update_piano_roll()
                self.status_bar.SetStatusText(
                    f"Added note: {self.midi_to_note_name(y)}")
                
                # Play audio feedback for the added note
                if self.audio_enabled:
                    self.play_midi_note(y, velocity)

        elif self.eraser_tool.GetValue():
            # Remove note
            notes_to_remove = []
            for note in self.current_track.notes:
                if (abs(note.start_time - x) < 0.5
                        and abs(note.pitch - y) < 0.5):
                    notes_to_remove.append(note)

            for note in notes_to_remove:
                self.current_track.remove_note(note)

            if notes_to_remove:
                self.update_piano_roll()
                self.status_bar.SetStatusText("Removed note(s)")

    def on_piano_roll_motion(self, event):
        """Handle mouse motion over piano roll"""
        # Convert wxPython coordinates to matplotlib data coordinates
        ax = self.piano_roll_figure.get_axes()[0]
        
        # Get mouse position in pixels from wxPython event
        pos = event.GetPosition()
        
        # Convert display coordinates to data coordinates
        try:
            # Transform from display coordinates to data coordinates
            inv = ax.transData.inverted()
            x, y = inv.transform(pos)
            
            # Check if coordinates are valid (within plot area)
            if x is not None and y is not None:
                note_name = self.midi_to_note_name(int(round(y)))
                time_pos = f"{x:.2f}"
                self.status_bar.SetStatusText(
                    f"Position: {time_pos} beats, Note: {note_name}")
        except:
            # Clear status bar if coordinate conversion fails
            self.status_bar.SetStatusText("")

    def get_quantize_value(self):
        """Get quantize value"""
        quantize_map = {"None": 0, "1/16": 0.25, "1/8": 0.5, "1/4": 1.0}
        return quantize_map.get(self.quantize_choice.GetStringSelection(), 1.0)

    def snap_to_scale(self, midi_note):
        """Snap MIDI note to current scale"""
        key_root = self.key_choice.GetSelection()
        scale_name = self.scale_choice.GetStringSelection()

        if scale_name not in self.scales:
            return midi_note

        scale_notes = self.scales[scale_name]

        # Find closest note in scale
        note_in_octave = (midi_note - key_root) % 12

        closest_distance = float('inf')
        closest_note = note_in_octave

        for scale_note in scale_notes:
            distance = abs(note_in_octave - scale_note)
            if distance < closest_distance:
                closest_distance = distance
                closest_note = scale_note

        # Calculate the snapped MIDI note
        octave_offset = (midi_note - key_root) // 12
        snapped_note = key_root + octave_offset * 12 + closest_note

        return snapped_note

    def on_track_selected(self, event):
        """Handle track selection"""
        selection = self.tracks_list.GetSelection()
        if 0 <= selection < len(self.project.tracks):
            self.current_track = self.project.tracks[selection]
            self.update_piano_roll()

    def on_add_track(self, event):
        """Add new track"""
        track_name = f"Track {len(self.project.tracks) + 1}"
        track = Track(track_name)
        self.project.add_track(track)
        self.current_track = track
        self.update_tracks_list()
        self.update_piano_roll()

    def on_remove_track(self, event):
        """Remove selected track"""
        if self.current_track and len(self.project.tracks) > 1:
            self.project.remove_track(self.current_track)
            self.current_track = self.project.tracks[
                0] if self.project.tracks else None
            self.update_tracks_list()
            self.update_piano_roll()

    def on_play(self, event):
        """Start playback"""
        if not self.is_playing:
            self.is_playing = True
            self.play_btn.SetLabel("⏸ Pause")
            self.playback_position = 0

            # Start playback thread
            self.playback_thread = threading.Thread(target=self.playback_loop,
                                                    daemon=True)
            self.playback_thread.start()

            self.status_bar.SetStatusText("Playing...")
        else:
            self.is_playing = False
            self.play_btn.SetLabel("▶ Play")
            self.status_bar.SetStatusText("Paused")

    def on_stop(self, event):
        """Stop playback"""
        self.is_playing = False
        self.playback_position = 0
        self.play_btn.SetLabel("▶ Play")
        self.update_piano_roll()
        self.status_bar.SetStatusText("Stopped")

    def on_record(self, event):
        """Toggle recording mode"""
        # Placeholder for recording functionality
        wx.MessageBox("Recording functionality would be implemented here.",
                      "Record", wx.OK | wx.ICON_INFORMATION)

    def on_tempo_changed(self, event):
        """Handle tempo change"""
        self.project.tempo = self.tempo_ctrl.GetValue()

    def playback_loop(self):
        """Playback loop thread"""
        beats_per_minute = self.project.tempo
        beats_per_second = beats_per_minute / 60.0
        time_per_beat = 1.0 / beats_per_second

        max_beats = self.project.length * self.project.time_signature[0]

        while self.is_playing and self.playback_position < max_beats:
            # Update position display
            measures = int(
                self.playback_position // self.project.time_signature[0]) + 1
            beats = int(
                self.playback_position % self.project.time_signature[0]) + 1
            ticks = int(
                (self.playback_position % 1) * 480)  # 480 ticks per beat

            wx.CallAfter(self.position_text.SetLabel,
                         f"{measures}:{beats}:{ticks}")
            # Removed frequent piano roll updates to prevent GUI hang

            # Play notes (simplified - would need proper audio implementation)
            if self.audio_enabled:
                self.play_notes_at_position(self.playback_position)

            # Advance position
            self.playback_position += 0.1  # 0.1 beat increments

            time.sleep(time_per_beat * 0.1)

        if self.is_playing:
            wx.CallAfter(self.on_stop, None)

    def play_notes_at_position(self, position):
        """Play notes at current position"""
        if not self.audio_enabled or not self.current_track:
            return
            
        # Find notes that should be playing at this position
        active_notes = []
        for note in self.current_track.notes:
            note_start = note.start_time
            note_end = note.start_time + note.duration
            
            # Check if note is active at current position
            if note_start <= position < note_end:
                active_notes.append(note)
        
        # Play active notes
        for note in active_notes:
            self.play_midi_note(note.pitch, note.velocity)
    
    def play_midi_note(self, midi_note, velocity=80):
        """Generate and play audio for a MIDI note"""
        if not self.audio_enabled:
            return
            
        try:
            # Convert MIDI note to frequency
            frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
            
            # Generate audio data
            sample_rate = 22050
            duration = 0.1  # Short note duration for playback
            volume = min(velocity / 127.0 * 0.3, 0.3)  # Keep volume reasonable
            
            # Generate sine wave
            samples = int(sample_rate * duration)
            wave_array = np.zeros((samples, 2))
            
            for i in range(samples):
                time_point = float(i) / sample_rate
                wave_value = volume * np.sin(frequency * 2 * np.pi * time_point)
                wave_array[i][0] = wave_value  # Left channel
                wave_array[i][1] = wave_value  # Right channel
            
            # Convert to integers for pygame
            wave_array = (wave_array * 32767).astype(np.int16)
            
            # Play the sound
            sound = pygame.sndarray.make_sound(wave_array)
            sound.play()
            
        except Exception as e:
            # Fail silently to avoid disrupting playback
            pass

    def on_generate_chords(self, event):
        """Generate chord progression"""
        chord_text = self.chord_text.GetValue()
        chords = [
            chord.strip() for chord in chord_text.split('-') if chord.strip()
        ]

        if not chords or not self.current_track:
            return

        # Clear existing notes
        self.current_track.notes.clear()

        # Generate chord notes
        chord_duration = 4.0  # 4 beats per chord

        for i, chord_name in enumerate(chords):
            start_time = i * chord_duration

            # Simple chord generation (would be more sophisticated in real implementation)
            root_note = self.chord_name_to_root(chord_name)

            if 'm' in chord_name.lower():
                # Minor chord
                chord_notes = [root_note, root_note + 3, root_note + 7]
            else:
                # Major chord
                chord_notes = [root_note, root_note + 4, root_note + 7]

            for note_pitch in chord_notes:
                note = Note(note_pitch, chord_duration, start_time, 70)
                self.current_track.add_note(note)

        self.update_piano_roll()
        self.status_bar.SetStatusText("Generated chord progression")

    def chord_name_to_root(self, chord_name):
        """Convert chord name to root note MIDI number"""
        # Simple mapping (would be more sophisticated in real implementation)
        note_map = {
            'C': 60,
            'D': 62,
            'E': 64,
            'F': 65,
            'G': 67,
            'A': 69,
            'B': 71,
            'Cm': 60,
            'Dm': 62,
            'Em': 64,
            'Fm': 65,
            'Gm': 67,
            'Am': 69,
            'Bm': 71
        }

        return note_map.get(chord_name, 60)

    def on_apply_rhythm(self, event):
        """Apply rhythm pattern"""
        rhythm_name = self.rhythm_choice.GetStringSelection()

        if not self.current_track:
            return

        # Simple rhythm patterns
        if rhythm_name == "4/4 Basic":
            pattern = [0, 1, 2, 3]  # Quarter notes
        elif rhythm_name == "4/4 Rock":
            pattern = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]  # Eighth notes
        elif rhythm_name == "3/4 Waltz":
            pattern = [0, 1, 2]  # Three quarter notes
        else:
            return

        # Apply pattern to existing notes or create new ones
        if not self.current_track.notes:
            # Create new notes
            base_pitch = 60  # C4
            for beat in pattern:
                note = Note(base_pitch, 0.5, beat, 80)
                self.current_track.add_note(note)
        else:
            # Quantize existing notes to pattern
            for note in self.current_track.notes:
                closest_beat = min(pattern,
                                   key=lambda x: abs(x - note.start_time))
                note.start_time = closest_beat

        self.update_piano_roll()
        self.status_bar.SetStatusText(f"Applied {rhythm_name} rhythm")

    def on_new_pattern(self, event):
        """Create new pattern"""
        # Placeholder for pattern creation
        wx.MessageBox("Pattern creation would be implemented here.",
                      "New Pattern", wx.OK | wx.ICON_INFORMATION)

    def on_load_pattern(self, event):
        """Load existing pattern"""
        # Placeholder for pattern loading
        wx.MessageBox("Pattern loading would be implemented here.",
                      "Load Pattern", wx.OK | wx.ICON_INFORMATION)

    def on_new_project(self, event):
        """Create new project"""
        self.project = MusicProject()
        self.current_track = None
        self.create_default_track()

    def on_open_project(self, event):
        """Open project file"""
        wildcard = "Music Maker projects (*.mmp)|*.mmp|All files (*.*)|*.*"
        with wx.FileDialog(self,
                           "Open project",
                           wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.load_project(dialog.GetPath())

    def on_save_project(self, event):
        """Save project file"""
        wildcard = "Music Maker projects (*.mmp)|*.mmp"
        with wx.FileDialog(self,
                           "Save project",
                           wildcard=wildcard,
                           style=wx.FD_SAVE
                           | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.save_project(dialog.GetPath())

    def load_project(self, filepath):
        """Load project from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Load project data
            self.project = MusicProject()
            self.project.tempo = data.get('tempo', 120)
            self.project.time_signature = tuple(
                data.get('time_signature', [4, 4]))
            self.project.key = data.get('key', 'C')
            self.project.length = data.get('length', 16)
            self.project.project_name = data.get('name', 'Untitled')

            # Load tracks
            for track_data in data.get('tracks', []):
                track = Track(track_data['name'],
                              track_data.get('instrument', 0))
                track.volume = track_data.get('volume', 80)

                # Load notes
                for note_data in track_data.get('notes', []):
                    note = Note(note_data['pitch'], note_data['duration'],
                                note_data['start_time'],
                                note_data.get('velocity', 80))
                    track.add_note(note)

                self.project.add_track(track)

            if self.project.tracks:
                self.current_track = self.project.tracks[0]
            else:
                self.create_default_track()

            self.tempo_ctrl.SetValue(self.project.tempo)
            self.update_tracks_list()
            self.update_piano_roll()

            self.status_bar.SetStatusText(
                f"Loaded: {os.path.basename(filepath)}")

        except Exception as e:
            wx.MessageBox(f"Error loading project: {str(e)}", "Load Error",
                          wx.OK | wx.ICON_ERROR)

    def save_project(self, filepath):
        """Save project to file"""
        try:
            data = {
                'name': self.project.project_name,
                'tempo': self.project.tempo,
                'time_signature': list(self.project.time_signature),
                'key': self.project.key,
                'length': self.project.length,
                'tracks': []
            }

            for track in self.project.tracks:
                track_data = {
                    'name': track.name,
                    'instrument': track.instrument,
                    'volume': track.volume,
                    'notes': []
                }

                for note in track.notes:
                    note_data = {
                        'pitch': note.pitch,
                        'duration': note.duration,
                        'start_time': note.start_time,
                        'velocity': note.velocity
                    }
                    track_data['notes'].append(note_data)

                data['tracks'].append(track_data)

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            self.status_bar.SetStatusText(
                f"Saved: {os.path.basename(filepath)}")

        except Exception as e:
            wx.MessageBox(f"Error saving project: {str(e)}", "Save Error",
                          wx.OK | wx.ICON_ERROR)

    def on_exit(self, event):
        """Exit application"""
        if self.is_playing:
            self.on_stop(event)
        self.Close()


class MusicMakerApp(wx.App):

    def OnInit(self):
        frame = MusicMakerFrame()
        frame.Show()
        return True


def main():
    """
    Main entry point for the Music Maker application.
    
    Creates and runs the Music Maker wxPython application.
    """
    app = MusicMakerApp()
    app.MainLoop()


if __name__ == "__main__":
    main()
