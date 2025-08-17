#!/usr/bin/env python3
"""
Setup script for Music Visualizer.
"""

import os
from pathlib import Path
from setuptools import setup, find_packages

# Read the contents of README file
this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding='utf-8')
except FileNotFoundError:
    long_description = "A wxPython-based music visualization application with real-time audio analysis and multiple visualization modes."


# Read requirements
def read_requirements(filename):
    """Read requirements from file."""

    requirements_file = this_directory / filename
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = []
            for line in f:
                line = line.strip()
                # Skip empty lines, comments, and -r references
                if line and not line.startswith('#') and not line.startswith('-r'):
                    requirements.append(line)
            return requirements
    return []


# Read version from the package __init__.py in src layout
def get_version():
    """Extract version from src/music_visualizer/__init__.py."""
    version_file = this_directory / "src" / "music_visualizer" / "__init__.py"
    if version_file.exists():
        import re
        content = version_file.read_text(encoding='utf-8')
        version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]*)['\"]", content)
        if version_match:
            return version_match.group(1)
    return "1.0.0"

setup(
    name="music-visualizer",
    version=get_version(),
    author="Music Visualizer Developer",
    author_email="developer@musicvisualizer.com",
    description="A wxPython-based music visualization application with real-time audio analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/music-visualizer",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/music-visualizer/issues",
        "Source": "https://github.com/yourusername/music-visualizer",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=[],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords="music audio visualizer gui wxpython matplotlib spectrum waveform",
    python_requires=">=3.8",
    install_requires=[
        "wxPython>=4.2.0",
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
        "pygame>=2.1.0",
    ],
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "audio": ["librosa>=0.9.0", "soundfile>=0.10.0"],
    },
    entry_points={
        "console_scripts": [
            # Console launcher that starts the GUI
            "music-visualizer=music_visualizer:main",
        ],
        "gui_scripts": [
            # Native GUI entry point (on Windows it hides the console)
            "music-visualizer-gui=music_visualizer:main",
        ],
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
) 