#!/bin/bash
# Upload script for Requirements to Test Generator

set -e

if [ ! -d "dist" ]; then
    echo "❌ No dist/ directory found. Run build.sh first."
    exit 1
fi

if [ -z "$(ls -A dist/)" ]; then
    echo "❌ No files in dist/ directory. Run build.sh first."
    exit 1
fi

echo "🚀 Uploading Requirements to Test Generator to PyPI..."

# Check if we should upload to TestPyPI first
read -p "🤔 Upload to TestPyPI first? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Uploading to TestPyPI..."
    python3 -m twine upload --repository testpypi dist/*
    
    echo "✅ Uploaded to TestPyPI!"
    echo "🔗 Check your package at: https://test.pypi.org/project/requirements-to-test/"
    echo ""
    echo "🧪 Test installation with:"
    echo "pip install --index-url https://test.pypi.org/simple/ requirements-to-test"
    echo ""
    
    read -p "Continue with PyPI upload? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Upload cancelled."
        exit 0
    fi
fi

echo "📤 Uploading to PyPI..."
python3 -m twine upload dist/*

echo "🎉 Successfully uploaded to PyPI!"
echo "🔗 Check your package at: https://pypi.org/project/requirements-to-test/"
echo ""
echo "📦 Users can now install with:"
echo "pip install requirements-to-test" 