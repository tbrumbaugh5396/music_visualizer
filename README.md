# 🎵 Music Visualizer

A cross-platform music visualization application built with wxPython that provides real-time audio analysis and stunning visual effects.

## ✨ Features

### 🎧 Audio Support
- **Multiple Formats**: MP3, WAV, OGG, FLAC, M4A
- **Real-time Playback**: Integrated audio player with volume control
- **Playlist Management**: Load individual files or entire folders
- **Audio Analysis**: Real-time spectrum analysis and waveform generation

### 🌈 Visualization Modes
- **Spectrum Analyzer**: Frequency domain visualization with customizable colors
- **Waveform Display**: Time domain audio representation
- **Bar Visualizer**: Classic spectrum bars with glow effects
- **Circular Spectrum**: Unique radial frequency display

### 🎨 Customization
- **Color Themes**: Multiple color schemes (cyan, magenta, yellow, lime)
- **Dynamic Switching**: Change visualizations on-the-fly
- **Responsive Design**: Adapts to different window sizes
- **Modern UI**: Clean, intuitive interface with dark theme

### 🎮 Playback Controls
- **Standard Controls**: Play, pause, stop, seek
- **Volume Control**: Adjustable audio levels
- **Progress Tracking**: Visual progress bar with time display
- **Playlist Navigation**: Easy track switching

## 🚀 Quick Start

### Installation

#### Option 1: Install from Package
```bash
pip install music-visualizer
music-visualizer
```

#### Option 2: Run from Source
```bash
git clone https://github.com/yourusername/music-visualizer.git
cd music-visualizer
pip install -r requirements.txt
python -m music_visualizer
```

#### Option 3: Development Install
```bash
git clone https://github.com/yourusername/music-visualizer.git
cd music-visualizer
pip install -e .
music-visualizer
```

### macOS App Bundle
Create a native macOS application:
```bash
python scripts/create_app_bundle.py
# Double-click "Music Visualizer.app" to launch
```

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Audio Hardware**: Sound card with speakers/headphones

### Python Dependencies
- `wxPython >= 4.2.0` - GUI framework
- `matplotlib >= 3.5.0` - Visualization rendering
- `numpy >= 1.21.0, < 2.0` - Numerical processing
- `pygame >= 2.1.0` - Audio playback

### Optional Dependencies
- `librosa >= 0.9.0` - Advanced audio analysis
- `soundfile >= 0.10.0` - Additional audio format support

Install optional dependencies:
```bash
pip install music-visualizer[audio]
```

## 🎮 Usage

### Basic Usage
1. **Launch the application**:
   ```bash
   python -m music_visualizer
   ```

2. **Load audio files**:
   - Click "Open File" to load a single track
   - Click "Open Folder" to load an entire directory
   - Drag and drop files onto the playlist

3. **Control playback**:
   - Use play/pause/stop buttons
   - Adjust volume with the slider
   - Seek through tracks with the progress bar

4. **Customize visualization**:
   - Select visualization type from dropdown
   - Click "Colors" to cycle through themes
   - Resize window for different views

### Advanced Usage

#### Command Line Options
```bash
# Run with specific audio file
python -m music_visualizer /path/to/music.mp3

# Run in fullscreen mode
python -m music_visualizer --fullscreen

# Set default visualization
python -m music_visualizer --viz spectrum
```

#### Scripting
```python
from music_visualizer import MusicVisualizerApp
import wx

# Create and run the application
app = MusicVisualizerApp()
app.MainLoop()
```

## 🛠️ Development

### Setting Up Development Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/music-visualizer.git
cd music-visualizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Code formatting
black src/
flake8 src/
```

### Project Structure
```
music-visualizer/
├── src/
│   └── music_visualizer/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Module entry point
│       └── music_visualizer.py  # Main application
├── scripts/
│   ├── build.sh                 # Build script
│   ├── create_app_bundle.py     # macOS app creator
│   └── create_icon.py           # Icon generator
├── tests/                       # Test suite
├── icons/                       # Application icons
├── requirements.txt             # Dependencies
├── setup.py                     # Package setup
├── pyproject.toml              # Modern package config
└── README.md                   # This file
```

### Building Distribution
```bash
# Build wheel and source distribution
python -m build

# Check distribution
python -m twine check dist/*

# Upload to PyPI (maintainers only)
python -m twine upload dist/*
```

### Creating Icons
Generate application icons:
```bash
python scripts/create_icon.py
```

## 🎨 Visualization Details

### Spectrum Analyzer
- **Real-time FFT**: Fast Fourier Transform for frequency analysis
- **Frequency Range**: 0-22kHz visualization
- **Color Mapping**: Amplitude-based color gradients
- **Smoothing**: Temporal smoothing for fluid animation

### Waveform Display
- **Time Domain**: Raw audio signal visualization
- **Multiple Harmonics**: Complex waveform rendering
- **Real-time Updates**: 50ms refresh rate
- **Anti-aliasing**: Smooth line rendering

### Bar Visualizer
- **32 Frequency Bands**: Logarithmic frequency distribution
- **Glow Effects**: Enhanced visual appeal
- **Dynamic Scaling**: Auto-adjusting amplitude range
- **Responsive Bars**: Variable height based on audio content

### Circular Spectrum
- **Radial Layout**: 360-degree frequency display
- **64 Data Points**: High-resolution circular visualization
- **Center Focus**: Amplitude-based radius scaling
- **Smooth Animation**: Interpolated transitions

## 🔧 Configuration

### Audio Settings
```python
# In music_visualizer.py, modify AudioVisualizer class
pygame.mixer.init(
    frequency=22050,  # Sample rate
    size=-16,         # 16-bit signed samples
    channels=2,       # Stereo
    buffer=1024       # Buffer size
)
```

### Visualization Settings
```python
# Update rate (milliseconds)
REFRESH_RATE = 50

# Spectrum analyzer bins
SPECTRUM_BINS = 256

# Color schemes
COLORS = ['cyan', 'magenta', 'yellow', 'lime']
```

## 🐛 Troubleshooting

### Common Issues

#### GUI Window Not Appearing
- **macOS**: Check Dock and Mission Control
- **Windows**: Check taskbar and system tray
- **Linux**: Verify X11 forwarding if using SSH

#### Audio Playback Issues
- **No Sound**: Check system volume and audio device
- **Format Errors**: Install additional codecs or use supported formats
- **Pygame Errors**: Reinstall pygame: `pip install --force-reinstall pygame`

#### Dependencies
- **wxPython Install Issues**: Check [wxPython installation guide](https://wxpython.org/pages/downloads/)
- **Matplotlib Problems**: Ensure compatible backend: `pip install --upgrade matplotlib`
- **Numpy Compatibility**: Use version < 2.0 for matplotlib compatibility

### Debug Mode
Run with debug output:
```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG); exec(open('src/music_visualizer/music_visualizer.py').read())"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Submit a pull request

### Code Style
- **Formatting**: Black with 88-character line length
- **Linting**: Flake8 for style checking
- **Type Hints**: Encouraged for new code
- **Documentation**: Docstrings for all public functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **wxPython**: Cross-platform GUI toolkit
- **Matplotlib**: Powerful visualization library
- **Pygame**: Multimedia and audio support
- **NumPy**: Numerical computing foundation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/music-visualizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/music-visualizer/discussions)
- **Email**: developer@musicvisualizer.com

## 🚀 Future Plans

- [ ] Real-time microphone input visualization
- [ ] Plugin system for custom visualizations
- [ ] Web-based remote control interface
- [ ] MIDI controller support
- [ ] Recording and export functionality
- [ ] Advanced audio effects processing
- [ ] Virtual reality visualization mode

---

**Made with ❤️ by the Music Visualizer Team**

*Transform your music into visual art!* 🎨🎵
