#!/bin/bash
# Build script for Music Visualizer

set -e

echo "🔧 Building Music Visualizer..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Install build dependencies
echo "📦 Installing build dependencies..."
python3 -m pip install --upgrade build twine

# Build the package
echo "🏗️  Building package..."
python3 -m build

# Check the distribution
echo "✅ Checking package..."
python3 -m twine check dist/*

echo "🎉 Build complete! Files created:"
ls -la dist/

echo ""
echo "📋 Next steps:"
echo "1. Test installation: pip install dist/*.whl"
echo "2. Test the application: music-visualizer"
echo "3. Upload to TestPyPI: python3 -m twine upload --repository testpypi dist/*"
echo "4. Upload to PyPI: python3 -m twine upload dist/*" 